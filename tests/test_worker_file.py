import allure
import pytest
import requests


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

    image_response = requests.get(image_url, timeout=10)
    assert image_response.status_code == 200

    content_type = image_response.headers.get("Content-Type", "")
    assert content_type.split(";")[0].strip() == "image/png"

    assert image_response.content == repair_image_path.read_bytes(), (
        "上传后的图片内容应与本地原图一致"
    )