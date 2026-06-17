import shutil
from pathlib import Path


KCONFIG_SOURCE_LINE = 'source "$BSP_DIR/applications/rt_ai_edgi/Kconfig"'
DEFAULT_APP_EXPORT_REL = Path("applications") / "rt_ai_edgi"
BACKEND_EXPORT_REL = Path("rt_ai_lib") / "backend_plugin_edgi"

APPLICATIONS_SCONSCRIPT_MARKER = "# RT-AK Edgi runner include paths"
APPLICATIONS_SCONSCRIPT_BLOCK = """\

# RT-AK Edgi runner include paths
rt_ai_edgi_dir = cwd + '/rt_ai_edgi'
rt_ai_lib_dir = cwd + '/../rt_ai_lib'
rt_ai_backend_dir = rt_ai_lib_dir + '/backend_plugin_edgi'
rt_ai_generated_object_detect_dir = rt_ai_edgi_dir + '/generated/object_detect'
for _rt_ai_edgi_path in [
    rt_ai_edgi_dir,
    rt_ai_lib_dir,
    rt_ai_lib_dir + '/include',
    rt_ai_backend_dir,
    rt_ai_generated_object_detect_dir,
    common_root + '/deepcraft_ai/model',
    common_root + '/deepcraft_ai/third_party/ml-middleware/include',
]:
    if _rt_ai_edgi_path not in path:
        path.append(_rt_ai_edgi_path)
"""


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


def _remove_dir_if_exists(path: Path):
    if path.exists():
        if not path.is_dir():
            raise NotADirectoryError(f"expected directory: {path}")
        shutil.rmtree(path)


def _read_text_keep_newline(path: Path):
    data = path.read_bytes()
    text = data.decode("utf-8")
    newline = "\r\n" if b"\r\n" in data else "\n"
    return text, newline


def ensure_root_kconfig_source(project_path: Path):
    kconfig = project_path / "Kconfig"
    if not kconfig.exists():
        raise FileNotFoundError(f"BSP root Kconfig not found: {kconfig}")

    text, newline = _read_text_keep_newline(kconfig)
    if KCONFIG_SOURCE_LINE in text:
        return

    suffix = "" if text.endswith(("\n", "\r")) else newline
    with kconfig.open("a", encoding="utf-8", newline="") as f:
        f.write(suffix + KCONFIG_SOURCE_LINE + newline)


def ensure_applications_sconscript_paths(project_path: Path):
    sconscript = project_path / "applications" / "SConscript"
    if not sconscript.exists():
        raise FileNotFoundError(f"BSP applications SConscript not found: {sconscript}")

    text, newline = _read_text_keep_newline(sconscript)
    if APPLICATIONS_SCONSCRIPT_MARKER in text:
        return

    anchor = "src  = Glob('*.c')"
    block = APPLICATIONS_SCONSCRIPT_BLOCK.replace("\n", newline)
    if anchor in text:
        text = text.replace(anchor, block + newline + anchor, 1)
    else:
        suffix = "" if text.endswith(("\n", "\r")) else newline
        text = text + suffix + block

    with sconscript.open("w", encoding="utf-8", newline="") as f:
        f.write(text)


def resolve_export_dir(project: str, export_dir: str = "") -> Path:
    if export_dir:
        return Path(export_dir).resolve()

    return Path(project).resolve() / DEFAULT_APP_EXPORT_REL


def export_to_project(project: str, output_dir: str, export_dir: str = "") -> Path:
    repo_root = Path(__file__).resolve().parent
    project_path = Path(project).resolve()
    app_target_dir = resolve_export_dir(project, export_dir)
    backend_target_dir = project_path / BACKEND_EXPORT_REL
    stale_app_backend_dir = app_target_dir / "backend_plugin_edgi"

    if not project_path.exists():
        raise FileNotFoundError(f"project path not found: {project_path}")

    source_backend_dir = repo_root / "backend_plugin_edgi"
    source_generated_dir = repo_root / output_dir
    source_sconscript = repo_root / "Sconscripts" / "SConscript"
    source_demo = repo_root / "examples" / "rt_ai_edgi_minimal_demo.c"
    source_runner_h = repo_root / "examples" / "rt_ai_edgi_runner.h"
    source_runner = repo_root / "examples" / "rt_ai_edgi_runner.c"
    source_runner_demo = repo_root / "examples" / "rt_ai_edgi_runner_demo.c"
    source_uvc_runner_app = repo_root / "examples" / "rt_ai_edgi_uvc_runner_app.c"
    source_active_model = repo_root / "templates" / "rt_ai_edgi_active_model.h"
    source_kconfig = repo_root / "Kconfig"

    app_target_dir.mkdir(parents=True, exist_ok=True)

    _remove_dir_if_exists(stale_app_backend_dir)
    _copy_dir(source_backend_dir, backend_target_dir)
    _copy_dir(source_generated_dir, app_target_dir / "generated")
    _copy_file(source_sconscript, app_target_dir / "SConscript")
    _copy_file(source_demo, app_target_dir / "rt_ai_edgi_minimal_demo.c")
    _copy_file(source_runner_h, app_target_dir / "rt_ai_edgi_runner.h")
    _copy_file(source_runner, app_target_dir / "rt_ai_edgi_runner.c")
    _copy_file(source_runner_demo, app_target_dir / "rt_ai_edgi_runner_demo.c")
    _copy_file(source_uvc_runner_app, project_path / "applications" / "uvc_ai_app.c")
    _copy_file(source_active_model, app_target_dir / "rt_ai_edgi_active_model.h")
    _copy_file(source_kconfig, app_target_dir / "Kconfig")
    ensure_root_kconfig_source(project_path)
    ensure_applications_sconscript_paths(project_path)

    return app_target_dir
