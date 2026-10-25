"""系统操作日志分页与权限测试。"""

import allure
import pytest
import time

from core.assertions import assert_response


@pytest.mark.p1
@allure.title("管理员可按成功状态分页查询操作日志")
def test_admin_can_query_successful_operation_logs(admin_operation_log_api):
    page = assert_response(
        admin_operation_log_api.page(params={
            "current": 1,
            "size": 5,
            "status": 1,
        })
    )["data"]

    assert page["current"] == 1
    assert page["size"] == 5
    assert isinstance(page["total"], int) and page["total"] >= 0
    assert isinstance(page["records"], list)
    assert len(page["records"]) <= 5
    assert all(log["status"] == 1 for log in page["records"])


@pytest.mark.p1
@allure.title("维修工没有操作日志列表权限时不能查询操作日志")
def test_worker_cannot_query_operation_logs(worker_operation_log_api):
    response = worker_operation_log_api.page()

    assert_response(response, http_status=403, code=403)


@pytest.mark.p1
@allure.title("成功的角色查询操作日志可按 ID 查看详情")
def test_role_query_log_can_be_found_and_opened(
    admin_role_api, admin_operation_log_api,
):
    assert_response(admin_role_api.enabled())

    deadline = time.monotonic() + 5
    matched_log = None
    while time.monotonic() < deadline:
        page = assert_response(
            admin_operation_log_api.page(params={
                "current": 1,
                "size": 10,
                "module": "角色管理",
                "operationType": "QUERY",
                "status": 1,
            })
        )["data"]
        matched_log = next(
            (
                log for log in page["records"]
                if log["requestUrl"].endswith("/system/role/enabled")
            ),
            None,
        )
        if matched_log is not None:
            break
        time.sleep(0.1)

    assert matched_log is not None, "成功查询角色后应能检索到对应操作日志"
    detail = assert_response(
        admin_operation_log_api.detail(matched_log["id"])
    )["data"]
    assert detail["id"] == matched_log["id"]
    assert detail["operationModule"] == "角色管理"
    assert detail["operationType"] == "QUERY"
    assert detail["status"] == 1


@pytest.mark.p1
@allure.title("操作日志模块统计返回非负数量")
def test_operation_log_module_statistics_are_nonnegative(admin_operation_log_api):
    statistics = assert_response(
        admin_operation_log_api.statistics_by_module()
    )["data"]

    assert isinstance(statistics, dict)
    assert all(
        isinstance(module, str)
        and type(count) is int
        and count >= 0
        for module, count in statistics.items()
    )
