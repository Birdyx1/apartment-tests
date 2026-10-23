"""入住与退房链路：测试体检查入住，created_lease 的 finally 检查退房恢复。
房间状态 0=空置、2=在住；入住记录状态 0=在住、1=已退房，不能混用。
"""

import pytest
import allure

@pytest.mark.p0
@allure.title("入住成功后房间状态变为在住")
def test_checkin_sets_room_occupied(admin_room_api,created_lease,admin_lease_api):
    """created_lease 先办理入住；测试验证房间在住=2、关联租约在住=0。
    退房及退房后状态检查在 fixture 的 finally 中执行，而不在本函数中。
    """
    response = admin_room_api.detail(
        room_id=created_lease["roomId"],
    )
    assert response.status_code == 200

    body = response.json()

    assert body['code'] == 200
    assert body['data']['id'] == created_lease['roomId']
    assert body['data']['status'] == 2
    # 从另一业务接口核对同一次入住：房间在住=2，租约在住=0。
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
    """created_lease 提供已在住前提；相同请求被拒绝且不新增租约。
    声明 fixture 即触发准备，即使函数内没有直接读取其返回值。
    """
    response = admin_lease_api.create(lease_payload)
    assert response.status_code == 200

    body = response.json()
    assert body['code'] == 500
    assert body['message'] == "该房间已有在住租客，请先办理退房"
    assert body.get('data', None) is None


    # 只按房间查，不按租客或状态过滤，以免错误新增的记录被筛选条件隐藏。
    check = admin_lease_api.page(
        params={
            "roomId": created_lease["roomId"],
            "current": 1,
            "size": 10,
        }
    )
    assert check.status_code == 200
    check_body = check.json()

    assert check_body['code'] == 200

    page = check_body['data']
    assert page["total"] == 1, "重复入住失败后不应新增入住记录"

    records = page["records"]
    assert isinstance(records, list)
    assert len(records) == 1
    assert records[0]["id"] == created_lease["id"]
    assert records[0]["tenantId"] == created_lease["tenantId"]
    assert records[0]["status"] == 0

