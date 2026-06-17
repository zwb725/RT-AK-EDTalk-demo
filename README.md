# RT-AK Edgi 插件教程

本教程说明如何把 Edgi Talk PSoC Edge E84 的 `object_detect` 视觉模型接入 RT-AK，并通过插件完成生成、导出、配置、编译和板端验证。

当前版本的目标不是替换 UVC 入口，而是让真实视频推理链路接入 RT-AK：

```text
UVC YUYV frame
-> RGB888 写入 rt_ai_input()
-> rt_ai_run()
-> 读取 rt_ai_output()
-> object_detect 后处理
-> LCD overlay 实时出框
```

板端有三个验证命令：

```text
rt_ai_edgi_minimal_demo    验证标准 RT-AK API
rt_ai_edgi_runner_demo     验证配置化 runner
usbh_uvc_start 0 320 240   拉起 UVC、RT-AK 推理和 LCD 出框
```

## 1. 准备环境

需要准备：

```text
RT-AK 主仓库
Edgi Talk BSP
RT-Thread Studio / Env 工具链
DeepCraft / Imagimob 生成的 model.c / model.h
```

Edgi Talk BSP 下载地址：

[RT-Thread-Studio/sdk-bsp-psoc_e84-edgi-talk](https://github.com/RT-Thread-Studio/sdk-bsp-psoc_e84-edgi-talk)

示例路径：

```powershell
$RtAkTools = "C:\RT-AK\RT-AK\rt_ai_tools"
$Bsp = "C:\RT-ThreadStudio\workspace\Edgi_Talk_M55_DEEPCRAFT_Deploy_Vision"
$DeepCraftDir = "$Bsp\libraries\Common\deepcraft_ai\model"
```

检查路径：

```powershell
Test-Path "$RtAkTools\aitools.py"
Test-Path "$Bsp\SConstruct"
Test-Path "$Bsp\Kconfig"
Test-Path "$DeepCraftDir\model.c"
Test-Path "$DeepCraftDir\model.h"
```

以上命令都应返回 `True`。

## 2. 注册插件

编辑 RT-AK 仓库中的：

```text
RT-AK/rt_ai_tools/platforms/support_platforms.json
```

加入：

```json
{
  "plugin_edgi": "https://github.com/zwb725/RT-AK-EDTalk-demo.git"
}
```

强制从 GitHub 重新下载插件：

```powershell
if (Test-Path "$RtAkTools\platforms\plugin_edgi") {
  Remove-Item -Recurse -Force "$RtAkTools\platforms\plugin_edgi"
}

cd $RtAkTools

python aitools.py `
  --platform edgi `
  --pull_repo_only True
```

检查下载结果：

```powershell
Test-Path "$RtAkTools\platforms\plugin_edgi\plugin_edgi.py"
Test-Path "$RtAkTools\platforms\plugin_edgi\Kconfig"
Test-Path "$RtAkTools\platforms\plugin_edgi\examples\rt_ai_edgi_uvc_runner_app.c"
```

## 3. Dry-Run 检查

`dry_run` 只检查 BSP 和模型产物，不修改 BSP。

```powershell
cd $RtAkTools

python aitools.py `
  --log .\edgi_dryrun.log `
  --project $Bsp `
  --platform edgi `
  --model_name object_detect `
  --deepcraft_dir $DeepCraftDir `
  --dry_run
```

检查日志：

```powershell
Select-String -Path ".\edgi_dryrun.log" -Pattern `
  "BSP check", `
  "Model check", `
  "FAILED", `
  "ERROR", `
  "Traceback"
```

期望结果：

```text
BSP check     : OK
Model check   : OK
```

## 4. 一键生成、导出、配置

推荐使用 `config_mode auto`。它会生成 RT-AK 模型文件，导出插件文件到 BSP，更新 `.config`，并重新生成 `rtconfig.h`。

```powershell
cd $RtAkTools

python aitools.py `
  --log .\edgi_export_auto.log `
  --project $Bsp `
  --platform edgi `
  --model_name object_detect `
  --deepcraft_dir $DeepCraftDir `
  --ethosu `
  --generate `
  --export `
  --config_mode auto
```

`auto` 模式会启用：

```text
CONFIG_RT_AI_USE_EDGI=y
CONFIG_RT_AI_USE_M55_ETHOSU=y
CONFIG_RT_AI_EDGI_MODEL_OBJECT_DETECT=y
CONFIG_RT_AI_EDGI_MINIMAL_DEMO=y
CONFIG_RT_AI_EDGI_RUNNER=y
CONFIG_RT_AI_EDGI_RUNNER_DEMO=y
CONFIG_RT_AI_EDGI_UVC_RUNNER_DEMO=y
```

检查导出日志和关键宏：

```powershell
Select-String -Path ".\edgi_export_auto.log" -Pattern `
  "Edgi RT-AK model skeleton generated", `
  "Edgi RT-AK files exported", `
  "Configuration mode : auto", `
  "rtconfig.h           : regenerated", `
  "ERROR", `
  "Traceback"

Select-String -Path "$Bsp\rtconfig.h" -Pattern `
  "RT_AI_USE_EDGI", `
  "RT_AI_USE_M55_ETHOSU", `
  "RT_AI_EDGI_MODEL_OBJECT_DETECT", `
  "RT_AI_EDGI_UVC_RUNNER_DEMO"
```

导出后的 BSP 应包含：

```text
applications/rt_ai_edgi/
applications/uvc_ai_app.c
rt_ai_lib/backend_plugin_edgi/
```

## 5. 编译 BSP

设置工具链：

```powershell
$env:RTT_EXEC_PATH = "C:\RT-ThreadStudio\platform\env_released\env\tools\gnu_gcc\arm_gcc\mingw\bin"
$env:PKGS_ROOT = "C:\RT-ThreadStudio\platform\env_released\env\packages"
```

编译：

```powershell
cd $Bsp
scons -c
scons -j6
```

期望产物：

```text
rt-thread.elf
Debug/rtthread.hex
```

## 6. 烧录

固件产物通常为：

```text
$Bsp\Debug\rtthread.hex
```

使用 Edgi Talk BSP / RT-Thread Studio 对应的 OpenOCD 流程烧录该 hex。烧录完成后打开串口，进入 MSH。

## 7. 板端验证

先查看命令：

```text
msh />help
```

应能看到：

```text
rt_ai_edgi_minimal_demo
rt_ai_edgi_runner_demo
usbh_uvc_start
usbh_uvc_stop
```

### 7.1 标准 RT-AK API

```text
msh />rt_ai_edgi_minimal_demo
```

关键日志：

```text
rt_ai_find success: object_detect
rt_ai_init success
rt_ai_input success
rt_ai_run success
rt_ai_output success
RT-AK Edgi standard API demo end
```

这个命令验证：

```text
rt_ai_find -> rt_ai_init -> rt_ai_input -> rt_ai_run -> rt_ai_output
```

### 7.2 配置化 Runner

```text
msh />rt_ai_edgi_runner_demo
```

关键日志：

```text
RT-AK Edgi config runner start
model      : object_detect
input      : 307200 bytes, uint8
output     : 160 bytes, float32
preprocess : yuyv_rgb888_320
postprocess: object_detect_rps
RT-AK Edgi config runner end
```

这个命令验证模型名、输入大小、输出大小、前处理和后处理都可以由配置表达。

### 7.3 UVC + LCD 实时推理

```text
msh />usbh_uvc_start 0 320 240
```

关键日志：

```text
UVC start: 320x240 format=yuyv
RT-AK UVC runner ready
RT-AK UVC AI app started (async)
RT-AK UVC inference ... det=...
```

LCD 应实时显示摄像头画面并绘制检测框。

停止：

```text
msh />usbh_uvc_stop
```

关键日志：

```text
RT-AK UVC AI app stopped
UVC stopped
```

如果 UVC 日志仍显示 `AI inference`，而不是 `RT-AK UVC inference`，通常说明烧录的不是最新插件导出的固件。

## 8. 常见问题

### command not found

以 `help` 输出为准。当前标准 API demo 命令是 `rt_ai_edgi_minimal_demo`，不是 `rt_ai_edgi_rtak_api_demo`。

### no model selected

检查 `rtconfig.h`：

```powershell
Select-String -Path "$Bsp\rtconfig.h" -Pattern `
  "RT_AI_USE_EDGI", `
  "RT_AI_EDGI_MODEL_OBJECT_DETECT"
```

如果缺失，重新执行第 4 节的 auto 导出命令。

### packages/Kconfig not found

先设置：

```powershell
$env:PKGS_ROOT = "C:\RT-ThreadStudio\platform\env_released\env\packages"
```

再重新执行 `config_mode auto`。

### uvc abort1

如果 `uvc abort1` 出现在流重启或停止阶段，并且后续还能继续推理或正常 `UVC stopped`，按非致命生命周期日志处理。

## 9. 版本结论

2026-06-17 已验证：

```text
GitHub 插件下载、导出、配置、编译和板端验证通过
rt_ai_find/init/input/run/output 路径通过
配置化 runner 路径通过
usbh_uvc_start 0 320 240 可拉起 RT-AK UVC inference
LCD 实时显示和 overlay 出框通过
usbh_uvc_stop 通过
```

当前完成度：

```text
P0 当前版本固化: 完成
P1 标准 RT-AK API 对齐: 完成
P2 UVC demo 与 RT-AK runner 接通: 完成
P3 Kconfig / menuconfig 正规化: 完成
```
