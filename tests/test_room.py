import pytest
import allure

@pytest.mark.p1
@allure.title("新建公寓的房间列表为空")
def test_new_apartment_has_no_rooms(admin_room_api,created_apartment):
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
    # 1.
    # 按created_room["id"]
    # 找到记录，且只有一条。
    cnt = 0
    for room in page ['records']:
        if room['id'] == created_room['id']:
            cnt += 1
            assert room['apartmentId'] == created_room['apartmentId']
            assert room['roomNo'] == created_room['roomNo']
            assert room["status"] == 0
    assert cnt == 1
    assert page["total"] == 1

@pytest.mark.p1
@allure.title("同公寓重复房间号被拒绝且不新增数据")
def test_duplicate_room_number_rejected(admin_room_api, created_room):
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
    assert page["total"] == 1, "重复创建失败后不应新增房间"
    assert len(page["records"]) == 1
    assert page["records"][0]["id"] == created_room["id"]