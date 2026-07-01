def setup_function(_):
    from entari_plugin_webui.core.extension import clear_extensions

    clear_extensions()


def test_webui_extend_idempotent():
    from entari_plugin_webui.core.extension import webui_extend

    a = webui_extend("plug_a")
    b = webui_extend("plug_a")
    assert a is b


def test_add_menu_and_collect():
    from entari_plugin_webui.core.extension import get_all_menus, webui_extend

    ext = webui_extend("plug_a")
    ext.add_menu(label_key="menu.a", icon="mdi:x", path="/a", order=5)
    menus = get_all_menus()
    assert menus[0]["label_key"] == "menu.a"


def test_add_route_and_ws():
    from entari_plugin_webui.core.extension import get_all_extension_routes, webui_extend

    ext = webui_extend("plug_a")
    ext.add_route("/ext/a/data", ["GET"], lambda: None)
    ext.add_websocket_route("/ws/ext/a", lambda ws: None)
    routes, ws_routes = get_all_extension_routes()
    assert len(routes) == 1
    assert len(ws_routes) == 1


def test_add_page_i18n_perm():
    from entari_plugin_webui.core.extension import webui_extend

    ext = webui_extend("plug_a")
    ext.add_page("panel_a", label_key="page.a", icon="mdi:p", component_url="/ext/a.html")
    ext.add_i18n("zh-CN", "page.a", "面板A")
    ext.add_permission("perm.a", label_key="perm.a")
    from entari_plugin_webui.core.i18n import get_i18n
    from entari_plugin_webui.core.permissions import get_permissions

    assert get_i18n("zh-CN")["page.a"] == "面板A"
    assert any(p["key"] == "perm.a" for p in get_permissions())
