import pytest
import allure

@pytest.mark.p0
@allure.title("入住成功后房间状态变为在住")
def test_checkin_sets_room_occupied(admin_room_api,created_lease):
    response = admin_room_api.detail(
        room_id=created_lease["roomId"],
    )
    assert response.status_code == 200

    body = response.json()

    assert body['code'] == 200
    assert body['data']['id'] == created_lease['roomId']
    assert body['data']['status'] == 2
