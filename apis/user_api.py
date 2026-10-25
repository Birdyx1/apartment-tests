class UserApi:
    """管理员维护系统用户的接口"""
    def __init__(self, client):
        self.client = client

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