"""房间测试：验证空列表、详情、分页数据与同公寓房间号唯一性。
created_room 依赖 created_apartment，清理时先删房间再删公寓。
"""

import pytest
import allure

@pytest.mark.p1
@allure.title("新建公寓的房间列表为空")
def test_new_apartment_has_no_rooms(admin_room_api,created_apartment):
    """本次公寓刚创建且尚无房间，因此 records 为空、total 为 0 才是明确预期。"""
    response = admin_room_api.list(
        params={
            "apartmentId": created_apartment["id"],
            "current": 1,
            "size": 10
        }
    )

    assert response.status_code == 200
    body = response.json()
    assert body['code'] == 200
    page = body['data']

    assert isinstance(page, dict)
    assert isinstance(page['records'], list)
    assert page['records'] == []
    assert page['total'] == 0

@pytest.mark.p0
@allure.title("房间详情与创建数据一致")
def test_room_detail(admin_room_api, created_room):
    """查询本次房间，核对所属公寓及创建字段；status=0 表示空置。"""
    response = admin_room_api.detail(
        created_room['id'],
    )
    assert response.status_code == 200
    body = response.json()
    assert body['code'] == 200
    room = body['data']
    assert isinstance(room, dict)
    assert room['id'] == created_room['id']
    assert room['apartmentId'] == created_room['apartmentId']
    assert room['roomNo'] == created_room['roomNo']
    assert room['floor'] == 1
    assert room['layout'] == "一室一厅"
    assert room['area'] == 30
    assert room['status'] == 0

@pytest.mark.p1
@allure.title("房间列表包含本次创建的房间")
def test_room_list_contains_created_room(admin_room_api, created_room):

    """分页查询独立公寓，核对目标唯一且字段正确；该公寓只创建一间房。"""
    response = admin_room_api.list(
        params={
            "apartmentId": created_room['apartmentId'],
        }
    )
    assert response.status_code == 200
    body = response.json()
    assert body['code'] == 200
    page = body['data']
    assert isinstance(page, dict)
    assert isinstance(page['records'], list)
    # 计数避免只核对部分字段，却没有发现目标缺失或重复。
    cnt = 0
    for room in page ['records']:
        if room['id'] == created_room['id']:
            cnt += 1
            assert room['apartmentId'] == created_room['apartmentId']
            assert room['roomNo'] == created_room['roomNo']
            assert room["status"] == 0
    assert cnt == 1
    # 此处公寓由本测试独立创建，且只创建一间房，因此总数 1 是可控预期。
    assert page["total"] == 1

@pytest.mark.p1
@allure.title("同公寓重复房间号被拒绝且不新增数据")
def test_duplicate_room_number_rejected(admin_room_api, created_room):
    """同公寓同房间号重复创建应失败，再查列表确认没有新增数据。"""
    payload = {
        "apartmentId": created_room["apartmentId"],
        "roomNo": created_room["roomNo"],
        "floor": 1,
        "layout": "一室一厅",
        "area": 30,
        "status": 0,
    }

    response = admin_room_api.create(
        payload=payload
    )
    assert response.status_code == 200
    body = response.json()
    assert body['code'] == 400
    assert body['message'] == "同公寓下房间号已存在"
    # 除明确拒绝原因外，还要保证没有返回新建房间的数据。
    assert body.get("data") is None, "重复创建失败不应返回新房间数据"

    # 重复创建失败后，是否仍然只有原来的房间。


    check = admin_room_api.list(
        params={
            "apartmentId": created_room["apartmentId"],
        })
    assert check.status_code == 200

    check_body = check.json()
    assert check_body["code"] == 200

    page = check_body["data"]
    # 此处公寓由本测试独立创建，且只创建一间房，因此总数 1 是可控预期。
    assert page["total"] == 1, "重复创建失败后不应新增房间"
    assert len(page["records"]) == 1
    assert page["records"][0]["id"] == created_room["id"]
