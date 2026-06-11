# coding=utf-8
"""
将 Edgi RT-AK 插件产物导出到 RT-Thread BSP 工程。

当前阶段：
- 复制 backend_plugin_edgi/
- 复制 generated/
- 复制 Sconscripts/SConscript 为目标目录 SConscript
- 不修改 BSP 根目录 SConscript
- 不修改 rtconfig.h
- 不修改 Kconfig
"""

import shutil
from pathlib import Path


def _copy_dir(src: Path, dst: Path):
    if not src.exists():
        raise FileNotFoundError(f"source directory not found: {src}")

    if dst.exists():
        shutil.rmtree(dst)

    shutil.copytree(src, dst)


def _copy_file(src: Path, dst: Path):
    if not src.exists():
        raise FileNotFoundError(f"source file not found: {src}")

    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def resolve_export_dir(project: str, export_dir: str = "") -> Path:
    if export_dir:
        return Path(export_dir).resolve()

    return Path(project).resolve() / "applications" / "rt_ai_edgi"


def export_to_project(project: str, output_dir: str, export_dir: str = "") -> Path:
    repo_root = Path(__file__).resolve().parent
    project_path = Path(project).resolve()
    target_dir = resolve_export_dir(project, export_dir)

    if not project_path.exists():
        raise FileNotFoundError(f"project path not found: {project_path}")

    source_backend_dir = repo_root / "backend_plugin_edgi"
    source_generated_dir = repo_root / output_dir
    source_sconscript = repo_root / "Sconscripts" / "SConscript"
    source_demo = repo_root / "examples" / "rt_ai_edgi_minimal_demo.c"

    target_dir.mkdir(parents=True, exist_ok=True)

    _copy_dir(source_backend_dir, target_dir / "backend_plugin_edgi")
    _copy_dir(source_generated_dir, target_dir / "generated")
    _copy_file(source_sconscript, target_dir / "SConscript")
    _copy_file(source_demo, target_dir / "rt_ai_edgi_minimal_demo.c")

    return target_dir