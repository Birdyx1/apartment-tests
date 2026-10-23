"""租客端“我的房间”接口：后端按令牌识别本人，无需传入任意房间 ID。
当前只有封装和 fixture，尚无对应的业务测试。
"""

class TenantRoomApi:
    """根据当前登录租客查询其在住房间。"""
    def __init__(self,client):
        """保存调用方提供的客户端/配置；初始化本身不发送 HTTP 请求。"""
        self.client = client

    def current_room(self):
        """查询当前在住房间；后端按租客令牌定位，不传任意 roomId。"""
        return self.client.request(
            "GET",
            "/tenant-app/my/room",
        )
