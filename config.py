"""环境配置入口：集中提供服务地址、超时与本地管理员账号。
测试通过 conftest.py 的 fixture 使用这些值；此文件不发送请求。
"""

import os

# 环境变量优先；未提供时使用本机演示服务。去掉末尾斜杠便于统一拼接。
BASE_URL = os.getenv(
    "APARTMENT_BASE_URL",
    "http://localhost:8080",
).rstrip("/")

# Requests 的默认超时参数（秒），不是整条业务链路的总时限。
REQUEST_TIMEOUT = 10

# 仅为本地练习提供默认账号；更换环境时可用环境变量覆盖。
ADMIN_USERNAME = os.getenv("APARTMENT_ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("APARTMENT_ADMIN_PASSWORD", "123456")


MINIO_ENDPOINT = os.getenv("APARTMENT_MINIO_ENDPOINT", "localhost:9000")
MINIO_PUBLIC_ORIGIN = os.getenv("APARTMENT_MINIO_PUBLIC_ORIGIN", "").rstrip("/")
MINIO_ACCESS_KEY = os.getenv("APARTMENT_MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("APARTMENT_MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("APARTMENT_MINIO_BUCKET", "apartment")

# 环境变量读出来是字符串；不能直接用 bool("false")，因为它会得到 True。
MINIO_SECURE = os.getenv("APARTMENT_MINIO_SECURE", "false").strip().lower() == "true"
