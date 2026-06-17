/*
 * Config-driven Edgi RT-AK model runner.
 *
 * This module owns only the RT-AK model lifecycle and single-frame inference:
 * rt_ai_find -> rt_ai_init -> rt_ai_input -> rt_ai_run -> rt_ai_output.
 *
 * UVC capture, LCD overlay and BSP frame scheduling stay outside this module.
 */

#include "rt_ai_edgi_runner.h"

#include <rtthread.h>
#include <string.h>

#include "backend_edgi.h"
#include "rt_ai_edgi_active_model.h"
#include "rt_ai_edgi_demo_config.h"

static const rt_ai_edgi_runner_config_t g_rt_ai_edgi_runner_default_config = {
    RT_AI_EDGI_RUNNER_MODEL_NAME,
    RT_AI_EDGI_RUNNER_INPUT_BYTES,
    RT_AI_EDGI_RUNNER_OUTPUT_BYTES,
    RT_AI_EDGI_RUNNER_INPUT_DTYPE,
    RT_AI_EDGI_RUNNER_OUTPUT_DTYPE,
    RT_AI_EDGI_RUNNER_PREPROCESS_TYPE,
    RT_AI_EDGI_RUNNER_POSTPROCESS_TYPE,
};

const rt_ai_edgi_runner_config_t *rt_ai_edgi_runner_default_config(void)
{
    return &g_rt_ai_edgi_runner_default_config;
}

int rt_ai_edgi_runner_init(rt_ai_edgi_runner_t *runner,
                           const rt_ai_edgi_runner_config_t *config)
{
    int ret;

    if (runner == RT_NULL)
    {
        return -RT_EINVAL;
    }

    if (runner->initialized)
    {
        return RT_EOK;
    }

    if (config == RT_NULL)
    {
        config = rt_ai_edgi_runner_default_config();
    }

    rt_memset(runner, 0, sizeof(*runner));
    runner->config = config;

    runner->model = rt_ai_find(config->model_name);
    if (runner->model == RT_NULL)
    {
        rt_kprintf("[RT-AK][Edgi][runner] rt_ai_find failed: %s\r\n",
                   config->model_name);
        return -RT_ERROR;
    }

    ret = rt_ai_init(runner->model, RT_NULL);
    if (ret != RT_AI_OK)
    {
        rt_kprintf("[RT-AK][Edgi][runner] rt_ai_init failed: %d\r\n", ret);
        runner->model = RT_AI_NULL;
        runner->config = RT_NULL;
        return -RT_ERROR;
    }

    runner->initialized = 1U;
    rt_kprintf("[RT-AK][Edgi][runner] init model=%s input=%lu output=%lu\r\n",
               config->model_name,
               (unsigned long)config->input_bytes,
               (unsigned long)config->output_bytes);

    return RT_EOK;
}

void rt_ai_edgi_runner_deinit(rt_ai_edgi_runner_t *runner)
{
    if ((runner == RT_NULL) || (!runner->initialized))
    {
        return;
    }

    if (runner->model != RT_AI_NULL)
    {
        int ret = rt_ai_config(runner->model, RT_AI_EDGI_CMD_DEINIT, RT_NULL);
        if (ret != RT_AI_OK)
        {
            rt_kprintf("[RT-AK][Edgi][runner] deinit failed: %d\r\n", ret);
        }
    }

    rt_memset(runner, 0, sizeof(*runner));
}

void *rt_ai_edgi_runner_input(rt_ai_edgi_runner_t *runner)
{
    if ((runner == RT_NULL) || (!runner->initialized) ||
        (runner->model == RT_AI_NULL))
    {
        return RT_NULL;
    }

    return rt_ai_input(runner->model, 0);
}

void *rt_ai_edgi_runner_output(rt_ai_edgi_runner_t *runner)
{
    if ((runner == RT_NULL) || (!runner->initialized) ||
        (runner->model == RT_AI_NULL))
    {
        return RT_NULL;
    }

    return rt_ai_output(runner->model, 0);
}

int rt_ai_edgi_runner_run(rt_ai_edgi_runner_t *runner)
{
    int ret;

    if ((runner == RT_NULL) || (!runner->initialized) ||
        (runner->model == RT_AI_NULL))
    {
        return -RT_ERROR;
    }

    ret = rt_ai_run(runner->model, RT_NULL, RT_NULL);
    if (ret != RT_AI_OK)
    {
        rt_kprintf("[RT-AK][Edgi][runner] rt_ai_run failed: %d\r\n", ret);
        return -RT_ERROR;
    }

    return RT_EOK;
}

int rt_ai_edgi_runner_run_input(rt_ai_edgi_runner_t *runner,
                                const void *input,
                                uint32_t input_bytes)
{
    void *runner_input;
    int ret;

    if ((runner == RT_NULL) || (input == RT_NULL) ||
        (runner->config == RT_NULL))
    {
        return -RT_EINVAL;
    }

    if (input_bytes != runner->config->input_bytes)
    {
        rt_kprintf("[RT-AK][Edgi][runner] input size mismatch: %lu != %lu\r\n",
                   (unsigned long)input_bytes,
                   (unsigned long)runner->config->input_bytes);
        return -RT_EINVAL;
    }

    runner_input = rt_ai_edgi_runner_input(runner);
    if (runner_input == RT_NULL)
    {
        return -RT_ERROR;
    }

    rt_memcpy(runner_input, input, input_bytes);

    ret = rt_ai_edgi_runner_run(runner);
    if (ret != RT_EOK)
    {
        return ret;
    }

    if (rt_ai_edgi_runner_output(runner) == RT_NULL)
    {
        return -RT_ERROR;
    }

    return RT_EOK;
}
