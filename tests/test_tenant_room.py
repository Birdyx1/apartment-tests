
from core.assertions import assert_response
import pytest
import allure

@pytest.mark.p0
@allure.title("管理员办理入住后租客可查询本人房间")
def test_tenant_current_room(
        created_lease,tenant_room_api,created_room
):
    # created_lease：保证“这个租客已经入住”

    """查询当前房间，验证返回房间信息与预期一致。"""
    response = tenant_room_api.current_room()

    body = assert_response(response)

    room = body["data"]
    assert room["roomId"] == created_lease["roomId"]
    assert room["roomNo"] == created_room["roomNo"]
    assert room["apartmentId"] == created_room["apartmentId"]
    assert room["status"] == 0

@pytest.mark.p1
@allure.title("未入住的租客查询房间时得到明确提示")
def test_tenant_without_lease_has_no_room(tenant_room_api):
    """未入住的租客查询房间，验证明确提示。"""
    response = tenant_room_api.current_room()
    body = assert_response(response, code=500)
    assert body['message'] == '当前没有在住记录'
    assert body.get('data') is None
