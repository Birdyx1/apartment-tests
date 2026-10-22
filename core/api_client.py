import logging
from urllib.parse import urlsplit

logger = logging.getLogger(__name__)
class ApiClient:
    def __init__(self, session,base_url,timeout):
        self.session = session
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def request(self,method,path,**kwargs):
        if not isinstance(path, str) or not path.strip():
            raise ValueError("接口路径必须是非空字符串")

        parts = urlsplit(path)
        if parts.scheme or parts.netloc:
            raise ValueError("请传相对接口路径，例如 /room/list，不要传完整 URL")
        url = f"{self.base_url}/{path.lstrip('/')}"
        logger.info(f"请求：{method} {path}")
        kwargs.setdefault("timeout",self.timeout)

        response = self.session.request(
            method=method,
            url=url,
            **kwargs
        )

        logger.info(f"HTTP 状态码：{response.status_code}")
        return response