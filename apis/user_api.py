class UserApi:
    """管理员维护系统用户的接口"""
    def __init__(self, client):
        self.client = client

    def page(self, **kwargs):
        """分页查询系统用户，支持 username 等筛选参数。"""
        return self.client.request(
            "GET",
            "/system/user/page",
            **kwargs
        )

    def detail(self, user_id):
        """查询系统用户详情。"""
        return self.client.request(
            "GET",
            f"/system/user/{user_id}"
        )

    def roles(self, user_id):
        """查询指定用户已分配的角色 ID。"""
        return self.client.request(
            "GET",
            f"/system/user/{user_id}/roles"
        )

    def change_status(self, user_id, status):
        """启用或禁用指定用户。"""
        return self.client.request(
            "PUT",
            f"/system/user/{user_id}/status",
            params={"status": status},
        )

    def create(self,payload):
        """创建系统用户，并分配角色"""
        return self.client.request(
            "POST",
            "/system/user",
            json = payload
        )

    def delete(self,user_id):
        """删除指定系统用户"""
        return self.client.request(
            "DELETE",
            f"/system/user/{user_id}",
        )
