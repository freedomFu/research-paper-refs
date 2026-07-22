# 科研论文参考文献库

一个用于学术写作的个人 BibTeX 文献库。

## 命名规范

每条文献条目遵循以下模式：**`作者 + 主题内容/期刊会议名称 + 年份`**

## 仓库结构

- `bb.bib` —— 汇总后的总文献库（由 `refs/` 目录下的文件合并生成）。
- `refs/` —— 源 `.bib` 文件，按条目类型与主题进行分类：
  - `0x-*-example.bib` —— 各类条目的示例（期刊、会议、网址）。
  - `1x-journal-*.bib` —— 期刊论文，按主题分组（身份认证、HCI、Web、其他）。
  - `2x-conference-*.bib` —— 会议论文，按相同主题分组。
  - `3x-url-*.bib` —— 网络资源（身份认证、HCI、Web、通用）。
  - `4x-techreport-*.bib` —— 技术报告。
  - `5x-degree-*.bib` —— 学位论文（博士 / 硕士）。
- `scripts/merge_bib.py` —— 用于将 `refs/` 中的所有文件合并为 `bb.bib` 的脚本。

## 编辑规则

- `refs/` 目录中的条目需要**保持完整**——**不要**删减 `pages`，**不要**缩短 URL，也**不要**对会议/期刊名称进行简写。
- 任何裁剪或缩短（例如去掉 `pages`、把长 URL 换成短链接）只应在为某篇具体论文准备的文献副本中进行，**绝不**在本仓库中操作。
- 会议论文必须显式填写 `year = {YYYY}`；cite key 或 `booktitle` 中的年份不能代替 `year` 字段。
- 按既有约定使用 `@manual` 保存网页，并将链接写在 `note = {\url{...}}` 中。
- 月份使用 BibTeX 宏 `jan` 至 `dec`，不要混用 `{Apr.}`、`{April}` 等写法。

更完整的规范见 [文献库维护指南](BIBLIOGRAPHY-GUIDE-zh.md)。

## 使用方式

在 `refs/` 下对应的文件中新增或更新条目，然后重新生成汇总文献库：

```bash
python scripts/merge_bib.py
```

脚本同时支持自定义输入、输出路径和文件名正则：

```bash
# 默认：合并 refs/*-local.bib 到 bb.bib，并扫描重复条目。
python scripts/merge_bib.py

# 自定义输出文件。
python scripts/merge_bib.py -o all-refs.bib

# 多个输入（目录或单个 .bib 文件均可混用）。
python scripts/merge_bib.py refs other_dir refs/extra.bib

# 修改目录内文件名的匹配规则（对文件名做正则匹配）。
python scripts/merge_bib.py -p '\.bib$'

# 跳过重复标题扫描。
python scripts/merge_bib.py --no-dedup

# 在合并前，把每个输入文件里的条目按「年份升序 + key 前缀字典序」排序。
# 默认开启；用 --no-sort 保留原始顺序。
python scripts/merge_bib.py --no-sort

# 同样的排序，并且把排序结果**写回** refs/ 中的源文件。
python scripts/merge_bib.py --sort-in-place

# 最新文献优先；也可以用 key 按 cite key 排序。
python scripts/merge_bib.py --sort-order year-desc

# 预览/应用会议年份与月份的保守规范化。
python scripts/normalize_bib.py
python scripts/normalize_bib.py --write
```

合并完成后，脚本会输出：

- **不以 4 位年份结尾**的条目 key（往往是命名规范没遵守）。
- **重复条目分组** —— `@类型` 相同、并且标题在「小写化 + 去掉所有非字母数字」之后相同的条目会被列出，方便手动清理。重复条目**只会被标记**，不会被自动删除。
- 重复 cite key（忽略大小写）、重复 DOI 和缺失核心字段的条目。

**排序细节。** 默认优先读取条目的 `year`/`date` 字段（升序），缺失时才回退到cite key 末尾的年份，同年按完整 cite key 排序。可用 `--sort-order year-desc` 或`--sort-order key` 改变顺序。条目正上方紧邻的注释和空行会跟随该条目一起移动，因此 `% === 2005 ===`这类分组横幅会保持贴在所属年份的第一条上面。第一条 `@entry` 之前的所有内容会被当作文件头原样保留。

在你的 LaTeX 项目中引用 `bb.bib`，或按需复制单条条目即可。

快乐科研！
