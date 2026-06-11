@"
# Edgi Talk to RT-AK Plugin Boundary

## Current Stage

Skeleton only. No Edgi BSP source is copied into this repository.

## Backend Boundary

The backend should only wrap:

- IMAI_init
- IMAI_compute
- IMAI_finalize
- IMAI_api
- input buffer
- output buffer
- Ethos-U55 RTOS shim
- cache / section / profile related hooks

## Not Backend

The following components must stay in examples or BSP application code:

- UVC camera capture
- CherryUSB UVC stream
- YUYV to RGB888 preprocessing
- model-specific postprocess
- LCD overlay
- MSH command control
- worker thread scheduling

## Minimal Demo Path

fixed input buffer
-> rt_ai_find
-> rt_ai_init
-> rt_ai_run
-> rt_ai_output
-> print output tensor
"@ | Out-File -Encoding utf8 docs\edgi_to_rtak_plugin_boundary.md