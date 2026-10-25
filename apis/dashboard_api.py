"""工作台运营概览接口封装。"""


class DashboardApi:
    def __init__(self, client):
        self.client = client

    def overview(self):
        """查询当前登录用户的数据概览。"""
        return self.client.request(
            "GET",
            "/dashboard/overview",
        )
