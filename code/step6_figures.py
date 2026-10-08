# -*- coding: utf-8 -*-
"""
Step 6 · 描述性统计与可视化（论文图表素材）
输出: figures/*.png + data_measure/descriptive.csv
"""
import os, warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
warnings.filterwarnings("ignore")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M = os.path.join(ROOT, "data_measure")
FIG = os.path.join(ROOT, "figures")
os.makedirs(FIG, exist_ok=True)

# 中文字体（沙箱内 matplotlib 的 ttc addfont 只注册第一个 face：Noto Sans CJK JP，
# 其字形覆盖全部简体汉字，显示无差异）
for fp in ["/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
           "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"]:
    if os.path.exists(fp):
        font_manager.fontManager.addfont(fp)
plt.rcParams["font.sans-serif"] = ["Noto Sans CJK JP", "WenQuanYi Zen Hei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

df = pd.read_csv(os.path.join(M, "job_measures.csv"))
df = df[df["log_salary"].notna()]

# ---------- 描述性统计表 ----------
cols = ["salary_mid", "DTS", "GCS", "PBS", "PES", "SKILL_TOTAL", "EDU", "GRF", "welfare_n"]
desc = df[cols].describe().T
desc["中位数"] = df[cols].median()
desc["变异系数"] = (desc["std"] / desc["mean"]).round(3)
desc.round(2).to_csv(os.path.join(M, "descriptive.csv"), encoding="utf-8-sig")
print("描述性统计:\n", desc.round(2).to_string())

# ---------- 图1 薪资分布 ----------
fig, ax = plt.subplots(1, 2, figsize=(11, 4))
ax[0].hist(df["salary_mid"].clip(0, 30000), bins=40, color="#2563eb", edgecolor="white")
ax[0].set_title("月薪分布直方图（截断至 3 万）"); ax[0].set_xlabel("月薪（元）"); ax[0].set_ylabel("岗位数")
ax[1].hist(df["log_salary"], bins=40, color="#7c3aed", edgecolor="white")
ax[1].set_title("对数月薪分布"); ax[1].set_xlabel("log(月薪)")
plt.tight_layout(); plt.savefig(os.path.join(FIG, "fig1_salary_dist.png"), dpi=150); plt.close()

# ---------- 图2 行业分布与薪资 ----------
g = df.groupby("industry").agg(岗位数=("job_id", "count"), 平均月薪=("salary_mid", "mean")).sort_values("岗位数", ascending=False)
fig, ax = plt.subplots(1, 2, figsize=(12, 5))
ax[0].barh(g.index[::-1], g["岗位数"][::-1], color="#0891b2")
ax[0].set_title("各行业岗位数量"); ax[0].set_xlabel("岗位数")
ax[1].barh(g.index[::-1], g["平均月薪"][::-1], color="#dc2626")
ax[1].set_title("各行业平均月薪"); ax[1].set_xlabel("月薪（元）")
plt.tight_layout(); plt.savefig(os.path.join(FIG, "fig2_industry.png"), dpi=150); plt.close()

# ---------- 图3 技能测度分布 ----------
dims = ["DTS", "GCS", "PBS", "PES"]
fig, ax = plt.subplots(figsize=(9, 4.5))
x = np.arange(len(dims)); w = 0.5
means = [df[d].mean() for d in dims]
ax.bar(x, means, w, color=["#2563eb", "#0891b2", "#f59e0b", "#16a34a"])
for i, v in enumerate(means):
    ax.text(i, v + 0.03, f"{v:.2f}", ha="center", fontsize=10)
ax.set_xticks(x); ax.set_xticklabels(["数字技术技能\nDTS", "通用职业技能\nGCS", "专业业务技能\nPBS", "实践经历信号\nPES"])
ax.set_ylabel("平均命中技能词数"); ax.set_title("四类技能测度均值分布（N=%d）" % len(df))
plt.tight_layout(); plt.savefig(os.path.join(FIG, "fig3_skill_dims.png"), dpi=150); plt.close()

# ---------- 图4 应届友好度 vs 薪资（核心发现）----------
fig, ax = plt.subplots(figsize=(8, 4.6))
grf_mean = df.groupby("GRF")["salary_mid"].agg(["mean", "count"])
bars = ax.bar(grf_mean.index.astype(str), grf_mean["mean"], color="#dc2626", width=0.55)
for i, (idx, row) in enumerate(grf_mean.iterrows()):
    ax.text(i, row["mean"] + 200, f"{row['mean']:.0f}\n(n={int(row['count'])})", ha="center", fontsize=9)
ax.set_xlabel("应届友好度得分 GRF"); ax.set_ylabel("平均月薪（元）")
ax.set_title("应届友好度与平均薪资的关系（负向）")
plt.tight_layout(); plt.savefig(os.path.join(FIG, "fig4_grf_salary.png"), dpi=150); plt.close()

# ---------- 图5 热力图：技能-薪资相关 ----------
corr = df[["salary_mid", "DTS", "GCS", "PBS", "PES", "EDU", "GRF", "welfare_n"]].corr()
fig, ax = plt.subplots(figsize=(7.5, 6))
im = ax.imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1)
ax.set_xticks(range(len(corr))); ax.set_xticklabels(corr.columns, rotation=45, ha="right")
ax.set_yticks(range(len(corr))); ax.set_yticklabels(corr.columns)
for i in range(len(corr)):
    for j in range(len(corr)):
        ax.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center", fontsize=8)
ax.set_title("变量相关系数矩阵")
plt.colorbar(im); plt.tight_layout(); plt.savefig(os.path.join(FIG, "fig5_corr_heatmap.png"), dpi=150); plt.close()

# ---------- 图6 聚类画像雷达 ----------
prof = pd.read_csv(os.path.join(M, "cluster_profiles.csv"), index_col=0)
labels = ["DTS", "GCS", "PBS", "PES"]
fig, ax = plt.subplots(figsize=(7, 6), subplot_kw=dict(polar=True))
angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
angles += angles[:1]
maxv = prof[labels].values.max() or 1
for idx, row in prof.iterrows():
    vals = [row[l] / maxv for l in labels]; vals += vals[:1]
    ax.plot(angles, vals, label=f"类{idx} (n={int(row['样本数'])})")
    ax.fill(angles, vals, alpha=0.06)
ax.set_xticks(angles[:-1]); ax.set_xticklabels(labels)
ax.set_title("岗位技能画像聚类（K-means，最优 K=5）")
ax.legend(loc="upper right", bbox_to_anchor=(1.28, 1.1), fontsize=8)
plt.tight_layout(); plt.savefig(os.path.join(FIG, "fig6_cluster_radar.png"), dpi=150); plt.close()

print("\n图表已生成:", len(os.listdir(FIG)), "张 →", FIG)
for f in sorted(os.listdir(FIG)):
    print("  ", f)
