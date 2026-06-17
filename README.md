# RT-AK Edgi 插件教程

本文档说明如何把 Edgi Talk BSP 中已经跑通的 DeepCraft / Imagimob object_detect 模型接入 RT-AK，并通过 GitHub 下载插件完成一键生成、导出、配置、编译和板端验证。

当前插件面向 PSoC Edge E84 / Cortex-M55 / Ethos-U55 的 Edgi Talk 视觉推理工程，默认模型为 `object_detect`，输入为 `320x320 RGB888`，输出为 object detection 后处理所需的 float tensor。

## 1. 当前版本做到了什么

当前版本已经把三个层次分清楚：

```text
rt_ai_edgi_minimal_demo
    只验证标准 RT-AK API 是否能跑通模型。

rt_ai_edgi_runner_demo
    只验证配置化 runner 是否能通过 rt_ai_find/init/input/run/output 跑通模型。

usbh_uvc_start 0 320 240
    拉起真实 UVC 摄像头和 LCD 显示，并把每帧图像送入 RT-AK runner 推理后实时出框。
```

真实 UVC 链路现在是：

```text
UVC YUYV frame
-> YUYV 转 RGB888，直接写入 rt_ai_input()
-> rt_ai_run()
-> rt_ai_output()
-> object_detect 后处理
-> LCD overlay 实时画框
```

所以 `usbh_uvc_start` 仍然是摄像头和 LCD 的入口，但推理本身已经走 RT-AK 标准 API / runner 路径，不再只是调用原 BSP 的私有推理函数。

## 2. 准备环境

需要准备：

```text
RT-AK 主仓库
Edgi Talk BSP
RT-Thread Studio / Env 工具链
DeepCraft / Imagimob 生成的 model.c / model.h
```

Edgi Talk BSP 下载地址：

[RT-Thread-Studio/sdk-bsp-psoc_e84-edgi-talk](https://github.com/RT-Thread-Studio/sdk-bsp-psoc_e84-edgi-talk)

示例路径如下，请按你的实际机器修改：

```powershell
$RtAkTools = "C:\RT-AK\RT-AK\rt_ai_tools"
$Bsp = "C:\RT-ThreadStudio\workspace\Edgi_Talk_M55_DEEPCRAFT_Deploy_Vision"
$DeepCraftDir = "$Bsp\libraries\Common\deepcraft_ai\model"
```

路径含义：

```text
$RtAkTools
    RT-AK 主仓库里的 rt_ai_tools 目录，下面应有 aitools.py。

$Bsp
    Edgi Talk BSP 工程目录，下面应有 SConstruct、Kconfig、rtconfig.h。

$DeepCraftDir
    DeepCraft / Imagimob 生成模型目录，下面应有 model.c、model.h。
```

先检查路径：

```powershell
Test-Path "$RtAkTools\aitools.py"
Test-Path "$Bsp\SConstruct"
Test-Path "$Bsp\Kconfig"
Test-Path "$Bsp\rtconfig.h"
Test-Path "$DeepCraftDir\model.c"
Test-Path "$DeepCraftDir\model.h"
```

以上命令都应返回 `True`。

## 3. 在 RT-AK 中注册本插件

编辑 RT-AK 主仓库中的：

```text
RT-AK/rt_ai_tools/platforms/support_platforms.json
```

加入：

```json
{
  "plugin_edgi": "https://github.com/zwb725/RT-AK-EDTalk-demo.git"
}
```

注册后，RT-AK 使用 `--platform edgi` 时会从 GitHub 下载本插件。

如果要强制验证 GitHub 下载链路，可以先删除本地缓存插件：

```powershell
if (Test-Path "$RtAkTools\platforms\plugin_edgi") {
  Remove-Item -Recurse -Force "$RtAkTools\platforms\plugin_edgi"
}
```

只拉取插件，不生成、不导出：

```powershell
cd $RtAkTools

python aitools.py `
  --platform edgi `
  --pull_repo_only True
```

检查是否下载成功：

```powershell
Test-Path "$RtAkTools\platforms\plugin_edgi\plugin_edgi.py"
Test-Path "$RtAkTools\platforms\plugin_edgi\Kconfig"
Test-Path "$RtAkTools\platforms\plugin_edgi\examples\rt_ai_edgi_uvc_runner_app.c"
```

## 4. dry-run 检查

dry-run 只检查 BSP 和 DeepCraft 模型产物，不改 BSP 文件：

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

期望看到：

```text
BSP check     : OK
Model check   : OK
```

dry-run 会检查的关键内容：

```text
BSP:
    SConstruct
    Kconfig
    rtconfig.h
    applications/

DeepCraft model:
    model.c
    model.h
    IMAI_init
    IMAI_compute
    IMAI_finalize
    IMAI_api
```

## 5. 一键生成、导出、配置

推荐使用 `auto` 模式。它会生成 RT-AK 模型文件，导出插件文件到 BSP，并通过 Kconfig 流程更新 `.config` 和 `rtconfig.h`。

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

`auto` 模式会启用这些配置：

```text
CONFIG_RT_AI_USE_EDGI=y
CONFIG_RT_AI_USE_M55_ETHOSU=y
CONFIG_RT_AI_EDGI_MODEL_OBJECT_DETECT=y
CONFIG_RT_AI_EDGI_MINIMAL_DEMO=y
CONFIG_RT_AI_EDGI_RUNNER=y
CONFIG_RT_AI_EDGI_RUNNER_DEMO=y
CONFIG_RT_AI_EDGI_UVC_RUNNER_DEMO=y
```

导出到 BSP 的主要文件：

```text
applications/rt_ai_edgi/
    Kconfig
    SConscript
    rt_ai_edgi_active_model.h
    rt_ai_edgi_minimal_demo.c
    rt_ai_edgi_runner.c
    rt_ai_edgi_runner.h
    rt_ai_edgi_runner_demo.c
    generated/object_detect/rt_ai_object_detect_model.c
    generated/object_detect/rt_ai_object_detect_model.h
    generated/object_detect/rt_ai_edgi_demo_config.h

applications/uvc_ai_app.c
    UVC + LCD + RT-AK runner 推理示例

rt_ai_lib/backend_plugin_edgi/
    backend_edgi.c
    backend_edgi.h
    ethosu_rtos_rtthread.c
    SConscript
```

导出后检查日志：

```powershell
Select-String -Path ".\edgi_export_auto.log" -Pattern `
  "Edgi RT-AK model skeleton generated", `
  "Edgi RT-AK files exported", `
  "Configuration mode : auto", `
  "rtconfig.h           : regenerated", `
  "ERROR", `
  "Traceback"
```

检查 BSP 根 Kconfig 中只出现一次 Edgi source：

```powershell
(Select-String -Path "$Bsp\Kconfig" -Pattern "applications/rt_ai_edgi/Kconfig").Count
```

期望输出：

```text
1
```

检查 `.config`：

```powershell
Select-String -Path "$Bsp\.config" -Pattern `
  "CONFIG_RT_AI_USE_EDGI=y", `
  "CONFIG_RT_AI_USE_M55_ETHOSU=y", `
  "CONFIG_RT_AI_EDGI_MODEL_OBJECT_DETECT=y", `
  "CONFIG_RT_AI_EDGI_MINIMAL_DEMO=y", `
  "CONFIG_RT_AI_EDGI_RUNNER=y", `
  "CONFIG_RT_AI_EDGI_RUNNER_DEMO=y", `
  "CONFIG_RT_AI_EDGI_UVC_RUNNER_DEMO=y"
```

检查 `rtconfig.h`：

```powershell
Select-String -Path "$Bsp\rtconfig.h" -Pattern `
  "#define RT_AI_USE_EDGI", `
  "#define RT_AI_USE_M55_ETHOSU", `
  "#define RT_AI_EDGI_MODEL_OBJECT_DETECT", `
  "#define RT_AI_EDGI_MINIMAL_DEMO", `
  "#define RT_AI_EDGI_RUNNER", `
  "#define RT_AI_EDGI_RUNNER_DEMO", `
  "#define RT_AI_EDGI_UVC_RUNNER_DEMO"
```

检查文件是否导出：

```powershell
Test-Path "$Bsp\applications\rt_ai_edgi\SConscript"
Test-Path "$Bsp\applications\rt_ai_edgi\Kconfig"
Test-Path "$Bsp\applications\rt_ai_edgi\rt_ai_edgi_runner.c"
Test-Path "$Bsp\applications\rt_ai_edgi\rt_ai_edgi_runner_demo.c"
Test-Path "$Bsp\applications\rt_ai_edgi\generated\object_detect\rt_ai_object_detect_model.c"
Test-Path "$Bsp\applications\uvc_ai_app.c"
Test-Path "$Bsp\rt_ai_lib\backend_plugin_edgi\backend_edgi.c"
```

以上命令应全部返回 `True`。

## 6. manual 模式

如果你只想导出文件，然后自己通过 menuconfig 打开配置，可以使用 `manual` 模式：

```powershell
cd $RtAkTools

python aitools.py `
  --log .\edgi_export_manual.log `
  --project $Bsp `
  --platform edgi `
  --model_name object_detect `
  --deepcraft_dir $DeepCraftDir `
  --ethosu `
  --generate `
  --export `
  --config_mode manual
```

manual 模式只做：

```text
生成 generated/object_detect/
导出 applications/rt_ai_edgi/
导出 rt_ai_lib/backend_plugin_edgi/
导出 applications/uvc_ai_app.c
向 BSP 根 Kconfig 幂等追加 source "$BSP_DIR/applications/rt_ai_edgi/Kconfig"
向 applications/SConscript 幂等追加 RT-AK runner include path
```

manual 模式不会自动修改：

```text
.config
.config.old
rtconfig.h
```

之后需要进入 BSP 配置界面手动打开：

```powershell
cd $Bsp
scons --menuconfig
```

如果当前 RT-Thread Studio BSP 使用 pyconfig：

```powershell
scons --pyconfig
```

## 7. 编译 BSP

设置工具链路径：

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

成功后应生成：

```text
rt-thread.elf
Debug/rtthread.hex
```

编译日志中应能看到这些文件参与编译：

```text
rt_ai_lib\backend_plugin_edgi\backend_edgi.o
rt_ai_lib\rt_ai.o
rt_ai_lib\rt_ai_core.o
rt_ai_lib\rt_ai_runtime.o
applications\rt_ai_edgi\generated\object_detect\rt_ai_object_detect_model.o
applications\rt_ai_edgi\rt_ai_edgi_minimal_demo.o
applications\rt_ai_edgi\rt_ai_edgi_runner_demo.o
applications\uvc_ai_app.o
```

如果没有这些编译项，先检查 `rtconfig.h` 中是否有 `RT_AI_USE_EDGI` 和模型选择宏。

## 8. 烧录 hex

编译产物通常在：

```text
$Bsp\Debug\rtthread.hex
```

烧录方式按你的 Edgi Talk BSP / RT-Thread Studio 工程流程执行。本文档只描述插件导出、编译和板端命令验证。

## 9. 板端验证

上电后进入 MSH，先看命令：

```text
msh />help
```

应能看到：

```text
rt_ai_edgi_minimal_demo - run Edgi model through standard RT-AK API
rt_ai_edgi_runner_demo  - run Edgi model through config runner
usbh_uvc_start          - Start UVC stream: usbh_uvc_start [fmt] [w] [h]
usbh_uvc_stop           - Stop UVC stream
```

### 9.1 标准 RT-AK API 验证

运行：

```text
msh />rt_ai_edgi_minimal_demo
```

它验证：

```text
rt_ai_find("object_detect")
rt_ai_init()
rt_ai_input()
rt_ai_run()
rt_ai_output()
backend_edgi -> IMAI_compute()
```

期望日志：

```text
RT-AK Edgi minimal demo scheduled
RT-AK Edgi standard API demo start
rt_ai_find success: object_detect
rt_ai_init success
rt_ai_input success
rt_ai_run success
rt_ai_output success
RT-AK Edgi standard API demo end
```

这个 demo 使用固定 pattern 输入，不拉起摄像头，也不做 LCD overlay。它只证明 RT-AK 标准 API 到 Edgi backend 的模型调用链能跑通。

### 9.2 配置化 runner 验证

运行：

```text
msh />rt_ai_edgi_runner_demo
```

它验证：

```text
rt_ai_edgi_runner_default_config()
rt_ai_edgi_runner_init()
rt_ai_edgi_runner_input()
rt_ai_edgi_runner_run()
rt_ai_edgi_runner_output()
rt_ai_edgi_runner_deinit()
```

期望日志：

```text
RT-AK Edgi runner demo scheduled
RT-AK Edgi config runner start
model      : object_detect
input      : 307200 bytes, uint8
output     : 160 bytes, float32
preprocess : yuyv_rgb888_320
postprocess: object_detect_rps
runner out[000]: ...
RT-AK Edgi config runner end
```

这个 demo 仍然不拉起摄像头。它证明“模型差异通过配置表达，runner 固定调用 RT-AK API”的路径能工作。

### 9.3 UVC + LCD 实时推理验证

运行：

```text
msh />usbh_uvc_start 0 320 240
```

它验证完整真实链路：

```text
UVC 摄像头
YUYV frame
rt_ai_input()
rt_ai_run()
rt_ai_output()
object_detect 后处理
LCD overlay 出框
```

期望日志包含：

```text
RT-AK UVC runner ready
RT-AK UVC AI app started (async)
RT-AK UVC inference ... det=...
RT-AK UVC #0 ...
```

如果 UVC 段日志仍显示旧标签，例如：

```text
AI model initialized
AI app started (async)
AI inference ... det=...
```

这通常说明板端烧入的不是最新 UVC runner 固件，或该固件仍走原 BSP UVC AI 分支。验证当前版本时，应以 `RT-AK UVC runner ready` 和 `RT-AK UVC inference` 为准。

LCD 应实时显示摄像头画面，并在 Rock / Paper / Scissors 目标上实时出框。

停止：

```text
msh />usbh_uvc_stop
```

建议做一次生命周期回归：

```text
usbh_uvc_start 0 320 240
usbh_uvc_stop
usbh_uvc_start 0 320 240
usbh_uvc_stop
```

## 10. 常见问题

### 10.1 为什么是 `usbh_uvc_start`，不是直接 `rt_ai_run`

`rt_ai_run` 只负责模型推理，不负责摄像头和 LCD。

真实视频推理需要先拉起 UVC 数据流，因此入口仍然是：

```text
usbh_uvc_start 0 320 240
```

但在当前版本中，每帧图像进入应用层后会走：

```text
rt_ai_input()
rt_ai_run()
rt_ai_output()
```

也就是说，摄像头入口保留，推理路径已经接入 RT-AK。

### 10.2 `rt_ai_edgi_runner_demo` 跑通了什么

它跑通的是配置化 runner 的 RT-AK 调用链，不是摄像头链路：

```text
配置
-> rt_ai_find
-> rt_ai_init
-> rt_ai_input
-> rt_ai_run
-> rt_ai_output
-> rt_ai_deinit
```

它的输入是固定 pattern，用于验证 runner 和 backend，不用于判断识别效果。

### 10.3 `rt_ai_edgi_rtak_api_demo: command not found`

当前命令名不是 `rt_ai_edgi_rtak_api_demo`。

请使用：

```text
rt_ai_edgi_minimal_demo
rt_ai_edgi_runner_demo
```

以 `help` 中实际列出的命令为准。

### 10.4 `thread:tshell stack overflow`

旧版本曾直接在 shell 线程里跑推理，容易压爆 tshell 栈。当前版本的 `rt_ai_edgi_minimal_demo` 和 `rt_ai_edgi_runner_demo` 都会调度到独立 worker thread 中执行。

如果仍看到该问题，请确认固件来自最新 GitHub 插件重新导出并编译，而不是旧 BSP 产物。

### 10.5 `RT-AK Edgi: no model selected`

说明插件已启用，但模型选择宏没有进入 `rtconfig.h`。

检查：

```powershell
Select-String -Path "$Bsp\rtconfig.h" -Pattern `
  "RT_AI_USE_EDGI", `
  "RT_AI_EDGI_MODEL_OBJECT_DETECT"
```

如果缺失，重新执行：

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

### 10.6 auto 模式报 packages/Kconfig 找不到

设置 RT-Thread Studio packages 路径：

```powershell
$env:PKGS_ROOT = "C:\RT-ThreadStudio\platform\env_released\env\packages"
```

然后重新执行 auto 导出命令。

## 11. 重新验证 GitHub 最新版本

如果你要确认 RT-AK 一键导出确实使用 GitHub 最新插件，而不是本地旧缓存，按下面顺序执行：

```powershell
if (Test-Path "$RtAkTools\platforms\plugin_edgi") {
  Remove-Item -Recurse -Force "$RtAkTools\platforms\plugin_edgi"
}

cd $RtAkTools

python aitools.py `
  --platform edgi `
  --pull_repo_only True

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

然后重新编译：

```powershell
cd $Bsp
scons -c
scons -j6
```

板端再验证：

```text
rt_ai_edgi_minimal_demo
rt_ai_edgi_runner_demo
usbh_uvc_start 0 320 240
usbh_uvc_stop
```

如果 `usbh_uvc_start 0 320 240` 能拉起摄像头、LCD 实时显示并出现 `RT-AK UVC inference` 日志，就说明 GitHub 最新插件版本已经打通“RT-AK API + UVC 实时出框”闭环。

## 12. 版本结论与实测记录

当前版本结论：

```text
P0 当前版本固化:
    README 已更新为教程型技术文档
    GitHub 插件下载链路已验证
    干净 RT-AK + 干净 BSP + 最新插件可导出、配置、编译并生成 hex

P1 标准 RT-AK API 对齐:
    rt_ai_find("object_detect") 跑通
    rt_ai_init() 跑通
    rt_ai_input() 跑通
    rt_ai_run() 跑通
    rt_ai_output() 跑通

P2 UVC demo 与 RT-AK runner 接通:
    usbh_uvc_start 0 320 240 保留为摄像头和 LCD 入口
    每帧 YUYV 输入转换后写入 RT-AK input buffer
    UVC 推理阶段走 RT-AK runner
    后处理结果进入 LCD overlay

P3 Kconfig / menuconfig 正规化:
    RT_AI_USE_EDGI 已进入 Kconfig
    RT_AI_USE_M55_ETHOSU 已进入 Kconfig
    RT_AI_EDGI_RUNNER_DEMO 已进入 Kconfig
    RT_AI_EDGI_UVC_RUNNER_DEMO 已进入 Kconfig
    auto 模式可更新 .config 并重新生成 rtconfig.h
```

2026-06-17 已完成一次 GitHub 最新插件闭环验证：

```text
验证目录:
    C:\demo-vetify0.4

插件来源:
    https://github.com/zwb725/RT-AK-EDTalk-demo.git

插件提交:
    9ca4a25 或更新版本

验证流程:
    干净 RT-AK clone
    干净 sdk-bsp-psoc_e84-edgi-talk clone
    RT-AK pull_repo_only 从 GitHub 下载 plugin_edgi
    aitools.py --dry_run
    aitools.py --generate --export --config_mode auto
    scons -c
    scons -j6
    OpenOCD 烧录 Debug/rtthread.hex
```

编译产物：

```text
C:\demo-vetify0.4\sdk-bsp-psoc_e84-edgi-talk\projects\Edgi_Talk_M55_DEEPCRAFT_Deploy_Vision\Debug\rtthread.hex

rtthread.hex SHA256:
    4357C67B34E3AB35C79F37C8793602B3055ED2AB96FDDA914E11750B8C487467
```

板端实测日志结论：

```text
rt_ai_edgi_minimal_demo:
    rt_ai_find success: object_detect
    rt_ai_init success
    rt_ai_input success
    rt_ai_run success
    rt_ai_output success
    RT-AK Edgi standard API demo end

rt_ai_edgi_runner_demo:
    model      : object_detect
    input      : 307200 bytes, uint8
    output     : 160 bytes, float32
    preprocess : yuyv_rgb888_320
    postprocess: object_detect_rps
    [RT-AK][Edgi][runner] init model=object_detect input=307200 output=160
    RT-AK Edgi config runner end

usbh_uvc_start 0 320 240:
    UVC start: 320x240 format=yuyv
    LCD: 512x800 16bpp
    [RT-AK][Edgi][runner] init model=object_detect input=307200 output=160
    RT-AK UVC runner ready
    RT-AK UVC AI app started (async)
    RT-AK UVC inference 74-75 ms, prep 10-11 ms, npu 33.6 ms
    LCD 实时显示链路正常

UVC 流恢复:
    出现过 uvc abort1
    随后 UVC stream restart
    后续继续出现 RT-AK UVC inference

usbh_uvc_stop:
    RT-AK UVC AI app stopped
    UVC stopped
```

最终验收结论：

```text
标准 RT-AK API 闭环已跑通
配置化 runner 闭环已跑通
UVC + LCD 实时推理闭环已接入 RT-AK runner
GitHub 最新插件一键下载、导出、配置、编译、烧录验证闭环已跑通
```

`uvc abort1` 如果出现在流切换或停止阶段，且后续出现 `UVC stream restart`、`RT-AK UVC inference` 或 `UVC stopped`，按非致命 UVC 生命周期日志处理。
