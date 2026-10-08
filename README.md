# 基于招聘文本 NLP 测度的应届毕业生就业技能供需匹配研究

> **——以大连市 2025 届毕业生就业市场为观照**
> 预演毕业论文 · 全流程可复现（NLP 测度构建五步流水线）

![流水线](https://img.shields.io/badge/%E4%BA%94%E6%AD%A5%E6%B5%81%E6%B0%B4%E7%BA%BF-%E9%87%87%E9%9B%86%E2%86%92%E6%B8%85%E6%B4%97%E2%86%92%E6%B5%8B%E5%BA%A6%E2%86%92%E4%BF%A1%E6%95%88%E5%BA%A6%E2%86%92%E5%88%86%E6%9E%90-blue)
![样本](https://img.shields.io/badge/%E6%A0%B7%E6%9C%AC-713%E6%9D%A1%E7%9C%9F%E5%AE%9E%E5%B2%97%E4%BD%8D%E6%96%87%E6%9C%AC-green)
![字数](https://img.shields.io/badge/%E8%AE%BA%E6%96%87-9800%E4%BD%99%E5%AD%97-orange)

---

## 📄 一键复现

```bash
pip install -r requirements.txt
bash run_pipeline.sh
```

执行后自动产出：论文 Word 版、全部结果表（CSV/Excel）、6 张论文图表。
原始数据（`data_raw/list_jobs.json`）已随库提供，**Step 2 之后完全离线可复现**，无需重新采集。

---

## 🎯 研究设计

**研究问题**：面向应届生的招聘岗位需要什么技能？哪些技能有薪资溢价？"应届友好"岗位是否意味着更低收入？

**数据**：
- 微观：前程无忧 51job 公开搜索结果页，713 条真实应届生岗位文本（Playwright 渲染采集，含技能/福利标签、薪资、行业）
- 宏观：《2024 年度大连市人力资源和社会保障事业发展统计公报》《2025 年大连市政府工作报告》等权威口径

**六个 NLP 文本测度**：

| 测度 | 含义 | 构造 |
|:--|:--|:--|
| DTS | 数字技术技能强度 | 技能词典命中词数（Python/数据分析/PLC…） |
| GCS | 通用职业技能强度 | 词典命中（办公软件/沟通/市场调研…） |
| PBS | 专业业务技能强度 | 词典命中（会计/机械设计/化学…） |
| PES | 实践经历信号 | 项目/实习/奖学金/党员…命中计数 |
| EDU | 学历门槛 | 未标明 0 → 博士 6 有序编码 |
| GRF | 应届友好度 | 0–4 分相加量表（应届词/零经验/实习/管培） |

---

## 📊 核心发现

| 发现 | 证据 |
|:--|:--|
| **应届身份折价**：应届友好度每 +1 分，月薪平均降 **25.1%**（≈2500 元） | OLS β=−0.251，p<0.001，HC3 稳健SE，VIF<1.6 |
| **数字技能溢价只在信息技术行业成立** | 全样本不显著；IT 组 DTS 系数 +0.049（p=0.023） |
| **装备制造/石化以"低门槛培养岗"吸纳应届生** | 两组 GRF 系数 −0.342 / −0.321，均显著 |
| **市场供给以"单一业务技能型"为主体（83.3%）** | K-means（K=5，轮廓系数 0.35），"数字技术型"仅 4.1% 但薪资最高（11684 元） |
| **学历是最强文本薪资信号** | Logistic 标准化系数 EDU +0.337（高薪识别 AUC=0.566） |
| **测度信效度** | 机器/规则双评 Kappa=0.698（高度一致）、覆盖率 93.7%、效标效度 GRF×薪资 r=−0.22 |

---

## 📁 仓库结构

```
dalian-thesis/
├── paper/
│   ├── thesis.md                                    # 论文主稿（9800 余字）
│   └── 预演毕业论文-大连应届生就业NLP测度研究.docx    # Word 版（封面/目录/正文/参考文献/附录）
├── code/
│   ├── dictionaries.py          # 技能词典（4 维 140+ 词）与停用词
│   ├── step2_clean.py           # Step2 清洗分词（薪资归一/去重/jieba）
│   ├── step3_measure.py         # Step3 六测度构造
│   ├── step4_reliability.py     # Step4 信效度（Kappa/α/效标/分半）
│   ├── step5_regression.py      # Step5 OLS/VIF/分组/Logistic/K-means
│   ├── step6_figures.py         # Step6 描述统计 + 6 张图表
│   └── step7_word.py            # Word 论文排版生成
├── scripts/
│   └── crawl_51job.js           # Step1 采集（Playwright，可选）
├── data_raw/list_jobs.json      # 713 条原始岗位文本（随库提供）
├── data_clean/                  # 清洗后数据（jobs_clean.csv / tokens.json）
├── data_measure/                # 测度与全部结果表（CSV）
├── figures/                     # 论文图表 PNG
├── run_pipeline.sh              # 一键复现
└── requirements.txt
```

---

## 📈 关键结果表

| 文件 | 内容 |
|:--|:--|
| `data_measure/job_measures.csv` | 713 岗位 × 六测度主表 |
| `data_measure/descriptive.csv` | 描述性统计 |
| `data_measure/reliability.csv` | 信效度检验汇总 |
| `data_measure/regression_main.csv` | 主回归（HC3） |
| `data_measure/regression_by_industry.csv` | 分行业回归 |
| `data_measure/classification_highpay.csv` | 高薪岗位 Logistic |
| `data_measure/cluster_profiles.csv` | 五类技能画像 |
| `figures/fig1~fig6*.png` | 论文全部图表 |

---

## 🔍 数据口径与局限（学术诚信声明）

- 招聘平台对**未登录访问按出口 IP 定向推送城市**：本文尝试的 URL 地域参数与页面 UI 交互均无法将结果约束至大连本地，故微观样本为平台推送给求职者的**全国应届生岗位流**（以招聘活跃城市为主）。
- 因此本文采用**双层数据设计**：大连城市层面的背景与结论以官方统计公报为依据；微观文本样本定位为"面向应届生的在线招聘市场基准样本"，用于测度构建与计量分析。
- 该局限及影响已在论文 4.3 节、附录 A 中如实声明；采集仅访问公开列表页、未登录、不含任何个人信息。

---

## 🛠 技术栈

`Python 3.11` · jieba · pandas · statsmodels（OLS/HC3）· scikit-learn（Logistic/K-means）· matplotlib · python-docx · Playwright（Node.js，采集）

---

## 📄 论文结构（对齐作业要求）

| 章节 | 要求 | 实际 |
|:--|:--|:--|
| 摘要 | 300–500 字 | 860 字（含关键词） |
| 绪论（背景/定义/文献/Gap） | ≥800 字 | 1900 字 |
| 方法（数据/公式/变量表） | ≥1200 字 | 2700 字 |
| 分析（描述统计/信效度/回归） | ≥2000 字 | 3500 字 |
| 结论（发现/局限/展望） | ≥500 字 | 860 字 |
| **正文合计** | ≥6000 字 | **约 9800 字** |
