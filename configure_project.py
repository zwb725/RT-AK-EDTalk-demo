# coding=utf-8

import os
import re
import shutil
import subprocess
import tempfile

from pathlib import Path


KCONFIG_SOURCE_LINE = 'source "$BSP_DIR/applications/rt_ai_edgi/Kconfig"'
MANAGED_BLOCK_TITLE = "RT-AK Edgi plugin configuration"
CONFIG_FILES = [".config", ".config.old", "rtconfig.h"]


class ConfigError(RuntimeError):
    pass


class ConfigResult(object):
    def __init__(self, mode):
        self.mode = mode
        self.dot_config_updated = False
        self.rtconfig_regenerated = False
        self.genconfig_ran = False
        self.config_command = ""
        self.enabled_symbols = []


class _ConfigBackup(object):
    def __init__(self, project_path):
        self.project_path = project_path
        self.temp_dir = Path(tempfile.mkdtemp(prefix="rtak_edgi_config_"))
        self.existed = {}

        for name in CONFIG_FILES:
            src = self.project_path / name
            self.existed[name] = src.exists()
            if src.exists():
                shutil.copy2(str(src), str(self.temp_dir / name))

    def restore(self):
        for name in CONFIG_FILES:
            dst = self.project_path / name
            saved = self.temp_dir / name
            if self.existed.get(name, False):
                shutil.copy2(str(saved), str(dst))
            elif dst.exists():
                dst.unlink()

    def cleanup(self):
        shutil.rmtree(str(self.temp_dir), ignore_errors=True)


def configure_project(project, config_mode, config_fragment, logger=None,
                      command_runner=None):
    project_path = Path(project).resolve()
    fragment_path = Path(config_fragment).resolve()
    mode = (config_mode or "manual").lower()

    if mode not in ("manual", "auto"):
        raise ConfigError("unsupported config_mode: {0}".format(config_mode))

    result = ConfigResult(mode)
    _check_project_prerequisites(project_path)
    _check_export_prerequisites(project_path)

    if not fragment_path.exists():
        raise ConfigError("config fragment not found: {0}".format(fragment_path))

    assignments = _read_config_fragment(fragment_path)
    result.enabled_symbols = [item[0][7:] for item in assignments]

    if mode == "manual":
        _log(logger, "Configuration mode : manual")
        _log(logger, "Next step:")
        _log(logger, "  cd {0}".format(project_path))
        _log(logger, "  scons --menuconfig")
        _log(logger, "  scons -j6")
        return result

    backup = _backup_config_files(project_path)
    try:
        _ensure_dot_config(project_path, command_runner=command_runner)
        if not (project_path / ".config").exists():
            raise ConfigError(".config was not generated")

        result.genconfig_ran = getattr(_ensure_dot_config, "last_genconfig_ran", False)

        _merge_config_fragment(project_path / ".config", fragment_path)
        result.dot_config_updated = True

        config_command = _select_noninteractive_config_option(project_path)
        result.config_command = config_command
        _run_scons(project_path, [config_command], command_runner=command_runner)

        if not (project_path / ".config").exists():
            raise ConfigError(".config missing after {0}".format(config_command))
        if not (project_path / "rtconfig.h").exists():
            raise ConfigError("rtconfig.h missing after {0}".format(config_command))

        result.rtconfig_regenerated = True

        missing_config = _validate_dot_config(project_path / ".config", assignments)
        missing_header = _validate_rtconfig_h(project_path / "rtconfig.h", assignments)
        if missing_config or missing_header:
            msg = []
            if missing_config:
                msg.append(".config missing: {0}".format(", ".join(missing_config)))
            if missing_header:
                msg.append("rtconfig.h missing: {0}".format(", ".join(missing_header)))
            raise ConfigError("auto configuration validation failed; " + "; ".join(msg))

    except Exception:
        backup.restore()
        raise
    finally:
        backup.cleanup()

    _log(logger, "Configuration mode : auto")
    _log(logger, ".config             : updated")
    _log(logger, "rtconfig.h           : regenerated")
    _log(logger, "RT_AI_USE_EDGI       : enabled")
    _log(logger, "M55 / Ethos-U55      : enabled")
    _log(logger, "Active model         : object_detect")
    _log(logger, "Minimal demo         : enabled")

    return result


def _check_project_prerequisites(project_path):
    for name in ("SConstruct", "Kconfig", "rtconfig.h"):
        path = project_path / name
        if not path.exists():
            raise ConfigError("BSP prerequisite not found: {0}".format(path))


def _check_export_prerequisites(project_path):
    app_kconfig = project_path / "applications" / "rt_ai_edgi" / "Kconfig"
    if not app_kconfig.exists():
        raise ConfigError("exported Edgi Kconfig not found: {0}".format(app_kconfig))

    root_kconfig = project_path / "Kconfig"
    text = _read_text(root_kconfig)
    count = text.count(KCONFIG_SOURCE_LINE)
    if count != 1:
        raise ConfigError(
            "BSP root Kconfig must contain exactly one Edgi source line; "
            "found {0}: {1}".format(count, KCONFIG_SOURCE_LINE)
        )


def _backup_config_files(project_path):
    return _ConfigBackup(project_path)


def _restore_config_files(backup):
    backup.restore()


def _ensure_dot_config(project_path, command_runner=None):
    ran = False
    if not (project_path / ".config").exists():
        _run_scons(project_path, ["--genconfig"], command_runner=command_runner)
        ran = True
    _ensure_dot_config.last_genconfig_ran = ran


_ensure_dot_config.last_genconfig_ran = False


def _read_config_fragment(fragment_path):
    assignments = []
    text = _read_text(fragment_path)
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        match = re.match(r"^(CONFIG_[A-Za-z0-9_]+)=(.+)$", line)
        if not match:
            raise ConfigError("invalid config fragment line: {0}".format(raw_line))

        assignments.append((match.group(1), match.group(2)))

    if not assignments:
        raise ConfigError("config fragment is empty: {0}".format(fragment_path))

    return assignments


def _merge_config_fragment(dot_config, config_fragment):
    assignments = _read_config_fragment(config_fragment)
    managed = set([name for name, _value in assignments])
    text, newline = _read_text_keep_newline(dot_config)
    lines = text.splitlines()

    cleaned = []
    i = 0
    while i < len(lines):
        if _is_managed_block_header(lines, i):
            i += 3
            continue

        line = lines[i]
        if _is_managed_symbol_line(line, managed):
            i += 1
            continue

        cleaned.append(line)
        i += 1

    while cleaned and cleaned[-1] == "":
        cleaned.pop()

    if cleaned:
        cleaned.append("")

    cleaned.extend([
        "#",
        "# {0}".format(MANAGED_BLOCK_TITLE),
        "#",
    ])
    cleaned.extend(["{0}={1}".format(name, value) for name, value in assignments])

    _write_text(dot_config, newline.join(cleaned) + newline, newline)


def _validate_dot_config(dot_config, assignments):
    text = _read_text(dot_config)
    lines = set([line.strip() for line in text.splitlines()])
    missing = []
    for name, value in assignments:
        if "{0}={1}".format(name, value) not in lines:
            missing.append(name)
    return missing


def _validate_rtconfig_h(rtconfig_h, assignments):
    text = _read_text(rtconfig_h)
    defines = set()
    for line in text.splitlines():
        match = re.match(r"^\s*#define\s+([A-Za-z0-9_]+)(?:\s|$)", line)
        if match:
            defines.add(match.group(1))

    missing = []
    for config_name, _value in assignments:
        symbol = config_name[7:] if config_name.startswith("CONFIG_") else config_name
        if symbol not in defines:
            missing.append(symbol)
    return missing


def _select_noninteractive_config_option(project_path):
    options_path = project_path / "rt-thread" / "tools" / "options.py"
    if options_path.exists():
        text = _read_text(options_path)
        if re.search(r"AddOption\(\s*['\"]--defconfig['\"]", text):
            return "--defconfig"
        if re.search(r"AddOption\(\s*['\"]--pyconfig-silent['\"]", text):
            return "--pyconfig-silent"

    raise ConfigError(
        "current BSP RT-Thread tools do not expose a non-interactive "
        "Kconfig normalization command; manual mode remains available"
    )


def _run_scons(project_path, args, command_runner=None):
    if command_runner is None:
        scons = _find_scons()
        cmd = [scons] + list(args)
        completed = subprocess.run(
            cmd,
            cwd=str(project_path),
            check=False,
            text=True,
            capture_output=True,
            env=_build_scons_env(project_path),
        )
    else:
        cmd = ["scons"] + list(args)
        completed = command_runner(cmd, project_path)

    if completed.returncode != 0:
        raise ConfigError(_format_command_error(cmd, project_path, completed))

    return completed


def _build_scons_env(project_path):
    env = os.environ.copy()
    env.setdefault("BSP_ROOT", str(project_path))
    rtt_root = project_path / "rt-thread"
    if rtt_root.exists():
        env.setdefault("RTT_ROOT", str(rtt_root))

    pkgs_root = _find_pkgs_root(project_path)
    if pkgs_root:
        env["PKGS_ROOT"] = str(pkgs_root)

    return env


def _find_pkgs_root(project_path):
    candidates = []

    current = os.environ.get("PKGS_ROOT")
    if current:
        candidates.append(Path(current))

    candidates.extend([
        project_path / "packages",
        Path(r"C:\RT-ThreadStudio\platform\env_released\env\packages"),
        Path.home() / ".env" / "packages",
    ])

    for candidate in candidates:
        if (candidate / "Kconfig").exists():
            return candidate

    return None


def _find_scons():
    candidates = []
    for env_name in ("RT_AK_EDGI_SCONS", "SCONS"):
        value = os.environ.get(env_name)
        if value:
            candidates.append(value)

    for name in ("scons", "scons.bat"):
        found = shutil.which(name)
        if found:
            candidates.append(found)

    candidates.append(
        r"C:\RT-ThreadStudio\platform\env_released\env\tools\Python27\Scripts\scons.bat"
    )

    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate

    raise ConfigError(
        "scons executable not found; set RT_AK_EDGI_SCONS or add scons to PATH"
    )


def _format_command_error(cmd, cwd, completed):
    return (
        "command failed\n"
        "  command : {0}\n"
        "  cwd     : {1}\n"
        "  exit    : {2}\n"
        "  stdout  : {3}\n"
        "  stderr  : {4}"
    ).format(
        " ".join([str(item) for item in cmd]),
        cwd,
        completed.returncode,
        _summarize(completed.stdout),
        _summarize(completed.stderr),
    )


def _summarize(text, limit=2000):
    if text is None:
        return ""
    text = str(text).strip()
    if len(text) <= limit:
        return text
    return text[-limit:]


def _is_managed_block_header(lines, index):
    return (
        index + 2 < len(lines)
        and lines[index].strip() == "#"
        and lines[index + 1].strip() == "# {0}".format(MANAGED_BLOCK_TITLE)
        and lines[index + 2].strip() == "#"
    )


def _is_managed_symbol_line(line, managed):
    stripped = line.strip()
    for name in managed:
        if stripped == "{0}=y".format(name):
            return True
        if stripped == "{0}=n".format(name):
            return True
        if stripped.startswith("{0}=".format(name)):
            return True
        if stripped == "# {0} is not set".format(name):
            return True
    return False


def _read_text(path):
    return path.read_bytes().decode("utf-8")


def _read_text_keep_newline(path):
    data = path.read_bytes()
    text = data.decode("utf-8")
    newline = "\r\n" if b"\r\n" in data else "\n"
    return text, newline


def _write_text(path, text, newline):
    with path.open("w", encoding="utf-8", newline="") as f:
        f.write(text)


def _log(logger, message):
    if logger:
        logger(message)
