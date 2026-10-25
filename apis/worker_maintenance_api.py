class WorkerMaintenanceApi:
    """维修工处理工单的接口"""
    def __init__(self, client):
        self.client = client
    def list(self,params=None):
        """查询维修工处理的工单列表"""
        """这里的params用于传URL
        查询条件：
        - {"tab": "todo"}：待接工单。
        - {"tab": "mine"}：本人已接的工单，包含处理中、已完成。"""
        return self.client.request(
            "GET",
            "/worker-app/maintenance/list",
            params=params,
        )

    def grab(self, order_id):
        """抢取指定的待处理工单。"""
        return self.client.request(
            "PUT",
            f"/worker-app/maintenance/{order_id}/grab",
        )

    def detail(self, order_id):
        """查询维修工可查看的工单详情。"""
        return self.client.request(
            "GET",
            f"/worker-app/maintenance/{order_id}",
        )

    def complete(self, order_id, payload):
        """提交处理备注和图片，完成指定工单。"""
        """
        order_id 决定完成哪条工单，payload 提供处理结果。先完成这个封装，下一步写“未填写处理备注”的异常用例。
        """
        return self.client.request(
            "PUT",
            f"/worker-app/maintenance/{order_id}/complete",
            json=payload,
        )