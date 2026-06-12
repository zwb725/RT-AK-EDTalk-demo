#include <rtthread.h>
#include "rt_ai.h"
#include "rt_ai_common.h"
#include "backend_edgi.h"
#include "rt_ai_object_detect_model.h"

#ifdef RT_AI_USE_EDGI

#define RT_AI_OBJECT_DETECT_IN_SIZE_BYTES       \
{                                               \
    RT_AI_OBJECT_DETECT_IN_1_SIZE_BYTES,        \
}

#define RT_AI_OBJECT_DETECT_OUT_SIZE_BYTES      \
{                                               \
    RT_AI_OBJECT_DETECT_OUT_1_SIZE_BYTES,       \
}

#define RT_AI_OBJECT_DETECT_INFO                \
{                                               \
    RT_AI_OBJECT_DETECT_IN_NUM,                 \
    RT_AI_OBJECT_DETECT_OUT_NUM,                \
    RT_AI_OBJECT_DETECT_IN_SIZE_BYTES,          \
    RT_AI_OBJECT_DETECT_OUT_SIZE_BYTES,         \
    RT_AI_OBJECT_DETECT_WORK_BUFFER_BYTES,      \
    0,                                          \
}

#define RT_AI_OBJECT_DETECT_HANDLE              \
{                                               \
    .info = RT_AI_OBJECT_DETECT_INFO,           \
}

#define RT_EDGI_AI_OBJECT_DETECT                \
{                                               \
    .parent = RT_AI_OBJECT_DETECT_HANDLE,       \
    .config =                                  \
    {                                           \
        RT_AI_OBJECT_DETECT_MODEL_NAME,         \
        RT_AI_OBJECT_DETECT_IN_1_SIZE_BYTES,    \
        RT_AI_OBJECT_DETECT_OUT_1_SIZE,         \
        RT_NULL,                                \
    },                                          \
}

static edgi_ai_t rt_edgi_ai_object_detect = RT_EDGI_AI_OBJECT_DETECT;

static int rt_ai_object_detect_model_register(void)
{
    return rt_ai_register(RT_AI_T(&rt_edgi_ai_object_detect),
                          RT_AI_OBJECT_DETECT_MODEL_NAME,
                          0,
                          backend_edgi,
                          &rt_edgi_ai_object_detect);
}
INIT_APP_EXPORT(rt_ai_object_detect_model_register);

#endif /* RT_AI_USE_EDGI */