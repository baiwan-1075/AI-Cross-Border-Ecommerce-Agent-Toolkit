# 自然流量与成交诊断

输入：Seller Center实际数据及来源截图/导出，MY/账号/商品SKU/视频身份、渠道、捕获时间、窗口起止、发布时间和指标定义。

使用：先读绑定项目当前文档，再组合[系统提示词](prompts/00_system.md)、[任务提示词](prompts/01_task.md)和商品简报。输出按[交付模板](templates/output.md)。

阻塞边界：渠道、SKU或窗口不一致不合算；仅榜单分数不报真实订单/完播率；没有费用不算广告承受能力。

可用命令：`python -B sovyn.py prepare --module performance --brief .local/product-brief.json --out .local/performance-task.md`。命令只整理任务输入，不完成模型推理或外部操作。
