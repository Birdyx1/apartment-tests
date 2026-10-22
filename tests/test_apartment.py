import pytest

@pytest.mark.p1
def test_apartment_list(admin_apartment_api, created_apartment):
    response = admin_apartment_api.list()
    # 检查列表是否包含创建的公寓

    assert response.status_code == 200
    body = response.json()
    assert body['code'] == 200
    assert isinstance(body['data'], list)

    matched = [
        item for item in body['data'] if item["id"] == created_apartment["id"]
    ]
    assert len(matched) == 1,"列表应包含本次创建的公寓，且只有一条"
    assert matched[0]['name'] == created_apartment["name"]


# ① fixture：创建一套公寓
#         ↓
# ② yield：把公寓 ID、名称交给测试
#         ↓
# ③ 测试：查询这套公寓，检查 ID、名称
#         ↓
# ④ fixture：删除刚才创建的公寓
@pytest.mark.p0
def test_apartment_detail(admin_apartment_api, created_apartment):
    response = admin_apartment_api.detail(created_apartment["id"])


    assert response.status_code == 200

    body = response.json()
    assert body["code"] == 200
    assert body["data"]["id"] == created_apartment["id"]
    assert body["data"]["name"] == created_apartment["name"]

@pytest.mark.p1
def test_apartment_list_filter_by_name(admin_apartment_api, created_apartment):
    response = admin_apartment_api.list(
        params={"name": created_apartment["name"]}
    )

    assert response.status_code == 200
    body = response.json()
    assert body['code'] == 200
    assert isinstance(body["data"], list)
    assert created_apartment["id"] in [
        item['id'] for item in body['data']
    ]
    for item in body["data"]:
        assert created_apartment["name"] in item["name"], (
            f"返回了不符合名称条件的公寓：{item['name']}"
        )


