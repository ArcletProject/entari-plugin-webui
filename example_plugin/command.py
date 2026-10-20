from arclet.entari import BasicConfModel, command, plugin
from arclet.entari.plugin import PluginRole


class Config(BasicConfModel):
    baz: str = "qux"
    """示例子插件的配置项，默认值为 'qux'"""

plugin.metadata(
    "示例子插件",
    PluginRole.NORMAL,
    [{"name": "RF-Tar-Railt", "email": "rf_tar_railt@qq.com"}],
    "0.1.0",
    description="WebUI 扩展开发示例 - 子插件",
    config=Config
)


@command.on("hello {name?}")
async def hello_command(name: str = "World"):
    """Hello command."""
    return f"Hello, {name}!"
