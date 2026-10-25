class AdminMaintenanceApi:
    """管理员维护维修工单的接口。"""
    # 管理员派单 → 维修工接单
    def __init__(self, client):
        self.client = client

    def assign(self, order_id, assignee_id):
        """
            将待处理工单指派给指定维修工。
            order_id 表示派哪张工单，assignee_id 表示派给谁
        """
        return self.client.request(
            "PUT",
            f"/maintenance-order/{order_id}/assign",
            json={"assigneeId": assignee_id},
        )