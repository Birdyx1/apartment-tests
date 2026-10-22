class RoomApi:
    def __init__(self,client):
        self.client = client
    def list(self,**kwargs):
        return self.client.request(
            "GET",
            "/room/list",
            **kwargs
        )

    def detail(self,room_id):
        return self.client.request(
            "GET",
            f"room/{room_id}"
        )

    def create(self,payload):
        return self.client.request(
            "POST",
            "/room/create",
            json = payload
        )

    def delete(self,room_id):
        return self.client.request(
            "DELETE",
            f"room/delete/{room_id}"
        )