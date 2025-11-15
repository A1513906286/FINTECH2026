"""
奖品概率与规则配置（可由产品在测试阶段直接调整）
- 所有额外因子的统一乘子为 1.3（你要求）
- new_user_only 表示该奖品只能被满足 is_new_user 条件的用户抽到
- max_multiplier 用来限制单个奖品的最大倍增，避免无限叠加
"""

# 基础最大倍数，防止过度放大
MAX_MULTIPLIER = 5.0

# 每条触发性规则的统一乘子（产品要求全部为 1.3）
RULE_MULTIPLIER = 1.3

# 把规则以名称映射到对哪些判定产生影响（示例）
# key: 规则名, value: 描述（仅作注释）
RULES_LIST = {
    "ratio_10_20": "total_consume_ratio 在 [10%,20%)",
    "available_ge_10000": "available_limit >= 10000",
    "total_consume_ge_3000": "total_consume >= 3000",
    "avg_tx_ge_500": "avg_tx >= 500",
    "is_new_user_no_purchase": "用户为未消费过的新用户",
    "ratio_ge_60_and_total_ge_2000": "ratio >= 60% 且 total_consume >= 2000",
    "avg_tx_lt_200": "avg_tx < 200",
    "ratio_lt_10": "ratio < 10%",
    "ratio_between_40_60": "40% < ratio < 60%"
}

# 定义每个奖品（reward.type 或 reward.id）对应要检查的规则列表（触发时乘以 RULE_MULTIPLIER）
# 这里使用示例 mapping（可以按 reward.title 或 reward.id 改写）
PRIZE_RULE_MAPPING = {
    # 汇率类：当满足任何一条汇率相关规则时会提升
    "rate": [
        "ratio_10_20",
        "available_ge_10000",
        "total_consume_ge_3000",
        "avg_tx_ge_500",
        "is_new_user_no_purchase",
        "ratio_ge_60_and_total_ge_2000"
    ],
    # 消费券类：不同子券可以共享这些规则（产品可以更细分）
    "coupon": [
        "is_new_user_no_purchase",  # 新用户专享类会在 reward.new_user_only 标注
        "avg_tx_lt_200",
        "ratio_lt_10",
        "ratio_between_40_60"
    ],
    # 合作商户：无条件提升（empty list）
    "merchant": [],
    # 星星卡：无条件提升（empty list）
    "star": []
}

# 额外策略：当某个 reward.new_user_only == 1 时，需要用户满足 is_new_user 才能参与该奖品
