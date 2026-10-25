"""管理端公告接口。客户端身份由 admin_notice_api fixture 提供。"""


class NoticeApi:
    """公告管理接口对象，返回原始 Response 供测试断言。"""

    def __init__(self, client):
        self.client = client

    def page(self, **kwargs):
        """分页查询当前管理员创建的公告。"""
        return self.client.request("GET", "/notice/page", **kwargs)

    def detail(self, notice_id):
        """查询公告详情。"""
        return self.client.request("GET", f"/notice/{notice_id}")

    def create(self, payload):
        """创建公告，payload 使用 JSON。"""
        return self.client.request("POST", "/notice", json=payload)

    def update(self, notice_id, payload):
        """更新公告标题、内容和所属公寓。"""
        return self.client.request(
            "PUT", f"/notice/{notice_id}", json=payload
        )

    def publish(self, notice_id):
        """发布公告。"""
        return self.client.request("PUT", f"/notice/{notice_id}/publish")

    def unpublish(self, notice_id):
        """下架公告。"""
        return self.client.request("PUT", f"/notice/{notice_id}/unpublish")

    def delete(self, notice_id):
        """删除公告。"""
        return self.client.request("DELETE", f"/notice/{notice_id}")
