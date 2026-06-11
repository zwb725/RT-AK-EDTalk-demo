#ifndef __BACKEND_EDGI_H__
#define __BACKEND_EDGI_H__

/*
 * RT-AK Plugin Edgi minimal backend interface.
 *
 * Current stage:
 * - wrap DeepCraft / Imagimob IMAI runtime
 * - expose input / output buffer
 * - keep UVC / LCD / postprocess outside backend
 */

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define BACKEND_EDGI_OK                  (0)
#define BACKEND_EDGI_ERROR              (-1)
#define BACKEND_EDGI_ERROR_NULL         (-2)
#define BACKEND_EDGI_ERROR_NOT_INIT     (-3)
#define BACKEND_EDGI_ERROR_BAD_INDEX    (-4)

#ifndef BACKEND_EDGI_INPUT_SIZE
#define BACKEND_EDGI_INPUT_SIZE         (320U * 320U * 3U)
#endif

#ifndef BACKEND_EDGI_OUTPUT_SIZE
#define BACKEND_EDGI_OUTPUT_SIZE        (40U)
#endif

typedef struct backend_edgi_config
{
    const char *model_name;
    uint32_t input_size;
    uint32_t output_size;
    void *user_data;
} backend_edgi_config_t;

int backend_edgi_init(const backend_edgi_config_t *config);
int backend_edgi_run(const void *input, void *output);
int backend_edgi_deinit(void);

void *backend_edgi_get_input(uint32_t index);
void *backend_edgi_get_output(uint32_t index);

int backend_edgi_is_initialized(void);
int backend_edgi_get_last_error(void);

#ifdef __cplusplus
}
#endif

#endif /* __BACKEND_EDGI_H__ */