\# Edgi RT-AK 插件构建集成边界



\## 1. 当前阶段目标



本阶段只梳理 Edgi RT-AK 插件最终如何进入 RT-Thread BSP 的 SCons 构建系统。



当前不自动修改 Edgi Talk BSP，不自动复制文件，不自动注入 `applications/SConscript`。



\## 2. 当前已有模块



当前插件仓库已经形成三层结构：



```text

generated/object\_detect/rt\_ai\_object\_detect\_model.c

&#x20;   -> backend\_edgi\_init / backend\_edgi\_run / backend\_edgi\_deinit



backend\_plugin\_edgi/backend\_edgi.c

&#x20;   -> IMAI\_init / IMAI\_compute / IMAI\_finalize



libraries/Common/deepcraft\_ai/model/model.c

&#x20;   -> DeepCraft / Imagimob 生成模型实现

