# Edgi Talk RT-AK Plugin Demo

## 1. 项目概述

本项目用于验证将 `Edgi_Talk_M55_DEEPCRAFT_Deploy_Vision` 工程中的 DeepCraft / Imagimob / Cortex-M55 / Ethos-U55 视觉推理链路，最小化适配为 RT-AK 平台插件和后端。

当前阶段目标不是重构完整 Edgi Talk BSP，也不是把 UVC / LCD demo 全部塞进 RT-AK backend，而是先完成一条真实可运行的端侧 AI 部署闭环：

```text
RT-AK plugin tool
↓
DeepCraft / Imagimob 模型产物检查
↓
rt_ai_<model>_model.c/h 生成
↓
backend_edgi 封装 IMAI runtime
↓
导出到 Edgi Talk BSP
↓
SCons 编译链接
↓
RT-AK core API 接入
↓
MSH minimal demo 板端验证
↓
真实 UVC 摄像头链路接入 RT-AK backend
↓
M55 + Ethos-U55 实时推理
↓
LCD overlay 显示检测结果
```

当前第一版已经完成真实板端验证：

```text
rt_ai_find("object_detect") 成功
rt_ai_init 成功
rt_ai_input 成功
rt_ai_run 成功
rt_ai_output 成功
usbh_uvc_start 0 320 240 启动成功
UVC 摄像头画面正常
AI app async worker 正常
推理链路通过 RT-AK wrapper/backend 执行
LCD 能显示 Rock / Paper / Scissors 检测结果
```

---

## 2. 当前适配边界

### 2.1 backend_edgi 负责的内容

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

backend 只关心：

```text
模型初始化
模型输入 buffer
模型输出 buffer
模型推理调用
DeepCraft / Imagimob runtime 封装
Cortex-M55 / Ethos-U55 相关 memory section 适配
RT-AK backend function pointer 适配
```

### 2.2 不放入 backend 的内容

以下内容保留在 application / example 层：

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

这样做的原因是：RT-AK backend 应该只抽象“模型如何被 RT-AK 调用”，不应该和具体输入源、显示设备或业务后处理强绑定。

---

## 3. 当前目录结构

插件仓库结构：

```text
RT-AK-EDTalk-demo/
├── plugin_edgi.py
├── plugin_edgi_parser.py
├── prepare_work.py
├── generate_rt_ai_model_h.py
├── gen_rt_ai_model_c.py
├── generate_model_files.py
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
│       └── rt_ai_object_detect_model.h
├── Sconscripts/
│   └── SConscript
├── templates/
│   ├── rt_ai_template_model.c
│   └── rt_ai_template_model.h
├── docs/
│   ├── edgi_to_rtak_plugin_boundary.md
│   ├── build_integration_boundary.md
│   └── minimal_demo_board_validation.md
└── README.md
```

导出到 Edgi Talk BSP 后，目标目录为：

```text
Edgi_Talk_M55_DEEPCRAFT_Deploy_Vision/
└── applications/
    └── rt_ai_edgi/
        ├── SConscript
        ├── Kconfig
        ├── rt_ai_edgi_minimal_demo.c
        ├── backend_plugin_edgi/
        │   ├── backend_edgi.c
        │   └── backend_edgi.h
        └── generated/
            └── object_detect/
                ├── rt_ai_object_detect_model.c
                └── rt_ai_object_detect_model.h
```

当前短期验证阶段临时引用本地 RT-AK core：

```text
C:/RT-AK/edge-ai/RT-AK/rt_ai_lib
```

后续会改为插件仓库自带或导出 `rt_ai_lib`，避免依赖本地绝对路径。

---

## 4. 已完成内容

### 4.1 插件骨架

已完成独立插件仓库初始化，包含：

```text
plugin_edgi.py
plugin_edgi_parser.py
prepare_work.py
generate_rt_ai_model_h.py
gen_rt_ai_model_c.py
export_to_project.py
backend_plugin_edgi/
examples/
Sconscripts/
docs/
```

该仓库不直接污染原始 Edgi Talk BSP，插件产物通过 `--export` 导出到 BSP 的：

```text
applications/rt_ai_edgi/
```

---

### 4.2 dry-run 检查

已完成 `plugin_edgi.py --dry_run` 检查逻辑，支持检查：

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

已验证：

```text
BSP check     : OK
Model check   : OK
```

---

### 4.3 模型注册文件生成

已完成 `rt_ai_object_detect_model.c/h` 自动生成，生成目录为：

```text
generated/object_detect/
├── rt_ai_object_detect_model.c
└── rt_ai_object_detect_model.h
```

当前 generated model 文件已经支持标准 RT-AK 注册路径：

```text
INIT_APP_EXPORT(rt_ai_object_detect_model_register)
↓
rt_ai_register()
↓
backend_edgi()
↓
object_detect 注册到 RT-AK core
```

同时为了短期兼容原 Edgi UVC 实时链路，保留了兼容 wrapper：

```c
rt_ai_object_detect_model_init();
rt_ai_object_detect_model_run();
rt_ai_object_detect_model_deinit();
rt_ai_object_detect_model_get_input();
rt_ai_object_detect_model_get_output();
```

这些 wrapper 内部转调 RT-AK 标准 API 或 backend buffer：

```text
rt_ai_object_detect_model_init()
    -> rt_ai_find("object_detect")
    -> rt_ai_init()

rt_ai_object_detect_model_get_input()
    -> rt_ai_input()

rt_ai_object_detect_model_run()
    -> rt_ai_run()
    -> backend_edgi_run()
    -> IMAI_compute()

rt_ai_object_detect_model_get_output()
    -> backend_edgi_get_output()

rt_ai_object_detect_model_deinit()
    -> backend_edgi_deinit()
```

注意：兼容 wrapper 是短期过渡层，不是最终架构。后续会将 UVC demo 改为直接调用标准 RT-AK API。

---

### 4.4 backend_edgi 后端封装

已完成最小 backend：

```text
backend_plugin_edgi/backend_edgi.c
backend_plugin_edgi/backend_edgi.h
```

backend 已解决以下真实接口适配问题：

```text
IMAI_compute 实际返回 void，不能按 int 接收返回值
IMAI_init 返回 IMAI_RET_SUCCESS 语义，但 backend 对外统一为 0 表示成功
input buffer 大小基于模型输入需求
output buffer 大小基于模型输出需求
```

当前 backend 关键路径：

```text
backend_edgi_init()
    -> IMAI_init()

backend_edgi_run(input, output)
    -> IMAI_compute(input, output)

backend_edgi_deinit()
    -> IMAI_finalize()
```

---

### 4.5 RT-AK core runtime 接入

当前 BSP 已临时接入 RT-AK core runtime：

```text
rt_ai.c
rt_ai_common.c
rt_ai_core.c
rt_ai_runtime.c
rt_ai_lib/include/
```

当前临时路径：

```text
C:/RT-AK/edge-ai/RT-AK/rt_ai_lib
```

该步骤解决了：

```text
fatal error: rt_ai.h: No such file or directory
```

并使以下 API 可用：

```c
rt_ai_find();
rt_ai_register();
rt_ai_init();
rt_ai_input();
rt_ai_run();
rt_ai_output();
```

---

### 4.6 BSP 导出

已完成：

```powershell
python plugin_edgi.py --generate --export
```

导出内容包括：

```text
backend_plugin_edgi/
generated/object_detect/
rt_ai_edgi_minimal_demo.c
SConscript
Kconfig
```

当前导出目录：

```text
C:\RT-ThreadStudio\workspace\Edgi_Talk_M55_DEEPCRAFT_Deploy_Vision\applications\rt_ai_edgi
```

---

### 4.7 SCons 构建集成

已确认原 BSP 的 `applications/SConscript` 会自动扫描子目录中的 `SConscript`，因此无需手动修改 `applications/SConscript`。

已确认以下文件进入编译：

```text
CC applications\rt_ai_edgi\backend_plugin_edgi\backend_edgi.o
CC applications\rt_ai_edgi\generated\object_detect\rt_ai_object_detect_model.o
CC applications\rt_ai_edgi\rt_ai_edgi_minimal_demo.o
```

同时临时接入 RT-AK core runtime 后，工程能够完成编译链接。

---

### 4.8 工具链问题修复

BSP `rtconfig.py` 原始工具链路径为占位路径：

```python
EXEC_PATH = r'C:\Users\XXYYZZ'
```

当前通过 PowerShell 环境变量指定真实工具链路径：

```powershell
$env:RTT_EXEC_PATH = "C:\RT-ThreadStudio\platform\env_released\env\tools\gnu_gcc\arm_gcc\mingw\bin"
```

验证工具链：

```powershell
& "$env:RTT_EXEC_PATH\arm-none-eabi-gcc.exe" --version
```

已确认版本：

```text
arm-none-eabi-gcc.exe 10.3.1
```

---

### 4.9 内存 section 适配

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
插件 input buffer 放入 .cy_ml_input_data
原工程 g_model_input_u8 也在 .cy_ml_input_data
导致 gfx_mem 中存在两份 320 * 320 * 3 输入 buffer
```

最终修复策略：

```text
插件 backend input buffer 放入 .cy_ml_arena_data
插件 backend output buffer 放入 .cy_ml_postproc_data
```

当前配置：

```c
#define BACKEND_EDGI_INPUT_SECTION   BACKEND_EDGI_SECTION(".cy_ml_arena_data")
#define BACKEND_EDGI_OUTPUT_SECTION  BACKEND_EDGI_SECTION(".cy_ml_postproc_data")
```

---

## 5. 板端验证结果

### 5.1 MSH minimal demo 验证

命令：

```text
msh />rt_ai_edgi_minimal_demo
```

板端输出摘要：

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

该验证说明：

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

### 5.2 UVC 摄像头实时推理验证

命令：

```text
msh />usbh_uvc_start 0 320 240
```

UVC 设备支持分辨率包括：

```text
1280x720  @ 10fps
640x480   @ 30fps
320x240   @ 30fps
1600x1200 @ 5fps
1920x1080 @ 5fps
2048x1536 @ 3fps
2560x1440 @ 3fps
2592x1944 @ 3fps
```

当前选择：

```text
320x240 YUYV @ 30fps
```

板端输出摘要：

```text
[I/uvc_app] UVC start: 320x240 format=yuyv
[RT-AK][Edgi][Compat] init success
[I/uvc_ai] AI clocks cpu=399MHz npu=399MHz cache=2
[I/uvc_ai] AI model initialized
[I/uvc_ai_app] AI app started (async)
[I/uvc_app] frame #1 size=153600 fmt=yuyv
[I/uvc_ai] AI inference 129.0 ms (prep 4.0 ms, npu 33.6 ms), det=0
[I/uvc_ai] AI inference 127.0 ms (prep 4.0 ms, npu 33.6 ms), det=1
[I/uvc_ai] AI #0 Rock 50.20% bbox=[100,95,192,168]
[I/uvc_ai] AI #0 Paper 68.92% bbox=[92,61,189,192]
[I/uvc_ai] AI #0 Scissors 30.42% bbox=[83,66,180,197]
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
rt_ai_object_detect_model_get_input()
↓
rt_ai_input()
↓
rt_ai_object_detect_model_run()
↓
rt_ai_run()
↓
backend_edgi_run()
↓
IMAI_compute()
↓
Ethos-U55 / TFLM 推理
↓
backend output buffer
↓
原后处理
↓
Rock / Paper / Scissors 检测结果
↓
LCD overlay
```

该结果说明：当前已不只是固定输入 demo，而是真实摄像头输入、异步 worker、M55 + Ethos-U55 推理、后处理和 LCD overlay 的完整链路已经通过 RT-AK backend 跑通。

---

## 6. 当前已解决的问题清单

### 6.1 PowerShell 多行命令问题

问题：

```text
PowerShell 中反引号使用错误，导致 --project / --model_name 被解析成非法表达式
```

解决：

```text
反引号必须放在行尾，且后面不能有空格
```

---

### 6.2 Python 文件写入 here-string 问题

问题：

```text
@' 被错误写入 Python 文件，导致 SyntaxError: unterminated string literal
```

解决：

```text
区分 PowerShell here-string 和 Python 源码内容，重新生成合法 Python 文件
```

---

### 6.3 scons 命令不存在

问题：

```text
scons : 无法将“scons”项识别为 cmdlet
```

解决：

```powershell
uv pip install scons
```

---

### 6.4 工具链路径不存在

问题：

```text
Error: the toolchain path (C:\Users\XXYYZZ) is not exist
```

解决：

```powershell
$env:RTT_EXEC_PATH = "真实 arm-none-eabi-gcc.exe 所在 bin 目录"
```

---

### 6.5 DeepCraft model.c 重复编译

问题：

```text
原 BSP 已经编译 libraries/Common/deepcraft_ai/model/model.c
插件 SConscript 又重复添加 model.c
```

解决：

```text
插件只引用 model.h，不重复编译 model.c
```

---

### 6.6 IMAI_compute 返回值不匹配

问题：

```text
error: void value not ignored as it ought to be
```

原因：

```text
IMAI_compute 实际返回 void
backend 中错误写成 ret = IMAI_compute(...)
```

解决：

```c
IMAI_compute(runtime_input, runtime_output);
return BACKEND_EDGI_OK;
```

---

### 6.7 大 buffer 默认进入 .bss

问题：

```text
.bss overflow m55_data_INTERNAL
```

解决：

```text
将 backend input/output buffer 放入 Edgi BSP 已定义的 ML memory section
```

---

### 6.8 gfx_mem 溢出

问题：

```text
.cy_gpu_buf overflow gfx_mem
```

原因：

```text
原工程 input buffer 和插件 input buffer 同时放入 .cy_ml_input_data
```

解决：

```text
插件 input buffer 改放 .cy_ml_arena_data
```

---

### 6.9 rt-thread.elf 文件被占用

问题：

```text
rt-thread.elf: 另一个程序正在使用此文件，进程无法访问
```

原因：

```text
RT-Thread Studio / OpenOCD / GDB / 下载调试进程占用 elf 文件
```

解决：

```text
关闭调试/下载会话，释放 rt-thread.elf 后重新 scons
```

---

### 6.10 RT-AK core 头文件缺失

问题：

```text
fatal error: rt_ai.h: No such file or directory
```

原因：

```text
BSP 中尚未接入 RT-AK core runtime
```

解决：

```text
临时链接本地 C:/RT-AK/edge-ai/RT-AK/rt_ai_lib
```

---

### 6.11 UVC 旧 wrapper 符号缺失

问题：

```text
undefined reference to `rt_ai_object_detect_model_init'
undefined reference to `rt_ai_object_detect_model_run'
undefined reference to `rt_ai_object_detect_model_get_input'
undefined reference to `rt_ai_object_detect_model_get_output'
undefined reference to `rt_ai_object_detect_model_deinit'
```

原因：

```text
generated model 已切到标准 rt_ai_register 路径
但原 uvc_ai.c 仍调用旧 wrapper 函数名
```

解决：

```text
短期保留兼容 wrapper
wrapper 内部转调 RT-AK 标准 API / backend buffer
```

---

## 7. 当前难点总结

### 7.1 边界划分难点

最大难点不是简单封装 API，而是判断哪些代码属于 RT-AK backend，哪些代码属于 application demo。

当前边界：

```text
backend：
    IMAI_init / IMAI_compute / IMAI_finalize
    input/output buffer
    memory section
    RT-AK backend function pointer
    runtime state

application：
    UVC
    YUYV -> RGB888
    后处理
    LCD overlay
    MSH 命令
    worker thread
```

---

### 7.2 构建系统难点

Edgi Talk BSP 已有自己的 SCons 构建结构，RT-AK 插件也有自己的导出结构。适配时需要解决：

```text
applications/SConscript 自动扫描逻辑
rt_ai_edgi/SConscript 独立构建组
DeepCraftAi 构建组 include path 扩展
避免 model.c 重复编译
RT-AK core runtime 接入
避免本地绝对路径污染最终插件
```

---

### 7.3 runtime 接口语义难点

IMAI 接口不是标准 RT-AK API，其行为需要通过编译错误和实际代码确认：

```text
IMAI_compute 返回 void
IMAI_init 返回 IMAI_RET_SUCCESS
IMAI_finalize 需要统一纳入 backend 生命周期
IMAI_api 可用于读取模型元数据
```

---

### 7.4 内存布局难点

端侧 AI 推理不是普通 C 函数调用，必须处理 memory section：

```text
M55 internal RAM
SoCMEM
HyperRAM
gfx_mem
.cy_ml_input_data
.cy_ml_arena_data
.cy_ml_postproc_data
.bss
```

尤其是 `320 * 320 * 3` 输入 buffer，默认进入 `.bss` 会直接导致链接失败。

---

### 7.5 生命周期难点

当前存在多个入口可能调用模型 runtime：

```text
minimal demo
UVC demo
原 DeepCraft AI app
RT-AK wrapper
backend_edgi
```

必须保证：

```text
init 不重复破坏状态
run 之前 backend 已初始化
deinit 不影响正在运行的 UVC 推理链路
```

当前已经跑通短期链路，但还没有实现完整引用计数、并发保护和统一 deinit 策略。

---

## 8. 当前仍未完成的内容

### 8.1 UVC 链路仍通过兼容 wrapper

当前真实 UVC 链路为：

```text
uvc_ai.c
↓
rt_ai_object_detect_model_* compatibility wrapper
↓
RT-AK standard API
↓
backend_edgi
↓
IMAI_compute
```

短期可用，但最终应改为：

```text
uvc_ai_rtak_app.c
↓
rt_ai_find()
rt_ai_init()
rt_ai_input()
rt_ai_run()
rt_ai_output()
```

也就是去掉旧 wrapper，使 UVC example 直接使用标准 RT-AK API。

---

### 8.2 Kconfig / menuconfig 正规化

当前部分宏仍依赖临时配置或手动改 `rtconfig.h`。后续需要补齐：

```text
Kconfig
RT_AI_USE_EDGI
RT_AI_USE_M55_ETHOSU
RT_AI_EDGI_MINIMAL_DEMO
RT_AI_EDGI_UVC_DEMO
```

目标是通过 RT-Thread Studio / menuconfig 配置，而不是手动修改 `rtconfig.h`。

---

### 8.3 去除 UVC 链路中的中间 memcpy

当前短期接入仍可能存在中间 buffer 拷贝。后续优化方向：

```text
YUYV -> RGB888 直接写 RT-AK input buffer
rt_ai_run
postprocess 直接读 RT-AK output buffer
LCD overlay
```

这样可以减少额外拷贝，更符合端侧推理优化目标。

---

### 8.4 backend 生命周期保护

当前需要进一步处理：

```text
重复 init
重复 deinit
minimal demo 与 UVC demo 同时使用 backend
UVC 运行中误调用 deinit
```

建议后续实现：

```text
backend initialized 状态保护
可选引用计数
run 时状态检查
minimal demo 不主动破坏 UVC runtime
```

---

### 8.5 cache / DMA 一致性检查

当前推理已成功，但仍需进一步确认：

```text
backend input buffer 放在 .cy_ml_arena_data 后，cache 管理是否完全可靠
Ethos-U55 / TFLM 是否需要额外 clean / invalidate
不同 input/output section 对推理稳定性的影响
```

---

### 8.6 性能数据记录

当前已看到实时链路中的关键日志：

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
RT-AK wrapper/backend 路径耗时
额外 memcpy 开销
UVC fps
display fps
drop frame
NPU cycles
```

目标是证明插件化适配没有引入不可接受的开销。

---

### 8.7 插件自动化程度

当前已经支持：

```text
dry-run
generate
export
```

但还未完全支持：

```text
自动复制或引用 RT-AK core runtime
自动 patch UVC demo
自动添加 DeepCraftAi include path
自动配置 Kconfig / menuconfig
自动生成 model-agnostic demo config
```

短期不建议自动修改原 BSP 核心 UVC 文件，建议先用文档记录 patch 步骤。后续再沉淀为可选 patch 或 example。

---

## 9. 后续交付批次

### P0：当前版本固化

目标：

```text
保存当前已跑通版本
提交插件仓库
归档 BSP patch
补充验证文档
```

交付物：

```text
README.md
docs/minimal_demo_board_validation.md
docs/uvc_rtak_integration_validation.md
patches/edgi_talk_bsp/uvc_ai.c.patch
patches/edgi_talk_bsp/SConscript.patch
```

验收标准：

```text
GitHub 仓库能看到当前成果
文档能说明真实 UVC 推理链路已通过 RT-AK wrapper/backend 执行
```

---

### P1：标准 RT-AK API 对齐

目标：

```text
让 UVC example 从 rt_ai_object_detect_model_* wrapper 过渡到标准 RT-AK API
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

交付物：

```text
examples/uvc_ai_rtak_app.c
docs/standard_rtak_api_uvc_path.md
```

验收标准：

```text
UVC 实时推理不再依赖 compatibility wrapper
```

---

### P2：UVC demo 清理与零拷贝优化

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

交付物：

```text
uvc_ai_rtak_app.c
docs/uvc_zero_copy_boundary.md
```

验收标准：

```text
UVC 推理稳定
LCD 出框正常
无额外 input/output 中转 buffer
```

---

### P3：Kconfig / menuconfig 正规化

目标：

```text
RT_AI_USE_EDGI / RT_AI_USE_M55_ETHOSU / demo 开关进入 Kconfig
```

交付物：

```text
Kconfig
docs/kconfig_integration.md
```

验收标准：

```text
不再需要手动修改 rtconfig.h
通过 menuconfig 可开关 Edgi RT-AK 插件
```

---

### P4：模型切换能力

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

交付物：

```text
rt_ai_edgi_demo_config.h
examples/uvc_ai_rtak_app.c
docs/model_agnostic_uvc_runner.md
```

验收标准：

```text
更换模型后，只重新 generate/export，不手动改 UVC runner 主流程
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
原生 IMAI 路径 vs RT-AK wrapper/backend 路径
```

交付物：

```text
docs/performance_validation.md
```

验收标准：

```text
有原始日志
有对比表
有开销分析
有后续优化方向
```

---

## 10. 当前版本结论

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
真实 UVC 摄像头推理链路可通过 RT-AK wrapper/backend 执行
LCD 可显示 Rock / Paper / Scissors 检测结果
```

当前仍需完善：

```text
去除 compatibility wrapper
UVC demo 标准 RT-AK API 化
Kconfig / menuconfig 正规化
RT-AK core runtime 工程化导出
UVC 零拷贝优化
backend 生命周期保护
性能对比文档
模型切换配置生成
```

本阶段最重要的结论是：Edgi / DeepCraft / Ethos-U55 推理链路已经可以被收敛到 RT-AK 插件 backend，并且已经通过真实板端 UVC 摄像头实时推理验证。
