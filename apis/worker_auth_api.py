class WorkerAuthApi:
    """维修工认证接口"""
    def __init__(self, client):
        self.client = client

    def login(self,payload):
        """使用维修工登录，返回原始响应"""
        return self.client.request(
            "POST",
            "/worker-app/auth/login",
            json=payload
        )

    def profile(self,**kwargs):
        return self.client.request(
            "GET",
            "/worker-app/profile",
            **kwargs,
        )