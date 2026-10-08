# -*- coding: utf-8 -*-
"""
Step 2 · 文本清洗与分词
输入: data_raw/list_jobs.json
输出: data_clean/jobs_clean.csv（结构化）+ data_clean/tokens.json（分词结果）
"""
import json, re, os, sys
import pandas as pd
import jieba

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dictionaries import DOMAIN_WORDS, STOPWORDS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data_raw", "list_jobs.json")
OUT_DIR = os.path.join(ROOT, "data_clean")
os.makedirs(OUT_DIR, exist_ok=True)

# 加载领域词典
for w in DOMAIN_WORDS:
    jieba.add_word(w, freq=10000)

# ---------- 1. 薪资解析（单位归一为「元/月」）----------
def parse_salary(s):
    """把 51job 薪资格式解析为月薪中位数（元）。
    支持: 4-6千 / 6.5-8千·13薪 / 1.2-1.5万 / 200元/天 / 5千-1万 / 8千-1.2万 / 3-5万·14薪
    返回 (下限, 上限, 中位数, 是否日薪)
    """
    if not s or not isinstance(s, str):
        return (None, None, None, False)
    t = s.replace("·13薪", "").replace("·14薪", "").replace("·15薪", "").strip()
    # 日薪
    m = re.match(r"^(\d+(?:\.\d+)?)\s*元\s*/\s*天", t)
    if m:
        d = float(m.group(1))
        return (d, d, d * 21.75, True)   # 按 21.75 工作日折算月薪
    # 提取数字与单位
    items = re.findall(r"(\d+(?:\.\d+)?)\s*(万|千|元|K|k|W|w)?", t)
    vals = []
    for num, unit in items:
        if num == "":
            continue
        v = float(num)
        unit = unit or "千"
        if unit in ("万", "W", "w"):
            v *= 10000
        elif unit in ("千", "K", "k"):
            v *= 1000
        vals.append(v)
    vals = [v for v in vals if v > 0]
    if not vals:
        return (None, None, None, False)
    if len(vals) == 1:
        return (vals[0], vals[0], vals[0], False)
    lo, hi = min(vals[0], vals[1]), max(vals[0], vals[1])
    return (lo, hi, (lo + hi) / 2, False)

# ---------- 2. 学历/经验解析 ----------
DEGREE_ORDER = ["博士", "硕士", "研究生", "本科", "大专", "专科", "中专", "高中"]
def parse_degree(text):
    for d in DEGREE_ORDER:
        if d in text:
            return {"博士": "博士", "硕士": "硕士", "研究生": "硕士", "本科": "本科",
                    "大专": "大专", "专科": "大专", "中专": "中专", "高中": "高中"}[d]
    return "不限"

def parse_exp(text):
    if re.search(r"无经验|无需经验|经验不限|不限经验|应届", text):
        return "无经验友好"
    m = re.search(r"(\d+)\s*年", text)
    if m:
        n = int(m.group(1))
        return "1年以下" if n <= 1 else ("1-3年" if n <= 3 else "3年以上")
    return "未标明"

# ---------- 3. 企业性质 / 行业 ----------
def parse_comp_type(tags):
    for t in tags:
        if t in ("国企", "央企", "民营", "外资", "合资", "上市公司", "创业公司", "事业单位", "股份制"):
            return t
    return "未标明"

# ---------- 4. 分词 + 清洗 ----------
def clean_text(s):
    if not s:
        return ""
    s = re.sub(r"[\u200b\ufeff\xa0]", " ", str(s))
    s = re.sub(r"[^\u4e00-\u9fa5A-Za-z0-9+#\.\s]", " ", s)  # 保留字母数字和 + # .
    s = re.sub(r"\s+", " ", s)
    return s.strip()

def tokenize(text):
    words = jieba.lcut(clean_text(text))
    out = []
    for w in words:
        w = w.strip()
        if not w or len(w) < 2 and not re.match(r"^[A-Za-z0-9+#\.]{1,}$", w):
            continue
        if w in STOPWORDS:
            continue
        if re.match(r"^[\d\.]+$", w):
            continue
        out.append(w)
    return out

def main():
    data = json.load(open(RAW, encoding="utf-8"))
    rows = data["dalian"] + data["other"]
    recs = []
    for i, r in enumerate(rows):
        welfare = r.get("welfareTags") or []
        comp = r.get("compInfo") or []
        text = " ".join([r.get("title", ""), " ".join(welfare), " ".join(comp), r.get("rawText", "")])
        lo, hi, mid, is_daily = parse_salary(r.get("salary", ""))
        recs.append({
            "job_id": i + 1,
            "title": r.get("title", "").strip(),
            "salary_raw": r.get("salary", ""),
            "salary_low": lo,
            "salary_high": hi,
            "salary_mid": mid,
            "is_daily_wage": is_daily,
            "city": (r.get("area") or "未知").split("·")[0].strip() or "未知",
            "district": (r.get("area") or "").split("·")[-1].strip() if "·" in (r.get("area") or "") else "",
            "company": r.get("company", "").strip(),
            "industry": comp[0] if len(comp) > 0 else "未标明",
            "comp_type": parse_comp_type(comp),
            "comp_size": comp[2] if len(comp) > 2 else "未标明",
            "degree": parse_degree(text),
            "exp_level": parse_exp(text),
            "welfare": "|".join(welfare),
            "welfare_n": len(welfare),
            "skill_text": clean_text(text),
            "job_url": r.get("jobUrl", ""),
        })
    df = pd.DataFrame(recs)
    # 分词
    df["tokens"] = df["skill_text"].apply(tokenize)
    df["token_str"] = df["tokens"].apply(lambda x: " ".join(x))

    df.drop(columns=["tokens"]).to_csv(os.path.join(OUT_DIR, "jobs_clean.csv"), index=False, encoding="utf-8-sig")
    json.dump({"count": len(df), "tokens": df["tokens"].tolist()}, open(os.path.join(OUT_DIR, "tokens.json"), "w", encoding="utf-8"), ensure_ascii=False)

    print("清洗完成：", len(df), "条")
    print("薪资可解析:", df["salary_mid"].notna().sum(), "/", len(df))
    print("学历分布:\n", df["degree"].value_counts().to_string())
    print("经验分布:\n", df["exp_level"].value_counts().to_string())
    print("\n输出:", OUT_DIR)

if __name__ == "__main__":
    main()
