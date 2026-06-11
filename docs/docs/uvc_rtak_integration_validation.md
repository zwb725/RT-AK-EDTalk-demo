1. 原 UVC 流程
2. 替换前 IMAI_compute 调用
3. 替换后 wrapper/backend 调用
4. 出现 -3 的原因：backend 未初始化
5. 修复方式：IMAI_init -> rt_ai_object_detect_model_init
6. 最终现象：UVC 图像正常，推理成功，LCD 出框