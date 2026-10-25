"""系统菜单树查询测试。"""

import allure
import pytest

from core.assertions import assert_response


def _flatten_menu_tree(nodes):
    """递归展开菜单树，便于校验层级结构中的菜单记录。"""
    flattened = []
    for node in nodes:
        flattened.append(node)
        flattened.extend(_flatten_menu_tree(node.get("children", [])))
    return flattened


@pytest.mark.p1
@allure.title("启用菜单树包含系统管理下的角色管理菜单")
def test_enabled_menu_tree_contains_role_management(admin_menu_api):
    tree = assert_response(admin_menu_api.enabled_tree())["data"]

    assert isinstance(tree, list), "菜单树接口应返回列表"
    menus = _flatten_menu_tree(tree)
    assert menus, "系统应至少配置一个启用菜单"
    assert all(menu["status"] == 1 for menu in menus), "启用菜单树不应包含禁用菜单"

    system_roots = [menu for menu in tree if menu["id"] == 1]
    assert len(system_roots) == 1, "应恰好存在一个系统管理根菜单"
    role_menus = [menu for menu in menus if menu["id"] == 102]
    assert len(role_menus) == 1, "系统管理下应恰好存在一个角色管理菜单"
    assert role_menus[0]["parentId"] == system_roots[0]["id"]
    assert role_menus[0]["menuName"] == "角色管理"


@pytest.mark.p1
@allure.title("维修工没有菜单列表权限时不能查询管理端菜单树")
def test_worker_cannot_query_admin_menu_tree(worker_menu_api):
    response = worker_menu_api.enabled_tree()

    assert_response(response, http_status=403, code=403)


@pytest.mark.p1
@allure.title("按维修工用户查询菜单时只返回其角色菜单并补全父级")
def test_user_menu_tree_matches_assigned_worker_role(
    admin_menu_api, created_worker,
):
    tree = assert_response(
        admin_menu_api.tree_for_user(created_worker["id"])
    )["data"]
    menus = _flatten_menu_tree(tree)
    menu_ids = {menu["id"] for menu in menus}

    assert 305 in menu_ids, "维修工应看到维修工单菜单"
    assert 301 in menu_ids, "返回树应补全维修工菜单的上级目录"
    assert 102 not in menu_ids, "维修工菜单树不应包含角色管理菜单"

    maintenance_menu = next(menu for menu in menus if menu["id"] == 305)
    assert maintenance_menu["parentId"] == 301
