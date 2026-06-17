# RT-AK Edgi 插件使用教程

本仓库是 Edgi Talk / DeepCraft / Cortex-M55 / Ethos-U55 视觉推理工程的 RT-AK 平台插件。它的目标是把现有 Edgi BSP 中已经可运行的 DeepCraft 模型推理链路，接入 RT-AK 的标准模型注册和调用路径。

当前版本面向单模型 `object_detect`，已验证的标准调用形式如下：

```c
rt_ai_t model;
void *input;
void *output;

model = rt_ai_find("object_detect");
rt_ai_init(model, RT_NULL);

input = rt_ai_input(model, 0);
rt_ai_run(model, RT_NULL, RT_NULL);
output = rt_ai_output(model, 0);
```

插件不会把 UVC 摄像头、LCD overlay、后处理业务逻辑塞进 backend。backend 只负责把 RT-AK runtime 调用转接到 Edgi / DeepCraft runtime。

## 1. 适用范围

当前教程基于以下工程形态：

```text
RT-AK 主仓库
Edgi_Talk_M55_DEEPCRAFT_Deploy_Vision BSP
DeepCraft / Imagimob 生成产物：model.c / model.h
Cortex-M55 + Ethos-U55 推理 runtime
RT-Thread SCons 构建系统
```

当前支持：

```text
模型名称：object_detect
输入尺寸：320 x 320 x 3
输入格式：RGB888
输出尺寸：5 x 8
板端 demo：rt_ai_edgi_minimal_demo
真实链路：UVC -> RT-AK API -> backend_edgi -> IMAI_compute -> LCD overlay
```

## 2. 插件导出的内容

执行 `--generate --export` 后，插件会向 BSP 导出两类文件。

应用侧文件：

```text
applications/rt_ai_edgi/
├── Kconfig
├── SConscript
├── rt_ai_edgi_active_model.h
├── rt_ai_edgi_minimal_demo.c
└── generated/
    └── object_detect/
        ├── rt_ai_object_detect_model.c
        ├── rt_ai_object_detect_model.h
        └── rt_ai_edgi_demo_config.h
```

RT-AK runtime / backend 文件：

```text
rt_ai_lib/
├── rt_ai.c
├── rt_ai_common.c
├── rt_ai_core.c
├── rt_ai_runtime.c
├── include/
└── backend_plugin_edgi/
    ├── backend_edgi.c
    ├── backend_edgi.h
    ├── ethosu_rtos_rtthread.c
    └── SConscript
```

`backend_edgi.c` 只会导出到 `rt_ai_lib/backend_plugin_edgi`。`applications/rt_ai_edgi` 下不会再保留一份 backend 副本，避免 multiple definition。

## 3. 准备路径

先准备 Edgi Talk BSP。官方 BSP 仓库：

```text
https://github.com/RT-Thread-Studio/sdk-bsp-psoc_e84-edgi-talk
```

可以用 Git 下载：

```powershell
git clone https://github.com/RT-Thread-Studio/sdk-bsp-psoc_e84-edgi-talk.git
```

也可以通过 RT-Thread Studio 导入该 BSP 工程。导入后，本教程中的 BSP 路径示例对应：

```text
Edgi_Talk_M55_DEEPCRAFT_Deploy_Vision
```

下面示例使用 PowerShell。请按你的实际路径设置变量：

```powershell
$RtAkTools = "C:\RT-AK\RT-AK\rt_ai_tools"
$Bsp = "C:\RT-ThreadStudio\workspace\Edgi_Talk_M55_DEEPCRAFT_Deploy_Vision"
$DeepCraftDir = "$Bsp\libraries\Common\deepcraft_ai\model"
```

BSP 中至少需要存在：

```text
SConstruct
Kconfig
rtconfig.h
applications/
libraries/Common/deepcraft_ai/model/model.c
libraries/Common/deepcraft_ai/model/model.h
```

`rtconfig.h` 必须已是一个可工作的基础 BSP 配置。当前插件的 auto 配置模式不是从空工程创建 BSP 配置，而是在已有 BSP 配置上追加 Edgi RT-AK 配置。

## 4. 在 RT-AK 中注册插件（个人仓库临时方案）

修改 RT-AK 主仓库的：

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

可以先只验证下载：

```powershell
cd $RtAkTools

python aitools.py `
  --platform edgi `
  --pull_repo_only True
```

## 5. dry-run 检查

dry-run 只检查 BSP 和 DeepCraft 模型产物，不导出文件：

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

期望结果：

```text
BSP check   : OK
Model check : OK
```

dry-run 会检查：

```text
BSP 路径
SConstruct
rtconfig.h
applications/
model.c
model.h
IMAI_init
IMAI_compute
IMAI_finalize
IMAI_api
```

## 6. 生成和导出

插件提供两种配置模式：

```text
manual：默认模式，只导出文件并接入 Kconfig，不自动修改 .config / rtconfig.h
auto  ：导出后自动合并 .config，并通过 RT-Thread 配置系统重新生成 rtconfig.h
```

### 6.1 manual 模式

manual 是默认模式，适合希望通过 menuconfig 手动开关插件的场景：

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

manual 模式会完成：

```text
生成 rt_ai_object_detect_model.c/h
生成 rt_ai_edgi_demo_config.h
导出 applications/rt_ai_edgi
导出 rt_ai_lib/backend_plugin_edgi
向 BSP 根 Kconfig 幂等追加 source "$BSP_DIR/applications/rt_ai_edgi/Kconfig"
```

manual 模式不会修改：

```text
.config
.config.old
rtconfig.h
```

导出后进入 BSP 配置界面启用插件：

```powershell
cd $Bsp
scons --menuconfig
```

在部分 Windows RT-Thread Studio BSP 中，命令入口可能是：

```powershell
scons --pyconfig
```

保存配置后，确认 `.config` 中存在：

```text
CONFIG_RT_AI_USE_EDGI=y
CONFIG_RT_AI_USE_M55_ETHOSU=y
CONFIG_RT_AI_EDGI_MODEL_OBJECT_DETECT=y
CONFIG_RT_AI_EDGI_MINIMAL_DEMO=y
```

确认 `rtconfig.h` 中存在：

```c
#define RT_AI_USE_EDGI
#define RT_AI_USE_M55_ETHOSU
#define RT_AI_EDGI_MODEL_OBJECT_DETECT
#define RT_AI_EDGI_MINIMAL_DEMO
```

### 6.2 auto 模式

auto 模式适合一条 RT-AK 命令完成导出和配置落地：

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

auto 模式的配置来源是：

```text
configs/edgi_default.config
```

默认内容：

```text
CONFIG_RT_AI_USE_EDGI=y
CONFIG_RT_AI_USE_M55_ETHOSU=y
CONFIG_RT_AI_EDGI_MODEL_OBJECT_DETECT=y
CONFIG_RT_AI_EDGI_MINIMAL_DEMO=y
```

auto 模式流程：

```text
检查 BSP SConstruct / Kconfig / rtconfig.h
检查 applications/rt_ai_edgi/Kconfig 已导出
检查 BSP 根 Kconfig 中 Edgi source 只有一次
必要时执行 scons --genconfig 生成 .config
合并 configs/edgi_default.config 到 .config
调用 BSP 本地 RT-Thread 非交互配置命令
重新生成 rtconfig.h
校验 .config 和 rtconfig.h 中的四个目标宏
```

在本地 RT-Thread 工具支持 `--defconfig` 时优先使用该命令；在 RT-Thread Studio Windows BSP 中通常使用 `--pyconfig-silent`。插件不会直接向 `rtconfig.h` 追加 `#define`。

auto 模式修改配置文件前会临时备份：

```text
.config
.config.old
rtconfig.h
```

如果配置生成或校验失败，会恢复原文件，不会留下长期 `.bak` / `.tmp` 文件。导出的插件源码不会回滚。

## 7. 编译 BSP

设置工具链路径：

```powershell
$env:RTT_EXEC_PATH = "C:\RT-ThreadStudio\platform\env_released\env\tools\gnu_gcc\arm_gcc\mingw\bin"
```

如果 BSP 的 Kconfig 依赖 RT-Thread Studio 自带 packages 索引，也可以设置：

```powershell
$env:PKGS_ROOT = "C:\RT-ThreadStudio\platform\env_released\env\packages"
```

编译：

```powershell
cd $Bsp
scons -c
scons -j6
```

成功时应生成：

```text
rt-thread.elf
Debug/rtthread.hex
```

编译日志中应能看到插件源码参与编译：

```text
CC build\rt_ai_lib\backend_plugin_edgi\backend_edgi.o
CC build\rt_ai_lib\rt_ai.o
CC build\rt_ai_lib\rt_ai_core.o
CC build\rt_ai_lib\rt_ai_runtime.o
CC applications\rt_ai_edgi\generated\object_detect\rt_ai_object_detect_model.o
CC applications\rt_ai_edgi\rt_ai_edgi_minimal_demo.o
```

如果没有这些编译项，说明 `RT_AI_USE_EDGI` 或模型选择宏没有进入 `rtconfig.h`，需要回到第 6 节检查配置。

## 8. 板端验证

烧录由 BSP / RT-Thread Studio 流程完成。启动后在 MSH 中检查命令：

```text
msh />help
```

应看到：

```text
rt_ai_edgi_minimal_demo - run Edgi model through standard RT-AK API
usbh_uvc_start
usbh_uvc_stop
```

### 8.1 minimal demo

运行：

```text
msh />rt_ai_edgi_minimal_demo
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

该 demo 使用固定 pattern 输入，只用于验证 RT-AK API、backend、input/output buffer 和 `IMAI_compute` 调用链路，不用于判断模型语义。

### 8.2 UVC 实时推理

启动 320x240 YUYV 摄像头输入：

```text
msh />usbh_uvc_start 0 320 240
```

期望日志摘要：

```text
[I/uvc_app] UVC start: 320x240 format=yuyv
[I/uvc_disp] LCD: 512x800 16bpp
[I/uvc_ai] AI clocks cpu=399MHz npu=399MHz cache=2
[I/uvc_ai] AI model initialized
[I/uvc_ai_app] AI app started (async)
[I/uvc_ai] AI inference ... det=...
[I/uvc_ai] AI #0 Rock / Paper / Scissors ... bbox=[...]
```

LCD 应实时显示 Rock / Paper / Scissors 检测框。

停止：

```text
msh />usbh_uvc_stop
```

期望看到：

```text
[I/uvc_ai] AI model deinitialized
[I/uvc_ai_app] AI app stopped
[I/uvc_app] UVC stopped
```

建议做一次生命周期回归：

```text
usbh_uvc_start 0 320 240
usbh_uvc_stop
usbh_uvc_start 0 320 240
usbh_uvc_stop
```

当前已验证 stop 后再次 start 可以恢复 AI 推理和 LCD overlay。stop 过程中如果出现 `uvc abort1` / `uvc abort2`，但仍然完成 AI deinit、UVC stopped，并且后续能再次 start，按非致命 stop 日志处理。

## 9. 关键实现说明

### 9.1 模型注册

生成文件：

```text
generated/object_detect/rt_ai_object_detect_model.c
generated/object_detect/rt_ai_object_detect_model.h
```

注册路径：

```text
INIT_APP_EXPORT(rt_ai_object_detect_model_register)
-> rt_ai_register()
-> backend_edgi()
-> object_detect 注册到 RT-AK core
```

生成文件不再提供 `rt_ai_object_detect_model_*()` 兼容 wrapper。应用侧应统一使用标准 RT-AK API。

### 9.2 backend

backend 关键映射：

```text
backend_edgi_init()
-> IMAI_init()

backend_edgi_run(input, output)
-> IMAI_compute(input, output)

backend_edgi_deinit()
-> IMAI_finalize()
```

backend 不处理：

```text
UVC 采集
YUYV -> RGB888
bbox 解析
LCD 绘制
MSH 命令调度
```

这些逻辑保留在 BSP application / demo 层。

### 9.3 Kconfig

插件 Kconfig 顶层开关保持默认关闭：

```kconfig
menuconfig RT_AI_USE_EDGI
    bool "Enable RT-AK Edgi backend"
    default n
```

插件启用后，当前默认启用：

```text
RT_AI_USE_M55_ETHOSU
RT_AI_EDGI_MODEL_OBJECT_DETECT
RT_AI_EDGI_MINIMAL_DEMO
```

`applications/rt_ai_edgi/SConscript` 只在 `RT_AI_USE_EDGI` 启用时要求选择模型。插件关闭时不会报 `RT-AK Edgi: no model selected`。

## 10. 常见问题

### 命令行提示找不到 `rt_ai_edgi_rtak_api_demo`

当前命令名是：

```text
rt_ai_edgi_minimal_demo
```

请用 `help` 查看 MSH 当前固件实际导出的命令。

### `RT-AK Edgi: no model selected`

说明插件已启用，但模型选择宏没有进入 `rtconfig.h`。检查：

```text
CONFIG_RT_AI_EDGI_MODEL_OBJECT_DETECT=y
#define RT_AI_EDGI_MODEL_OBJECT_DETECT
```

如果使用 auto 模式，确认 `--config_mode auto` 执行成功且没有回滚。

### 编译日志没有插件源码

检查 `rtconfig.h`：

```c
#define RT_AI_USE_EDGI
#define RT_AI_EDGI_MODEL_OBJECT_DETECT
```

如果缺失，SCons `GetDepend()` 不会让插件源码参与编译。

### `scons --pyconfig-silent` 报 packages/Kconfig 不存在

设置 RT-Thread Studio packages 索引：

```powershell
$env:PKGS_ROOT = "C:\RT-ThreadStudio\platform\env_released\env\packages"
```

auto 模式也会优先尝试使用该位置。

### `thread:tshell stack overflow`

旧版本 minimal demo 曾直接在 shell 线程执行推理。当前版本已改为 MSH 命令只调度 worker thread，推理在独立 `edgi_demo` 线程中运行。

## 11. 当前验证状态

当前本地已验证：

```text
GitHub 下载插件链路可生成和导出
manual 配置模式可导出 Kconfig
auto 配置模式可更新 .config 并生成 rtconfig.h
auto 重复执行不会重复追加 symbol
SCons 可真实编译 RT-AK core、backend、generated model 和 minimal demo
minimal demo 可通过标准 RT-AK API 调用 object_detect
UVC stop/start 生命周期可恢复
LCD 可实时显示检测框
```

如果本地修改尚未 commit / push，则 GitHub 一键下载链路仍会使用远端旧版本。完成本地验证后，应再执行：

```text
审查 git diff
commit
push origin main
删除全新 RT-AK 的 platforms/plugin_edgi
重新通过 GitHub clone 验证 --config_mode auto
重新编译 BSP
重新板端验证 minimal / UVC / LCD / stop-start
```
