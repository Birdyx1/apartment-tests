"""租客端已发布公告接口。客户端身份由 tenant_notice_api fixture 提供。"""


class TenantNoticeApi:
    """按当前租客入住范围查询公告。"""

    def __init__(self, client):
        self.client = client

    def list(self, **kwargs):
        """查询当前租客可见的已发布公告。"""
        return self.client.request("GET", "/tenant-app/notices", **kwargs)

    def detail(self, notice_id):
        """查询当前租客可见的公告详情。"""
        return self.client.request("GET", f"/tenant-app/notices/{notice_id}")
