#!/usr/bin/env bash
# 大连应届生就业 NLP 测度研究 —— 五步流水线一键复现
# 用法: bash run_pipeline.sh
# 说明: Step1 采集为可选项（原始数据已随库提供）；Step2 之后可完全离线复现
set -e
cd "$(dirname "$0")"

echo "════════ Step 0 · 环境依赖 ════════"
python3 - <<'EOF'
import importlib.util, sys
need = ["pandas", "numpy", "jieba", "sklearn", "statsmodels", "matplotlib", "openpyxl"]
missing = [m for m in need if importlib.util.find_spec(m) is None]
if missing:
    print("缺少依赖:", ", ".join(missing))
    print("请执行: pip install -r requirements.txt")
    sys.exit(1)
print("依赖完整 ✓")
EOF

echo
echo "════════ Step 1 · 数据采集（可选，已提供原始数据） ════════"
if [ ! -f data_raw/list_jobs.json ]; then
    echo "本地无原始数据，尝试采集（需要 Node.js + Playwright + 可访问 51job 的网络）…"
    if command -v node >/dev/null 2>&1 && node -e "require('playwright')" 2>/dev/null; then
        node scripts/crawl_51job.js
    else
        echo "⚠ 跳过采集（无 Node/Playwright）。请自备 data_raw/list_jobs.json 后重跑。"
        exit 1
    fi
else
    echo "已存在 data_raw/list_jobs.json（$(python3 -c "import json;print(json.load(open('data_raw/list_jobs.json'))['count']['all'])") 条），跳过采集。"
fi

echo
echo "════════ Step 2 · 清洗与分词 ════════"
python3 code/step2_clean.py 2>/dev/null | grep -v "Loading\|Prefix\|Dump\|Building"

echo
echo "════════ Step 3 · NLP 测度构造 ════════"
python3 code/step3_measure.py 2>/dev/null | grep -v pkg_resources

echo
echo "════════ Step 4 · 信度与效度检验 ════════"
python3 code/step4_reliability.py 2>/dev/null | grep -v pkg_resources

echo
echo "════════ Step 5 · 回归 / 分类 / 聚类 ════════"
python3 code/step5_regression.py 2>/dev/null | grep -v pkg_resources

echo
echo "════════ Step 6 · 描述统计与图表 ════════"
python3 code/step6_figures.py 2>/dev/null | grep -v "pkg_resources\|findfont" | tail -9

echo
echo "════════ Step 7 · 生成 Word 论文 ════════"
python3 code/step7_word.py 2>/dev/null | grep -v pkg_resources

echo
echo "════════ Step 8 · 汇总 Excel 结果簿 ════════"
python3 code/step8_excel.py 2>/dev/null | grep -v pkg_resources

echo
echo "✅ 全部流水线执行完毕。"
echo "   论文: paper/预演毕业论文-大连应届生就业NLP测度研究.docx"
echo "   结果: data_measure/  图表: figures/  Excel: results/"
