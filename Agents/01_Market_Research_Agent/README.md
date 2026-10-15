# 市场与选品

输入：商品原始资料、明确市场MY、目标使用者假设、已有1688/Kalodata/Shopee MY参考及来源周期。研究数量/范围/费用沿用当批授权。

使用：先读绑定项目当前文档，再组合[系统提示词](prompts/00_system.md)、[任务提示词](prompts/01_task.md)和商品简报。输出按[交付模板](templates/output.md)。

阻塞边界：主推身份冲突、市场/规格不可比、供货与实物关键门槛缺失时，不报已选中可上架；可继续有依据的探索分析。

可用命令：`python -B sovyn.py prepare --module market --brief .local/product-brief.json --out .local/market-task.md`。命令只整理任务输入，不完成模型推理或外部操作。
