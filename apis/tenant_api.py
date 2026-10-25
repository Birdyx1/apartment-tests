"""管理端租客资料接口，由管理员建档、查询和删除租客资料。
租客本人登录不调用本类，而是使用 tenant_auth_api.py。
"""


class TenantAPI:
    """管理员使用的租客资料接口对象，与租客端认证对象职责不同。"""
    def __init__(self, client):
        """保存调用方提供的客户端/配置；初始化本身不发送 HTTP 请求。"""
        self.client = client

    def create(self,payload):
        """管理员创建租客资料，可同时设置本地练习密码。"""
        return self.client.request(
            "POST",
            "/tenant/create",
            json = payload
        )
    def delete(self,tenant_id):
        """删除指定租客资料，供数据 fixture 清理使用。"""
        return self.client.request(
            "DELETE",
            f"/tenant/delete/{tenant_id}"
        )

    def detail(self, tenant_id):
        """管理员查询指定租客，不是租客查询本人资料。"""
        return self.client.request(
            "GET",
            f"/tenant/{tenant_id}",
        )

    def page(self, **kwargs):
        """管理员分页查询租客资料，可通过 params 传入筛选条件。"""
        return self.client.request(
            "GET",
            "/tenant/page",
            **kwargs
        )

    def update(self, tenant_id, payload):
        """管理员更新租客资料；password 可选，省略时不应修改登录密码。"""
        return self.client.request(
            "PUT",
            f"/tenant/update/{tenant_id}",
            json=payload,
        )

    def set_password(self, tenant_id, password):
        """管理员为租客设置新密码。"""
        return self.client.request(
            "PUT",
            f"/tenant/set-password/{tenant_id}",
            json={"password": password},
        )

    def reset_password(self, tenant_id):
        """管理员重置租客密码；后端返回本次生成的默认密码。"""
        return self.client.request(
            "PUT",
            f"/tenant/reset-password/{tenant_id}",
        )
