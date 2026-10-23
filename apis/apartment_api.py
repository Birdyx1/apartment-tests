"""管理端公寓接口。客户端身份由 admin_apartment_api fixture 提供。"""

class ApartmentApi:
    """公寓接口对象，返回原始 Response，测试自行断言。"""
    def __init__(self,client):
        """保存调用方提供的客户端/配置；初始化本身不发送 HTTP 请求。"""
        self.client = client

    def list(self,**kwargs):
        """查询当前管理员的公寓列表；通过 params 传递名称等筛选条件。"""
        return self.client.request(
            "GET",
            "/apartment/list",
            **kwargs
        )

    def detail(self,apartment_id):
        """查询指定公寓详情。"""
        return self.client.request(
            "GET",
            f"/apartment/{apartment_id}",
        )

    def create(self,payload):
        """创建公寓，payload 为 JSON 字典。"""
        return self.client.request(
            "POST",
            "/apartment",
            json = payload
        )
    def delete(self,apartment_id):
        """按 ID 逻辑删除公寓。"""
        return self.client.request(
            "DELETE",
            f"/apartment/{apartment_id}"
        )
