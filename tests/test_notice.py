"""管理员公告管理：草稿查询、编辑、发布和下架。"""

import allure
import pytest

from core.assertions import assert_response, assert_true_response


@pytest.mark.p1
@allure.title("管理员创建的公告以草稿状态出现在列表和详情")
def test_admin_notice_create_and_query(admin_notice_api, created_notice):
    detail = assert_response(admin_notice_api.detail(created_notice["id"]))
    notice = detail["data"]
    assert notice["id"] == created_notice["id"]
    assert notice["title"] == created_notice["title"]
    assert notice["content"] == created_notice["content"]
    assert notice["apartmentId"] == created_notice["apartmentId"]
    assert notice["status"] == 0

    page = assert_response(
        admin_notice_api.page(
            params={"current": 1, "size": 10, "apartmentId": created_notice["apartmentId"]}
        )
    )["data"]
    matched = [item for item in page["records"] if item["id"] == created_notice["id"]]
    assert len(matched) == 1
    assert matched[0]["status"] == 0


@pytest.mark.p1
@allure.title("管理员可以编辑本人创建的公告")
def test_admin_notice_update(admin_notice_api, created_notice):
    updated_payload = {
        "title": f"{created_notice['title']}-已更新",
        "content": f"{created_notice['content']}-已更新",
        "apartmentId": created_notice["apartmentId"],
    }
    assert_true_response(
        admin_notice_api.update(created_notice["id"], updated_payload)
    )

    detail = assert_response(admin_notice_api.detail(created_notice["id"]))["data"]
    assert detail["title"] == updated_payload["title"]
    assert detail["content"] == updated_payload["content"]
    assert detail["apartmentId"] == updated_payload["apartmentId"]


@pytest.mark.p1
@allure.title("管理员可以发布并下架本人创建的公告")
def test_admin_notice_publish_and_unpublish(admin_notice_api, created_notice):
    assert_true_response(admin_notice_api.publish(created_notice["id"]))
    published = assert_response(admin_notice_api.detail(created_notice["id"]))["data"]
    assert published["status"] == 1

    assert_true_response(admin_notice_api.unpublish(created_notice["id"]))
    draft = assert_response(admin_notice_api.detail(created_notice["id"]))["data"]
    assert draft["status"] == 0
