class TenantAuthApi:
    def __init__(self, client):
        self.client = client

    # 注意租客登录路径是 / tenant - app / auth / login，与管理员的 / auth / login不同。
    def login(self,payload):
        return self.client.request(
            "POST",
            "/tenant-app/auth/login",
            json=payload,
        )
