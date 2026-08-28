"""
并发超卖测试脚本。

用法（需本地/服务器已启动 MySQL + Redis）：
    cd backend
    python scripts/test_oversell_lock.py

逻辑：
- 创建一个库存为 10 的测试商品。
- 使用 20 个线程同时尝试下单 1 件。
- 预期：恰好 10 个订单成功，最终库存为 0，无超卖。
"""

from __future__ import annotations

import concurrent.futures
import os
import sys
import uuid

# 将 backend 目录加入模块搜索路径
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from database import SessionLocal, engine
from schemas.models import Artisan, Category, Order, OrderItem, Product, User, Address
from schemas.schemas import OrderCreate
from crud.orders import create_order
from sqlalchemy.orm import Session

TEST_STOCK = 10
CONCURRENT_ORDERS = 20


def create_test_data(db: Session) -> tuple[int, int, int, int]:
    """创建测试用的用户、匠人、地址和商品，返回对应 ID。"""
    suffix = uuid.uuid4().hex[:8]

    # 先创建用户，再创建匠人，避免外键约束失败
    user = User(
        username=f"test_user_{suffix}",
        password="test",
        phone=f"138{suffix[:8]}",
        role="user",
    )
    db.add(user)
    db.flush()

    artisan = Artisan(
        user_id=user.id,
        real_name=f"测试匠人-{suffix}",
        shop_name=f"测试店铺-{suffix}",
        status="approved",
    )
    db.add(artisan)
    db.flush()

    address = Address(
        user_id=user.id,
        name="测试收件人",
        phone="13800138000",
        province="北京",
        city="北京市",
        district="朝阳区",
        detail="测试地址",
    )
    db.add(address)
    db.flush()

    # 复用数据库中已有的一个分类，避免外键失败
    category = db.query(Category).first()
    if not category:
        category = Category(name="测试分类")
        db.add(category)
        db.flush()

    product = Product(
        name=f"测试商品-{suffix}",
        description="用于并发超卖测试",
        price=1.00,
        stock=TEST_STOCK,
        sales=0,
        category_id=category.id,
        artisan_id=artisan.id,
        status="approved",
        images=[],
        specs=[],
    )
    db.add(product)
    db.flush()

    db.commit()
    return user.id, address.id, product.id, artisan.id


def attempt_order(user_id: int, address_id: int, product_id: int) -> str:
    """单个线程尝试下单一次。"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return "fail:user_not_found"

        data = OrderCreate(
            items=[{"product_id": product_id, "qty": 1}],
            address_id=address_id,
            remark="并发超卖测试",
        )
        create_order(db, user, data)
        return "success"
    except ValueError as exc:
        return f"fail:{exc}"
    except Exception as exc:
        return f"error:{type(exc).__name__}:{exc}"
    finally:
        db.close()


def cleanup(db: Session, user_id: int, product_id: int, artisan_id: int) -> None:
    """清理测试产生的订单、商品、用户和匠人。"""
    db.query(OrderItem).filter(
        OrderItem.product_id == product_id
    ).delete(synchronize_session=False)
    db.query(Order).filter(
        Order.user_id == user_id
    ).delete(synchronize_session=False)
    db.query(Product).filter(Product.id == product_id).delete(synchronize_session=False)
    db.query(Address).filter(Address.user_id == user_id).delete(synchronize_session=False)
    # 先删匠人再删用户，避免外键约束失败
    db.query(Artisan).filter(Artisan.id == artisan_id).delete(synchronize_session=False)
    db.query(User).filter(User.id == user_id).delete(synchronize_session=False)
    db.commit()


def main() -> int:
    db = SessionLocal()
    try:
        user_id, address_id, product_id, artisan_id = create_test_data(db)
    finally:
        db.close()

    print(f"测试商品 ID={product_id}, 初始库存={TEST_STOCK}, 并发请求数={CONCURRENT_ORDERS}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENT_ORDERS) as executor:
        futures = [
            executor.submit(attempt_order, user_id, address_id, product_id)
            for _ in range(CONCURRENT_ORDERS)
        ]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    success_count = results.count("success")
    fail_results = [r for r in results if r != "success"]

    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        final_stock = product.stock if product else None
        final_sales = product.sales if product else None
    finally:
        db.close()

    print(f"成功订单数: {success_count}/{CONCURRENT_ORDERS}")
    print(f"最终库存: {final_stock}, 最终销量: {final_sales}")
    if fail_results:
        # 去重展示失败原因
        unique_fails = sorted(set(fail_results))
        print(f"失败原因示例: {unique_fails[:5]}")

    # 清理
    db = SessionLocal()
    try:
        cleanup(db, user_id, product_id, artisan_id)
        print("测试数据已清理")
    finally:
        db.close()

    if success_count == TEST_STOCK and final_stock == 0:
        print("✅ 超卖防护测试通过")
        return 0
    else:
        print("❌ 超卖防护测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
