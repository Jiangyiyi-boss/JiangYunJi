from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from models import Order, OrderItem, Product, Address, User, Artisan, Transaction, Enrollment, CommissionAppeal
from schemas import OrderCreate
from utils.lock import product_stock_locks
from datetime import datetime
from decimal import Decimal
import uuid


def generate_order_no() -> str:
    return datetime.now().strftime("%Y%m%d%H%M%S") + uuid.uuid4().hex[:8].upper()


def create_order(db: Session, user: User, data: OrderCreate) -> Order:
    address = db.query(Address).filter(
        Address.id == data.address_id,
        Address.user_id == user.id,
    ).first()
    if not address:
        raise ValueError("地址不存在")

    if not data.items:
        raise ValueError("订单商品不能为空")

    total_amount = 0
    order_items = []

    # 收集涉及的商品 ID，按升序排序后统一加锁，避免并发死锁
    product_ids = sorted({item["product_id"] for item in data.items})

    # Redis 分布式锁 + 数据库 SELECT FOR UPDATE 双重保护，防止超卖
    with product_stock_locks(product_ids, ttl=10, timeout=5):
        for item_data in data.items:
            # 行级锁：同一事务内对该商品行加锁，保证检查与扣减原子化
            product = (
                db.query(Product)
                .filter(Product.id == item_data["product_id"])
                .with_for_update()
                .first()
            )
            if not product:
                raise ValueError(f"商品 {item_data['product_id']} 不存在")
            if product.status != "approved":
                raise ValueError(f"商品 {product.name} 不可购买")

            # 如果有选规格，使用规格价格和库存
            spec_price = float(product.price)
            spec_name = item_data.get("spec_name", "")
            if spec_name and product.specs:
                spec_found = False
                for spec in product.specs:
                    if spec.get("name") == spec_name:
                        spec_price = float(spec.get("price", product.price))
                        if spec.get("stock", 0) < item_data["qty"]:
                            raise ValueError(f"商品 {product.name} 规格 {spec_name} 库存不足")
                        # 扣减规格库存（JSON 字段需标记已修改）
                        spec["stock"] = spec.get("stock", 0) - item_data["qty"]
                        spec_found = True
                        break
                if not spec_found:
                    raise ValueError(f"商品 {product.name} 规格 {spec_name} 不存在")
                flag_modified(product, "specs")

            # Check overall stock
            if product.stock < item_data["qty"]:
                raise ValueError(f"商品 {product.name} 库存不足")

            subtotal = spec_price * item_data["qty"]
            total_amount += subtotal

            # 计算佣金
            commission_rate = float(product.commission_rate) if product.commission_rate else 0.10
            commission_amount = round(subtotal * commission_rate, 2)
            artisan_income = round(subtotal - commission_amount, 2)

            order_items.append({
                "product_id": product.id,
                "product_name": f"{product.name}{' - ' + spec_name if spec_name else ''}",
                "product_image": product.images[0] if product.images else "",
                "price": spec_price,
                "qty": item_data["qty"],
                "subtotal": subtotal,
                "commission_rate": commission_rate,
                "commission_amount": commission_amount,
                "artisan_income": artisan_income,
            })

            # Deduct stock
            product.stock -= item_data["qty"]
            product.sales += item_data["qty"]

    order = Order(
        order_no=generate_order_no(),
        user_id=user.id,
        total_amount=total_amount,
        pay_amount=total_amount,
        status="pending",
        receiver_name=address.name,
        receiver_phone=address.phone,
        receiver_address=f"{address.province}{address.city}{address.district}{address.detail}",
        remark=data.remark,
    )
    db.add(order)
    db.flush()

    for item_data in order_items:
        order_item = OrderItem(
            order_id=order.id,
            **item_data,
        )
        db.add(order_item)

    db.commit()
    db.refresh(order)
    return order


def get_order_by_id(db: Session, order_id: int):
    return db.query(Order).filter(Order.id == order_id).first()


def get_order_by_no(db: Session, order_no: str):
    return db.query(Order).filter(Order.order_no == order_no).first()


def get_user_orders(db: Session, user_id: int, skip: int = 0, limit: int = 20, status: str = None, goods_type: int = None):
    query = db.query(Order).filter(Order.user_id == user_id)
    if status:
        statuses = [s.strip() for s in status.split(",")]
        query = query.filter(Order.status.in_(statuses))
    if goods_type is not None:
        query = query.filter(Order.goods_type == goods_type)
    total = query.count()
    items = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
    return items, total


def get_artisan_orders(db: Session, artisan_id: int, skip: int = 0, limit: int = 20, status: str = None, goods_type: str = None):
    """获取匠人的订单（商品通过Product，课程通过Course）"""
    from models import OrderItem, Product, Course

    if goods_type == 2:
        # 课程订单
        query = (
            db.query(Order)
            .join(OrderItem, OrderItem.order_id == Order.id)
            .join(Course, Course.id == OrderItem.course_id)
            .filter(Course.artisan_id == artisan_id)
            .distinct()
        )
    elif goods_type == 1:
        # 商品订单
        query = (
            db.query(Order)
            .join(OrderItem, OrderItem.order_id == Order.id)
            .join(Product, Product.id == OrderItem.product_id)
            .filter(Product.artisan_id == artisan_id)
            .distinct()
        )
    else:
        # 全部：合并商品和课程订单
        product_ids = (
            db.query(Order.id)
            .join(OrderItem, OrderItem.order_id == Order.id)
            .join(Product, Product.id == OrderItem.product_id)
            .filter(Product.artisan_id == artisan_id)
            .distinct()
        )
        course_ids = (
            db.query(Order.id)
            .join(OrderItem, OrderItem.order_id == Order.id)
            .join(Course, Course.id == OrderItem.course_id)
            .filter(Course.artisan_id == artisan_id)
            .distinct()
        )
        all_ids = [r[0] for r in product_ids.all()] + [r[0] for r in course_ids.all()]
        query = db.query(Order).filter(Order.id.in_(all_ids)) if all_ids else db.query(Order).filter(Order.id == -1)
    
    # 待发货状态只包含商品订单，课程订单不需要发货
    if status and "paid" in [s.strip() for s in status.split(",")]:
        # 排除课程订单（goods_type == 2）
        query = query.filter(Order.goods_type != 2)
    
    if status:
        statuses = [s.strip() for s in status.split(",")]
        query = query.filter(Order.status.in_(statuses))
    if goods_type:
        from models import Order as OrderModel
        query = query.filter(OrderModel.goods_type == goods_type)
    total = query.count()
    items = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
    return items, total


def get_all_orders(db: Session, skip: int = 0, limit: int = 20, status: str = None, keyword: str = None):
    query = db.query(Order)
    if status:
        statuses = [s.strip() for s in status.split(",")]
        query = query.filter(Order.status.in_(statuses))
    if keyword:
        query = query.filter(Order.order_no.contains(keyword))
    total = query.count()
    items = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
    return items, total


def cancel_order(db: Session, order_id: int, user_id: int = None) -> Order:
    order = get_order_by_id(db, order_id)
    if not order:
        raise ValueError("订单不存在")
    if user_id and order.user_id != user_id:
        raise ValueError("无权操作")
    if order.status != "pending":
        raise ValueError("订单状态不允许取消")

    order.status = "cancelled"
    order.cancel_time = datetime.now()

    # Restore stock
    for item in order.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product:
            product.stock += item.qty
            product.sales -= item.qty

    db.commit()
    db.refresh(order)
    return order


def pay_order(db: Session, order_id: int, pay_method: str = "wechat") -> Order:
    order = get_order_by_id(db, order_id)
    if not order:
        raise ValueError("订单不存在")
    if order.status != "pending":
        raise ValueError("订单状态不允许支付")

    order.status = "paid"
    order.pay_method = pay_method
    order.pay_time = datetime.now()
    order.payment_started_at = None

    # 课程订单：直接完成，激活报名
    if order.goods_type == 2:
        order.status = "completed"
        order.complete_time = datetime.now()
        for item in order.items:
            if item.course_id:
                enrollment = db.query(Enrollment).filter(
                    Enrollment.order_id == order_id,
                    Enrollment.type == "purchased",
                ).first()
                if enrollment:
                    enrollment.status = "active"
                    enrollment.enrolled_at = datetime.now()
                # 更新课程所属匠人的 total_sales
                from models import Course
                course = db.query(Course).filter(Course.id == item.course_id).first()
                if course and course.artisan_id:
                    artisan = db.query(Artisan).filter(Artisan.id == course.artisan_id).first()
                    if artisan:
                        artisan.total_sales = (artisan.total_sales or 0) + Decimal(str(item.subtotal))

    # 商品订单：记录交易流水 + 更新匠人累计销售额
    if order.goods_type == 1:
        for item in order.items:
            if not item.product_id: continue
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if product and product.artisan_id:
                commission_rate = Decimal('0.10')
                artisan_income = Decimal(str(item.subtotal)) * (Decimal('1') - commission_rate)

                txn = Transaction(
                    artisan_id=product.artisan_id, type="order_income",
                    amount=artisan_income, order_id=order.id,
                    status="success", remark=f"订单 {order.order_no} 收入",
                )
                db.add(txn)

                # 更新匠人 total_sales
                artisan = db.query(Artisan).filter(Artisan.id == product.artisan_id).first()
                if artisan:
                    artisan.total_sales = (artisan.total_sales or 0) + Decimal(str(item.subtotal))

    db.commit()
    db.refresh(order)
    return order


def ship_order(db: Session, order_id: int) -> Order:
    order = get_order_by_id(db, order_id)
    if not order or order.status != "paid":
        raise ValueError("订单状态不允许发货")
    order.status = "shipped"
    order.ship_time = datetime.now()
    db.commit()
    db.refresh(order)
    return order


def complete_order(db: Session, order_id: int) -> Order:
    order = get_order_by_id(db, order_id)
    if not order or order.status not in ("shipped", "paid"):
        raise ValueError("订单状态不允许完成")
    # 课程订单：paid → completed（跳过发货）
    # 商品订单：shipped → completed
    order.status = "completed"
    order.complete_time = datetime.now()
    db.commit()
    db.refresh(order)
    return order


def get_order_stats(db: Session):
    from sqlalchemy import func
    today = datetime.now().date()

    # 交易数据
    today_orders = db.query(func.count(Order.id)).filter(
        func.date(Order.created_at) == today
    ).scalar() or 0

    today_sales = db.query(func.sum(Order.pay_amount)).filter(
        func.date(Order.created_at) == today,
        Order.status.in_(["paid", "shipped", "completed"]),
    ).scalar() or 0

    total_orders = db.query(func.count(Order.id)).scalar() or 0
    total_sales = db.query(func.sum(Order.pay_amount)).filter(
        Order.status.in_(["paid", "shipped", "completed"]),
    ).scalar() or 0

    # 平台收入（佣金 = 商品售价 * 佣金比例）
    # 对历史订单（commission_amount=0），用 subtotal * commission_rate 推算
    from sqlalchemy import case
    today_commission = db.query(func.sum(
        case(
            (OrderItem.commission_amount > 0, OrderItem.commission_amount),
            else_=OrderItem.subtotal * OrderItem.commission_rate
        )
    )).join(Order).filter(
        func.date(Order.created_at) == today,
        Order.status.in_(["paid", "shipped", "completed"]),
    ).scalar() or 0

    total_income = db.query(func.sum(
        case(
            (OrderItem.commission_amount > 0, OrderItem.commission_amount),
            else_=OrderItem.subtotal * OrderItem.commission_rate
        )
    )).join(Order).filter(
        Order.status.in_(["paid", "shipped", "completed"]),
    ).scalar() or 0

    # 平台增长
    today_new_users = db.query(func.count(User.id)).filter(
        User.role == "user",
        func.date(User.created_at) == today,
    ).scalar() or 0

    today_new_artisans = db.query(func.count(Artisan.id)).filter(
        func.date(Artisan.created_at) == today,
    ).scalar() or 0

    total_users = db.query(func.count(User.id)).filter(User.role == "user").scalar() or 0
    total_artisans = db.query(func.count(Artisan.id)).scalar() or 0

    # 待处理任务
    pending_artisans = db.query(func.count(Artisan.id)).filter(
        Artisan.status == "pending",
    ).scalar() or 0

    pending_products = db.query(func.count(Product.id)).filter(
        Product.status == "pending",
    ).scalar() or 0

    return {
        "today_orders": today_orders,
        "today_sales": float(today_sales),
        "total_orders": total_orders,
        "total_sales": float(total_sales),
        "today_commission": float(today_commission),
        "total_income": float(total_income),
        "today_new_users": today_new_users,
        "today_new_artisans": today_new_artisans,
        "total_users": total_users,
        "total_artisans": total_artisans,
        "pending_artisans": pending_artisans,
        "pending_products": pending_products,
    }


# ==================== 课程订单 ====================

def create_course_order(db: Session, user: User, course_id: int) -> Order:
    from models import Course
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course: raise ValueError("课程不存在")
    if course.status != "published": raise ValueError("课程暂不可购买")

    existing = db.query(Enrollment).filter(
        Enrollment.user_id == user.id, Enrollment.course_id == course_id,
        Enrollment.type == "purchased", Enrollment.status == "active",
    ).first()
    if existing: raise ValueError("已购买此课程")

    existing_pending = db.query(Order).filter(
        Order.user_id == user.id, Order.goods_type == 2, Order.status == "pending",
    ).join(OrderItem, OrderItem.order_id == Order.id).filter(OrderItem.course_id == course_id).first()
    if existing_pending:
        # 重置支付开始时间，给用户新的10分钟支付窗口
        existing_pending.payment_started_at = None
        db.commit()
        return existing_pending

    order = Order(order_no=generate_order_no(), user_id=user.id, total_amount=float(course.price), pay_amount=float(course.price), goods_type=2, status="pending")
    db.add(order); db.flush()

    course_price = float(course.price)
    commission_rate = 0.10
    commission_amount = round(course_price * commission_rate, 2)
    artisan_income = round(course_price - commission_amount, 2)
    db.add(OrderItem(order_id=order.id, product_id=None, course_id=course_id, product_name=course.title, product_image=course.cover_image or "", price=course_price, qty=1, subtotal=course_price, commission_rate=commission_rate, commission_amount=commission_amount, artisan_income=artisan_income))
    db.add(Enrollment(user_id=user.id, course_id=course_id, order_id=order.id, type="purchased", status="inactive"))
    db.commit(); db.refresh(order)
    return order


def cancel_course_order(db: Session, order_id: int) -> Order:
    order = get_order_by_id(db, order_id)
    if not order: raise ValueError("订单不存在")
    if order.status != "pending": raise ValueError("订单状态不允许取消")
    order.status = "cancelled"; order.cancel_time = datetime.now()
    for item in order.items:
        if item.course_id:
            e = db.query(Enrollment).filter(Enrollment.order_id == order_id, Enrollment.course_id == item.course_id, Enrollment.type == "purchased").first()
            if e: e.status = "inactive"
    db.commit(); db.refresh(order)
    return order
