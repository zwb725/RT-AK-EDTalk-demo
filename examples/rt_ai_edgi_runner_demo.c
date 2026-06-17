/*
 * Config-driven Edgi RT-AK runner demo.
 *
 * This command demonstrates the runner path that a UVC application can reuse:
 * config -> rt_ai_find -> rt_ai_init -> rt_ai_input -> rt_ai_run -> rt_ai_output.
 */

#include <rtthread.h>
#include <stdint.h>

#include "rt_ai_edgi_runner.h"

#define RT_AI_EDGI_RUNNER_DEMO_THREAD_STACK_SIZE  (65536U)
#define RT_AI_EDGI_RUNNER_DEMO_THREAD_PRIORITY    (20)
#define RT_AI_EDGI_RUNNER_DEMO_THREAD_TICK        (10)

static rt_thread_t g_rt_ai_edgi_runner_demo_thread = RT_NULL;
static struct rt_semaphore g_rt_ai_edgi_runner_demo_sem;
static rt_bool_t g_rt_ai_edgi_runner_demo_thread_started = RT_FALSE;
static rt_bool_t g_rt_ai_edgi_runner_demo_running = RT_FALSE;

static void rt_ai_edgi_runner_demo_fill_input(uint8_t *input, uint32_t size)
{
    uint32_t i;

    if (input == RT_NULL)
    {
        return;
    }

    for (i = 0; i < size; i++)
    {
        input[i] = (uint8_t)((i * 17U) & 0xFFU);
    }
}

static void rt_ai_edgi_runner_demo_print_output(const uint8_t *output,
                                                uint32_t bytes)
{
    uint32_t i;
    uint32_t limit = bytes;

    if (output == RT_NULL)
    {
        rt_kprintf("runner output is NULL\r\n");
        return;
    }

    if (limit > 32U)
    {
        limit = 32U;
    }

    for (i = 0; i < limit; i++)
    {
        if ((i % 16U) == 0U)
        {
            rt_kprintf("runner out[%03lu]:", (unsigned long)i);
        }

        rt_kprintf(" %02x", output[i]);

        if (((i % 16U) == 15U) || ((i + 1U) == limit))
        {
            rt_kprintf("\r\n");
        }
    }
}

static void rt_ai_edgi_runner_demo_run_once(void)
{
    rt_ai_edgi_runner_t runner;
    const rt_ai_edgi_runner_config_t *config;
    uint8_t *input;
    uint8_t *output;
    int ret;

    rt_memset(&runner, 0, sizeof(runner));
    config = rt_ai_edgi_runner_default_config();

    rt_kprintf("RT-AK Edgi config runner start\r\n");
    rt_kprintf("model      : %s\r\n", config->model_name);
    rt_kprintf("input      : %lu bytes, %s\r\n",
               (unsigned long)config->input_bytes,
               config->input_dtype);
    rt_kprintf("output     : %lu bytes, %s\r\n",
               (unsigned long)config->output_bytes,
               config->output_dtype);
    rt_kprintf("preprocess : %s\r\n", config->preprocess_type);
    rt_kprintf("postprocess: %s\r\n", config->postprocess_type);

    ret = rt_ai_edgi_runner_init(&runner, config);
    if (ret != RT_EOK)
    {
        goto out;
    }

    input = (uint8_t *)rt_ai_edgi_runner_input(&runner);
    if (input == RT_NULL)
    {
        rt_kprintf("runner input failed\r\n");
        goto out;
    }

    rt_ai_edgi_runner_demo_fill_input(input, config->input_bytes);

    ret = rt_ai_edgi_runner_run(&runner);
    if (ret != RT_EOK)
    {
        goto out;
    }

    output = (uint8_t *)rt_ai_edgi_runner_output(&runner);
    if (output == RT_NULL)
    {
        rt_kprintf("runner output failed\r\n");
        goto out;
    }

    rt_ai_edgi_runner_demo_print_output(output, config->output_bytes);
    rt_kprintf("RT-AK Edgi config runner end\r\n");

out:
    rt_ai_edgi_runner_deinit(&runner);
}

static void rt_ai_edgi_runner_demo_thread_entry(void *parameter)
{
    RT_UNUSED(parameter);

    while (1)
    {
        if (rt_sem_take(&g_rt_ai_edgi_runner_demo_sem,
                        RT_WAITING_FOREVER) != RT_EOK)
        {
            continue;
        }

        rt_ai_edgi_runner_demo_run_once();
        g_rt_ai_edgi_runner_demo_running = RT_FALSE;
    }
}

static rt_err_t rt_ai_edgi_runner_demo_ensure_thread(void)
{
    rt_err_t ret;

    if (g_rt_ai_edgi_runner_demo_thread_started)
    {
        return RT_EOK;
    }

    ret = rt_sem_init(&g_rt_ai_edgi_runner_demo_sem,
                      "edgirun",
                      0,
                      RT_IPC_FLAG_FIFO);
    if (ret != RT_EOK)
    {
        return ret;
    }

    g_rt_ai_edgi_runner_demo_thread =
        rt_thread_create("edgi_run",
                         rt_ai_edgi_runner_demo_thread_entry,
                         RT_NULL,
                         RT_AI_EDGI_RUNNER_DEMO_THREAD_STACK_SIZE,
                         RT_AI_EDGI_RUNNER_DEMO_THREAD_PRIORITY,
                         RT_AI_EDGI_RUNNER_DEMO_THREAD_TICK);
    if (g_rt_ai_edgi_runner_demo_thread == RT_NULL)
    {
        rt_sem_detach(&g_rt_ai_edgi_runner_demo_sem);
        return -RT_ERROR;
    }

    ret = rt_thread_startup(g_rt_ai_edgi_runner_demo_thread);
    if (ret != RT_EOK)
    {
        rt_thread_delete(g_rt_ai_edgi_runner_demo_thread);
        g_rt_ai_edgi_runner_demo_thread = RT_NULL;
        rt_sem_detach(&g_rt_ai_edgi_runner_demo_sem);
        return ret;
    }

    g_rt_ai_edgi_runner_demo_thread_started = RT_TRUE;
    return RT_EOK;
}

static int rt_ai_edgi_runner_demo(int argc, char **argv)
{
    rt_err_t ret;

    RT_UNUSED(argc);
    RT_UNUSED(argv);

    if (g_rt_ai_edgi_runner_demo_running)
    {
        rt_kprintf("RT-AK Edgi runner demo is already running\r\n");
        return -RT_EBUSY;
    }

    ret = rt_ai_edgi_runner_demo_ensure_thread();
    if (ret != RT_EOK)
    {
        return ret;
    }

    g_rt_ai_edgi_runner_demo_running = RT_TRUE;
    ret = rt_sem_release(&g_rt_ai_edgi_runner_demo_sem);
    if (ret != RT_EOK)
    {
        g_rt_ai_edgi_runner_demo_running = RT_FALSE;
        return ret;
    }

    rt_kprintf("RT-AK Edgi runner demo scheduled\r\n");
    return RT_EOK;
}
MSH_CMD_EXPORT(rt_ai_edgi_runner_demo, run Edgi model through config runner);
