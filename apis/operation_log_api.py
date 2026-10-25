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
