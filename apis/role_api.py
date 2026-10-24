"""
创建维修工账号时，需要把“维修工角色 ID”传给后端。我们会按角色编码 MAINTENANCE_WORKER 查找它
"""
class RoleApi:
    """管理员查询系统角色的接口。"""

    def __init__(self, client):
        self.client = client

    def enabled(self):
        """查询所有启用的角色。"""
        return self.client.request(
            "GET",
            "/system/role/enabled",
        )