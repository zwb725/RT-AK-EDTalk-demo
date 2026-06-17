# coding=utf-8

import shutil
import tempfile
import unittest

from pathlib import Path
from types import SimpleNamespace

from configure_project import (
    ConfigError,
    KCONFIG_SOURCE_LINE,
    _merge_config_fragment,
    configure_project,
)


FRAGMENT_TEXT = """CONFIG_RT_AI_USE_EDGI=y
CONFIG_RT_AI_USE_M55_ETHOSU=y
CONFIG_RT_AI_EDGI_MODEL_OBJECT_DETECT=y
CONFIG_RT_AI_EDGI_MINIMAL_DEMO=y
CONFIG_RT_AI_EDGI_RUNNER=y
CONFIG_RT_AI_EDGI_RUNNER_DEMO=y
"""


MANAGED_CONFIGS = [
    "CONFIG_RT_AI_USE_EDGI",
    "CONFIG_RT_AI_USE_M55_ETHOSU",
    "CONFIG_RT_AI_EDGI_MODEL_OBJECT_DETECT",
    "CONFIG_RT_AI_EDGI_MINIMAL_DEMO",
    "CONFIG_RT_AI_EDGI_RUNNER",
    "CONFIG_RT_AI_EDGI_RUNNER_DEMO",
]


class ConfigureProjectTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="rtak_edgi_test_"))
        self.fragment = self.tmp / "edgi_default.config"
        self.fragment.write_text(FRAGMENT_TEXT, encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(str(self.tmp), ignore_errors=True)

    def _make_project(self, with_dot_config=True):
        project = self.tmp / "bsp"
        (project / "applications" / "rt_ai_edgi").mkdir(parents=True)
        (project / "rt-thread" / "tools").mkdir(parents=True)
        (project / "SConstruct").write_text("# test\n", encoding="utf-8")
        (project / "Kconfig").write_text(KCONFIG_SOURCE_LINE + "\n", encoding="utf-8")
        (project / "applications" / "rt_ai_edgi" / "Kconfig").write_text(
            """
menuconfig RT_AI_USE_EDGI
    bool "Enable RT-AK Edgi backend"
    default n

if RT_AI_USE_EDGI

choice
    prompt "Select Edgi AI model"
    default RT_AI_EDGI_MODEL_OBJECT_DETECT

config RT_AI_EDGI_MODEL_OBJECT_DETECT
    bool "Object detect model"

endchoice

config RT_AI_USE_M55_ETHOSU
    bool "Enable Cortex-M55 / Ethos-U55 runtime binding"
    default y

config RT_AI_EDGI_MINIMAL_DEMO
    bool "Enable Edgi RT-AK minimal MSH demo"
    default y

config RT_AI_EDGI_RUNNER
    bool "Enable Edgi RT-AK config runner API"
    default y

config RT_AI_EDGI_RUNNER_DEMO
    bool "Enable Edgi RT-AK config runner demo"
    depends on RT_AI_EDGI_RUNNER
    default y

endif
""".lstrip(),
            encoding="utf-8",
        )
        (project / "rtconfig.h").write_text(
            "#ifndef RT_CONFIG_H__\n#define RT_CONFIG_H__\n#endif\n",
            encoding="utf-8",
        )
        (project / "rt-thread" / "tools" / "options.py").write_text(
            "AddOption('--pyconfig-silent')\n", encoding="utf-8"
        )

        if with_dot_config:
            (project / ".config").write_text("CONFIG_RT_USING_FINSH=y\n", encoding="utf-8")

        return project

    def _runner(self, fail_on=None):
        calls = []

        def run(cmd, cwd):
            calls.append(list(cmd))
            option = cmd[-1]
            if fail_on and option == fail_on:
                return SimpleNamespace(returncode=1, stdout="failed stdout", stderr="failed stderr")

            if option == "--genconfig":
                (Path(cwd) / ".config").write_text(
                    "CONFIG_RT_USING_FINSH=y\n", encoding="utf-8"
                )

            if option == "--pyconfig-silent":
                text = (Path(cwd) / ".config").read_text(encoding="utf-8")
                (Path(cwd) / ".config").write_text(text, encoding="utf-8")
                header = ["#ifndef RT_CONFIG_H__", "#define RT_CONFIG_H__", ""]
                for line in text.splitlines():
                    if not line.startswith("CONFIG_") or not line.endswith("=y"):
                        continue
                    header.append("#define {0}".format(line[7:-2]))
                header.extend(["", "#endif", ""])
                (Path(cwd) / "rtconfig.h").write_text("\n".join(header), encoding="utf-8")

            return SimpleNamespace(returncode=0, stdout="ok", stderr="")

        run.calls = calls
        return run

    def test_config_missing_runs_genconfig(self):
        project = self._make_project(with_dot_config=False)
        runner = self._runner()

        configure_project(str(project), "auto", str(self.fragment), command_runner=runner)

        self.assertIn(["scons", "--genconfig"], runner.calls)
        self.assertTrue((project / ".config").exists())

    def test_closed_config_is_enabled(self):
        dot_config = self.tmp / ".config"
        dot_config.write_text("# CONFIG_RT_AI_USE_EDGI is not set\n", encoding="utf-8")

        _merge_config_fragment(dot_config, self.fragment)

        text = dot_config.read_text(encoding="utf-8")
        self.assertIn("CONFIG_RT_AI_USE_EDGI=y", text)
        self.assertNotIn("# CONFIG_RT_AI_USE_EDGI is not set", text)

    def test_idempotent_existing_enabled_config(self):
        dot_config = self.tmp / ".config"
        dot_config.write_text(FRAGMENT_TEXT, encoding="utf-8")

        _merge_config_fragment(dot_config, self.fragment)
        _merge_config_fragment(dot_config, self.fragment)

        text = dot_config.read_text(encoding="utf-8")
        for symbol in MANAGED_CONFIGS:
            self.assertEqual(text.count(symbol + "=y"), 1)

    def test_preserves_unrelated_config(self):
        dot_config = self.tmp / ".config"
        dot_config.write_text(
            "CONFIG_RT_USING_FINSH=y\nCONFIG_USB_HOST=y\n", encoding="utf-8"
        )

        _merge_config_fragment(dot_config, self.fragment)

        text = dot_config.read_text(encoding="utf-8")
        self.assertIn("CONFIG_RT_USING_FINSH=y", text)
        self.assertIn("CONFIG_USB_HOST=y", text)

    def test_defconfig_failure_restores_config_files(self):
        project = self._make_project(with_dot_config=True)
        original_config = (project / ".config").read_text(encoding="utf-8")
        original_header = (project / "rtconfig.h").read_text(encoding="utf-8")
        runner = self._runner(fail_on="--pyconfig-silent")

        with self.assertRaises(ConfigError):
            configure_project(str(project), "auto", str(self.fragment), command_runner=runner)

        self.assertEqual((project / ".config").read_text(encoding="utf-8"), original_config)
        self.assertEqual((project / "rtconfig.h").read_text(encoding="utf-8"), original_header)


if __name__ == "__main__":
    unittest.main()
