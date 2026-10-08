# -*- coding: utf-8 -*-
"""
Step 3 · NLP 测度构建
构造 5 类可计算测度（对应论文"测度构建"核心）：
  M1 数字技术技能强度 (DTS)
  M2 通用职业技能强度 (GCS)
  M3 专业业务技能强度 (PBS)
  M4 学历门槛 (EDU)
  M5 应届友好度 (GRF)
输出: data_measure/job_measures.csv
"""
import json, os, re, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dictionaries import SKILL_DICT, INDUSTRY_MAP

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEAN = os.path.join(ROOT, "data_clean", "jobs_clean.csv")
TOKENS = os.path.join(ROOT, "data_clean", "tokens.json")
OUT = os.path.join(ROOT, "data_measure")
os.makedirs(OUT, exist_ok=True)

# ---------- M1/M2/M3：技能强度（词典命中密度）----------
DIM_ORDER = ["数字技术技能", "通用职业技能", "专业业务技能", "实践经历信号"]
DIM_CODE = {"数字技术技能": "DTS", "通用职业技能": "GCS", "专业业务技能": "PBS", "实践经历信号": "PES"}

def count_skills(text, tokens):
    """返回各维度命中的技能词集合。同时用子串匹配（应对分词切碎）与 token 精确匹配。"""
    low = text.lower()
    tok_set = set(t.lower() for t in tokens)
    res = {}
    for dim, words in SKILL_DICT.items():
        hit = set()
        for w in words:
            wl = w.lower()
            if wl in tok_set or wl in low:
                hit.add(w)
        res[dim] = hit
    return res

# ---------- M4：学历门槛（有序编码）----------
EDU_SCORE = {"高中": 1, "中专": 2, "大专": 3, "本科": 4, "硕士": 5, "博士": 6, "不限": 0}
def edu_from_title(title):
    # 标题优先（如「27应届博士」「本科应届生」）
    for k, v in [("博士", "博士"), ("硕士", "硕士"), ("研究生", "硕士"),
                 ("本科", "本科"), ("大专", "大专"), ("专科", "大专"), ("中专", "中专")]:
        if k in title:
            return v
    return None

# ---------- M5：应届友好度 ----------
def grad_friendly(title, text):
    """0-4 分：title 含应届相关词 +1，含"无经验/零经验/培养" +1，含"实习" +1，含"管培/储备" +1"""
    s = 0
    if re.search(r"应届|毕业生|校招|2025届|2026届|2027届", title):
        s += 1
    if re.search(r"无经验|零经验|无需经验|经验不限|培养|可培养", text) or re.search(r"无经验|零经验|培养", title):
        s += 1
    if re.search(r"实习|见习", title):
        s += 1
    if re.search(r"管培|储备干部|储备人才|培训生", title):
        s += 1
    return s

# ---------- 行业归类 ----------
def map_industry(industry_text, title):
    blob = (industry_text or "") + " " + (title or "")
    for ind, kws in INDUSTRY_MAP.items():
        for kw in kws:
            if kw in blob:
                return ind
    return "其他"

def main():
    df = pd.read_csv(CLEAN)
    tokens_all = json.load(open(TOKENS, encoding="utf-8"))["tokens"]

    recs = []
    for i, row in df.iterrows():
        text = str(row.get("skill_text", "")) + " " + str(row.get("title", ""))
        toks = tokens_all[i] if i < len(tokens_all) else []
        sk = count_skills(text, toks)

        dts = len(sk["数字技术技能"])
        gcs = len(sk["通用职业技能"])
        pbs = len(sk["专业业务技能"])
        pes = len(sk["实践经历信号"])
        skill_total = dts + gcs + pbs + pes

        et = edu_from_title(str(row.get("title", "")))
        edu = EDU_SCORE[et] if et else EDU_SCORE["不限"]
        grf = grad_friendly(str(row.get("title", "")), text)

        recs.append({
            "job_id": row["job_id"],
            "title": row["title"],
            "city": row["city"],
            "company": row["company"],
            "industry": map_industry(row.get("industry", ""), row.get("title", "")),
            "industry_raw": row.get("industry", ""),
            "comp_type": row.get("comp_type", "未标明"),
            "comp_size": row.get("comp_size", "未标明"),

            "salary_raw": row["salary_raw"],
            "salary_mid": row["salary_mid"],
            "salary_low": row["salary_low"],
            "salary_high": row["salary_high"],
            "is_daily_wage": row["is_daily_wage"],
            "log_salary": np.log(row["salary_mid"]) if pd.notna(row["salary_mid"]) and row["salary_mid"] > 0 else np.nan,

            # ---- 5 个 NLP 测度 ----
            "DTS": dts, "GCS": gcs, "PBS": pbs, "PES": pes,
            "SKILL_TOTAL": skill_total,
            "SKILL_DIM_N": sum(1 for v in [dts, gcs, pbs, pes] if v > 0),   # 技能维度覆盖数
            "EDU": edu, "GRF": grf,

            "welfare_n": row.get("welfare_n", 0),
            "skill_hits": "|".join(sorted(set().union(*sk.values()))),
        })

    out = pd.DataFrame(recs)
    out.to_csv(os.path.join(OUT, "job_measures.csv"), index=False, encoding="utf-8-sig")

    print("测度构建完成：", len(out), "条")
    print("\n--- 5 个测度描述统计 ---")
    cols = ["DTS", "GCS", "PBS", "PES", "SKILL_TOTAL", "EDU", "GRF", "salary_mid"]
    print(out[cols].describe().round(2).to_string())
    print("\n行业分布:\n", out["industry"].value_counts().to_string())
    print("\n输出:", os.path.join(OUT, "job_measures.csv"))

if __name__ == "__main__":
    main()
