# coding=utf-8
"""
Edgi Talk 平台插件参数定义。

该文件只负责追加 Edgi 平台相关参数。
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
        help="只检查工程和模型产物，不复制文件，不修改 BSP",
    )

    return parser
