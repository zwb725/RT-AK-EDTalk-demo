/*
 * Minimal Edgi RT-AK backend validation demo.
 *
 * This demo verifies:
 * - generated model wrapper
 * - backend_edgi
 * - DeepCraft / Imagimob IMAI runtime
 *
 * It intentionally does not use:
 * - UVC camera
 * - LCD overlay
 * - model-specific postprocess
 */

#include <rtthread.h>
#include <stdint.h>
#include <string.h>

#include "rt_ai_object_detect_model.h"

static void rt_ai_edgi_fill_test_input(uint8_t *input, uint32_t size)
{
    uint32_t i;

    if (input == RT_NULL)
    {
        return;
    }

    /*
     * Fixed deterministic test pattern.
     * This is not a real image. It is only used to validate the runtime path.
     */
    for (i = 0; i < size; i++)
    {
        input[i] = (uint8_t)(i & 0xFFU);
    }
}

static void rt_ai_edgi_print_output_as_hex(const float *output, uint32_t count)
{
    uint32_t i;

    if (output == RT_NULL)
    {
        rt_kprintf("output is NULL\r\n");
        return;
    }

    for (i = 0; i < count; i++)
    {
        union
        {
            float f;
            uint32_t u32;
        } v;

        v.f = output[i];

        /*
         * Print float raw bits to avoid depending on float printf support.
         */
        rt_kprintf("out[%02d] = 0x%08x\r\n", i, v.u32);
    }
}

static int rt_ai_edgi_minimal_demo(int argc, char **argv)
{
    int ret;
    uint8_t *input;
    float *output;

    RT_UNUSED(argc);
    RT_UNUSED(argv);

    rt_kprintf("RT-AK Edgi minimal demo start\r\n");

    ret = rt_ai_object_detect_model_init();
    if (ret != 0)
    {
        rt_kprintf("model init failed: %d\r\n", ret);
        return ret;
    }

    input = (uint8_t *)rt_ai_object_detect_model_get_input(0);
    output = (float *)rt_ai_object_detect_model_get_output(0);

    if (input == RT_NULL)
    {
        rt_kprintf("input buffer is NULL\r\n");
        rt_ai_object_detect_model_deinit();
        return -1;
    }

    if (output == RT_NULL)
    {
        rt_kprintf("output buffer is NULL\r\n");
        rt_ai_object_detect_model_deinit();
        return -2;
    }

    rt_ai_edgi_fill_test_input(input, RT_AI_OBJECT_DETECT_INPUT_SIZE);

    ret = rt_ai_object_detect_model_run();
    if (ret != 0)
    {
        rt_kprintf("model run failed: %d\r\n", ret);
        rt_ai_object_detect_model_deinit();
        return ret;
    }

    rt_kprintf("model run done\r\n");
    rt_ai_edgi_print_output_as_hex(output, RT_AI_OBJECT_DETECT_OUTPUT_SIZE);

    rt_ai_object_detect_model_deinit();

    rt_kprintf("RT-AK Edgi minimal demo end\r\n");

    return 0;
}

MSH_CMD_EXPORT(rt_ai_edgi_minimal_demo, run Edgi RT-AK minimal inference demo);