# -*- coding: utf-8 -*-
"""
Step 5 · 回归分析与分类分析（论文评分要点）
- 主回归：log(薪资) ~ 技能测度 + 学历 + 应届友好度 + 行业 + 企业性质
- 分组回归：按行业 / 企业规模
- 分类分析：高薪岗位(前25%)的 logistic 回归
- 聚类分析：K-means 识别岗位技能画像
输出: data_measure/regression_*.csv, cluster_*.csv, model_summary.txt
"""
import os, sys, warnings
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, roc_auc_score
from sklearn.model_selection import cross_val_predict
from sklearn.linear_model import LogisticRegression
warnings.filterwarnings("ignore")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M = os.path.join(ROOT, "data_measure")
df = pd.read_csv(os.path.join(M, "job_measures.csv"))
df = df[df["log_salary"].notna()].copy()

PRED = ["DTS", "GCS", "PBS", "PES", "EDU", "GRF"]

# 行业哑变量（以「装备制造」为基准）
df["ind"] = pd.Categorical(df["industry"], categories=["装备制造", "商贸服务", "信息技术", "石油化工", "建筑地产", "教育科研", "金融", "医疗健康", "其他"])
ind_dum = pd.get_dummies(df["ind"], prefix="ind", drop_first=True)

# 企业性质：仅保留样本量足够的国企/民营/外资三类（以「其他/未标明」为基准），避免稀疏哑变量导致高 VIF
ct_keep = ["国企", "民营", "外资", "合资"]
df["ct_simple"] = df["comp_type"].where(df["comp_type"].isin(ct_keep), "其他")
size_dum = pd.get_dummies(df["ct_simple"], prefix="ct", drop_first=True)

out_lines = []
def P(s=""):
    print(s); out_lines.append(str(s))

P("=" * 70)
P("Step 5 · 回归分析与分类分析")
P("=" * 70)
P(f"建模样本: {len(df)} 条（剔除薪资缺失）")

# ---------- 1. 主回归（OLS，log 薪资）----------
X = pd.concat([df[PRED], ind_dum, size_dum], axis=1).astype(float)
X = sm.add_constant(X)
y = df["log_salary"].astype(float)
m1 = sm.OLS(y, X).fit(cov_type="HC3")   # 稳健标准误

P("\n【主回归 OLS - 因变量: log(月薪) | 稳健标准误 HC3】")
P(f"R² = {m1.rsquared:.4f}   Adj.R² = {m1.rsquared_adj:.4f}   F = {m1.fvalue:.3f}   N = {int(m1.nobs)}   Prob(F) = {m1.f_pvalue:.4g}")
tbl = pd.DataFrame({
    "变量": m1.params.index,
    "系数": m1.params.values.round(4),
    "稳健标准误": m1.bse.values.round(4),
    "t值": m1.tvalues.values.round(3),
    "p值": m1.pvalues.values.round(4),
    "显著性": ["***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else "" for p in m1.pvalues],
})
P(tbl.to_string(index=False))
tbl.to_csv(os.path.join(M, "regression_main.csv"), index=False, encoding="utf-8-sig")

# ---------- 2. 多重共线性 ----------
vifs = []
for i, c in enumerate(X.columns):
    if c == "const":
        continue
    try:
        v = variance_inflation_factor(X.values, i)
        vifs.append((c, round(v, 3)))
    except Exception:
        pass
vif_df = pd.DataFrame(vifs, columns=["变量", "VIF"])
P("\n【多重共线性检验 VIF】（<10 视为无严重共线性）")
P(vif_df.to_string(index=False))
vif_df.to_csv(os.path.join(M, "regression_vif.csv"), index=False, encoding="utf-8-sig")

# ---------- 3. 仅核心测度的简约模型 ----------
X2 = sm.add_constant(df[PRED].astype(float))
m2 = sm.OLS(y, X2).fit(cov_type="HC3")
P(f"\n【简约模型（仅 6 个核心测度）】R² = {m2.rsquared:.4f}  Adj.R² = {m2.rsquared_adj:.4f}")
t2 = pd.DataFrame({"变量": m2.params.index, "系数": m2.params.values.round(4),
                   "t值": m2.tvalues.values.round(3), "p值": m2.pvalues.values.round(4)})
P(t2.to_string(index=False))
t2.to_csv(os.path.join(M, "regression_parsimonious.csv"), index=False, encoding="utf-8-sig")

# ---------- 4. 分组回归（按行业）----------
P("\n【分组回归：按行业（仅含核心测度）】")
group_rows = []
for ind, sub in df.groupby("industry"):
    if len(sub) < 25:
        continue
    Xg = sm.add_constant(sub[PRED].astype(float))
    yg = sub["log_salary"].astype(float)
    try:
        mg = sm.OLS(yg, Xg).fit(cov_type="HC3")
        group_rows.append({
            "行业": ind, "N": len(sub), "R²": round(mg.rsquared, 4),
            "PBS系数": round(mg.params.get("PBS", np.nan), 4),
            "PBS_p值": round(mg.pvalues.get("PBS", np.nan), 4),
            "DTS系数": round(mg.params.get("DTS", np.nan), 4),
            "DTS_p值": round(mg.pvalues.get("DTS", np.nan), 4),
            "GRF系数": round(mg.params.get("GRF", np.nan), 4),
            "GRF_p值": round(mg.pvalues.get("GRF", np.nan), 4),
        })
    except Exception as e:
        pass
grp = pd.DataFrame(group_rows)
P(grp.to_string(index=False))
grp.to_csv(os.path.join(M, "regression_by_industry.csv"), index=False, encoding="utf-8-sig")

# ---------- 5. 分类：高薪岗位识别（Logistic）----------
thr = df["salary_mid"].quantile(0.75)
df["high_pay"] = (df["salary_mid"] >= thr).astype(int)
Xc = StandardScaler().fit_transform(df[PRED].astype(float))
yc = df["high_pay"].values
lr = LogisticRegression(max_iter=2000, class_weight="balanced")
prob = cross_val_predict(lr, Xc, yc, cv=5, method="predict_proba")[:, 1]
auc = roc_auc_score(yc, prob)
lr.fit(Xc, yc)
coef = pd.DataFrame({"变量": PRED, "标准化系数": lr.coef_[0].round(4)}).sort_values("标准化系数", ascending=False)
P(f"\n【分类模型：识别高薪岗位（薪资≥P75 = {thr:.0f} 元，5折交叉验证）】")
P(f"样本正例比例 = {yc.mean():.3f}   AUC = {auc:.4f}")
P(coef.to_string(index=False))
coef.to_csv(os.path.join(M, "classification_highpay.csv"), index=False, encoding="utf-8-sig")

# ---------- 6. 技能画像聚类（K-means）----------
Xk = StandardScaler().fit_transform(df[PRED].astype(float))
best_k, best_s, sil = None, -1, {}
for k in range(2, 7):
    km = KMeans(n_clusters=k, n_init=10, random_state=42)
    lab = km.fit_predict(Xk)
    s = silhouette_score(Xk, lab)
    sil[k] = round(s, 4)
    if s > best_s:
        best_s, best_k = s, k
km = KMeans(n_clusters=best_k, n_init=10, random_state=42)
df["cluster"] = km.fit_predict(Xk)
prof = df.groupby("cluster")[PRED + ["salary_mid", "welfare_n"]].mean().round(2)
prof["样本数"] = df.groupby("cluster").size()
prof["主要行业"] = df.groupby("cluster")["industry"].agg(lambda s: s.value_counts().index[0])
P(f"\n【岗位技能画像聚类 K-means】最优 K = {best_k}（轮廓系数 {best_s}）")
P(f"各 K 轮廓系数: {sil}")
P(prof.to_string())
prof.to_csv(os.path.join(M, "cluster_profiles.csv"), encoding="utf-8-sig")
df[["job_id", "title", "industry", "cluster"]].to_csv(os.path.join(M, "cluster_assign.csv"), index=False, encoding="utf-8-sig")

with open(os.path.join(M, "model_summary.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(out_lines))
P("\n输出: " + M)
