\# Edgi RT-AK 插件 dry-run 检查记录



\## 1. 阶段目标



本阶段验证 Edgi Talk / PSoC Edge E84 / Cortex-M55 / Ethos-U55 / DeepCraft / Imagimob 推理链路接入 RT-AK 的工具侧入口。



当前阶段只做 dry-run 检查，不修改原始 Edgi Talk BSP 工程，不复制 BSP 源码，不接入 UVC / LCD demo。



\## 2. 当前已验证内容



\- 插件参数解析

\- BSP 工程路径检查

\- DeepCraft / Imagimob 模型产物目录检查

\- model.c / model.h 文件检查

\- IMAI\_init / IMAI\_compute / IMAI\_finalize / IMAI\_api 符号检查

\- Edgi / M55 / Ethos-U55 相关宏规划输出



\## 3. 项目路径



插件仓库路径：



```text

C:\\RT-AK-EDTalk-demo

