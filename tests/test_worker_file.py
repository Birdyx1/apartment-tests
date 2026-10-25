import allure
import pytest
import requests


@pytest.mark.p1
@allure.title("维修工上传 PNG 处理图片成功")
def test_worker_upload_image_success(worker_file_api, repair_image_path):
    response = worker_file_api.upload_image(repair_image_path)
    assert response.status_code == 200

    body = response.json()
    assert body["code"] == 200, body.get("message")

    data = body["data"]
    object_key = data["objectKey"]
    image_url = data["url"]

    assert isinstance(object_key, str)
    assert object_key.startswith("maintenance/")
    assert object_key.endswith(".png")

    assert isinstance(image_url, str)
    assert image_url.strip(), "图片访问地址不能为空"
    # 读取上传后的图片，核对文件类型和实际内容。
    image_response = requests.get(image_url, timeout=10)
    assert image_response.status_code == 200

    content_type = image_response.headers.get("Content-Type", "")
    assert content_type.split(";")[0].strip() == "image/png"

    assert image_response.content == repair_image_path.read_bytes(), (
        "上传后的图片内容应与本地原图一致"
    )