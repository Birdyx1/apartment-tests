"""管理员查询系统菜单的接口封装。"""


class MenuApi:
    def __init__(self, client):
        self.client = client

    def enabled_tree(self):
        """查询启用菜单树。"""
        return self.client.request(
            "GET",
            "/system/menu/tree/enabled",
        )

    def tree_for_user(self, user_id):
        """查询指定用户按已分配角色过滤后的菜单树。"""
        return self.client.request(
            "GET",
            f"/system/menu/tree/user/{user_id}",
        )
