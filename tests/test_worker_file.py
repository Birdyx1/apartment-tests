from urllib.parse import urlsplit, urlunsplit

import allure
import pytest
import requests

from config import MINIO_PUBLIC_ORIGIN


def _image_url_for_current_environment(image_url):
    """按当前运行环境替换图片 URL 的 origin，保留对象路径与查询参数。"""
    if not MINIO_PUBLIC_ORIGIN:
        return image_url

    original_url = urlsplit(image_url)
    public_origin = urlsplit(MINIO_PUBLIC_ORIGIN)
    assert public_origin.scheme in {"http", "https"} and public_origin.netloc, (
        "APARTMENT_MINIO_PUBLIC_ORIGIN 必须是包含协议和主机的 URL"
    )
    return urlunsplit((
        public_origin.scheme,
        public_origin.netloc,
        original_url.path,
        original_url.query,
        original_url.fragment,
    ))


@pytest.mark.p1
@allure.title("维修工上传 PNG 处理图片成功")
def test_worker_upload_image_success(
        uploaded_repair_image,
        repair_image_path,
):
    # fixture 已完成上传，这里直接取得上传结果。
    object_key = uploaded_repair_image["objectKey"]
    image_url = uploaded_repair_image["url"]

    assert isinstance(object_key, str)
    assert object_key.startswith("maintenance/")
    assert object_key.endswith(".png")

    assert isinstance(image_url, str)
    assert image_url.strip(), "图片访问地址不能为空"

    # Jenkins 容器内的 localhost 指向 Jenkins 自身；替换为容器可达的 origin。
    image_url = _image_url_for_current_environment(image_url)

    image_response = requests.get(image_url, timeout=10)
    assert image_response.status_code == 200

    content_type = image_response.headers.get("Content-Type", "")
    assert content_type.split(";")[0].strip() == "image/png"

    assert image_response.content == repair_image_path.read_bytes(), (
        "上传后的图片内容应与本地原图一致"
    )
