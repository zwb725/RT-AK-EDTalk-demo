#ifndef __RT_AI_EDGI_RUNNER_H__
#define __RT_AI_EDGI_RUNNER_H__

#include <stddef.h>
#include <stdint.h>

#include "rt_ai.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct rt_ai_edgi_runner_config
{
    const char *model_name;
    uint32_t input_bytes;
    uint32_t output_bytes;
    const char *input_dtype;
    const char *output_dtype;
    const char *preprocess_type;
    const char *postprocess_type;
} rt_ai_edgi_runner_config_t;

typedef struct rt_ai_edgi_runner
{
    rt_ai_t model;
    const rt_ai_edgi_runner_config_t *config;
    uint8_t initialized;
} rt_ai_edgi_runner_t;

int rt_ai_edgi_runner_init(rt_ai_edgi_runner_t *runner,
                           const rt_ai_edgi_runner_config_t *config);
void rt_ai_edgi_runner_deinit(rt_ai_edgi_runner_t *runner);
void *rt_ai_edgi_runner_input(rt_ai_edgi_runner_t *runner);
void *rt_ai_edgi_runner_output(rt_ai_edgi_runner_t *runner);
int rt_ai_edgi_runner_run(rt_ai_edgi_runner_t *runner);
int rt_ai_edgi_runner_run_input(rt_ai_edgi_runner_t *runner,
                                const void *input,
                                uint32_t input_bytes);
const rt_ai_edgi_runner_config_t *rt_ai_edgi_runner_default_config(void);

#ifdef __cplusplus
}
#endif

#endif /* __RT_AI_EDGI_RUNNER_H__ */
