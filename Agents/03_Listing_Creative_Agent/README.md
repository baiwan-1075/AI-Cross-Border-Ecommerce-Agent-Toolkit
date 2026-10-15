# 马来文商品页面

输入：商品事实、主推和选中SKU、销售件数、购买理由、当前关键词证据。沿用唯一工作台，不新建日常标题TXT。

使用：先读绑定项目当前文档，再组合[系统提示词](prompts/00_system.md)、[任务提示词](prompts/01_task.md)和商品简报。输出按[交付模板](templates/output.md)。

阻塞边界：商品身份、销售数量或关键适用条件冲突时，暂停相关宣称；无关键词证据不假称热搜。

可用命令：`python -B sovyn.py prepare --module listing --brief .local/product-brief.json --out .local/listing-task.md`。命令只整理任务输入，不完成模型推理或外部操作。
