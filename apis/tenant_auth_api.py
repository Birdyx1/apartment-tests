"""租客端登录与本人资料接口，使用独立的租客 Session，避免混入管理员令牌。"""

class TenantAuthApi:
    """租客本人登录及资料查询接口对象。"""
    def __init__(self, client):
        """保存调用方提供的客户端/配置；初始化本身不发送 HTTP 请求。"""
        self.client = client

    # 租客认证与管理员认证路径不同，不能把 /auth/login 直接复用到这里。
    def login(self,payload):
        """租客账号登录，请求字段为 account/password，与管理员登录不同。"""
        return self.client.request(
            "POST",
            "/tenant-app/auth/login",
            json=payload,
        )

    def profile(self,**kwargs):
        """租客查询本人资料，身份来自令牌；可通过 headers 为单次请求传令牌。"""
        return self.client.request(
            "GET",
            "/tenant-app/profile",
            **kwargs,
        )
