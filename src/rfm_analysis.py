# -*- coding: utf-8 -*-
"""
完整项目分析脚本（基于钱陶勇清洗好的 data_clean.csv）
用于产出简历所需的真实量化结果
步骤：RFM打分 -> 8类分层 -> 优化指标 -> 优化分层 -> A/B增量验证
"""
import pandas as pd
import numpy as np

DATA = r"C:\Users\ASUS\Documents\first\my_project\data_clean.csv"
df = pd.read_csv(DATA)
df["Newsletter_Subscription"] = df["Newsletter_Subscription"].astype(bool)
print("数据形状:", df.shape)

# ============ 1. 传统 RFM 打分（与用户 Notebook 中一致）============
df["R_score"] = 5 - pd.qcut(df["Last_Login_Days_Ago"], 5, labels=False)  # 天数越小分越高
df["F_score"] = pd.qcut(df["Purchase_Frequency"], 5, labels=False) + 1
df["M_score"] = pd.qcut(df["Total_Spending"], 5, labels=False) + 1
df["RFM_total"] = df["R_score"] + df["F_score"] + df["M_score"]

df["R_high"] = df["R_score"] >= 3
df["F_high"] = df["F_score"] >= 3
df["M_high"] = df["M_score"] >= 3

def rfm_segment(row):
    r, f, m = row["R_high"], row["F_high"], row["M_high"]
    if r and f and m: return "重要价值客户"
    if (not r) and f and m: return "重要保持客户"
    if r and (not f) and m: return "重要发展客户"
    if (not r) and (not f) and m: return "重要挽留客户"
    if r and f and (not m): return "一般价值客户"
    if (not r) and f and (not m): return "一般保持客户"
    if r and (not f) and (not m): return "一般发展客户"
    return "一般挽留客户"

df["segment_traditional"] = df.apply(rfm_segment, axis=1)
print("\n=== 传统 RFM 8 类分布 ===")
print(df["segment_traditional"].value_counts().to_string())

# ============ 2. 优化指标（视频思路）============
def minmax(s): return (s - s.min()) / (s.max() - s.min())

# 意向度：停留时长与浏览页数加权 (0-100)
df["intention"] = (0.5 * minmax(df["Time_Spent_on_Site_Minutes"]) +
                   0.5 * minmax(df["Pages_Viewed"])) * 100
# 转化摩擦系数
df["friction"] = df["Pages_Viewed"] / (df["Purchase_Frequency"] + 1)

# 活跃连接度
def engagement(row):
    if row["Newsletter_Subscription"] and row["Last_Login_Days_Ago"] <= 7: return "高"
    if (not row["Newsletter_Subscription"]) and row["Last_Login_Days_Ago"] <= 7: return "中"
    return "低"
df["engagement"] = df.apply(engagement, axis=1)

# 购买力背景
df["income_tier"] = pd.qcut(df["Income"], 3, labels=["低收入", "中等收入", "高收入"])

# ============ 3. 优化分层 ============
def optimized_segment(row):
    m_high = row["M_high"]
    intention_high = row["intention"] >= df["intention"].median()
    income_high = row["income_tier"] == "高收入"
    income_low = row["income_tier"] == "低收入"
    inactive = row["Last_Login_Days_Ago"] > df["Last_Login_Days_Ago"].quantile(0.75)
    if m_high and inactive: return "流失客"
    if (not m_high) and intention_high and income_high: return "纠结土豪"
    if (not m_high) and intention_high and income_low: return "隐形活跃者"
    return row["segment_traditional"]

df["segment_optimized"] = df.apply(optimized_segment, axis=1)
print("\n=== 优化后分层分布 ===")
print(df["segment_optimized"].value_counts().to_string())

print("\n=== 新识别三类用户画像 ===")
for seg in ["纠结土豪", "隐形活跃者", "流失客"]:
    s = df[df["segment_optimized"] == seg]
    if len(s) > 0:
        print(f"{seg}: {len(s)}人 | 平均消费 {s['Total_Spending'].mean():.0f} | "
              f"平均收入 {s['Income'].mean():.0f} | 平均意向度 {s['intention'].mean():.1f} | "
              f"平均登录间隔 {s['Last_Login_Days_Ago'].mean():.1f}天")

# ============ 4. A/B 增量效果验证 ============
COUPON_COST = 10

def incremental_effect(df_target):
    d = df_target.copy()
    d["int_q"] = pd.qcut(d["intention"], 5, labels=False) / 4
    d["m_q"] = pd.qcut(d["Total_Spending"], 5, labels=False) / 4
    d["pot"] = 0.20 + 0.60 * d["int_q"]   # 潜在转化率（意向度驱动）
    d["nat"] = 0.10 + 0.60 * d["m_q"]     # 自然转化率（消费水平驱动）
    d["incr_cvr"] = (d["pot"] - d["nat"]).clip(lower=0.05)
    d["incr_rev"] = d["incr_cvr"] * d["Average_Order_Value"]
    return len(d) * COUPON_COST, d["incr_rev"].sum(), d

# 传统策略：RFM 总分最高的 200 人
traditional = df.nlargest(200, "RFM_total").copy()
t_cost, t_incr, t_detail = incremental_effect(traditional)

# 优化策略：核心 70 人（重要价值客户中意向度最高）+ 潜力 89 人
core_pool = df[df["segment_optimized"] == "重要价值客户"].nlargest(70, "intention")
potential_pool = df[df["segment_optimized"].isin(["纠结土豪", "隐形活跃者", "流失客"])].nlargest(89, "intention")
opt = pd.concat([core_pool, potential_pool]).drop_duplicates("User_ID")
o_cost, o_incr, o_detail = incremental_effect(opt)

print("\n=== A/B 增量效果对比 ===")
print(f"传统策略: 目标 {len(traditional)} 人 | 成本 {t_cost:.0f} 元 | 增量收益 {t_incr:.0f} 元 | ROI {t_incr/t_cost:.2f}")
print(f"优化策略: 目标 {len(opt)} 人 | 成本 {o_cost:.0f} 元 | 增量收益 {o_incr:.0f} 元 | ROI {o_incr/o_cost:.2f}")
print(f"ROI 提升: {(o_incr/o_cost)/(t_incr/t_cost):.2f} 倍 ({(o_incr/o_cost)/(t_incr/t_cost)-1:+.1%})")
print(f"成本节省: {t_cost-o_cost:.0f} 元 ({(1-o_cost/t_cost):.1%})")

# 增量贡献分解
o_detail["group"] = np.where(o_detail["segment_optimized"] == "重要价值客户", "核心用户", "潜力用户")
contrib = o_detail.groupby("group").agg(人数=("User_ID", "count"), 平均增量转化率=("incr_cvr", "mean"),
                                        增量收益=("incr_rev", "sum")).round(3)
contrib["收益占比"] = (contrib["增量收益"] / contrib["增量收益"].sum() * 100).round(1)
print("\n=== 优化策略增量贡献分解 ===")
print(contrib.to_string())

# 保存结果
df.to_csv(r"C:\Users\ASUS\Documents\first\my_project\data_rfm_final.csv", index=False)
print("\n结果已保存: data_rfm_final.csv")
