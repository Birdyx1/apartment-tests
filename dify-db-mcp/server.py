import os
import re
import hmac
from decimal import Decimal

import pymysql
import uvicorn
from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings

load_dotenv()

server = MCPServer(name="apartment-db-mcp", version="0.1.0")

BILL_STATUS = {
    0: "待缴",
    1: "已缴",
    2: "逾期",
    3: "已关闭",
}

MAINTENANCE_STATUS = {
    0: "待处理",
    1: "处理中",
    2: "已完成",
    3: "已取消",
}

URGENCY = {
    1: "普通",
    2: "紧急",
    3: "非常紧急",
}


class BearerTokenMiddleware:
    """校验所有 MCP HTTP 请求携带的 Bearer 令牌。"""

    def __init__(self, app, token: str):
        self.app = app
        self.expected = f"Bearer {token}".encode()

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope.get("path", "").rstrip("/") == "/mcp":
            headers = dict(scope.get("headers", []))
            actual = headers.get(b"authorization", b"")

            if not hmac.compare_digest(actual, self.expected):
                body = b'{"error":"unauthorized"}'
                await send({
                    "type": "http.response.start",
                    "status": 401,
                    "headers": [
                        (b"content-type", b"application/json"),
                        (b"content-length", str(len(body)).encode()),
                    ],
                })
                await send({
                    "type": "http.response.body",
                    "body": body,
                })
                return

        await self.app(scope, receive, send)


def connect_db():
    """使用本机 .env 中的只读账号连接测试数据库。"""
    return pymysql.connect(
        host=os.environ["DB_HOST"],
        port=int(os.getenv("DB_PORT", "13306")),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=5,
        read_timeout=10,
    )


@server.tool()
def get_bill_summary(bill_month: str) -> list[dict]:
    """按账期汇总账单数量和金额。账期格式必须是 YYYY-MM，例如 2026-10。"""
    if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", bill_month):
        raise ValueError("账期格式应为 YYYY-MM")

    sql = """
        SELECT bill_month, status,
               COUNT(*) AS bill_count,
               COALESCE(SUM(amount), 0) AS total_amount
        FROM rent_bill
        WHERE deleted = 0 AND bill_month = %s
        GROUP BY bill_month, status
        ORDER BY status
    """

    with connect_db() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, (bill_month,))
            rows = cursor.fetchall()

    return [
        {
            "bill_month": row["bill_month"],
            "status": int(row["status"]),
            "status_name": BILL_STATUS.get(int(row["status"]), "未知状态"),
            "bill_count": int(row["bill_count"]),
            "total_amount": f"{Decimal(row['total_amount']):.2f}",
        }
        for row in rows
    ]

@server.tool()
def list_maintenance_orders(status: int | None = None, limit: int = 20) -> list[dict]:
    """查询维修工单，可按状态筛选；最多返回 50 条，不返回工单描述等详细个人信息。"""
    if status is not None and status not in MAINTENANCE_STATUS:
        raise ValueError("status 必须是 0、1、2、3，或不传")
    if not 1 <= limit <= 50:
        raise ValueError("limit 必须在 1 到 50 之间")

    sql = """
        SELECT id, room_id, title, urgency, status,
               assignee_id, handler_id, create_time
        FROM maintenance_order
        WHERE deleted = 0
    """
    params = []

    if status is not None:
        sql += " AND status = %s"
        params.append(status)

    sql += " ORDER BY create_time DESC LIMIT %s"
    params.append(limit)

    with connect_db() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            rows = cursor.fetchall()

    return [
        {
            "id": int(row["id"]),
            "room_id": int(row["room_id"]),
            "title": row["title"],
            "urgency": int(row["urgency"]),
            "urgency_name": URGENCY.get(int(row["urgency"]), "未知"),
            "status": int(row["status"]),
            "status_name": MAINTENANCE_STATUS.get(int(row["status"]), "未知"),
            "assignee_id": row["assignee_id"],
            "handler_id": row["handler_id"],
            "create_time": (
                row["create_time"].isoformat(sep=" ", timespec="seconds")
                if row["create_time"] else None
            ),
        }
        for row in rows
    ]
if __name__ == "__main__":
    host = os.getenv("MCP_HOST", "127.0.0.1")
    port = int(os.getenv("MCP_PORT", "8765"))
    token = os.getenv("MCP_API_TOKEN")
    if not token:
        raise RuntimeError("MCP_API_TOKEN must be set in .env")

    public_hosts = [
        host.strip()
        for host in os.getenv("MCP_ALLOWED_HOSTS", "").split(",")
        if host.strip()
    ]

    app = server.streamable_http_app(
        json_response=True,
        stateless_http=True,
        transport_security=TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            # The MCP SDK auto-allows loopback Host values when bound locally.
            # Supplying explicit settings replaces those defaults, so retain
            # loopback access and allow the current public tunnel hostname.
            allowed_hosts=[
                "127.0.0.1:*",
                "localhost:*",
                "[::1]:*",
                *[value for host in public_hosts for value in (host, f"{host}:*")],
            ],
        ),
        host=host,
    )
    app.add_middleware(BearerTokenMiddleware, token=token)

    uvicorn.run(app, host=host, port=port, log_level="info")
