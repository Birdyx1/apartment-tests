"""系统角色查询接口测试。"""

import allure
import pytest

from core.assertions import assert_response


@pytest.mark.p1
@allure.title("启用角色列表只返回有效角色并包含维修工角色")
def test_enabled_roles_contains_active_worker_role(admin_role_api):
    roles = assert_response(admin_role_api.enabled())["data"]

    assert isinstance(roles, list), "启用角色接口应返回列表"
    assert roles, "系统应至少配置一个启用角色"
    assert all(role["status"] == 1 for role in roles), "启用角色列表不应包含禁用角色"

    worker_roles = [
        role for role in roles
        if role["roleCode"] == "MAINTENANCE_WORKER"
    ]
    assert len(worker_roles) == 1, "应恰好存在一个启用的维修工角色"
    assert isinstance(worker_roles[0]["id"], int) and worker_roles[0]["id"] > 0


@pytest.mark.p1
@allure.title("管理员可按角色编码和状态筛选角色分页")
def test_role_page_filters_by_code_and_status(admin_role_api):
    page = assert_response(
        admin_role_api.page(params={
            "current": 1,
            "size": 10,
            "roleCode": "MAINTENANCE_WORKER",
            "status": 1,
        })
    )["data"]

    assert page["current"] == 1
    assert page["size"] == 10
    assert page["total"] == 1
    assert len(page["records"]) == 1
    role = page["records"][0]
    assert role["roleCode"] == "MAINTENANCE_WORKER"
    assert role["status"] == 1


@pytest.mark.p1
@allure.title("管理员查询维修工角色详情时返回对应角色")
def test_worker_role_detail_matches_role_id(admin_role_api, worker_role_id):
    role = assert_response(admin_role_api.detail(worker_role_id))["data"]

    assert role["id"] == worker_role_id
    assert role["roleCode"] == "MAINTENANCE_WORKER"
    assert role["status"] == 1
