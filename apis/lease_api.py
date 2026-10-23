# 入住关系
class LeaseApi:
    def __init__(self, client):
        self.client = client
    def create(self,payload):
        return self.client.request(
            "POST",
            "/tenant/lease",
            json = payload
        )
    def checkout(self,payload):
        return self.client.request(
            "POST",
            "/tenant/lease/checkout",
            json = payload
        )
    def page(self,**kwargs):
        return self.client.request(
            "GET",
            "/tenant/lease/page",
            **kwargs,
        )
