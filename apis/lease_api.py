"""管理端入住接口：办理入住、退房，以及分页查询入住记录。
退房是业务状态变化，不等于删除入住和账单历史。
"""

# 入住关系
class LeaseApi:
    """租客与房间的入住关系接口对象，由管理员操作。"""
    def __init__(self, client):
        """保存调用方提供的客户端/配置；初始化本身不发送 HTTP 请求。"""
        self.client = client
    def create(self,payload):
        """办理入住，成功后返回入住记录 ID，关联房间进入在住状态。"""
        return self.client.request(
            "POST",
            "/tenant/lease",
            json = payload
        )
    def checkout(self,payload):
        """按 leaseId 办理退房，payload 包含退房时间，不使用 roomId 替代。"""
        return self.client.request(
            "POST",
            "/tenant/lease/checkout",
            json = payload
        )
    def page(self,**kwargs):
        """分页查询入住记录，通过 params 传递 tenantId/roomId 等条件。"""
        return self.client.request(
            "GET",
            "/tenant/lease/page",
            **kwargs,
        )
