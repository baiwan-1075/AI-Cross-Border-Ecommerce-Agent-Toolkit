# Sovyn MY 宠物运营工具箱 · v0.1.0

为TikTok Shop Malaysia宠物业务定制：从1688商品资料、真实购买价值、成本约束出发，准备马来文页面、八图方案和专属视频脚本，再用后台数据复盘。

这是可供现有智能体直接使用的工作流、提示词和本地辅助命令。命令能整理输入、检查来源、计算明确口径的漏斗并调用现有定价内核；内容判断仍由智能体完成。没有模型服务、自动生成、自动上架或自动改价。

## 日常怎么用

1. 在Codex中打开本目录；首次绑定业务项目。真实绑定和报告只保存在`.local/`。
2. 告诉小冕任务、商品编号或资料目录、做到哪一阶段。已有授权和资料复用，不必重复填一张新表。
3. 小冕先核本地权威文档与商品身份，再选择模块。完成结果附来源、未知项、实际验收与下一步。

可直接说：

> 查看这款商品原始资料，先判断购买价值和关键演示，核对价格竞争力，交付一条完整视频脚本。缺证的规格不要写，先不生成。

> 比较这两条实际视频和对应后台数据，指出具体区间的问题，提出一轮只改变一个内容版本的测试方案。不要把低播放直接归因于挂车。

## 七个模块

|模块|入口|结果与边界|
|---|---|---|
|01市场与选品|[市场模块](Agents/01_Market_Research_Agent/README.md)|购买动机、演示设想、MY需求/竞争和缺口；第三方线索不当本店成交|
|02产品与经济性|[策略模块](Agents/02_Product_Strategy_Agent/README.md)|主推身份、价格口径、条件贡献；复用现役计算器|
|03马来文页面|[文案模块](Agents/03_Listing_Creative_Agent/README.md)|一个最终标题、详情、规格/适用边界；回填需对应授权|
|04八图策划|[图片模块](Agents/04_Product_Image_Agent/README.md)|白底＋场景＋六详情；同SKU、选款覆盖、实际视觉验收分开|
|05商品视频|[视频模块](Agents/05_Product_Video_Agent/README.md)|完整本地口播、释义及必要分镜；按问题选形式，制作另按授权|
|06自然流量诊断|[数据模块](Agents/06_Organic_Performance_Agent/README.md)|观看→商品曝光→点击→成交；没有广告也能使用|
|07评论与售后|[评论模块](Agents/07_Review_Analysis_Agent/README.md)|具体归因、可直接使用的页面修补与回流建议|

现役业务项目的规则是唯一权威，本仓库的[配置](profiles/sovyn-my/profile.json)只维护路由和接口；来源变更通过`doctor`报告，不静默沿用旧哈希。

## 本地命令

只需Python 3.11标准库，无需安装依赖。输出路径限本仓库`.local/`且不得覆盖已有文件。

```powershell
python -B sovyn.py bind --project-root "你的TK项目路径" --assets-root "你的商品资料路径" --pricing-root "你的现役定价工具路径"
python -B sovyn.py doctor
python -B sovyn.py inventory --folder "商品文件夹名" --out .local/inventory.json
python -B sovyn.py prepare --module video --brief .local/product-brief.json --out .local/video-task.md
python -B sovyn.py prepare --module workflow --brief .local/product-brief.json --out .local/workflow-task.md
python -B sovyn.py funnel --input .local/video-metrics.json --out .local/funnel-report.json
python -B sovyn.py pricing --product-cost-cny 你的采购成本 --weight-g 你的包装后计费重 --out .local/pricing-report.json
python -B sovyn.py check
python -B -m unittest discover -s tests -v
```

`inventory`只枚举资料和匹配工作台记录，不证明图片正确。`prepare`整理给智能体的任务输入，不执行模型推理。`pricing`只读保存参数、调用本地内核，输出条件报价与未核项；不以旧草稿里的商品成本替代本次商品。`funnel`要求统一周期、商品与渠道，不使用固定行业阈值。

输入示例见[合成商品简报](examples/synthetic-product.json)、[合成指标](examples/synthetic-metrics.json)和[使用指南](docs/USAGE.md)。真实演练在本地`.local/acceptance/`，不会提交。

## 来源、交付与回退

源自`heqiangdiao-wq/AI-Cross-Border-Ecommerce-Agent-Toolkit`，上游基线`8a7d0d5b73d38853df0a33d69e506146b2cce394`，原始文件及案例保存在[上游参考](reference/upstream/README.md)，完整Git历史及[MIT许可证](LICENSE)保留。上游巴西站方法、九图和广告阈值不作为本版本默认规则。

设计与实施依据见[首版设计](docs/superpowers/specs/2026-10-16-sovyn-my-toolkit-design.md)、[实施计划](docs/superpowers/plans/2026-10-16-sovyn-my-toolkit-plan.md)、[迁移说明](docs/MIGRATION.md)。回退到上游commit可查看原始版本；外部业务工作台、素材和定价库不会随本仓库回退。

远程fork与本地改造是两个状态，实际结果见[交付状态](docs/DELIVERY.md)。本地测试不证明远程fork、已发布、视觉通过或成交效果。
