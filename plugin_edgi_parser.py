# coding=utf-8
"""
Edgi Talk 平台插件参数定义。

对标 RT-AK 现有平台插件的 parser 层：
- 只负责追加平台相关参数；
- 不执行模型转换；
- 不访问 BSP；
- 不产生副作用。
"""


def platform_parameters(parser):
    """添加 Edgi Talk 平台专用参数。"""

    parser.add_argument(
        "--deepcraft_dir",
        type=str,
        default="",
        help="DeepCraft / Imagimob 生成产物目录，第一版要求其中包含 model.c 和 model.h",
    )

    parser.add_argument(
        "--runtime",
        type=str,
        default="deepcraft",
        choices=["deepcraft", "imagimob"],
        help="Edgi 后端 runtime 类型，第一版默认 deepcraft",
    )

    parser.add_argument(
        "--ethosu",
        action="store_true",
        help="声明目标后端使用 Cortex-M55 + Ethos-U55",
    )

    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="只检查工程和模型产物；注意：通过 aitools.py 跑时，RT-AK 主流程后续仍可能执行 enable_platform/load_rt_ai_lib",
    )

    parser.add_argument(
        "--enable_rt_lib",
        default="RT_AI_USE_EDGI",
        help="RT-AK platform macro enabled in rtconfig.h",
    )

    parser.add_argument(
        "--generate",
        action="store_true",
        help="生成 rt_ai_<model>_model.c/h 和 Edgi demo config",
    )

    parser.add_argument(
        "--output_dir",
        type=str,
        default="",
        help="生成文件输出目录，默认输出到插件 generated/<model_name>/",
    )

    parser.add_argument(
        "--export",
        action="store_true",
        help="将 backend/generated/examples/Kconfig/SConscript 导出到 BSP",
    )

    parser.add_argument(
        "--export_dir",
        type=str,
        default="",
        help="导出目录，默认导出到 BSP applications/rt_ai_edgi/",
    )

    parser.add_argument(
        "--config_mode",
        type=str,
        default="manual",
        choices=["manual", "auto"],
        help="BSP 配置模式：manual 只接入 Kconfig 并提示 menuconfig；auto 自动更新 .config 并通过 Kconfig 系统生成 rtconfig.h",
    )

    return parser
