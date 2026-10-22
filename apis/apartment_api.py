class ApartmentApi:
    def __init__(self,client):
        self.client = client

    def list(self,**kwargs):
        return self.client.request(
            "GET",
            "/apartment/list",
            **kwargs
        )

    def detail(self,apartment_id):
        return self.client.request(
            "GET",
            f"/apartment/{apartment_id}",
        )

    def create(self,payload):
        return self.client.request(
            "POST",
            "/apartment",
            json = payload
        )
    def delete(self,apartment_id):
        return self.client.request(
            "DELETE",
            f"/apartment/{apartment_id}"
        )
