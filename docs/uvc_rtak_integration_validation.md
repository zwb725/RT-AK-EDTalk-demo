1. 当前 UVC 流程已经迁移到标准 RT-AK API。
2. 调用链路：`rt_ai_find -> rt_ai_init -> rt_ai_input -> memcpy input -> rt_ai_run -> rt_ai_output -> memcpy output`。
3. 旧 `rt_ai_object_detect_model_*` compatibility wrapper 已移除。
4. 板端已验证 `rt_ai_edgi_minimal_demo` 成功。
5. 板端已验证 `usbh_uvc_start 0 320 240` 后真实 UVC 图像正常、推理成功、LCD 实时出框。
6. 日志中已出现 Rock / Paper / Scissors 检测结果和 bbox，例如 `Rock 47.92% bbox=[170,66,287,158]`。
7. `usbh_uvc_stop` 已触发 `AI model deinitialized`。
8. `stop` 后第二次 `start` 仍需单独回归。
