"""通用 HTTP 请求层：校验相对路径、拼接地址、设置默认超时并发送请求。
返回 Requests Response，由上层读取 JSON 和判断业务结果。
"""

import logging
from urllib.parse import urlsplit

logger = logging.getLogger(__name__)
class ApiClient:
    """通用请求客户端，保存 Session、服务地址和默认超时。"""
    def __init__(self, session,base_url,timeout):
        """保存调用方提供的客户端/配置；初始化本身不发送 HTTP 请求。"""
        self.session = session
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def request(self,method,path,**kwargs):
        """发送一个相对路径请求，并将 json、params、headers 等参数原样转交 Session。
        不吞异常、不自动重试、不添加业务成功断言。
        """
        if not isinstance(path, str) or not path.strip():
            raise ValueError("接口路径必须是非空字符串")

        # 先拒绝完整 URL，再拼接；避免出现“基础地址 + 完整地址”的错误。
        parts = urlsplit(path)
        if parts.scheme or parts.netloc:
            raise ValueError("请传相对接口路径，例如 /room/list，不要传完整 URL")
        url = f"{self.base_url}/{path.lstrip('/')}"
        logger.info(f"请求：{method} {path}")
        # 没传 timeout 才补默认值；调用方显式传值时保留原值。
        kwargs.setdefault("timeout",self.timeout)

        # **kwargs 可包含 json（请求体）、params（查询条件）、headers（本次请求头）。
        # 日志只记录方法/路径/状态，不输出密码、令牌或完整请求响应。
        response = self.session.request(
            method=method,
            url=url,
            **kwargs
        )

        logger.info(f"HTTP 状态码：{response.status_code}")
        return response
