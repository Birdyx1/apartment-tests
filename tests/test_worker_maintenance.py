import pytest
import allure


@pytest.mark.p1
@allure.title("新维修工的本人已接工单列表为空")
def test_new_worker_has_no_mine_orders(worker_maintenance_api):
    """创建账号 → 登录 → 查询 → 结束后删除账号"""
    response = worker_maintenance_api.list(
        params={"tab": "mine"}
    )
    assert response.status_code == 200

    body = response.json()
    assert body["code"] == 200, body.get("message")

    orders = body["data"]
    assert isinstance(orders, list)
    assert orders == [], "新维修工尚未接单，本人列表应为空"

@pytest.mark.p0
@allure.title("租客创建报修后维修工待接列表包含该工单")
def test_tenant_order_visible_in_worker_todo(
        created_maintenance,
        worker_maintenance_api,
        maintenance_payload,
):
    """创建报修后，维修工待接列表应包含该工单"""
    """三个 fixture 分别准备：租客的报修工单、已登录维修工接口、创建时的原始数据。"""
    response = worker_maintenance_api.list(
        params = {"tab": "todo"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 200, body.get("message")

    orders = body['data']
    assert isinstance(orders, list)

    matched = [
        item for item in orders
        if item["id"] == created_maintenance["id"]
    ]

    assert len(matched) == 1, "待接列表应唯一包含本次创建的工单"

    order = matched[0]
    assert order["tenantId"] == created_maintenance["tenantId"]
    assert order["roomId"] == created_maintenance["roomId"]
    assert order["title"] == maintenance_payload["title"]
    assert order["status"] == 0

@pytest.mark.p0
@allure.title("维修工抢单成功后工单进入处理中")
def test_worker_grab_order_success(
        created_maintenance,
        worker_maintenance_api,
        created_worker,
):
    order_id = created_maintenance["id"]

    response = worker_maintenance_api.grab(order_id)
    assert response.status_code == 200

    body = response.json()
    assert body["code"] == 200, body.get("message")
    assert body["data"] is True

    # 查询详情，确认状态和处理人实际更新。
    response = worker_maintenance_api.detail(order_id)
    assert response.status_code == 200

    body = response.json()
    assert body["code"] == 200, body.get("message")

    order = body["data"]
    assert order["id"] == order_id
    assert order["status"] == 1
    assert order["handlerId"] == created_worker["id"]
    assert order["assigneeId"] == created_worker["id"]
    assert order["tenantId"] == created_maintenance["tenantId"]
    assert order["roomId"] == created_maintenance["roomId"]

    # 抢单后，工单应进入当前维修工的本人列表。
    response = worker_maintenance_api.list(params={"tab": "mine"})
    assert response.status_code == 200

    body = response.json()
    assert body["code"] == 200, body.get("message")

    orders = body["data"]
    assert isinstance(orders, list)

    matched = [
        item for item in orders
        if item["id"] == order_id
    ]
    assert len(matched) == 1, "本人列表应唯一包含本次抢到的工单"

    mine_order = matched[0]
    assert mine_order["status"] == 1
    assert mine_order["handlerId"] == created_worker["id"]
    # 已被抢取的工单，不应继续出现在待接列表。
    response = worker_maintenance_api.list(params={"tab": "todo"})
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 200, body.get("message")

    orders = body["data"]
    assert isinstance(orders, list)

    order_ids = [item["id"] for item in orders]
    assert order_id not in order_ids, "抢单成功后，该工单应从待接列表移除"

# 同一维修工不能重复抢取已进入处理中的工单
@pytest.mark.p1
@allure.title("维修工不能重复抢取处理中的工单")
def test_worker_cannot_grab_order_twice(
        created_maintenance,
        worker_maintenance_api,
        created_worker,
):
    order_id = created_maintenance["id"]
    # 第一次抢单成功，让工单进入处理中。
    response = worker_maintenance_api.grab(order_id)
    assert response.status_code == 200

    body = response.json()
    assert body["code"] == 200, body.get("message")
    assert body["data"] is True

    # 对同一工单再次发起抢单，应被拒绝。
    response = worker_maintenance_api.grab(order_id)
    assert response.status_code == 200

    body = response.json()
    assert body["code"] == 500
    assert body["message"] == "仅待处理工单可抢单"

    # 重复抢单失败后，原来的状态和归属应保持不变。
    response = worker_maintenance_api.detail(order_id)
    assert response.status_code == 200

    body = response.json()
    assert body["code"] == 200, body.get("message")

    order = body["data"]
    assert order["id"] == order_id
    assert order["status"] == 1
    assert order["handlerId"] == created_worker["id"]
    assert order["assigneeId"] == created_worker["id"]
