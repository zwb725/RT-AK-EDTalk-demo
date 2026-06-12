# coding=utf-8

from pathlib import Path

from .config import (
    REQUIRED_BSP_ITEMS,
    REQUIRED_DEEPCRAFT_FILES,
    REQUIRED_IMAI_SYMBOLS,
    RT_CONFIG_MACROS,
)


def _as_path(path_str):
    if not path_str:
        return None
    return Path(path_str).expanduser().resolve()


def check_bsp_project(project):
    """检查 RT-Thread BSP 工程基础结构。"""
    project_path = _as_path(project)
    if project_path is None:
        return False, ["未指定 --project"]

    errors = []

    if not project_path.exists():
        errors.append(f"BSP 工程路径不存在: {project_path}")
        return False, errors

    for item in REQUIRED_BSP_ITEMS:
        item_path = project_path / item
        if not item_path.exists():
            errors.append(f"缺少 BSP 必需项: {item_path}")

    return len(errors) == 0, errors


def check_deepcraft_dir(deepcraft_dir):
    """检查 DeepCraft / Imagimob 生成产物目录。"""
    model_path = _as_path(deepcraft_dir)
    if model_path is None:
        return False, ["未指定 --deepcraft_dir"]

    errors = []

    if not model_path.exists():
        errors.append(f"DeepCraft 目录不存在: {model_path}")
        return False, errors

    for filename in REQUIRED_DEEPCRAFT_FILES:
        file_path = model_path / filename
        if not file_path.exists():
            errors.append(f"缺少模型产物文件: {file_path}")

    if errors:
        return False, errors

    symbol_errors = check_imai_symbols(model_path)
    errors.extend(symbol_errors)

    return len(errors) == 0, errors


def check_imai_symbols(model_path):
    """在 model.c/model.h 中粗略检查 IMAI 关键符号。"""
    model_c = model_path / "model.c"
    model_h = model_path / "model.h"

    text = ""
    for file_path in [model_c, model_h]:
        try:
            text += file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError as exc:
            return [f"读取文件失败: {file_path}, {exc}"]

    errors = []
    for symbol in REQUIRED_IMAI_SYMBOLS:
        if symbol not in text:
            errors.append(f"未找到 IMAI 符号: {symbol}")

    return errors


def print_dry_run_report(opt):
    """打印 dry-run 检查报告。"""
    print("=" * 70)
    print("RT-AK Plugin Edgi Talk dry-run report")
    print("=" * 70)
    print(f"project       : {opt.project}")
    print(f"model_name    : {opt.model_name}")
    print(f"deepcraft_dir : {opt.deepcraft_dir}")
    print(f"runtime       : {opt.runtime}")
    print(f"ethosu        : {opt.ethosu}")
    print(f"dry_run       : {opt.dry_run}")
    print("-" * 70)

    bsp_ok, bsp_errors = check_bsp_project(opt.project)
    model_ok, model_errors = check_deepcraft_dir(opt.deepcraft_dir)

    print(f"BSP check     : {'OK' if bsp_ok else 'FAILED'}")
    for err in bsp_errors:
        print(f"  - {err}")

    print(f"Model check   : {'OK' if model_ok else 'FAILED'}")
    for err in model_errors:
        print(f"  - {err}")

    print("-" * 70)
    print("后续将启用的 RT-Thread / RT-AK 宏：")
    for macro in RT_CONFIG_MACROS:
        print(f"  - {macro}")

    print("-" * 70)
    if bsp_ok and model_ok:
        print("dry-run 通过：可以进入下一阶段，即生成 rt_ai_<model>_model.c/h 草图。")
        return 0

    print("dry-run 失败：先修正上述路径或模型产物问题。")
    return 1