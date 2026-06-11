# coding=utf-8
"""
Edgi Talk RT-AK 插件配置。

当前阶段：
- 只做 dry-run 检查；
- 不复制 BSP 文件；
- 不修改 Edgi 工程；
- 不生成最终 rt_ai_<model>_model.c/h。
"""

PLUGIN_NAME = "edgi"
PLUGIN_FULL_NAME = "RT-AK Plugin Edgi Talk"

BACKEND_DIR = "backend_plugin_edgi"
TEMPLATE_DIR = "templates"
SCONSCRIPT_DIR = "Sconscripts"

DEFAULT_MODEL_NAME = "object_detect"
DEFAULT_RUNTIME = "deepcraft"

REQUIRED_BSP_ITEMS = [
    "SConstruct",
    "rtconfig.h",
    "applications",
]

REQUIRED_DEEPCRAFT_FILES = [
    "model.c",
    "model.h",
]

REQUIRED_IMAI_SYMBOLS = [
    "IMAI_init",
    "IMAI_compute",
    "IMAI_finalize",
    "IMAI_api",
]

RT_CONFIG_MACROS = [
    "RT_AI_USE_EDGI",
    "RT_AI_USE_M55_ETHOSU",
    "BSP_USING_DEEPCRAFT_AI",
]
