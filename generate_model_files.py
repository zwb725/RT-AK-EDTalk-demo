# coding=utf-8
"""
Edgi RT-AK 模型文件生成入口。

输入：
- DeepCraft / Imagimob 产物目录
- model name
- output dir

输出：
- generated/<model_name>/rt_ai_<model_name>_model.h
- generated/<model_name>/rt_ai_<model_name>_model.c
"""

import argparse
import re
from pathlib import Path
from functools import reduce
from operator import mul

from .generate_rt_ai_model_h import generate_rt_ai_model_h
from .gen_rt_ai_model_c import generate_rt_ai_model_c


def _extract_numbers(text: str):
    return [int(x) for x in re.findall(r"\d+", text)]


def _product(values):
    if not values:
        return 0
    return reduce(mul, values, 1)


def _find_macro_line(text: str, macro_name: str):
    for line in text.splitlines():
        if macro_name in line:
            return line.strip()
    return ""


def parse_model_metadata(deepcraft_dir: str) -> dict:
    model_h = Path(deepcraft_dir) / "model.h"
    if not model_h.exists():
        raise FileNotFoundError(f"model.h not found: {model_h}")

    text = model_h.read_text(encoding="utf-8", errors="ignore")

    input_shape_line = _find_macro_line(text, "IMAI_DATAIN_SHAPE")
    output_shape_line = _find_macro_line(text, "IMAI_DATAOUT_SHAPE")

    input_shape = _extract_numbers(input_shape_line)
    output_shape = _extract_numbers(output_shape_line)

    if not input_shape:
        input_shape = [3, 320, 320]

    if not output_shape:
        output_shape = [40]

    input_size = _product(input_shape)
    output_size = _product(output_shape)

    return {
        "input_shape": input_shape,
        "output_shape": output_shape,
        "input_size": input_size,
        "output_size": output_size,
        "model_h": str(model_h),
    }


def build_parser():
    parser = argparse.ArgumentParser(
        description="Generate Edgi RT-AK model wrapper skeleton"
    )

    parser.add_argument(
        "--model_name",
        required=True,
        help="RT-AK model name, for example: object_detect",
    )

    parser.add_argument(
        "--deepcraft_dir",
        required=True,
        help="Directory containing DeepCraft / Imagimob model.c and model.h",
    )

    parser.add_argument(
        "--output_dir",
        default="generated",
        help="Output directory. Default: generated",
    )

    return parser


def main():
    parser = build_parser()
    opt = parser.parse_args()

    metadata = parse_model_metadata(opt.deepcraft_dir)

    h_path = generate_rt_ai_model_h(
        model_name=opt.model_name,
        output_dir=opt.output_dir,
        metadata=metadata,
    )

    c_path = generate_rt_ai_model_c(
        model_name=opt.model_name,
        output_dir=opt.output_dir,
        metadata=metadata,
    )

    print("=" * 70)
    print("Edgi RT-AK model skeleton generated")
    print("=" * 70)
    print(f"model_name  : {opt.model_name}")
    print(f"model_h     : {metadata['model_h']}")
    print(f"input_shape : {metadata['input_shape']}")
    print(f"output_shape: {metadata['output_shape']}")
    print(f"input_size  : {metadata['input_size']}")
    print(f"output_size : {metadata['output_size']}")
    print("-" * 70)
    print(f"generated h : {h_path}")
    print(f"generated c : {c_path}")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())