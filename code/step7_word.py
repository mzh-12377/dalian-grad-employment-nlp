# -*- coding: utf-8 -*-
"""
Step 7 · 生成规范 Word 版论文（封面、目录、正文、参考文献）
输出: paper/预演毕业论文-大连应届生就业NLP测度研究.docx
"""
import os, re
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "paper", "thesis.md")
OUT = os.path.join(ROOT, "paper", "预演毕业论文-大连应届生就业NLP测度研究.docx")

doc = Document()

# ---------- 页面与默认字体 ----------
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21), Cm(29.7)
sec.left_margin = sec.right_margin = Cm(2.8)
sec.top_margin, sec.bottom_margin = Cm(2.5), Cm(2.5)

style = doc.styles["Normal"]
style.font.name = "Times New Roman"
style.font.size = Pt(12)
style.element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
style.paragraph_format.line_spacing = 1.5

def set_font(run, name_cn="宋体", name_en="Times New Roman", size=12, bold=False, color=None):
    run.font.name = name_en
    run.font.size = Pt(size)
    run.font.bold = bold
    if color:
        run.font.color.rgb = RGBColor(*color)
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name_cn)

def para(text="", size=12, bold=False, align="left", name_cn="宋体", space_after=6, indent=True, color=None):
    p = doc.add_paragraph()
    aligns = {"left": WD_ALIGN_PARAGRAPH.LEFT, "center": WD_ALIGN_PARAGRAPH.CENTER,
              "right": WD_ALIGN_PARAGRAPH.RIGHT, "just": WD_ALIGN_PARAGRAPH.JUSTIFY}
    p.alignment = aligns[align]
    p.paragraph_format.space_after = Pt(space_after)
    if indent and align == "left":
        p.paragraph_format.first_line_indent = Pt(24)
    r = p.add_run(text)
    set_font(r, name_cn=name_cn, size=size, bold=bold, color=color)
    return p

# ---------- 封面 ----------
for _ in range(5):
    para("", indent=False)
para("本科毕业论文（预演稿）", 22, True, "center", "黑体", space_after=18, indent=False)
para("基于招聘文本 NLP 测度的应届毕业生就业", 16, True, "center", "黑体", space_after=0, indent=False)
para("技能供需匹配研究", 16, True, "center", "黑体", space_after=8, indent=False)
para("——以大连市 2025 届毕业生就业市场为观照", 14, True, "center", "楷体", space_after=30, indent=False)
for label, val in [("学    院", "×××学院"), ("专    业", "×××专业"), ("姓    名", "×××"),
                   ("学    号", "××××××××"), ("指导教师", "×××"), ("完成日期", "2025 年 × 月")]:
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(f"{label}：  {val}")
    set_font(r, name_cn="宋体", size=13)
    p.paragraph_format.space_after = Pt(10)
doc.add_page_break()

# ---------- 目录（静态） ----------
para("目  录", 16, True, "center", "黑体", space_after=16, indent=False)
toc = [
    ("摘  要", "I"), ("Abstract（关键词见摘要）", "I"),
    ("一、绪论", "1"), ("1.1 选题背景", "1"), ("1.2 研究定义与研究问题", "2"), ("1.3 文献综述与研究空白", "2"),
    ("二、研究方法", "3"), ("2.1 数据来源与采集", "3"), ("2.2 文本清洗与预处理", "4"), ("2.3 NLP 测度构造", "4"),
    ("2.4 检验与模型设定", "5"), ("2.5 五步流水线与可复现性", "6"),
    ("三、实证分析", "6"), ("3.1 描述性统计", "6"), ("3.2 信度与效度检验", "7"), ("3.3 回归分析", "8"),
    ("3.4 高薪岗位识别与技能画像", "9"), ("3.5 结果汇总", "10"),
    ("四、结论", "10"), ("4.1 主要发现", "10"), ("4.2 政策与实践启示", "11"), ("4.3 研究局限与展望", "11"),
    ("参考文献", "12"), ("附录 A 数据来源说明", "13"),
]
for t, pg in toc:
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(4)
    r = p.add_run(t + "　" + "·" * max(2, 46 - len(t) * 2) + " " + pg)
    set_font(r, size=11.5)
doc.add_page_break()

# ---------- 解析 markdown 并输出正文 ----------
md = open(SRC, encoding="utf-8").read()
lines = md.split("\n")

def flush_table(rows):
    """rows: list of cell-list"""
    if not rows:
        return
    ncol = max(len(r) for r in rows)
    tb = doc.add_table(rows=len(rows), cols=ncol)
    tb.style = "Table Grid"
    tb.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, row in enumerate(rows):
        for j in range(ncol):
            cell = tb.cell(i, j)
            cell.text = ""
            txt = row[j] if j < len(row) else ""
            cp = cell.paragraphs[0]
            cp.alignment = WD_ALIGN_PARAGRAPH.CENTER if i == 0 else WD_ALIGN_PARAGRAPH.LEFT
            r = cp.add_run(txt)
            set_font(r, size=9.5, bold=(i == 0))
    doc.add_paragraph().paragraph_format.space_after = Pt(2)

i = 0
in_ref = False
table_buf = []
while i < len(lines):
    ln = lines[i].rstrip()
    # 表格收集
    if ln.startswith("|"):
        cells = [c.strip() for c in ln.strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
            i += 1; continue   # 分隔行
        table_buf.append(cells)
        i += 1; continue
    else:
        if table_buf:
            flush_table(table_buf); table_buf = []

    if not ln.strip():
        i += 1; continue
    if ln.startswith("# "):          # 论文大标题
        i += 1; continue              # 封面已含
    if ln.startswith("---"):
        i += 1; continue
    if ln.startswith("## "):
        title = ln[3:].strip()
        if title.startswith("摘要"):
            para("摘  要", 15, True, "center", "黑体", space_after=12, indent=False)
        elif title.startswith("一"):
            para("一、绪论", 15, True, "center", "黑体", space_after=12, indent=False)
        elif title.startswith("二"):
            para("二、研究方法", 15, True, "center", "黑体", space_after=12, indent=False)
        elif title.startswith("三"):
            para("三、实证分析", 15, True, "center", "黑体", space_after=12, indent=False)
        elif title.startswith("四"):
            para("四、结论", 15, True, "center", "黑体", space_after=12, indent=False)
        elif title.startswith("参考文献"):
            para("参考文献", 15, True, "center", "黑体", space_after=12, indent=False)
            in_ref = True
        i += 1; continue
    if ln.startswith("### "):
        para(ln[4:].strip(), 13, True, "left", "黑体", space_after=8, indent=False)
        i += 1; continue
    if ln.startswith("> "):          # 公式行
        para(ln[2:].strip(), 11.5, False, "center", "宋体", space_after=8, indent=False)
        i += 1; continue
    if ln.startswith("**表") or ln.startswith("**图"):
        para(ln.replace("**", ""), 11, True, "center", "黑体", space_after=6, indent=False)
        i += 1; continue
    if ln.startswith("**关键词**"):
        para(ln.replace("**", "").strip(), 12, False, "left", "宋体", space_after=10, indent=False)
        i += 1; continue
    # 普通段落（合并续行）
    text = ln
    while i + 1 < len(lines) and lines[i+1].strip() and not re.match(r"^(#{1,3} |\||> |- |\*\*表|\*\*图|\*\*关键词)", lines[i+1]):
        i += 1
        text += lines[i].strip()
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)   # 去粗体标记
    if in_ref:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.first_line_indent = Pt(-24)
        p.paragraph_format.left_indent = Pt(24)
        r = p.add_run(text)
        set_font(r, size=10.5)
    else:
        para(text, 12, False, "just", "宋体", space_after=6)
    i += 1
if table_buf:
    flush_table(table_buf)

# ---------- 附录：数据来源说明 ----------
doc.add_page_break()
para("附录 A  数据来源说明", 15, True, "center", "黑体", space_after=12, indent=False)
app = [
    "一、宏观背景数据（官方公开）",
    "1.《2024 年度大连市人力资源和社会保障事业发展统计公报》，大连市人社局、统计局，2025-07-25，https://rsj.dl.gov.cn/art/2025/7/25/art_4374_2453139.html",
    "2.《2025 年大连市政府工作报告》，2025-02-05，https://www.ln.gov.cn/web/zwgkx/zfgzbg/shizfgzbg/dls/2025020510204834948/index.shtml",
    "3. 人民日报客户端：大连理工大学 2025 届毕业生秋季双选会报道，2024-10-28，https://news.dlut.edu.cn/info/1071/106774.htm",
    "4. 东北财经大学 2025 届本科毕业生升学就业情况，阳光高考平台，https://gaokao.chsi.com.cn/sch/schoolInfo--schId-145,categoryId-47372,mindex-10.dhtml",
    "",
    "二、微观岗位文本数据（公开搜索结果页采集）",
    "来源：前程无忧 51job（we.51job.com）公开搜索结果页；采集方式：Playwright 无头浏览器渲染 + DOM 可见文本提取（非接口破解、未登录、无个人数据）；检索词：应届生/校招/管培生/毕业生/实习生及大连组合共 25 组；去重键：标题+公司+薪资。",
    "重要口径说明：该平台对未登录访问按出口 IP 定向推送城市，URL 地域参数与页面交互均无法约束城市，故微观样本为平台推送给求职者的全国应届生岗位流（以招聘活跃城市为主），本文将其定位为“面向应届生的在线招聘市场基准样本”，以大连权威统计为观照背景，城市代表性局限已在论文 4.3 节声明。",
    "",
    "三、处理步骤（对应五步流水线，全部代码见 code/ 目录）",
    "Step1 采集 crawl_51job.js（713 条原始记录，data_raw/list_jobs.json）→ Step2 清洗分词 step2_clean.py（薪资归一/去重/停用词，data_clean/jobs_clean.csv）→ Step3 测度构造 step3_measure.py（六测度，data_measure/job_measures.csv）→ Step4 信效度 step4_reliability.py（Kappa/α/效标，reliability.csv）→ Step5 分析 step5_regression.py（OLS/分组/Logistic/K-means，model_summary.txt）→ Step6 图表 step6_figures.py（figures/*.png）。",
    "复现环境：Python 3.11；依赖 jieba 0.42.1、pandas 3.0.0、scikit-learn 1.8.0、statsmodels 0.14.6、matplotlib、openpyxl；Node.js 22 + Playwright（采集步骤可选，原始数据已随库提供，跳过采集亦可复现 Step2 之后全部结果）。",
]
for a in app:
    if a.startswith(("一、", "二、", "三、")):
        para(a, 12.5, True, "left", "黑体", space_after=6, indent=False)
    else:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(5)
        r = p.add_run(a)
        set_font(r, size=10.5)

doc.save(OUT)
print("Word 已生成:", OUT)
print("大小:", os.path.getsize(OUT), "字节")
