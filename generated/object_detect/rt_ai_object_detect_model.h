#ifndef __RT_AI_OBJECT_DETECT_MODEL_H__
#define __RT_AI_OBJECT_DETECT_MODEL_H__

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define RT_AI_OBJECT_DETECT_MODEL_NAME              "object_detect"

#define RT_AI_OBJECT_DETECT_IN_NUM                  (1)
#define RT_AI_OBJECT_DETECT_OUT_NUM                 (1)

#define RT_AI_OBJECT_DETECT_IN_1_SIZE               (320U * 320U * 3U)
#define RT_AI_OBJECT_DETECT_IN_1_SIZE_BYTES         (RT_AI_OBJECT_DETECT_IN_1_SIZE * sizeof(uint8_t))

#define RT_AI_OBJECT_DETECT_OUT_1_SIZE              (40U)
#define RT_AI_OBJECT_DETECT_OUT_1_SIZE_BYTES        (RT_AI_OBJECT_DETECT_OUT_1_SIZE * sizeof(float))

#define RT_AI_OBJECT_DETECT_WORK_BUFFER_BYTES       (0U)
#define RT_AI_OBJECT_DETECT_BUFFER_ALIGNMENT        (16U)

/* Compatibility aliases for old minimal wrapper/demo */
#define RT_AI_OBJECT_DETECT_INPUT_SIZE              RT_AI_OBJECT_DETECT_IN_1_SIZE
#define RT_AI_OBJECT_DETECT_OUTPUT_SIZE             RT_AI_OBJECT_DETECT_OUT_1_SIZE

#define RT_AI_OBJECT_DETECT_INPUT_DTYPE             "uint8"
#define RT_AI_OBJECT_DETECT_OUTPUT_DTYPE            "float32"
#define RT_AI_OBJECT_DETECT_INPUT_SHAPE_TEXT        "[3, 320, 320]"
#define RT_AI_OBJECT_DETECT_OUTPUT_SHAPE_TEXT       "[5, 8]"

int rt_ai_object_detect_model_init(void);
int rt_ai_object_detect_model_run(void);
int rt_ai_object_detect_model_deinit(void);

void *rt_ai_object_detect_model_get_input(uint32_t index);
void *rt_ai_object_detect_model_get_output(uint32_t index);

#ifdef __cplusplus
}
#endif

#endif /* __RT_AI_OBJECT_DETECT_MODEL_H__ */
