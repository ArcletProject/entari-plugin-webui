from arclet.entari import plugin
from arclet.entari.plugin import PluginRole

from entari_plugin_webui import webui_extend

from .routes import router as ext_router, serve_example_page

plugin.metadata(
    "示例插件",
    PluginRole.NORMAL,
    [{"name": "RF-Tar-Railt", "email": "rf_tar_railt@qq.com"}],
    "0.1.0",
    description="WebUI 扩展开发示例",
)

ext = webui_extend("example_plugin")

ext.add_menu("example_plugin.name", "mdi:information-outline", "/extension/example", order=50)
ext.add_menu("example_plugin.sub", "mdi:account-group", "/extension/example", order=51,
             badge_key="example_plugin.badge")

ext.add_page("example", "example_plugin.name", "mdi:information-outline",
             "/api/example/page", permission="example_plugin.access")

ext.add_route("/api/example/hello", ["GET"], ext_router.hello, permission="example_plugin.access")
ext.add_route("/api/example/page", ["GET"], serve_example_page, permission="example_plugin.access")
ext.add_route("/api/example/echo", ["POST"], ext_router.echo, permission="example_plugin.access")

ext.add_i18n("zh-CN", "example_plugin.name", "示例插件")
ext.add_i18n("en-US", "example_plugin.name", "Example Plugin")
ext.add_i18n("zh-CN", "example_plugin.sub", "子菜单")
ext.add_i18n("en-US", "example_plugin.sub", "Sub Menu")
ext.add_i18n("zh-CN", "example_plugin.badge", "New")
ext.add_i18n("zh-CN", "example_plugin.permission.access", "访问示例插件")
ext.add_i18n("en-US", "example_plugin.permission.access", "Access Example Plugin")

ext.add_permission("example_plugin.access", "example_plugin.permission.access")
