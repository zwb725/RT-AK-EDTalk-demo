@'
# RT-AK-EDTalk-demo

本仓库用于验证 Edgi Talk / PSoC Edge E84 / Cortex-M55 / Ethos-U55 / DeepCraft / Imagimob 推理链路接入 RT-AK 的最小插件适配流程。

## 当前目标

先做最小 RT-AK 平台插件，不直接搬运完整 Edgi Talk BSP 工程。

第一阶段只做：

- 插件目录骨架
- Edgi 平台参数解析
- BSP 路径检查
- DeepCraft / Imagimob 模型产物检查
- IMAI 关键符号检查
- dry-run 报告输出

## 当前不做

本仓库当前不包含：

- UVC 摄像头采集
- CherryUSB UVC demo
- LCD overlay
- MSH 命令
- worker thread 调度
- 业务后处理
- Edgi Talk BSP 源码复制

## 第一阶段运行方式

```powershell
python plugin_edgi.py `
  --project "C:\RT-ThreadStudio\workspace\Edgi_Talk_M55_DEEPCRAFT_Deploy_Vision" `
  --model_name object_detect `
  --deepcraft_dir "C:\RT-ThreadStudio\workspace\Edgi_Talk_M55_DEEPCRAFT_Deploy_Vision\libraries\Common\deepcraft_ai" `
  --platform edgi `
  --ethosu `
  --dry_run