import os

BASE_URL = os.getenv(
    "APARTMENT_BASE_URL",
    "http://localhost:8080",
).rstrip("/")

REQUEST_TIMEOUT = 10

ADMIN_USERNAME = os.getenv("APARTMENT_ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("APARTMENT_ADMIN_PASSWORD", "123456")
