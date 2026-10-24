import pytest
import allure

@pytest.mark.p0
@allure.title("管理员办理入住后租客可查询本人房间")
def test_tenant_current_room(
        created_lease,tenant_room_api,created_room
):
    """查询当前房间，验证返回房间信息与预期一致。"""
    response = tenant_room_api.current_room()
    assert response.status_code == 200
    body = response.json()

    room = body["data"]
    assert room["roomId"] == created_lease["roomId"]
    assert room["roomNo"] == created_room["roomNo"]
    assert room["apartmentId"] == created_room["apartmentId"]
    assert room["status"] == 0
