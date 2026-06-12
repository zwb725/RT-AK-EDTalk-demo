#include <rtthread.h>
#include <stdint.h>

#include "rt_ai.h"
#include "rt_ai_object_detect_model.h"

/*
 * Some upstream RT-AK versions implement rt_ai_input()
 * but do not declare it in rt_ai.h.
 * Compatible duplicate extern declaration is allowed.
 */
extern rt_ai_buffer_t *rt_ai_input(rt_ai_t ai, rt_uint32_t index);

static void rt_ai_edgi_fill_test_input(uint8_t *input, uint32_t size)
{
    uint32_t i;

    if (input == RT_NULL)
    {
        return;
    }

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
         * Avoid depending on float printf support.
         */
        rt_kprintf("out[%02d] = 0x%08x\r\n", i, v.u32);
    }
}

static int rt_ai_edgi_rtak_api_demo(int argc, char **argv)
{
    int ret;
    rt_ai_t model;
    uint8_t *input;
    float *output;

    RT_UNUSED(argc);
    RT_UNUSED(argv);

    rt_kprintf("RT-AK Edgi standard API demo start\r\n");

    model = rt_ai_find(RT_AI_OBJECT_DETECT_MODEL_NAME);
    if (model == RT_AI_NULL)
    {
        rt_kprintf("rt_ai_find(%s) failed\r\n", RT_AI_OBJECT_DETECT_MODEL_NAME);
        return -1;
    }

    ret = rt_ai_init(model, RT_NULL);
    if (ret != RT_AI_OK)
    {
        rt_kprintf("rt_ai_init failed: %d\r\n", ret);
        return ret;
    }

    input = (uint8_t *)rt_ai_input(model, 0);
    if (input == RT_NULL)
    {
        rt_kprintf("rt_ai_input failed\r\n");
        return -2;
    }

    rt_ai_edgi_fill_test_input(input, RT_AI_OBJECT_DETECT_INPUT_SIZE);

    ret = rt_ai_run(model, RT_NULL, RT_NULL);
    if (ret != RT_AI_OK)
    {
        rt_kprintf("rt_ai_run failed: %d\r\n", ret);
        return ret;
    }

    output = (float *)rt_ai_output(model, 0);
    if (output == RT_NULL)
    {
        rt_kprintf("rt_ai_output failed\r\n");
        return -3;
    }

    rt_kprintf("rt_ai_run done\r\n");
    rt_ai_edgi_print_output_as_hex(output, RT_AI_OBJECT_DETECT_OUTPUT_SIZE);

    rt_kprintf("RT-AK Edgi standard API demo end\r\n");

    return 0;
}
MSH_CMD_EXPORT(rt_ai_edgi_rtak_api_demo, run Edgi model through standard RT-AK API);