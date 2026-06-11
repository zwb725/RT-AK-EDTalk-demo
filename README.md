@"
# RT-AK-EDTalk-demo

Experimental RT-AK plugin demo for PSoC Edge E84 / Cortex-M55 / Ethos-U55 / DeepCraft / Imagimob runtime.

## Goal

Build a minimal RT-AK platform plugin skeleton for Edgi Talk M55 DeepCraft AI deployment.

## Scope

This repository only contains:

- RT-AK tools plugin skeleton
- RT-AK model file generation skeleton
- Edgi backend wrapper skeleton
- Ethos-U55 RTOS shim skeleton
- minimal fixed-input demo placeholder

This repository does not contain:

- UVC camera capture
- CherryUSB UVC demo logic
- LCD overlay
- MSH command demo
- application-specific postprocess
- copied Edgi Talk BSP source files

## First Target

Run a fixed input buffer through:

rt_ai_find -> rt_ai_init -> rt_ai_run -> rt_ai_output

and print the raw output tensor.
"@ | Out-File -Encoding utf8 README.md