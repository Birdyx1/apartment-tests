"""系统用户角色绑定查询测试。"""

import allure
import pytest

from core.assertions import assert_response


@pytest.mark.p1
@allure.title("管理员创建维修工后可查询其已分配角色")
def test_created_worker_has_expected_role(admin_user_api, created_worker, worker_role_id):
    role_ids = assert_response(
        admin_user_api.roles(created_worker["id"])
    )["data"]

    assert isinstance(role_ids, list), "用户角色接口应返回角色 ID 列表"
    assert role_ids == [worker_role_id], "新建维修工应且仅应绑定维修工角色"
