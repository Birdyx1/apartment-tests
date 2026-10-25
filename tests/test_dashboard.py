"""工作台运营概览与权限测试。"""

import allure
import pytest

from core.assertions import assert_response


@pytest.mark.p1
@allure.title("管理员运营概览返回完整且非负的统计数据")
def test_admin_dashboard_overview_has_valid_counts(admin_dashboard_api):
    overview = assert_response(admin_dashboard_api.overview())["data"]

    count_fields = [
        "apartmentCount",
        "roomCount",
        "vacantRoomCount",
        "reservedRoomCount",
        "occupiedRoomCount",
        "repairRoomCount",
        "livingTenantCount",
        "pendingOrderCount",
        "urgentOrderCount",
        "expiringLeaseCount",
    ]
    for field in count_fields:
        assert type(overview[field]) is int and overview[field] >= 0, (
            f"{field} 应为非负整数"
        )

    room_status = overview["roomStatus"]
    assert [item["status"] for item in room_status] == [0, 1, 2, 3]
    assert all(type(item["count"]) is int and item["count"] >= 0 for item in room_status)

    for trend_name in ("checkInTrend", "checkOutTrend"):
        trend = overview[trend_name]
        assert isinstance(trend, list) and len(trend) == 6
        assert all(
            isinstance(item["month"], str)
            and len(item["month"]) == 7
            and type(item["count"]) is int
            and item["count"] >= 0
            for item in trend
        )


@pytest.mark.p1
@allure.title("工作台公寓总数与当前管理员可见公寓列表一致")
def test_dashboard_apartment_count_matches_admin_apartment_list(
    admin_dashboard_api, admin_apartment_api, created_apartment,
):
    apartments = assert_response(admin_apartment_api.list())["data"]
    overview = assert_response(admin_dashboard_api.overview())["data"]

    assert created_apartment["id"] in {item["id"] for item in apartments}
    assert overview["apartmentCount"] == len(apartments)


@pytest.mark.p1
@allure.title("维修工没有工作台查看权限时不能查询运营概览")
def test_worker_cannot_query_dashboard_overview(worker_dashboard_api):
    response = worker_dashboard_api.overview()

    assert_response(response, http_status=403, code=403)
