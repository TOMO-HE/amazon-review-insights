# Amazon Review Insights Skill

一个用于 **Codex 的亚马逊评论分析 Skill**。导入评论文件，提取有原文依据的主题、情绪、场景、购买动机和需求，生成可离线查看的中文 VOC 风格交互报告。

支持 Windows，也可在有 Python 的 macOS/Linux 环境运行。与 VOC.AI 无隶属关系；它复用常见的评论洞察结构，不复制其内部模型、数据或品牌。

## 它如何工作

1. Python 读取 CSV、TSV、XLSX，识别常见中英文表头，检查重复 ID、日期、国家和缺失值。
2. Codex 阅读评论并作语义标注，为每个观点保留标题或正文中的原文证据。
3. 本地脚本验证引文、覆盖率和数据指纹，再计算提及条数、比例与星级。
4. 输出双栏卡片报告：任务画像、场景、明确需求、好评、差评、动机、改进建议、统计图和评论明细。

报告支持产品、变体、发布国家筛选；点击主题查看支持评论；搜索、按星级/主题筛选、分页和导出列表。所有静态数据随报告保存，打开报告不需要联网。

**这不是双击即可自动调用 AI 的 Windows 软件。** 它是给 Codex 使用的工作流与本地工具。Python 脚本负责准备、验证和呈现，不会独立理解所有新评论，也不调用模型。实际分析发生在执行 Skill 的 AI 环境中；数据如何进入模型、费用与隐私取决于该环境。报告只支持已导出的评论，不承诺从亚马逊链接抓取全部评论。

## 安装到 Codex

将本仓库里的 **`amazon-review-insights` 整个文件夹**放入 Codex 的 skills 目录。常见 Windows 路径：

```text
%USERPROFILE%\.codex\skills\amazon-review-insights\SKILL.md
```

若配置了 `CODEX_HOME`，放到它的 `skills` 子目录。让 Codex 重新加载技能后，通过 `$amazon-review-insights` 显式调用；也支持适用时自动选择。

推荐的请求：

> 使用 $amazon-review-insights 分析我上传的评论文件。生成类似 VOC 的中文交互报告，标明统计口径，保留每个结论对应的原文。多个变体请分别对比，不要猜测用户性别。

Skill 不依赖 GitHub、VOC.AI 账号或额外 API 密钥。XLSX 读取需要 `openpyxl`；如果执行环境已经提供该库，无需重复安装。普通 Python 环境可在仓库根目录运行：

```powershell
python -m pip install -r requirements.txt
```

## 本地演示（合成数据）

在仓库根目录运行以下命令。示例中的产品、评论与观点均为虚构，不是任何真实商品的分析结果。

```powershell
python amazon-review-insights/scripts/review_tool.py prepare examples/reviews.csv --out work/prepared.json
python amazon-review-insights/scripts/review_tool.py validate --data work/prepared.json --annotations examples/annotations.json
python amazon-review-insights/scripts/review_tool.py render --data work/prepared.json --annotations examples/annotations.json --out generated/demo.html
python -m unittest discover -s tests -v
```

用浏览器打开 `generated/demo.html`，另有 `generated/demo.audit.csv` 可用 Excel 查看。演示标注只适用于随包的示例文件；换新数据必须重新分析，不能直接复用示例标注或替换指纹。

## 新文件的使用方式

```powershell
python amazon-review-insights/scripts/review_tool.py prepare my-reviews.xlsx other-reviews.csv --out work/prepared.json
```

之后由 Codex 读取标准化记录、生成 `work/annotations.json`，再执行验证与生成。数据结构、表头映射和标注方式见 [数据契约](amazon-review-insights/references/data-contract.md)。分析边界见 [分析方法](amazon-review-insights/references/analysis-method.md)。

多工作表的 XLSX 如包含说明页，请通过 `--sheet` 选择评论页。非标准表头使用 `--mapping`；GBK CSV 使用 `--encoding gb18030`。旧 `.xls` 请先导出为 `.xlsx` 或 `.csv`。脚本不会修改源文件，也不会读取截图中的隐藏数据。

## 从参考报告学到的改进

- 保留六卡片、双栏排行和橙色统计图的阅读顺序；每项附实际条数、分母和原文入口。
- 不用星级代替主题情绪，允许五星评论里有续航或噪声问题。
- 区分磁力与胶粘、短续航与充电故障、USB 线与电源适配器。
- 明确需求与推导建议分开，功能优点与购买动机分开。
- 数据不足时不制造男女比例、职业分布、功能评分、Vine 数量或其他变体。
- 媒体评论与已验证购买并非互斥，不共用误导性的占比环图。
- 不同国家、变体、时间和覆盖范围的报告不能直接比较百分比。

验证器能发现引文不在原文、漏分析、重复标注、旧数据指纹等问题，**不能证明模型解释一定正确**。仍需抽查语义和具体建议。样本提及率也不是全体买家的问题发生率。

## 上传到 GitHub

在 GitHub 创建仓库后，将本目录内容放在仓库根目录上传：`README.md`、`LICENSE`、`requirements.txt`、`.gitignore`、技能目录、`examples` 与 `tests`。无需上传外层 ZIP。

本包不含真实客户评论、原参考截图、密钥或个人路径。不要默认将未来的 `work/`、`private-data/`、`generated/` 或客户报告提交到公开仓库。`.gitignore` 只是防误提交的辅助，发布前仍需检查暂存文件。

## 许可

代码、模板和说明按 [MIT](LICENSE) 发布。用户导入的评论、截图和其他第三方内容不因使用本工具而获得该许可。
