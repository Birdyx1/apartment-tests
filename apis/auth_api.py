"""管理端认证接口：普通对象用于登录/拒绝场景，管理员对象用于已登录查询。"""

class AuthApi:
    """管理端认证接口对象；是否已登录由传入客户端决定。"""
    def __init__(self, client):
        """保存调用方提供的客户端/配置；初始化本身不发送 HTTP 请求。"""
        self.client = client

    def login(self,payload):
        """管理员账号登录，请求字段为 username/password 及验证码信息。"""
        return self.client.request(
            "POST",
            "/auth/login",
            json=payload
        )

    def current_user(self, **kwargs):
        """按请求令牌查询管理端当前用户，可通过 headers 指定本次请求身份。"""
        return self.client.request(
            "GET",
            "/auth/me",
            **kwargs,
        )
