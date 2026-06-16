# Edgi Talk RT-AK Plugin Demo

## 1. 项目概述

本项目用于验证将 `Edgi_Talk_M55_DEEPCRAFT_Deploy_Vision` 工程中的 DeepCraft / Imagimob / Cortex-M55 / Ethos-U55 视觉推理链路，适配为 RT-AK 平台插件与后端。

当前版本目标不是重构完整 Edgi Talk BSP，也不是把 UVC / LCD / 后处理逻辑全部塞进 RT-AK backend，而是先完成一条真实可运行、可复现、可编译、可板端验证的端侧 AI 部署闭环：

```text
RT-AK 主仓库
↓
support_platforms.json 注册 plugin_edgi
↓
--platform edgi 自动下载插件
↓
插件检查 DeepCraft / Imagimob 模型产物
↓
生成 rt_ai_<model>_model.c/h 与 demo config
↓
导出 backend / generated / SConscript / Kconfig 到 Edgi BSP
↓
RT-AK core runtime 接入 BSP
↓
SCons 编译链接生成 rt-thread.elf / rtthread.hex
↓
MSH minimal demo 验证标准 RT-AK API
↓
UVC 摄像头实时推理
↓
M55 + Ethos-U55 执行推理
↓
LCD overlay 显示 Rock / Paper / Scissors 检测结果
```

当前版本已经完成真实板端验证：

```text
rt_ai_find("object_detect") 成功
rt_ai_init 成功
rt_ai_input 成功
rt_ai_run 成功
rt_ai_output 成功

usbh_uvc_start 0 320 240 启动成功
UVC 摄像头画面正常
AI async worker 正常
标准 RT-AK API / backend 能触发 IMAI_compute
LCD 能显示 Rock / Paper / Scissors 检测框
```

---

## 2. 当前状态

当前版本可以定义为：

```text
RT-AK Edgi plugin v0.2：标准 RT-AK API 与单模型条件编译收口版
```

已验证能力：

| 模块                                  | 当前状态 |
| ----------------------------------- | ---- |
| RT-AK 插件自动下载                        | 已通过  |
| `--dry_run` 检查                      | 已通过  |
| `--generate` 生成模型注册文件           | 已通过  |
| `--export` 导出到 BSP                  | 已通过  |
| RT-AK core runtime 接入               | 已通过  |
| SCons 编译链接                          | 已通过  |
| `rt-thread.elf` / `rtthread.hex` 生成 | 已通过  |
| MSH minimal demo                    | 已通过  |
| 标准 RT-AK API 路径                     | 已通过  |
| UVC 摄像头实时推理                         | 已通过  |
| LCD overlay 出框                      | 已通过  |

当前 v0.2 收口状态：

```text
真实 UVC 已直接使用标准 RT-AK API
compatibility wrapper 已移除
backend 只导出到 rt_ai_lib/backend_plugin_edgi
当前通过 Kconfig 编译期选择一个模型
当前只支持 object_detect
不支持运行时模型切换
未进行内存管理和零拷贝优化
```

---

## 3. 架构边界

### 3.1 backend_edgi 负责什么

`backend_edgi` 只负责模型 runtime 和 RT-AK 后端适配：

```text
backend_edgi()
    -> 填充 rt_ai_t 的 init / run / get_input / get_output 等函数指针

backend_edgi_init()
    -> IMAI_init()

backend_edgi_run()
    -> IMAI_compute(input, output)

backend_edgi_deinit()
    -> IMAI_finalize()

backend_edgi_get_input()
backend_edgi_get_output()
```

backend 负责：

```text
模型初始化
模型输入 buffer
模型输出 buffer
模型推理调用
DeepCraft / Imagimob runtime 封装
Cortex-M55 / Ethos-U55 memory section 适配
RT-AK backend function pointer 适配
```

### 3.2 backend 不负责什么

以下内容不放入 backend，保留在 application / example 层：

```text
UVC 摄像头采集
CherryUSB UVC 流控制
YUYV -> RGB888 图像预处理
模型输出后处理
bbox / class / confidence 解析
LCD overlay 绘制
MSH demo 命令
worker thread 调度策略
```

这样可以保证 backend 只抽象“模型如何被 RT-AK 调用”，不和具体输入源、显示设备或业务后处理强绑定。

---

## 4. 插件目录结构

插件仓库：

```text
RT-AK-EDTalk-demo/
├── plugin_edgi.py
├── plugin_edgi_parser.py
├── prepare_work.py
├── generate_rt_ai_model_h.py
├── gen_rt_ai_model_c.py
├── generate_model_files.py
├── generate_demo_config.py
├── export_to_project.py
├── Kconfig
├── backend_plugin_edgi/
│   ├── backend_edgi.c
│   ├── backend_edgi.h
│   ├── ethosu_rtos_rtthread.c
│   ├── README.md
│   └── SConscript
├── examples/
│   ├── README.md
│   └── rt_ai_edgi_minimal_demo.c
├── generated/
│   └── object_detect/
│       ├── rt_ai_object_detect_model.c
│       ├── rt_ai_object_detect_model.h
│       └── rt_ai_edgi_demo_config.h
├── Sconscripts/
│   └── SConscript
├── templates/
├── docs/
└── README.md
```

导出到 Edgi Talk BSP 后：

```text
Edgi_Talk_M55_DEEPCRAFT_Deploy_Vision/
├── rt_ai_lib/
│   ├── rt_ai.c
│   ├── rt_ai_common.c
│   ├── rt_ai_core.c
│   ├── rt_ai_runtime.c
│   ├── include/
│   └── backend_plugin_edgi/
│       ├── backend_edgi.c
│       ├── backend_edgi.h
│       └── ethosu_rtos_rtthread.c
└── applications/
    └── rt_ai_edgi/
        ├── SConscript
        ├── Kconfig
        ├── rt_ai_edgi_minimal_demo.c
        ├── rt_ai_edgi_active_model.h
        └── generated/
            └── object_detect/
                ├── rt_ai_object_detect_model.c
                ├── rt_ai_object_detect_model.h
                └── rt_ai_edgi_demo_config.h
```

说明：

```text
实际编译时，backend_edgi.c 只由 rt_ai_lib/backend_plugin_edgi 编译；applications/rt_ai_edgi 下不再导出 backend_plugin_edgi 副本。
```

---

## 5. 使用方式

### 5.1 在 RT-AK 中注册 Edgi 插件

修改本地 RT-AK：

```text
RT-AK/rt_ai_tools/platforms/support_platforms.json
```

加入：

```json
{
  "plugin_edgi": "https://github.com/zwb725/RT-AK-EDTalk-demo.git"
}
```

验证自动下载：

```powershell
cd $FreshTools

python aitools.py `
  --platform edgi `
  --pull_repo_only True
```

---

### 5.2 dry-run 检查

```powershell
cd $FreshTools

python aitools.py `
  --log .\edgi_dryrun.log `
  --project $Bsp `
  --platform edgi `
  --model_name object_detect `
  --deepcraft_dir $DeepCraftDir `
  --dry_run
```

已验证结果：

```text
BSP check     : OK
Model check   : OK
```

dry-run 会检查：

```text
BSP 工程路径
SConstruct
rtconfig.h
applications/
DeepCraft / Imagimob 模型产物目录
model.c
model.h
IMAI_init
IMAI_compute
IMAI_finalize
IMAI_api
```

---

### 5.3 generate / export

```powershell
cd $FreshTools

python aitools.py `
  --log .\edgi_export.log `
  --project $Bsp `
  --platform edgi `
  --model_name object_detect `
  --deepcraft_dir $DeepCraftDir `
  --generate `
  --export
```

导出后关键文件：

```text
applications/rt_ai_edgi/
├── SConscript
├── Kconfig
├── rt_ai_edgi_minimal_demo.c
└── generated/object_detect/
    ├── rt_ai_object_detect_model.c
    ├── rt_ai_object_detect_model.h
    └── rt_ai_edgi_demo_config.h

rt_ai_lib/
├── rt_ai.c
├── rt_ai_common.c
├── rt_ai_core.c
├── rt_ai_runtime.c
├── include/
└── backend_plugin_edgi/
```

---

### 5.4 编译 BSP

如果工具链路径未配置，需要先设置：

```powershell
$env:RTT_EXEC_PATH = $ArmGccBin
```

验证工具链：

```powershell
& "$env:RTT_EXEC_PATH\arm-none-eabi-gcc.exe" --version
```

编译：

```powershell
cd $Bsp

scons -c
scons -j6
```

已验证输出：

```text
LINK rt-thread.elf
arm-none-eabi-objcopy -O ihex rt-thread.elf Debug/rtthread.hex
arm-none-eabi-size rt-thread.elf

text    data     bss     dec     hex filename
522412  3164240  5284568 8971220 88e3d4 rt-thread.elf

scons: done building targets.
```

---

## 6. 板端验证

### 6.1 MSH minimal demo

命令：

```text
msh />rt_ai_edgi_minimal_demo
```

已验证日志：

```text
RT-AK Edgi standard API demo start
rt_ai_find success: object_detect
rt_ai_init success
rt_ai_input success: 0x64400000
rt_ai_run success
rt_ai_output success: 0x26370000
out[00] = 0x00000000
...
out[39] = 0x00000000
RT-AK Edgi standard API demo end
```

说明：

```text
MSH 命令导出成功
object_detect 已注册到 RT-AK core
rt_ai_find 成功
rt_ai_init 成功
rt_ai_input 成功
rt_ai_run 成功
rt_ai_output 成功
backend_edgi_run 能触发 IMAI_compute
output buffer 可访问
```

该 demo 使用固定 pattern 输入，不用于判断模型语义正确性，只用于验证 RT-AK API、buffer、backend 调用链路不 HardFault、不阻塞、不链接失败。

---

### 6.2 UVC 摄像头实时推理

命令：

```text
msh />usbh_uvc_start 0 320 240
```

当前使用：

```text
320x240 YUYV @ 30fps
```

已验证日志摘要：

```text
[I/uvc_app] UVC start: 320x240 format=yuyv
[I/uvc_disp] LCD: 512x800 16bpp fb=0x263fb000 size=819200
[I/uvc_ai] AI clocks cpu=399MHz npu=399MHz cache=2
[I/uvc_ai] AI model initialized
[I/uvc_ai_app] AI app started (async)
[I/uvc_app] frame #1 size=153600 fmt=yuyv

[I/uvc_ai] AI inference 120.0 ms (prep 4.0 ms, npu 33.6 ms), det=1
[I/uvc_ai] AI #0 Rock 47.92% bbox=[170,66,287,158]
[I/uvc_ai] AI #0 Scissors 42.11% bbox=[124,51,274,202]
[I/uvc_ai] AI #0 Paper 50.20% bbox=[100,27,289,177]
[I/uvc_app] UVC fps:30 disp:13 drop:140 urb:10358
[I/uvc_ai] AI model deinitialized
[I/uvc_app] UVC stopped
```

当前真实运行链路：

```text
UVC 摄像头
↓
CherryUSB UVC stream
↓
uvc_ai_app async worker
↓
YUYV -> RGB888 预处理
↓
rt_ai_find()
↓
rt_ai_init()
↓
rt_ai_input()
↓
memcpy input
↓
rt_ai_run()
↓
rt_ai_output()
↓
memcpy output
↓
backend_edgi_run()
↓
IMAI_compute()
↓
Ethos-U55 / TFLM 推理
↓
原后处理
↓
Rock / Paper / Scissors 检测结果
↓
LCD overlay
```

该结果说明：当前已经完成真实摄像头输入、异步 worker、M55 + Ethos-U55 推理、后处理和 LCD overlay 实时出框的完整链路验证；UVC stop 路径也已触发 backend deinit。

---

## 7. 关键实现点

### 7.1 generated model

插件会生成：

```text
rt_ai_object_detect_model.c
rt_ai_object_detect_model.h
rt_ai_edgi_demo_config.h
```

标准 RT-AK 注册路径：

```text
INIT_APP_EXPORT(rt_ai_object_detect_model_register)
↓
rt_ai_register()
↓
backend_edgi()
↓
object_detect 注册到 RT-AK core
```

生成的模型注册文件不再生成 `rt_ai_object_detect_model_*()` compatibility wrapper。UVC 和 minimal demo 均通过 `rt_ai_find / rt_ai_init / rt_ai_input / rt_ai_run / rt_ai_output` 接入。

---

### 7.2 backend_edgi

当前 backend 关键路径：

```text
backend_edgi_init()
    -> IMAI_init()

backend_edgi_run(input, output)
    -> IMAI_compute(input, output)

backend_edgi_deinit()
    -> IMAI_finalize()
```

已处理接口语义差异：

```text
IMAI_compute 实际返回 void，backend 不能按 int 接收返回值
IMAI_init 返回 IMAI_RET_SUCCESS，backend 对外统一为 0 表示成功
input/output buffer 根据模型输入输出大小分配
```

---

### 7.3 memory section

适配过程中解决了两个链接阶段内存问题。

第一次问题：

```text
.bss will not fit in region m55_data_INTERNAL
```

原因：

```text
backend 默认 static input buffer 进入 .bss
320 * 320 * 3 input buffer 挤爆 M55 内部 RAM
```

第二次问题：

```text
.cy_gpu_buf will not fit in region gfx_mem
```

原因：

```text
插件 input buffer 与原工程 g_model_input_u8 同时进入 .cy_ml_input_data
导致 gfx_mem 中存在两份 320 * 320 * 3 输入 buffer
```

当前修复策略：

```c
#define BACKEND_EDGI_INPUT_SECTION   BACKEND_EDGI_SECTION(".cy_ml_arena_data")
#define BACKEND_EDGI_OUTPUT_SECTION  BACKEND_EDGI_SECTION(".cy_ml_postproc_data")
```

---

### 7.4 SCons 集成

原 BSP 的：

```text
applications/SConscript
```

会自动扫描 `applications/` 下带 `SConscript` 的子目录，因此 `applications/rt_ai_edgi/SConscript` 能自动进入编译。

已解决的问题：

```text
backend_edgi.c 不能同时由 applications/rt_ai_edgi 和 rt_ai_lib/backend_plugin_edgi 编译
否则会出现 multiple definition
```

当前策略：

```text
backend_edgi.c 只由 rt_ai_lib/backend_plugin_edgi 编译
applications/rt_ai_edgi/SConscript 只编译 generated model 和 minimal demo
```

---

## 8. 已解决问题

| 问题                                                | 原因                                     | 处理方式                                          |
| ------------------------------------------------- | -------------------------------------- | --------------------------------------------- |
| PowerShell 多行参数解析失败                               | 反引号位置错误                                | 反引号必须位于行尾且后面不能有空格                             |
| Python here-string 写坏源码                           | PowerShell here-string 内容误写入 Python 文件 | 重新生成合法 Python 文件                              |
| `scons` 命令不存在                                     | 当前 Python 环境未安装 SCons                  | `uv pip install scons`                        |
| 工具链路径不存在                                          | `rtconfig.py` 中 `EXEC_PATH` 为占位路径      | 设置 `RTT_EXEC_PATH`                            |
| `model.c` 重复编译                                    | 原 BSP 已编译 DeepCraft model.c，插件又重复加入    | 插件只引用 model.h                                 |
| `IMAI_compute` 返回值错误                              | `IMAI_compute` 实际返回 void               | backend 中直接调用后返回 `BACKEND_EDGI_OK`            |
| `.bss` 溢出                                         | 大 input buffer 默认进入内部 RAM              | 将 buffer 放到 ML memory section                 |
| `gfx_mem` 溢出                                      | 两份 input buffer 进入同一 section           | 插件 input buffer 改到 `.cy_ml_arena_data`        |
| `rt-thread.elf` 被占用                               | RT-Thread Studio / OpenOCD / GDB 占用文件  | 关闭调试会话后重新编译                                   |
| `rt_ai.h` 缺失                                      | BSP 尚未接入 RT-AK core runtime            | 导出并编译 `rt_ai_lib`                             |
| `backend_edgi_*` multiple definition              | backend 编译了两份                          | 只在 `rt_ai_lib/backend_plugin_edgi` 编译 backend |
| `rt_ai_object_detect_model_*` undefined reference | 残留代码仍调用旧 wrapper                   | 迁移到标准 RT-AK API，重新 generate/export      |

---

## 9. 当前未完成项

### 9.1 UVC 板端 stop/start 回归验证

当前代码已迁移到标准 RT-AK API，仍需在真实板端重复验证：

```text
usbh_uvc_start 0 320 240
usbh_uvc_stop
usbh_uvc_start 0 320 240
```

---

### 9.2 Kconfig / menuconfig 正规化

当前部分宏仍依赖临时配置或导出逻辑写入：

```text
RT_AI_USE_EDGI
RT_AI_USE_M55_ETHOSU
RT_AI_EDGI_MINIMAL_DEMO
RT_AI_EDGI_UVC_DEMO
```

后续目标：

```text
通过 RT-Thread Studio / menuconfig 控制开关
不再手动修改 rtconfig.h
```

---

### 9.3 UVC 零拷贝优化

当前短期接入仍可能存在中间 buffer 拷贝。后续优化方向：

```text
YUYV -> RGB888 直接写 RT-AK input buffer
rt_ai_run
postprocess 直接读 RT-AK output buffer
LCD overlay
```

---

### 9.4 backend 生命周期保护

当前仍需完善：

```text
重复 init
重复 deinit
minimal demo 与 UVC demo 同时使用 backend
UVC 运行中误调用 deinit
```

后续建议：

```text
backend initialized 状态保护
可选引用计数
run 时状态检查
minimal demo 不主动破坏 UVC runtime
```

---

### 9.5 cache / DMA 一致性检查

当前推理已成功，但仍需进一步确认：

```text
backend input buffer 放在 .cy_ml_arena_data 后，cache 管理是否完全可靠
Ethos-U55 / TFLM 是否需要额外 clean / invalidate
不同 input/output section 对推理稳定性的影响
```

---

### 9.6 性能数据补充

当前已看到：

```text
AI inference 127~129 ms
prep 4~5 ms
npu 33.6 ms
UVC fps 29~30
display fps 11~13
drop frame 持续增长
```

后续应补充：

```text
原生 IMAI_compute 路径耗时
标准 RT-AK API / backend 路径耗时
额外 memcpy 开销
UVC fps
display fps
drop frame
NPU cycles
```

---

## 10. 后续路线

### P0：当前版本固化

状态：

```text
部分完成
```

已完成：

```text
README.md 已补充 v0.2 状态和板端验证结论
docs/minimal_demo_board_validation.md 已记录 minimal demo 板端验证
docs/uvc_rtak_integration_validation.md 已记录标准 RT-AK API、真实摄像头推理和 LCD 实时出框
patches/edgi_talk_bsp/uvc_ai.c.patch 已归档
patches/edgi_talk_bsp/SConscript.patch 已归档
```

仍需完成：

```text
提交插件仓库
```

目标：

```text
保存当前已跑通版本
提交插件仓库
归档 BSP patch
补充验证文档
```

建议交付物：

```text
README.md
docs/minimal_demo_board_validation.md
docs/uvc_rtak_integration_validation.md
patches/edgi_talk_bsp/uvc_ai.c.patch
patches/edgi_talk_bsp/SConscript.patch
```

---

### P1：标准 RT-AK API 对齐

状态：

```text
主体已完成，stop 后第二次 start 仍需单独回归
```

已完成：

```text
UVC example 已从 rt_ai_object_detect_model_* wrapper 迁移到标准 RT-AK API
真实 UVC 链路已通过 rt_ai_find / rt_ai_init / rt_ai_input / rt_ai_run / rt_ai_output 执行推理
usbh_uvc_stop 已触发 RT-AK backend deinit
```

仍需完成：

```text
同一次上电周期内执行 usbh_uvc_start -> usbh_uvc_stop -> usbh_uvc_start 回归验证
```

目标：

```text
让 UVC example 保持标准 RT-AK API 路径并验证 stop/start 生命周期
```

目标调用形式：

```c
rt_ai_t model;

model = rt_ai_find("object_detect");
rt_ai_init(model, RT_NULL);

input = rt_ai_input(model, 0);
rt_ai_run(model, RT_NULL, RT_NULL);
output = rt_ai_output(model, 0);
```

---

### P2：UVC demo 清理与零拷贝优化

状态：

```text
未完成
```

当前状态：

```text
当前链路仍保留 g_model_input_u8 -> RT-AK input buffer 的 memcpy
当前链路仍保留 RT-AK output buffer -> g_model_output 的 memcpy
preprocess / run / postprocess 已可区分，但还没有做零拷贝收口
```

目标：

```text
减少 UVC 真实链路中的临时 memcpy
明确 preprocess / run / postprocess 的边界
```

优化后链路：

```text
YUYV -> RGB888 直接写 RT-AK input buffer
rt_ai_run
postprocess 直接读 RT-AK output buffer
LCD overlay
```

---

### P3：Kconfig / menuconfig 正规化

状态：

```text
部分完成
```

已完成：

```text
插件侧已有 Kconfig 模型选择项
SConscript 已按 Kconfig 选择单模型编译
```

仍需完成：

```text
RT_AI_USE_EDGI / RT_AI_USE_M55_ETHOSU / demo 开关完整进入 BSP menuconfig
当前 BSP 仍需要手动补 rtconfig.h 中的 RT_AI_EDGI_MODEL_OBJECT_DETECT
```

目标：

```text
RT_AI_USE_EDGI / RT_AI_USE_M55_ETHOSU / demo 开关进入 Kconfig
```

验收标准：

```text
不再手动改 rtconfig.h
通过 menuconfig 可开关 Edgi RT-AK 插件
```

---

### P4：模型切换能力

状态：

```text
部分完成
```

已完成：

```text
plugin_edgi.py / 生成器已生成 rt_ai_<model>_model.c/h
生成器已生成 rt_ai_edgi_demo_config.h
UVC runner 已固定为标准 RT-AK API 调度形式
当前 active model 通过 rt_ai_edgi_active_model.h 统一暴露 model name / input bytes / output bytes
```

仍需完成：

```text
接入第二个真实模型验证
抽象 preprocess / postprocess 类型
让模型差异完全通过配置和前后处理模块表达
```

目标：

```text
换模型时不手动改 UVC 调度代码
```

设计方向：

```text
plugin_edgi.py 生成：
    rt_ai_<model>_model.c/h
    rt_ai_edgi_demo_config.h

UVC runner 固定：
    rt_ai_find()
    rt_ai_init()
    rt_ai_input()
    rt_ai_run()
    rt_ai_output()

模型差异通过配置和前后处理模块表达：
    model_name
    input shape
    input dtype
    preprocess type
    postprocess type
```

---

### P5：性能与稳定性验证

目标：

```text
证明插件化适配不会显著破坏原 demo 的实时性
```

记录指标：

```text
inference_ms
prep_ms
npu_ms
UVC fps
display fps
drop frame
原生 IMAI 路径 vs 标准 RT-AK API / backend 路径
```

---

## 11. 当前版本结论

当前版本已经完成 Edgi Talk / PSoC Edge E84 / Cortex-M55 / Ethos-U55 / DeepCraft 视觉推理链路到 RT-AK 插件的第一版可运行适配。

当前已经验证：

```text
插件工具链可运行
模型文件可生成
backend_edgi 可编译
RT-AK core runtime 可接入
BSP 可导出
SCons 可集成
rt-thread.elf 可生成
MSH minimal demo 可运行
rt_ai_find / rt_ai_init / rt_ai_input / rt_ai_run / rt_ai_output 可用
真实 UVC 摄像头推理链路可直接通过标准 RT-AK API / backend 执行
LCD 可实时显示 Rock / Paper / Scissors 检测框
```

当前仍需完善：

```text
stop 后第二次 start 回归验证
未来第二模型适配
RT-AK core runtime 工程化导出
UVC 零拷贝优化
更复杂的 backend 生命周期保护
性能对比文档
内存管理优化
```

本阶段最重要的结论是：

```text
Edgi / DeepCraft / Ethos-U55 推理链路已经可以收敛到 RT-AK 插件 backend，并且已通过真实板端 UVC 摄像头实时推理验证。
```
