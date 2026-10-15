# 白底主图、场景主图与六详情

输入：主推原始图和必要视角、选中SKU覆盖、用途/结构/尺寸依据、每单销售数量，绑定视觉规范。

使用：先读绑定项目当前文档，再组合[系统提示词](prompts/00_system.md)、[任务提示词](prompts/01_task.md)和商品简报。输出按[交付模板](templates/output.md)。

阻塞边界：原图不足时限制相关视角或换有证据构图，不拼别款或补隐藏结构；本次策划不自动调用出图或移除失败稿。

可用命令：`python -B sovyn.py prepare --module image --brief .local/product-brief.json --out .local/image-task.md`。命令只整理任务输入，不完成模型推理或外部操作。
