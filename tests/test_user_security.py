"""系统用户查询接口的敏感字段保护测试。"""

import allure
import pytest

from core.assertions import assert_response


@pytest.mark.p1
@allure.title("管理员分页查询用户时不应返回密码字段")
def test_admin_user_page_does_not_expose_password(admin_user_api, created_worker):
    page = assert_response(
        admin_user_api.page(params={"username": created_worker["username"]})
    )["data"]

    matched = [item for item in page["records"] if item["id"] == created_worker["id"]]
    assert len(matched) == 1
    assert matched[0]["username"] == created_worker["username"]
    assert "password" not in matched[0], "用户分页响应不应包含密码字段"


@pytest.mark.p1
@allure.title("管理员查询用户详情时不应返回密码字段")
def test_admin_user_detail_does_not_expose_password(admin_user_api, created_worker):
    user = assert_response(admin_user_api.detail(created_worker["id"]))["data"]

    assert user["id"] == created_worker["id"]
    assert user["username"] == created_worker["username"]
    assert "password" not in user, "用户详情响应不应包含密码字段"


@pytest.mark.p1
@allure.title("维修工没有用户列表权限时不能查询管理员用户分页")
def test_worker_cannot_query_admin_user_page(worker_user_api):
    response = worker_user_api.page()

    assert_response(response, http_status=403, code=403)
