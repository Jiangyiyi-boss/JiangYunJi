from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from database import get_db
from config import settings
from alipay import AliPay
from crud.orders import get_order_by_id, pay_order
from crud.services import get_custom_order_by_id, pay_custom_order
from dependencies import get_current_user
from models import User, Order, CustomOrder, OrderItem
from urllib.parse import urlencode
import logging
import time
from datetime import datetime, timezone


def format_payment_started_at(dt):
    """将 naive UTC datetime 格式化为带时区的 ISO 字符串，避免前端时区解析错误"""
    if not dt:
        return None
    return dt.replace(tzinfo=timezone.utc).isoformat()

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/payment", tags=["支付"])


def _sync_course_after_pay(db: Session, order) -> None:
    """课程订单支付成功后，把最新报名人数同步到 ES（失败不影响支付流程）"""
    if not order or getattr(order, "goods_type", None) != 2:
        return
    try:
        from utils.es_sync_helper import safe_sync_course
        for item in order.items:
            if item.course_id:
                safe_sync_course(db, item.course_id)
    except Exception as e:
        logger.error("同步课程报名数到 ES 异常 order_id=%s: %s", getattr(order, "id", "?"), e)


def get_alipay():
    """创建支付宝实例"""
    with open(settings.ALIPAY_APP_PRIVATE_KEY_PATH, "r") as f:
        app_private_key = f.read()
    with open(settings.ALIPAY_PUBLIC_KEY_PATH, "r") as f:
        alipay_public_key = f.read()

    return AliPay(
        appid=settings.ALIPAY_APP_ID,
        app_notify_url=settings.ALIPAY_NOTIFY_URL,
        app_private_key_string=app_private_key,
        alipay_public_key_string=alipay_public_key,
        sign_type="RSA2",
        debug=settings.ALIPAY_DEBUG,
        verbose=True,
    )


@router.get("/pay/{order_id}")
def create_alipay_payment(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """生成支付宝支付链接"""
    order = get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作此订单")
    if order.status != "pending":
        raise HTTPException(status_code=400, detail="订单状态不正确，无法支付")

    # 记录支付开始时间（仅首次进入支付页时设置，避免重复发布延时消息）
    if not order.payment_started_at:
        order.payment_started_at = datetime.now()
        db.commit()

        # 发布延时消息（10 分钟后自动取消未支付订单）
        try:
            from rabbitmq import publish_delay
            delay_type = "course" if order.goods_type == 2 else "product"
            publish_delay(order_id, order_type=delay_type)
        except Exception:
            pass

    alipay = get_alipay()

    # 预下单：返回二维码链接 qr_code
    result = alipay.api_alipay_trade_precreate(
        out_trade_no=order.order_no,
        total_amount=str(float(order.pay_amount)),
        subject=f"匠韵集-{order.order_no}",
        notify_url=settings.ALIPAY_NOTIFY_URL,
    )

    if result.get("code") != "10000":
        logger.error(f"Alipay precreate failed: {result}")
        raise HTTPException(status_code=500, detail=f"支付宝预下单失败: {result.get('sub_msg', '未知错误')}")

    qr_code = result.get("qr_code", "")
    logger.info(f"Payment QR generated: order_no={order.order_no}, amount={order.pay_amount}")

    return {"qr_code": qr_code, "order_no": order.order_no, "amount": str(float(order.pay_amount))}


@router.post("/notify")
async def alipay_notify(request: Request, db: Session = Depends(get_db)):
    """支付宝异步通知回调"""
    # 记录原始请求信息
    logger.info(f"========== Alipay notify received ==========")
    logger.info(f"Client: {request.client}")
    logger.info(f"Method: {request.method}")
    logger.info(f"URL: {request.url}")

    form_data = await request.form()
    data = dict(form_data)

    # 脱敏日志（隐藏签名部分）
    safe_data = {k: v for k, v in data.items() if k != "sign"}
    logger.info(f"Notify params (without sign): {safe_data}")
    logger.info(f"Sign present: {'sign' in data}, sign_type: {data.get('sign_type', 'N/A')}")

    alipay = get_alipay()

    # 验证签名
    signature = data.pop("sign", "")
    sign_type = data.pop("sign_type", "")
    verified = alipay.verify(data, signature)

    logger.info(f"Signature verification: {'PASSED' if verified else 'FAILED'}")
    logger.info(f"trade_status: {data.get('trade_status')}, out_trade_no: {data.get('out_trade_no')}, trade_no: {data.get('trade_no')}")
    logger.info(f"total_amount: {data.get('total_amount')}, seller_id: {data.get('seller_id')}, app_id: {data.get('app_id')}")

    if verified and data.get("trade_status") in ("TRADE_SUCCESS", "TRADE_FINISHED"):
        order_no = data.get("out_trade_no")
        trade_no = data.get("trade_no")
        logger.info(f"Processing payment for order_no={order_no}, trade_no={trade_no}")

        # 检查是否为定制订单支付（以CUSTOM开头）
        if order_no and order_no.startswith("CUSTOM"):
            custom_id = int(order_no.split("-")[1])
            order = db.query(CustomOrder).filter(CustomOrder.id == custom_id).first()
            if order and order.pay_status == "unpaid" and order.status == "accepted":
                try:
                    pay_custom_order(db, order.id, order.user_id)
                    logger.info(f"Custom order {order_no} paid successfully via notify")
                except Exception as e:
                    logger.error(f"Failed to process custom payment for {order_no}: {e}", exc_info=True)
                    db.rollback()
                    return "fail"
            return "success"

        # 普通订单支付
        # 根据订单号查找订单
        order = db.query(Order).filter(Order.order_no == order_no).first()
        if order is None:
            logger.warning(f"Order {order_no} NOT FOUND in database")
            return "fail"

        logger.info(f"Found order: id={order.id}, status={order.status}, amount={order.pay_amount}")

        if order.status == "pending":
            try:
                pay_order(db, order.id, "alipay")
                # pay_order already commits, no need to commit again
                # 课程订单：报名已激活，同步 ES 报名人数
                _sync_course_after_pay(db, order)
                logger.info(f"Order {order_no} paid successfully via notify")
            except Exception as e:
                logger.error(f"Failed to process payment for order {order_no}: {e}", exc_info=True)
                db.rollback()
                return "fail"
        else:
            logger.info(f"Order {order_no} already processed, status={order.status}")
    else:
        logger.warning(f"Notify rejected: verified={verified}, trade_status={data.get('trade_status')}")
        if not verified:
            logger.error(f"Signature mismatch! Check RSA keys. Sign type: {sign_type}")

    # 支付宝要求返回纯文本 "success"
    return "success"


@router.get("/callback")
def alipay_return_callback(
    request: Request,
    db: Session = Depends(get_db),
):
    """支付宝同步回调 — 支付成功后浏览器跳转回来
    后端先验签 → 更新订单状态 → 再重定向到前端页面
    这样即使异步通知没到达，订单也能在用户跳回时更新
    """
    params = dict(request.query_params)
    logger.info(f"========== Alipay return callback (sync) ==========")
    logger.info(f"Return params: {params}")

    alipay = get_alipay()

    # 提取签名并验签
    signature = params.pop("sign", "")
    sign_type = params.pop("sign_type", "")
    verified = alipay.verify(params, signature)

    logger.info(f"Return signature verification: {'PASSED' if verified else 'FAILED'}")

    out_trade_no = params.get("out_trade_no", "")
    total_amount = params.get("total_amount", "")
    trade_no = params.get("trade_no", "")
    trade_status = params.get("trade_status", "")

    # 验签通过且交易成功 → 更新订单状态
    if verified and trade_status in ("TRADE_SUCCESS", "TRADE_FINISHED"):
        logger.info(f"Return callback: trade success for {out_trade_no}, updating order...")

        # 定制订单
        if out_trade_no.startswith("CUSTOM"):
            custom_id = int(out_trade_no.split("-")[1])
            order = db.query(CustomOrder).filter(CustomOrder.id == custom_id).first()
            if order and order.pay_status == "unpaid" and order.status == "accepted":
                try:
                    pay_custom_order(db, order.id, order.user_id)
                    logger.info(f"Custom order {out_trade_no} PAID via return callback")
                except Exception as e:
                    logger.error(f"Return callback pay_custom_order failed: {e}", exc_info=True)
                    db.rollback()
            elif order:
                logger.info(f"Custom order {out_trade_no} status already: {order.status}")
            else:
                logger.warning(f"Custom order {out_trade_no} NOT FOUND in DB")
        else:
            # 普通订单
            order = db.query(Order).filter(Order.order_no == out_trade_no).first()
            if order and order.status == "pending":
                try:
                    pay_order(db, order.id, "alipay")
                    # 课程订单：报名已激活，同步 ES 报名人数
                    _sync_course_after_pay(db, order)
                    logger.info(f"Order {out_trade_no} PAID via return callback")
                except Exception as e:
                    logger.error(f"Return callback pay_order failed: {e}", exc_info=True)
                    db.rollback()
            elif order:
                logger.info(f"Order {out_trade_no} status already: {order.status}")
            else:
                logger.warning(f"Order {out_trade_no} NOT FOUND in DB")
    else:
        logger.warning(
            f"Return callback NOT updating order: verified={verified}, trade_status={trade_status}"
        )

    # 重定向到前端回调页（带关键参数，无需登录）
    frontend_params = urlencode({
        "out_trade_no": out_trade_no,
        "total_amount": total_amount,
        "trade_no": trade_no,
    })
    redirect_url = f"/pay/callback?{frontend_params}"
    logger.info(f"Redirecting to frontend: {redirect_url}")

    return RedirectResponse(url=redirect_url, status_code=302)


@router.get("/query/{order_id}")
def query_payment_status(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """查询订单支付状态（需要登录）"""
    order = get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权查看此订单")

    return {
        "order_id": order.id,
        "order_no": order.order_no,
        "status": order.status,
        "pay_amount": str(float(order.pay_amount)),
        "goods_type": order.goods_type,
        "payment_started_at": format_payment_started_at(order.payment_started_at),
    }


@router.get("/status-by-no/{order_no}")
def query_payment_status_by_no(
    order_no: str,
    db: Session = Depends(get_db),
):
    """通过订单号查询支付状态（无需登录，供支付宝同步回调页使用）"""
    # 先查定制订单
    if order_no.startswith("CUSTOM"):
        order = db.query(CustomOrder).filter(CustomOrder.order_no == order_no).first()
        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")
        return {
            "order_id": order.id,
            "order_no": order.order_no,
            "status": order.status,
            "pay_amount": str(float(order.quote_amount or 0)),
            "pay_status": order.pay_status,
            "goods_type": "custom",
        }

    # 普通订单
    order = db.query(Order).filter(Order.order_no == order_no).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    return {
        "order_id": order.id,
        "order_no": order.order_no,
        "status": order.status,
        "pay_amount": str(float(order.pay_amount)),
        "goods_type": order.goods_type,
    }


# ==================== 定制订单支付 ====================

@router.get("/custom-pay/{order_id}")
def create_custom_alipay_payment(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """生成定制订单支付宝支付链接"""
    order = get_custom_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="定制订单不存在")
    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作此订单")
    if order.status != "accepted":
        raise HTTPException(status_code=400, detail="订单状态不正确，需要商家报价且用户接受后才能支付")
    if not order.quote_amount:
        raise HTTPException(status_code=400, detail="商家尚未报价，无法支付")

    # 生成订单号
    if not order.order_no:
        order.order_no = f"CUSTOM-{order_id}-{int(time.time())}"
        db.commit()

    # 记录/重置支付开始时间：首次进入或已过期时重新计时，支持重新支付
    ttl_seconds = settings.RABBITMQ_PAYMENT_TTL_MS / 1000
    is_expired = order.payment_started_at and (
        (datetime.now() - order.payment_started_at).total_seconds() > ttl_seconds
    )
    if not order.payment_started_at or is_expired:
        order.payment_started_at = datetime.now()
        db.commit()

    alipay = get_alipay()
    result = alipay.api_alipay_trade_precreate(
        out_trade_no=order.order_no,
        total_amount=str(float(order.quote_amount)),
        subject=f"匠韵集-定制服务-{order.order_no}",
        notify_url=settings.ALIPAY_NOTIFY_URL,
    )

    if result.get("code") != "10000":
        logger.error(f"Alipay precreate failed (custom): {result}")
        raise HTTPException(status_code=500, detail=f"支付宝预下单失败: {result.get('sub_msg', '未知错误')}")

    qr_code = result.get("qr_code", "")
    logger.info(f"Custom payment QR generated: order_no={order.order_no}, amount={order.quote_amount}")

    return {"qr_code": qr_code, "order_no": order.order_no, "amount": str(float(order.quote_amount))}


@router.get("/custom-query/{order_id}")
def query_custom_payment_status(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """查询定制订单支付状态"""
    order = get_custom_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="定制订单不存在")
    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权查看此订单")

    return {
        "order_id": order.id,
        "order_no": order.order_no,
        "status": order.status,
        "pay_amount": str(float(order.quote_amount or 0)),
        "pay_status": order.pay_status,
        "goods_type": "custom",
        "payment_started_at": format_payment_started_at(order.payment_started_at),
    }


# ==================== 课程支付 ====================

@router.get("/course-pay/{course_id}")
def create_course_alipay_payment(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """生成课程购买支付宝支付链接"""
    from crud.orders import create_course_order, get_order_by_id

    # 查找是否有未支付的课程订单（复用）
    existing_order = db.query(Order).filter(
        Order.user_id == current_user.id,
        Order.goods_type == 2,
        Order.status == "pending",
    ).join(OrderItem, OrderItem.order_id == Order.id).filter(
        OrderItem.course_id == course_id,
    ).first()

    if existing_order:
        order = existing_order
        # 重置支付开始时间，给用户新的支付窗口
        order.payment_started_at = None
        db.commit()
    else:
        try:
            order = create_course_order(db, current_user, course_id)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    # 记录支付开始时间（课程订单复用时会先重置为 None，因此这里会重新设置并发布延时消息）
    if not order.payment_started_at:
        order.payment_started_at = datetime.now()
        db.commit()

        # 发布延时消息
        try:
            from rabbitmq import publish_delay
            publish_delay(order.id, order_type="course")
        except Exception:
            pass

    alipay = get_alipay()
    result = alipay.api_alipay_trade_precreate(
        out_trade_no=order.order_no,
        total_amount=str(float(order.pay_amount)),
        subject=f"匠韵集-课程-{order.order_no}",
        notify_url=settings.ALIPAY_NOTIFY_URL,
    )

    if result.get("code") != "10000":
        logger.error(f"Alipay precreate failed (course): {result}")
        raise HTTPException(status_code=500, detail=f"支付宝预下单失败: {result.get('sub_msg', '未知错误')}")

    qr_code = result.get("qr_code", "")
    logger.info(f"Course payment QR generated: order_no={order.order_no}, amount={order.pay_amount}")

    return {"qr_code": qr_code, "order_no": order.order_no, "amount": str(float(order.pay_amount))}


# ==================== 支付倒计时 ====================

@router.get("/remaining-time/{order_id}")
def get_payment_remaining_time(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """查询商品/课程订单的剩余支付时间（秒）"""
    from crud.orders import get_order_by_id

    order = get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    if order.status != "pending":
        return {"remaining_seconds": 0, "expired": True}

    if not order.payment_started_at:
        return {"remaining_seconds": 600, "expired": False}

    elapsed = (datetime.now() - order.payment_started_at).total_seconds()
    ttl = settings.RABBITMQ_PAYMENT_TTL_MS / 1000
    remaining = max(0, int(ttl - elapsed))

    return {
        "remaining_seconds": remaining,
        "expired": remaining <= 0,
        "payment_started_at": format_payment_started_at(order.payment_started_at),
    }


@router.get("/custom-remaining-time/{order_id}")
def get_custom_payment_remaining_time(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """查询定制订单的剩余支付时间（秒）"""
    from crud.services import get_custom_order_by_id

    order = get_custom_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="定制订单不存在")

    if order.status != "accepted" or order.pay_status == "paid":
        return {"remaining_seconds": 0, "expired": True}

    if not order.payment_started_at:
        return {"remaining_seconds": 600, "expired": False}

    elapsed = (datetime.now() - order.payment_started_at).total_seconds()
    ttl = settings.RABBITMQ_PAYMENT_TTL_MS / 1000
    remaining = max(0, int(ttl - elapsed))

    return {
        "remaining_seconds": remaining,
        "expired": remaining <= 0,
        "payment_started_at": format_payment_started_at(order.payment_started_at),
    }
