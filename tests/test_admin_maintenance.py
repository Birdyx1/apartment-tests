
from core.assertions import assert_response, assert_true_response
from helpers.maintenance import assert_order_identity, assert_worker_assignment
import allure
import pytest




def _assign_and_check(admin_api, tenant_api, source, worker_id):
    """每条场景独立派单，并确认状态仍为待处理。"""
    assert_true_response(admin_api.assign(source["id"], worker_id))
    order = assert_response(tenant_api.detail(source["id"]))["data"]
    assert_order_identity(order, source, status=0)
    assert order["assigneeId"] == worker_id


def _accept_and_check(worker_api, source, worker_id):
    """指定维修工接单后，核对状态和实际处理人。"""
    assert_true_response(worker_api.accept(source["id"]))
    order = assert_response(worker_api.detail(source["id"]))["data"]
    assert_order_identity(order, source, status=1)
    assert_worker_assignment(order, worker_id)


@pytest.mark.p0
@allure.title("管理员派单成功后工单仍为待处理")
def test_admin_assign_order_success(
        created_maintenance,
        created_worker,
        admin_maintenance_api,
        tenant_maintenance_api,
):
    order_id = created_maintenance["id"]
    worker_id = created_worker["id"]
    _assign_and_check(admin_maintenance_api, tenant_maintenance_api, created_maintenance, worker_id)


@pytest.mark.p0
@allure.title("指定维修工接单后工单进入处理中")
def test_assigned_worker_accept_order_success(
        created_maintenance,
        created_worker,
        admin_maintenance_api,
        tenant_maintenance_api,
        worker_maintenance_api,
):
    order_id = created_maintenance["id"]
    worker_id = created_worker["id"]
    _assign_and_check(admin_maintenance_api, tenant_maintenance_api, created_maintenance, worker_id)
    _accept_and_check(worker_maintenance_api, created_maintenance, worker_id)



@pytest.mark.p0
@allure.title("维修工不能接取指派给其他人的工单")
def test_other_worker_cannot_accept_assigned_order(
        created_maintenance,
        created_worker,
        created_second_worker,
        admin_maintenance_api,
        second_worker_maintenance_api,
        tenant_maintenance_api,
):
    order_id = created_maintenance["id"]
    worker_id = created_worker["id"]
    _assign_and_check(admin_maintenance_api, tenant_maintenance_api, created_maintenance, worker_id)
    assert worker_id != created_second_worker["id"]
    body = assert_response(second_worker_maintenance_api.accept(order_id), code=500)
    assert body["message"] == "该工单未指派给你"
    order = assert_response(tenant_maintenance_api.detail(order_id))["data"]
    assert_order_identity(order, created_maintenance, status=0)
    assert order["assigneeId"] == worker_id




@pytest.mark.p1
@allure.title("指定维修工不能抢取已派单工单")
def test_assigned_worker_cannot_grab_order(
        created_maintenance,
        created_worker,
        admin_maintenance_api,
        tenant_maintenance_api,
        worker_maintenance_api,
):
    order_id = created_maintenance["id"]
    worker_id = created_worker["id"]
    _assign_and_check(admin_maintenance_api, tenant_maintenance_api, created_maintenance, worker_id)
    body = assert_response(worker_maintenance_api.grab(order_id), code=500)
    assert body["message"] == "该工单已指派，无法抢单"
    order = assert_response(tenant_maintenance_api.detail(order_id))["data"]
    assert_order_identity(order, created_maintenance, status=0)
    assert order["assigneeId"] == worker_id

@pytest.mark.p1
@allure.title("管理员取消指派后工单保持待处理")
def test_admin_cancel_assignment_success(
        created_maintenance,
        created_worker,
        admin_maintenance_api,
        tenant_maintenance_api,
):
    order_id = created_maintenance["id"]
    worker_id = created_worker["id"]
    _assign_and_check(admin_maintenance_api, tenant_maintenance_api, created_maintenance, worker_id)
    # D03 保留：返回成功后，指派人必须真正清空。
    assert_true_response(admin_maintenance_api.assign(order_id, None))
    order = assert_response(tenant_maintenance_api.detail(order_id))["data"]
    assert_order_identity(order, created_maintenance, status=0)
    assert order["assigneeId"] is None


@pytest.mark.p1
@allure.title("处理中工单不能重新派单")
def test_admin_cannot_reassign_processing_order(
        created_maintenance,
        created_worker,
        admin_maintenance_api,
        tenant_maintenance_api,
        worker_maintenance_api,
        created_second_worker
):
    order_id = created_maintenance["id"]
    worker_id = created_worker["id"]
    _assign_and_check(admin_maintenance_api, tenant_maintenance_api, created_maintenance, worker_id)
    _accept_and_check(worker_maintenance_api, created_maintenance, worker_id)
    assert worker_id != created_second_worker["id"]
    body = assert_response(
        admin_maintenance_api.assign(order_id, created_second_worker["id"]), code=500,
    )
    assert body["message"] == "仅待处理工单可派单"
    order = assert_response(worker_maintenance_api.detail(order_id))["data"]
    assert_order_identity(order, created_maintenance, status=1)
    assert_worker_assignment(order, worker_id)

@pytest.mark.p1
@allure.title("维修工不能接取未指派的工单")
def test_worker_cannot_accept_unassigned_order(
        created_maintenance,
        worker_maintenance_api,

):
    order_id = created_maintenance["id"]
    body = assert_response(worker_maintenance_api.accept(order_id), code=500)
    assert body["message"] == "该工单未指派给你"
    order = assert_response(worker_maintenance_api.detail(order_id))["data"]
    assert_order_identity(order, created_maintenance, status=0)
