# 商品视频内容与导演分镜

输入：本品真实参考、目标人群/购买疑问、已有有效分析和同SKU身份；改稿时另提供实际成片、发布时间及可比数据。

使用：先读绑定项目当前文档，再组合[系统提示词](prompts/00_system.md)、[任务提示词](prompts/01_task.md)和商品简报。输出按[交付模板](templates/output.md)。

阻塞边界：SKU/关键操作冲突只暂停相应方向；缺未知背面可改有依据视角。脚本交付不等于生成、视听验收或发布。

可用命令：`python -B sovyn.py prepare --module video --brief .local/product-brief.json --out .local/video-task.md`。命令只整理任务输入，不完成模型推理或外部操作。
