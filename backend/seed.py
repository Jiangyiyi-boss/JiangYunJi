"""
匠韵集 - 种子数据脚本
运行: python seed.py
"""
from database import SessionLocal, Base, engine
from models import User, Category, Product, Artisan
from auth_utils import hash_password

db = SessionLocal()

# 创建表
Base.metadata.create_all(bind=engine)

print("创建管理员账号...")
existing_admin = db.query(User).filter(User.username == "admin").first()
if not existing_admin:
    admin = User(
        username="admin",
        password=hash_password("admin123"),
        nickname="超级管理员",
        role="admin",
    )
    db.add(admin)
    db.flush()
    print("  管理员账号创建成功")
else:
    print("  管理员账号已存在，跳过")

print("创建测试用户...")
users = []
for i in range(1, 6):
    existing = db.query(User).filter(User.username == f"user{i}").first()
    if not existing:
        user = User(
            username=f"user{i}",
            password=hash_password("user123"),
            phone=f"1380000000{i}",
            nickname=f"测试用户{i}",
            role="user",
        )
        db.add(user)
        users.append(user)
if users:
    db.flush()
    print(f"  创建了 {len(users)} 个测试用户")
else:
    print("  测试用户已存在，跳过")

print("创建匠人账号...")
artisans = []
artisan_data = [
    {"username": "artisan1", "name": "张师傅", "specialty": "陶瓷", "shop": "张氏陶瓷坊", "bio": "从事陶瓷制作30年，擅长青花瓷"},
    {"username": "artisan2", "name": "李师傅", "specialty": "刺绣", "shop": "李氏绣庄", "bio": "苏绣传承人，作品多次获奖"},
    {"username": "artisan3", "name": "王师傅", "specialty": "木雕", "shop": "王氏木雕", "bio": "东阳木雕传人，精于人物雕刻"},
]

for data in artisan_data:
    existing = db.query(User).filter(User.username == data["username"]).first()
    if not existing:
        user = User(
            username=data["username"],
            password=hash_password("artisan123"),
            nickname=data["name"],
            role="artisan",
        )
        db.add(user)
        db.flush()

        artisan = Artisan(
            user_id=user.id,
            real_name=data["name"],
            id_card=f"11010119900101000{len(artisans)+1}",
            specialty=data["specialty"],
            bio=data["bio"],
            shop_name=data["shop"],
            status="approved",
            fans_count=100 + len(artisans) * 50,
        )
        db.add(artisan)
        db.flush()

        artisans.append(artisan)

if artisans:
    print(f"  创建了 {len(artisans)} 个匠人账号")
else:
    print("  匠人账号已存在，跳过")

print("创建商品分类...")
categories = []
existing_cats = db.query(Category).count()
if existing_cats == 0:
    cat_data = [
        # 一级分类
        ("茶事生活", None, ""),
        ("家居器物", None, ""),
        ("服饰配饰", None, "👘"),
        ("文房雅玩", None, "📜"),
        ("伴手好礼", None, "🎁"),
        # 二级分类 - 茶事生活
        ("紫砂茶器", 1, ""),
        ("手工茶具", 1, ""),
        ("茶道配件", 1, ""),
        # 二级分类 - 家居器物
        ("竹编收纳", 2, ""),
        ("漆器餐具", 2, ""),
        ("木雕摆件", 2, ""),
        ("手工花器", 2, ""),
        # 二级分类 - 服饰配饰
        ("刺绣围巾", 3, ""),
        ("扎染服饰", 3, ""),
        ("手工银饰", 3, ""),
        # 二级分类 - 文房雅玩
        ("笔墨纸砚", 4, ""),
        ("篆刻印章", 4, ""),
        ("香道器具", 4, ""),
        # 二级分类 - 伴手好礼
        ("非遗礼盒", 5, ""),
        ("定制礼品", 5, ""),
    ]

    for name, parent_id, icon in cat_data:
        level = 1 if parent_id is None else 2
        cat = Category(name=name, parent_id=parent_id, icon=icon, level=level)
        db.add(cat)
        categories.append(cat)

    db.flush()
    print(f"  创建了 {len(categories)} 个分类")
else:
    print(f"  分类已存在 ({existing_cats}个)，跳过")

print("创建商品...")
# 获取匠人ID映射
artisan_map = {}
all_artisans = db.query(Artisan).all()
for a in all_artisans:
    artisan_map[a.user.username] = a.id

# 获取分类ID映射（按名称查找）
cat_map = {}
all_cats = db.query(Category).all()
for c in all_cats:
    cat_map[c.name] = c.id

if not artisan_map:
    print("  未找到匠人账号，请先创建匠人账号")
    db.close()
    exit(1)

products = [
    {"name": "宜兴紫砂壶", "price": 1288.00, "original_price": 1688.00, "stock": 20, "category_name": "紫砂茶器", "artisan_username": "artisan1", "desc": "手工紫砂壶，传统工艺"},
    {"name": "手工盖碗茶具", "price": 688.00, "original_price": 888.00, "stock": 15, "category_name": "手工茶具", "artisan_username": "artisan1", "desc": "手工茶具套装，精美实用"},
    {"name": "竹编茶则", "price": 168.00, "original_price": 228.00, "stock": 50, "category_name": "茶道配件", "artisan_username": "artisan3", "desc": "天然竹编茶则，茶道配件"},
    {"name": "竹编收纳盒", "price": 198.00, "original_price": 268.00, "stock": 40, "category_name": "竹编收纳", "artisan_username": "artisan3", "desc": "天然竹编收纳，环保实用"},
    {"name": "漆器餐具套装", "price": 888.00, "original_price": 1188.00, "stock": 10, "category_name": "漆器餐具", "artisan_username": "artisan2", "desc": "传统漆器工艺，精美餐具"},
    {"name": "木雕山水摆件", "price": 2688.00, "original_price": 3288.00, "stock": 5, "category_name": "木雕摆件", "artisan_username": "artisan3", "desc": "东阳木雕，精雕细琢"},
    {"name": "手工陶瓷花器", "price": 588.00, "original_price": 788.00, "stock": 25, "category_name": "手工花器", "artisan_username": "artisan1", "desc": "手工陶瓷花器，雅致脱俗"},
    {"name": "苏绣真丝围巾", "price": 488.00, "original_price": 688.00, "stock": 30, "category_name": "刺绣围巾", "artisan_username": "artisan2", "desc": "精致苏绣，真丝面料"},
    {"name": "扎染连衣裙", "price": 368.00, "original_price": 488.00, "stock": 20, "category_name": "扎染服饰", "artisan_username": "artisan2", "desc": "传统扎染工艺，独特花纹"},
    {"name": "手工银镯", "price": 1288.00, "original_price": 1588.00, "stock": 15, "category_name": "手工银饰", "artisan_username": "artisan1", "desc": "纯手工银饰，匠心打造"},
    {"name": "端砚石砚台", "price": 1688.00, "original_price": 2088.00, "stock": 8, "category_name": "笔墨纸砚", "artisan_username": "artisan3", "desc": "端砚名品，文房四宝"},
    {"name": "手工篆刻印章", "price": 388.00, "original_price": 488.00, "stock": 35, "category_name": "篆刻印章", "artisan_username": "artisan3", "desc": "手工篆刻，个性定制"},
    {"name": "沉香香炉", "price": 888.00, "original_price": 1188.00, "stock": 12, "category_name": "香道器具", "artisan_username": "artisan1", "desc": "传统香道器具，雅致生活"},
    {"name": "非遗文化礼盒", "price": 588.00, "original_price": 788.00, "stock": 50, "category_name": "非遗礼盒", "artisan_username": "artisan2", "desc": "非遗好物精选，送礼佳品"},
    {"name": "定制刺绣礼品", "price": 368.00, "original_price": 468.00, "stock": 40, "category_name": "定制礼品", "artisan_username": "artisan2", "desc": "个性定制，心意满满"},
]

created_count = 0
for data in products:
    existing = db.query(Product).filter(Product.name == data["name"]).first()
    if not existing:
        artisan_id = artisan_map.get(data["artisan_username"])
        category_id = cat_map.get(data["category_name"])
        if artisan_id and category_id:
            product = Product(
                name=data["name"],
                description=data["desc"],
                price=data["price"],
                original_price=data["original_price"],
                stock=data["stock"],
                category_id=category_id,
                artisan_id=artisan_id,
                status="approved",
                is_recommend=True,
            )
            db.add(product)
            created_count += 1
        else:
            print(f"  跳过商品 '{data['name']}': artisan_id={artisan_id}, category_id={category_id}")

db.commit()
print(f"  创建了 {created_count} 个商品")
print("种子数据创建完成！")
print("\n测试账号：")
print("  管理员: admin / admin123")
print("  用户: user1~5 / user123")
print("  匠人: artisan1~3 / artisan123")

db.close()
