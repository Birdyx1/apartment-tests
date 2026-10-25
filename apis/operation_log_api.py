"""系统操作日志查询接口封装。"""


class OperationLogApi:
    def __init__(self, client):
        self.client = client

    def page(self, **kwargs):
        """分页查询操作日志，可通过 params 传入筛选条件。"""
        return self.client.request(
            "GET",
            "/system/operation-log/page",
            **kwargs
        )

    def detail(self, log_id):
        """根据日志 ID 查询操作日志详情。"""
        return self.client.request(
            "GET",
            f"/system/operation-log/{log_id}",
        )

    def statistics_by_module(self, **kwargs):
        """查询按操作模块汇总的日志数量。"""
        return self.client.request(
            "GET",
            "/system/operation-log/statistics/module",
            **kwargs
        )
