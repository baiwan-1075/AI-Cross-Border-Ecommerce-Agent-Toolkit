# Sovyn MY 工具箱实施计划

目标：交付可使用的本地专属工作流，并验证其业务数据边界。

设计：[首版设计](../specs/2026-10-16-sovyn-my-toolkit-design.md)。按用户已确认方案由当前智能体顺序实施，不派发其他线程。

技术：Markdown / JSON / Python 3.11标准库 / Git；不安装依赖。

## 实施与验证

1. **基线与分离。** 独立克隆上游，建`codex/sovyn-my-v1`；归档上游活跃文档，保留LICENSE与历史。真实配置默认忽略；记录外部文件改前哈希。
2. **配置和七模块。** `profiles/sovyn-my/profile.json`保存业务定位、文档路由；`Agents/*/{README,prompts,templates}`保存具体输入输出；`docs/`说明授权、证据、迁移和验收。
3. **只读适配。** `toolkit/context.py`负责本地绑定、文档指纹、只读XLSX与资料清单；`toolkit/workflow.py`负责简报检查和任务包；`toolkit/metrics.py`负责自然漏斗；`toolkit/pricing.py`复用外部计算内核；`sovyn.py`是命令入口。
4. **行为检查。** `tests/`覆盖缺失不当0、非法数字、统计口径、商品路径逃逸、输出越界/覆盖、XLSX富文本、同SKU及授权边界。用`unittest`复验，不用测试证明市场效果。
5. **真实演练。** 只读选定一款商品的原始资料与工作台，生成本地简报、七模块任务包和实际分析稿。核对未知尺寸/安装条件不被补造；没成本不报确定利润。真实案例不提交。
6. **交付。** `doctor`、`check`、单测、实际CLI和外部哈希一致检查；写本地验收报告，审查diff与Git隐私边界后创建checkpoint。远程fork、push分别如实报告。

主要失败路径：资料不存在/编号冲突、过期规则或来源变动、私有资料误跟踪、指标窗口或SKU不一致、正式DB占用/缺失、费用参数未知、GitHub认证/网络障碍。保留缺口，返回可操作错误，不越界重试或造数据。
