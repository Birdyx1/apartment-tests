"""系统操作日志分页与权限测试。"""

import allure
import pytest

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
