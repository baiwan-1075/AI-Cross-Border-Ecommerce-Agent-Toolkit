# 产品策略与经济性

输入：已锁主推SKU、选中款范围与每单件数，供应价/国内费用包含关系，包装后计费重和当前保存计算参数，同行同规格可比价格。

使用：先读绑定项目当前文档，再组合[系统提示词](prompts/00_system.md)、[任务提示词](prompts/01_task.md)和商品简报。输出按[交付模板](templates/output.md)。

阻塞边界：采购或计费重未知不报确定售价/利润；当前费用资格未知仅作条件试算；不自动调价、采购或修改正式DB。

可用命令：`python -B sovyn.py prepare --module strategy --brief .local/product-brief.json --out .local/strategy-task.md`。命令只整理任务输入，不完成模型推理或外部操作。
