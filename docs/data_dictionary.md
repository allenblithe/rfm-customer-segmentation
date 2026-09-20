# 📖 数据字典（随时查阅）

**文件**：`user_personalized_features.csv`
**规模**：1000 行 × 14 列（+1 个无名的序号列，读取时叫 `Unnamed: 0`，可删掉）

| 字段名 | 中文含义 | 类型 | 说明 | 属于哪类数据 |
|---|---|---|---|---|
| User_ID | 用户ID | 字符串 | #1 ~ #1000 | 标识 |
| Age | 年龄 | 数值 | 18–64 | 用户画像 |
| Gender | 性别 | 分类 | Male / Female | 用户画像 |
| Location | 地区 | 分类 | Suburban / Urban / Rural | 用户画像 |
| Income | 收入 | 数值 | 20,155 – 149,951 | 用户画像 |
| Interests | 兴趣 | 分类 | Sports / Fashion / Travel / Food / Technology | 用户画像 |
| Last_Login_Days_Ago | 距最近登录天数 | 数值 | 1–29 天 | 行为数据 |
| Purchase_Frequency | 购买频率 | 数值 | 0–9 次 | 消费数据 |
| Average_Order_Value | 平均客单价 | 数值 | 10–199 | 消费数据 |
| Total_Spending | 总消费金额 | 数值 | 112–4,999 | 消费数据 |
| Product_Category_Preference | 偏好品类 | 分类 | Apparel / Electronics / Books / Home & Kitchen / Health & Beauty | 用户画像 |
| Time_Spent_on_Site_Minutes | 网站停留时长 | 数值 | 2–599 分钟 | 行为数据 |
| Pages_Viewed | 浏览页数 | 数值 | 1–49 | 行为数据 |
| Newsletter_Subscription | 是否订阅邮件 | 布尔 | True / False | 行为数据 |

## 🧠 与 RFM 的对应关系（第 5 步会用）

| RFM 维度 | 用哪个字段 | 为什么 |
|---|---|---|
| R (Recency 最近性) | `Last_Login_Days_Ago` | 数据里没有"最近购买日期"，用"最近登录天数"近似——天数越小越活跃 |
| F (Frequency 频率) | `Purchase_Frequency` | 购买次数，越高越忠诚 |
| M (Monetary 金额) | `Total_Spending` | 总消费金额，越高贡献越大 |

> ⚠️ 注意：`Average_Order_Value`（客单价）是单均金额，`Total_Spending`（总消费）才是 M 的正确选择。

## 💡 视频核心思路备忘（整个项目的灵魂）

1. **业务问题**：优惠券发给谁最有效？（用户分层 → 精准营销）
2. **传统 RFM 的两个缺陷**：
   - 看不见"高潜观望者"（逛得多买得少的人被误判为低价值）
   - 一刀切看待消费金额（有钱人花 1000 和穷人花 1000 意义不同）
3. **优化思路**：在 RFM 基础上加 4 个修正因子：
   - 意向度 = 0.5×停留时长分 + 0.5×浏览页数分（想不想买）
   - 转化摩擦系数 = 浏览页数 ÷ (购买次数+1)（纠结程度）
   - 活跃连接度（订阅 + 7天内登录 → 高/中/低）
   - 购买力背景（收入分层，作修正标签）
4. **验证**：A/B 对比——传统策略（RFM 最高 200 人）vs 优化策略（核心 70 + 潜力 89 人），比 ROI
