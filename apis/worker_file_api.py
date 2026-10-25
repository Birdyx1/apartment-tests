from pathlib import Path


class WorkerFileApi:
    """维修工上传处理图片的接口。"""

    def __init__(self, client):
        self.client = client

    def upload_image(self, file_path):
        """上传本地 PNG 图片，返回原始响应。"""
        path = Path(file_path)

        with path.open("rb") as image:
            return self.client.request(
                "POST",
                "/worker-app/files/upload",
                files={
                    "file": (path.name, image, "image/png"),
                },
            )