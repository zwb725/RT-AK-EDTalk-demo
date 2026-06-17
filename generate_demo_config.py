# coding=utf-8
"""Generate RT-AK Edgi demo config header."""

from pathlib import Path


def _macro_model_name(model_name: str) -> str:
    return model_name.upper().replace("-", "_").replace(" ", "_")


def generate_demo_config(model_name: str, output_dir: str, metadata: dict):
    model_macro = _macro_model_name(model_name)
    out_dir = Path(output_dir) / model_name
    out_dir.mkdir(parents=True, exist_ok=True)

    path = out_dir / "rt_ai_edgi_demo_config.h"

    input_shape = metadata.get("input_shape", [3, 320, 320])
    input_size = metadata.get("input_size", 320 * 320 * 3)
    output_size = metadata.get("output_size", 40)

    # 当前第一版默认按 DeepCraft RPS object detect:
    # input_shape 当前通常是 [3, 320, 320]，对应 C/H/W。
    c = input_shape[0] if len(input_shape) >= 1 else 3
    h = input_shape[1] if len(input_shape) >= 2 else 320
    w = input_shape[2] if len(input_shape) >= 3 else 320

    content = f"""#ifndef __RT_AI_EDGI_DEMO_CONFIG_H__
#define __RT_AI_EDGI_DEMO_CONFIG_H__

#include "rt_ai_{model_name}_model.h"

#define RT_AI_EDGI_DEMO_MODEL_NAME                RT_AI_{model_macro}_MODEL_NAME

#define RT_AI_EDGI_INPUT_W                        {w}
#define RT_AI_EDGI_INPUT_H                        {h}
#define RT_AI_EDGI_INPUT_C                        {c}
#define RT_AI_EDGI_INPUT_SIZE                     RT_AI_{model_macro}_INPUT_SIZE
#define RT_AI_EDGI_OUTPUT_SIZE                    RT_AI_{model_macro}_OUTPUT_SIZE

#define RT_AI_EDGI_RUNNER_MODEL_NAME              RT_AI_EDGI_DEMO_MODEL_NAME
#define RT_AI_EDGI_RUNNER_INPUT_BYTES             RT_AI_{model_macro}_IN_1_SIZE_BYTES
#define RT_AI_EDGI_RUNNER_OUTPUT_BYTES            RT_AI_{model_macro}_OUT_1_SIZE_BYTES
#define RT_AI_EDGI_RUNNER_INPUT_DTYPE             RT_AI_{model_macro}_INPUT_DTYPE
#define RT_AI_EDGI_RUNNER_OUTPUT_DTYPE            RT_AI_{model_macro}_OUTPUT_DTYPE
#define RT_AI_EDGI_RUNNER_INPUT_SHAPE_TEXT        RT_AI_{model_macro}_INPUT_SHAPE_TEXT
#define RT_AI_EDGI_RUNNER_OUTPUT_SHAPE_TEXT       RT_AI_{model_macro}_OUTPUT_SHAPE_TEXT

#define RT_AI_EDGI_PREPROCESS_YUYV_RGB888_320     1
#define RT_AI_EDGI_POSTPROCESS_OBJECT_DETECT_RPS  1
#define RT_AI_EDGI_RUNNER_PREPROCESS_TYPE         "yuyv_rgb888_320"
#define RT_AI_EDGI_RUNNER_POSTPROCESS_TYPE        "object_detect_rps"

#endif /* __RT_AI_EDGI_DEMO_CONFIG_H__ */
"""

    path.write_text(content, encoding="utf-8")
    return path
