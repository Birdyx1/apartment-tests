
from core.assertions import assert_response, assert_true_response
import pytest
import allure

@pytest.mark.p0
@allure.title('在住租客创建报修后可查询正确的工单详情和本人列表')
def test_tenant_create_maintenance(
        created_maintenance,
        tenant_maintenance_api,
        maintenance_payload,
):
    response = tenant_maintenance_api.detail(
        created_maintenance['id']
    )

    body = assert_response(response)

    order = body["data"]
    assert order["id"] == created_maintenance["id"]
    assert order["tenantId"] == created_maintenance["tenantId"]
    assert order["roomId"] == created_maintenance["roomId"]
    assert order["title"] == maintenance_payload["title"]
    assert order["description"] == maintenance_payload["description"]
    assert order["urgency"] == maintenance_payload["urgency"]
    assert order["status"] == 0

    # 创建后，详情和列表中的工单均应处于待处理状态。
    list_response = tenant_maintenance_api.list()
    list_body = assert_response(list_response)
    orders = list_body["data"]
    assert isinstance(orders, list)

    matched = [
        item for item in orders
        if item["id"] == created_maintenance["id"]
    ]
    assert len(matched) == 1, "本人工单列表中应恰好存在一条目标工单"

    item = matched[0]
    assert item["tenantId"] == created_maintenance["tenantId"]
    assert item["roomId"] == created_maintenance["roomId"]
    assert item["title"] == maintenance_payload["title"]
    assert item["status"] == 0


@pytest.mark.p0
@allure.title("租客取消报修后工单状态变为已取消")
def test_tenant_cancel_maintenance(
        created_maintenance,
        tenant_maintenance_api,
):
    response = tenant_maintenance_api.cancel(
        created_maintenance['id']
    )
    body = assert_true_response(response)

    # 再查询详情，确认取消操作真正更新了状态。
    response = tenant_maintenance_api.detail(
        created_maintenance['id']
    )
    body = assert_response(response)
    assert body['data']['id'] == created_maintenance["id"]
    assert body['data']['status'] == 3

    # 取消后任保留历史工单，历史中的状态也应该变
    list_response = tenant_maintenance_api.list()
    list_body = assert_response(list_response)

    orders = list_body["data"]
    assert isinstance(orders, list)

    matched = [
        item for item in orders
        if item["id"] == created_maintenance["id"]
    ]

    assert len(matched) == 1,'取消后工单应保留在列表中'

    item = matched[0]
    assert item["tenantId"] == created_maintenance["tenantId"]
    assert item["roomId"] == created_maintenance["roomId"]
    assert item["status"] == 3


@pytest.mark.p1
@allure.title("未入住租客申请报修时被拒绝且不产生工单")
def test_tenant_without_lease_cannot_create_maintenance(
        tenant_maintenance_api,
        maintenance_payload,
):
    response = tenant_maintenance_api.create(maintenance_payload)
    body = assert_response(response, code=400)
    assert body["message"] == "您当前没有在住记录，无法申请工单"
    assert body.get("data") is None

    # 请求被拒绝后，不应产生工单。
    list_response = tenant_maintenance_api.list()
    list_body = assert_response(list_response)
    assert list_body["data"] == []

@pytest.mark.p1
@allure.title("报修标题为空时被拒绝且不产生工单")
@pytest.mark.parametrize(
    "title",
    ["", "   "],
    ids=["empty-title", "blank-title"],
)
def test_tenant_create_maintenance_invalid_title(
        title,
        created_lease,
        tenant_maintenance_api,
        maintenance_payload,
):
    payload = maintenance_payload.copy()
    payload["title"] = title

    response = tenant_maintenance_api.create(payload)
    body = assert_response(response, http_status=400, code=400)
    assert "工单标题不能为空" in body["message"]
    assert body.get("data") is None

    list_response = tenant_maintenance_api.list()
    list_body = assert_response(list_response)
    assert list_body["data"] == []


@pytest.mark.p1
@allure.title("缺少紧急程度时拒绝报修且不产生工单")
def test_tenant_create_maintenance_missing_urgency(
        created_lease,
        tenant_maintenance_api,
        maintenance_payload,
):
    payload = maintenance_payload.copy()
    payload.pop("urgency")

    response = tenant_maintenance_api.create(payload)
    body = assert_response(response, http_status=400, code=400)
    assert "紧急程度不能为空" in body["message"]
    assert body.get("data") is None

    list_response = tenant_maintenance_api.list()
    list_body = assert_response(list_response)
    assert list_body["data"] == []


# 已取消的工单不能再次取消，状态仍保持 3。
@pytest.mark.p1
@allure.title("重复取消工单时被拒绝且状态保持已取消")
def test_tenant_cannot_cancel_maintenance_twice(
        created_maintenance,
        tenant_maintenance_api,
):
    order_id = created_maintenance["id"]
    # 第一次取消应成功。
    response = tenant_maintenance_api.cancel(order_id)
    body = assert_true_response(response)

    # 第二次取消同一工单，应明确拒绝。
    response = tenant_maintenance_api.cancel(order_id)
    body = assert_response(response, code=500)
    assert body["message"] == "只能取消待处理或处理中的工单"
    assert body.get("data") is None

    # 拒绝后，原工单应仍保持已取消状态。
    response = tenant_maintenance_api.detail(order_id)
    body = assert_response(response)
    assert body["data"]["id"] == order_id
    assert body["data"]["status"] == 3
    assert body["data"]["tenantId"] == created_maintenance["tenantId"]
    assert body["data"]["roomId"] == created_maintenance["roomId"]
