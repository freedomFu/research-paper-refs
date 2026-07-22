# 科研文献库维护指南

## 主库的职责

本仓库保存可用于正式引用的权威元数据。主库应尽量完整，不为某一本期刊的版式要求
删字段；期刊名缩写以及 DOI、URL 是否显示，应交给论文项目的参考文献样式处理。

阅读笔记和论文评价不宜塞入会直接交给期刊的 `bb.bib`。建议用 cite key 关联独立的
Markdown 笔记，例如 `notes/MainkaSingleSignOn2017.md`。

## 最低字段要求

- `@article`：`author`、`title`、`journal`、`year`；能找到时补 `volume`、
  `number`、`pages`、`doi`。
- `@inproceedings`：`author`、`title`、`booktitle`、`year`；能找到时补
  `pages`、`doi`、`publisher`。年份即使已出现在 cite key 或会议名中，也要单独填写。
- `@manual` 网页：`title`、`year`、`note = {\url{完整链接}}`；有作者时填写
  `author`，机构作者用双花括号保护，例如 `author = {{NIST}}`。
- `@techreport`：`author`、`title`、`institution`、`number`、`year`。
- 学位论文：`author`、`title`、`school`、`year`。

网页没有发布日期时，`year` 可以表示访问/核验年份，但应在阅读笔记中记录完整访问
日期，以免日后把访问年份误认为发布日期。

## Cite key

继续使用“作者 + 简短主题或 venue + 年份”的现有习惯，但应满足：仅使用稳定字符、
末尾保留四位年份、发生冲突时加 `a`/`b`。key 一旦在论文中使用，不应随意修改。

## 推荐录入流程

1. 优先从 DOI 落地页、出版社或会议官网取得元数据。
2. 人工核对作者顺序、标题、年份、页码和正式 venue 名称。
3. 保存到 `refs/` 中对应的类型/主题文件。
4. 运行 `python scripts/normalize_bib.py` 预览规范化。
5. 确认后运行 `python scripts/normalize_bib.py --write`。
6. 运行 `python scripts/merge_bib.py --sort-in-place`，处理核心字段、重复 key、
   重复 DOI 和重复标题警告。
7. 运行 `python -m unittest discover -s tests -v`。
8. 检查本地差异，由仓库所有者自行提交和推送。

## 排序策略

默认的 `year-asc` 适合观察研究演进；文献综述若关注最新工作，可使用
`--sort-order year-desc`；`--sort-order key` 用于纯 cite key 排序。排序首先使用
条目的 `year`/`date`，缺失时才读取 cite key 年份，同年按 cite key 排序，以保证
多次运行结果稳定。

## 阅读笔记建议

独立笔记可记录：阅读状态、研究问题、方法、数据集、样本量、核心结论、局限性、
复现材料、与当前项目的关系、计划引用章节、个人评价和最后核验日期。主题标签适合
一篇论文对应多个主题，避免为了分类而复制 BibTeX 条目。

## 备份与隐私

当前 `*-local.bib` 和 `bb.bib` 被 `.gitignore` 排除，不会随普通 Git 提交上传。
这适合只公开工具和模板，但也意味着真实文献库没有 Git 历史，应另行使用私有仓库、
加密云盘或定期快照备份。
