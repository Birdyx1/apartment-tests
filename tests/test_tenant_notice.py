"""租客端公告可见性与当前入住范围测试。"""

import allure
import pytest

from core.assertions import assert_response, assert_true_response


@pytest.mark.p1
@allure.title("没有在住记录的租客看不到公告")
def test_tenant_without_lease_sees_no_notices(tenant_notice_api):
    body = assert_response(tenant_notice_api.list())
    assert body["data"] == []


@pytest.mark.p1
@allure.title("租客只能看到当前公寓中已发布的公告")
def test_tenant_sees_published_notice_for_current_apartment(
    admin_notice_api,
    created_notice,
    created_lease,
    tenant_notice_api,
):
    """created_lease 建立租客入住范围，测试草稿不可见、发布后可见。"""
    draft_list = assert_response(tenant_notice_api.list())["data"]
    assert created_notice["id"] not in [item["id"] for item in draft_list]

    assert_true_response(admin_notice_api.publish(created_notice["id"]))

    published_list = assert_response(tenant_notice_api.list())["data"]
    matched = [item for item in published_list if item["id"] == created_notice["id"]]
    assert len(matched) == 1
    assert matched[0]["title"] == created_notice["title"]
    assert matched[0]["apartmentId"] == created_notice["apartmentId"]

    detail = assert_response(tenant_notice_api.detail(created_notice["id"]))["data"]
    assert detail["id"] == created_notice["id"]
    assert detail["status"] == 1
    assert detail["content"] == created_notice["content"]
