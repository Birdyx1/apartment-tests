import pytest
import allure

@pytest.mark.p0
@allure.title("入住成功后房间状态变为在住")
def test_checkin_sets_room_occupied(admin_room_api,created_lease,admin_lease_api):
    response = admin_room_api.detail(
        room_id=created_lease["roomId"],
    )
    assert response.status_code == 200

    body = response.json()

    assert body['code'] == 200
    assert body['data']['id'] == created_lease['roomId']
    assert body['data']['status'] == 2
    # 检查入住记录
    lease_response = admin_lease_api.page(
        params={
            "tenantId": created_lease["tenantId"],
            "roomId": created_lease["roomId"],
            "current": 1,
            "size": 10,
        }
    )
    assert lease_response.status_code == 200
    lease_body = lease_response.json()
    assert lease_body['code'] == 200

    records = lease_body['data']['records']
    assert isinstance(records, list)

    matched = [
        item for item in records
        if item['id'] == created_lease['id']
    ]
    assert len(matched) == 1
    assert matched[0]["tenantId"] == created_lease["tenantId"]
    assert matched[0]["roomId"] == created_lease["roomId"]
    assert matched[0]["status"] == 0



@pytest.mark.p1
@allure.title("已入住的房间不能重复办理入住")
def test_duplicate_checkin_rejected(
        admin_lease_api,
        created_lease,
        lease_payload
):
    response = admin_lease_api.create(lease_payload)
    assert response.status_code == 200

    body = response.json()
    assert body['code'] == 500
    assert body['message'] == "该房间已有在住租客，请先办理退房"
    assert body.get('data', None) is None
