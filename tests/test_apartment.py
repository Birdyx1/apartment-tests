"""公寓查询测试：每个测试使用独立数据，结束后由 fixture 删除并检查不可见。"""

from core.assertions import assert_response

import pytest

@pytest.mark.p1
def test_apartment_list(admin_apartment_api, created_apartment):
    """新建目标公寓后查列表，检查目标恰好一条，不能假定整个列表只有一条。"""
    response = admin_apartment_api.list()
    # 检查列表是否包含创建的公寓

    body = assert_response(response)
    assert isinstance(body['data'], list)

    # 整个列表可能有其他公寓，只按本次 ID 找目标，不假定全局总数。
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
    """查询本次 fixture 创建的公寓，按 ID 和名称核对，避免依赖人工数据。"""
    response = admin_apartment_api.detail(created_apartment["id"])


    body = assert_response(response)
    assert body["data"]["id"] == created_apartment["id"]
    assert body["data"]["name"] == created_apartment["name"]

@pytest.mark.p1
def test_apartment_list_filter_by_name(admin_apartment_api, created_apartment):
    """同时检查目标存在及所有名称匹配，避免空列表让逐条检查假通过。
    当前未主动准备不匹配对照数据，不能将其解释为完整筛选覆盖。
    """
    response = admin_apartment_api.list(
        params={"name": created_apartment["name"]}
    )

    body = assert_response(response)
    assert isinstance(body["data"], list)
    assert created_apartment["id"] in [
        item['id'] for item in body['data']
    ]
    # 目标存在检查防止空列表假通过；逐条名称检查防止混入不匹配结果。
    for item in body["data"]:
        assert created_apartment["name"] in item["name"], (
            f"返回了不符合名称条件的公寓：{item['name']}"
        )


