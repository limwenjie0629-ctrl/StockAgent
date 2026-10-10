"""一次性脚本：在 MongoDB 中创建 admin 用户（同步 pymongo 版本）"""
import sys
sys.path.insert(0, "/app")

from app.services.user_service import user_service


def main():
    print("=" * 60)
    print("🔧 初始化管理员用户")
    print("=" * 60)

    # 1) 检查 admin 是否已存在（同步 pymongo）
    existing = user_service.users_collection.find_one({"username": "admin"})
    if existing:
        print(f"⚠️  admin 用户已存在 (is_active={existing.get('is_active')}, is_admin={existing.get('is_admin')})")
        new_hash = user_service.hash_password("admin123")
        user_service.users_collection.update_one(
            {"username": "admin"},
            {"$set": {"hashed_password": new_hash, "is_active": True, "is_admin": True}}
        )
        print("✅ 已重置 admin 密码为: admin123")
    else:
        # 2) 创建 admin
        admin_doc = {
            "username": "admin",
            "email": "admin@tradingagents.cn",
            "hashed_password": user_service.hash_password("admin123"),
            "is_active": True,
            "is_verified": True,
            "is_admin": True,
            "created_at": __import__("datetime").datetime.utcnow(),
            "updated_at": __import__("datetime").datetime.utcnow(),
            "last_login": None,
            "preferences": {
                "default_market": "A股",
                "default_depth": "深度",
                "ui_theme": "light",
                "language": "zh-CN",
                "notifications_enabled": True,
                "email_notifications": False
            },
            "daily_quota": 10000,
            "concurrent_limit": 10,
            "total_analyses": 0,
            "successful_analyses": 0,
            "failed_analyses": 0,
            "favorite_stocks": []
        }
        result = user_service.users_collection.insert_one(admin_doc)
        print(f"✅ 管理员用户创建成功 (id={result.inserted_id})")
        print(f"   用户名: admin")
        print(f"   密码:   admin123")

    # 3) 验证
    print()
    print("🧪 测试认证...")
    user_doc = user_service.users_collection.find_one({"username": "admin"})
    if user_doc:
        import bcrypt
        if bcrypt.checkpw("admin123".encode(), user_doc["hashed_password"].encode()):
            print("✅ 密码校验通过! 可以用 admin/admin123 登录了")
        else:
            print("❌ 密码校验失败")
    else:
        print("❌ 用户查找失败")

    user_service.close()


if __name__ == "__main__":
    main()