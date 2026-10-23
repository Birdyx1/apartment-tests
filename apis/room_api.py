"""管理端房间接口。房间依附公寓，创建前由数据 fixture 准备所属公寓。"""

class RoomApi:
    """管理端房间接口对象，调用者通过 fixture 获得管理员身份。"""
    def __init__(self,client):
        """保存调用方提供的客户端/配置；初始化本身不发送 HTTP 请求。"""
        self.client = client
    def list(self,**kwargs):
        """查询房间分页；返回 data.records，而非直接返回 data 列表。"""
        return self.client.request(
            "GET",
            "/room/list",
            **kwargs
        )

    def detail(self,room_id):
        """查询指定房间详情；路径无前导斜杠也由请求层统一拼接。"""
        return self.client.request(
            "GET",
            f"room/{room_id}"
        )

    def create(self,payload):
        """创建属于指定公寓的房间，字段包含 apartmentId。"""
        return self.client.request(
            "POST",
            "/room/create",
            json = payload
        )

    def delete(self,room_id):
        """删除本次指定房间；路径包含 /delete/。"""
        return self.client.request(
            "DELETE",
            f"room/delete/{room_id}"
        )
