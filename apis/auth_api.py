class AuthApi:
    def __init__(self, client):
        self.client = client

    def login(self,payload):
        return self.client.request(
            "POST",
            "/auth/login",
            json=payload
        )

    def current_user(self, **kwargs):
        return self.client.request(
            "GET",
            "/auth/me",
            **kwargs,
        )
