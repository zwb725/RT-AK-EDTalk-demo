1. 生成命令
2. 导出路径
3. scons -j 8 编译成功
4. Debug/rtthread.hex 生成
5. RT-Thread Studio 烧录成功
6. 串口执行 rt_ai_edgi_minimal_demo
7. 输出 output[0..39]
8. 当前结论：链路跑通，但固定 pattern 输入导致 output 全 0，后续需要接真实图像输入验证