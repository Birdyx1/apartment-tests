import allure
import pytest


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

    # 管理员把工单指派给本次创建的维修工。
    response = admin_maintenance_api.assign(order_id, worker_id)
    assert response.status_code == 200

    body = response.json()
    assert body["code"] == 200, body.get("message")
    assert body["data"] is True

    # 申请租客查询详情，核对派单结果。
    response = tenant_maintenance_api.detail(order_id)
    assert response.status_code == 200

    body = response.json()
    assert body["code"] == 200, body.get("message")

    order = body["data"]
    assert order["id"] == order_id
    assert order["status"] == 0
    assert order["assigneeId"] == worker_id
    assert order["tenantId"] == created_maintenance["tenantId"]
    assert order["roomId"] == created_maintenance["roomId"]


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

    # 本用例独立准备派单，不能依赖上一条测试的工单或执行顺序。
    response = admin_maintenance_api.assign(order_id, worker_id)
    assert response.status_code == 200

    body = response.json()
    assert body["code"] == 200, body.get("message")
    assert body["data"] is True

    # 派单只指定维修工，此时工单仍为待处理。
    response = tenant_maintenance_api.detail(order_id)
    assert response.status_code == 200

    body = response.json()
    assert body["code"] == 200, body.get("message")

    order = body["data"]
    assert order["id"] == order_id
    assert order["status"] == 0
    assert order["assigneeId"] == worker_id
    assert order["tenantId"] == created_maintenance["tenantId"]
    assert order["roomId"] == created_maintenance["roomId"]

    # 指定维修工接取管理员派来的工单。
    response = worker_maintenance_api.accept(order_id)
    assert response.status_code == 200

    body = response.json()
    assert body["code"] == 200, body.get("message")
    assert body["data"] is True

    # 查询详情，确认已进入处理中。
    response = worker_maintenance_api.detail(order_id)
    assert response.status_code == 200

    body = response.json()
    assert body["code"] == 200, body.get("message")

    order = body["data"]
    assert order["id"] == order_id
    assert order["status"] == 1
    assert order["handlerId"] == worker_id
    assert order["assigneeId"] == worker_id
    assert order["tenantId"] == created_maintenance["tenantId"]
    assert order["roomId"] == created_maintenance["roomId"]



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
    assert created_worker["id"] != created_second_worker["id"]

    # 管理员将工单派给 A。
    response = admin_maintenance_api.assign(
        order_id, created_worker["id"],
    )
    assert response.status_code == 200

    body = response.json()
    assert body["code"] == 200, body.get("message")
    assert body["data"] is True

    # B 尝试接取派给 A 的工单。
    response = second_worker_maintenance_api.accept(order_id)
    assert response.status_code == 200

    body = response.json()
    assert body["code"] == 500
    assert body["message"] == "该工单未指派给你"