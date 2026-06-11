# coding=utf-8
"""
RT-AK Edgi Talk 平台插件入口。

第一版目标：
- 能独立运行；
- 能解析 Edgi 平台参数；
- 能 dry-run 检查 BSP 与 DeepCraft/Imagimob 模型产物；
- 不修改任何外部工程。
"""

import argparse
import sys

from config import DEFAULT_MODEL_NAME, DEFAULT_RUNTIME
from plugin_edgi_parser import platform_parameters
from prepare_work import print_dry_run_report


def build_parser():
    parser = argparse.ArgumentParser(
        description="RT-AK Edgi Talk plugin dry-run tool"
    )

    parser.add_argument(
        "--project",
        type=str,
        required=True,
        help="RT-Thread BSP 工程路径",
    )

    parser.add_argument(
        "--model",
        type=str,
        default="",
        help="模型路径。第一版 Edgi 插件暂不直接使用该参数，保留用于兼容 RT-AK 基础参数",
    )

    parser.add_argument(
        "--model_name",
        type=str,
        default=DEFAULT_MODEL_NAME,
        help="注册到 RT-AK 的模型名称",
    )

    parser.add_argument(
        "--platform",
        type=str,
        default="edgi",
        help="RT-AK 平台名称，第一版固定为 edgi",
    )

    parser.add_argument(
        "--clear",
        action="store_true",
        help="保留 RT-AK 通用参数。第一版 dry-run 不执行清理动作",
    )

    parser = platform_parameters(parser)
    return parser


def main(argv=None):
    parser = build_parser()
    opt = parser.parse_args(argv)

    if opt.platform != "edgi":
        print(f"错误：当前插件只支持 --platform edgi，当前输入为: {opt.platform}")
        return 1

    if not opt.runtime:
        opt.runtime = DEFAULT_RUNTIME

    if opt.dry_run:
        return print_dry_run_report(opt)

    print("当前阶段只支持 --dry_run。请先执行 dry-run 检查。")
    return 1


if __name__ == "__main__":
    sys.exit(main())
