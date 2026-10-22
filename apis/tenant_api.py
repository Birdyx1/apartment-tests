
class TenantAPI:
    def __init__(self, client):
        self.client = client

    def create(self,payload):
        return self.client.request(
            "POST",
            "/tenant/create",
            json = payload
        )
    def delete(self,tenant_id):
        return self.client.request(
            "DELETE",
            f"/tenant/delete/{tenant_id}"
        )

    def detail(self, tenant_id):
        return self.client.request(
            "GET",
            f"/tenant/{tenant_id}",
        )