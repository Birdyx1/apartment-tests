class TenantMaintenanceApi:
    def __init__(self,client):
        self.client = client
    def create(self,payload):
        return self.client.request(
            "POST",
            "/tenant-app/maintenance/create",
            json=payload
        )

    def cancel(self,order_id):
        return self.client.request(
            "PUT",
            f"/tenant-app/maintenance/{order_id}/cancel"
        )
    def detail(self, order_id):
        """查询当前租客的工单详情。"""
        return self.client.request(
            "GET",
            f"/tenant-app/maintenance/{order_id}"
        )

    def list(self):
        """查询当前登录租客的工单列表。"""
        return self.client.request(
            "GET",
            "/tenant-app/maintenance/list"
        )