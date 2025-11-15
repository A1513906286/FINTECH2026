import random
from config.lottery_rules import PRIZE_RULE_MAPPING, RULE_MULTIPLIER, MAX_MULTIPLIER
# 需要 database.list_all_rewards(), database.aggregate_transactions(), database.get_credit_info()
# 假设注入 db 对象

def evaluate_user_rules(user_profile):
    """
    根据用户聚合数据判断规则是否命中，返回 dict { rule_name: bool }
    user_profile 应包含:
      - total_consume, tx_count, avg_tx
      - total_limit, available_limit
      - is_new_user_no_purchase (True/False)
      - is_new_user (True/False)
    """
    total_consume = user_profile.get('total_consume', 0.0) or 0.0
    total_limit = user_profile.get('total_limit', 0.0) or 0.0
    available_limit = user_profile.get('available_limit', 0.0) or 0.0
    avg_tx = user_profile.get('avg_tx', 0.0) or 0.0

    ratio = (total_consume / total_limit) if total_limit > 0 else 0.0

    rules_hit = {
        "ratio_10_20": 0.10 <= ratio < 0.20,
        "available_ge_10000": available_limit >= 10000,
        "total_consume_ge_3000": total_consume >= 3000,
        "avg_tx_ge_500": avg_tx >= 500,
        "is_new_user_no_purchase": bool(user_profile.get('is_new_user_no_purchase', False)),
        "ratio_ge_60_and_total_ge_2000": (ratio >= 0.60 and total_consume >= 2000),

        "is_new_user": bool(user_profile.get('is_new_user', False)),
        "avg_tx_lt_200": avg_tx < 200,
        "ratio_lt_10": ratio < 0.10,
        "ratio_between_40_60": 0.40 < ratio < 0.60
    }
    return rules_hit


def compute_weights(db, user_id):
    """
    计算所有奖品（来自 reward 表）的最终权重（基于 base_prob 与命中规则的乘子）
    返回列表: [ { reward_row..., 'weight': float } ... ]
    """
    # 1) 读取奖励表
    rewards = db.list_all_rewards()  # list of dict, 含 base_prob, type, new_user_only 等

    # 2) 读取用户聚合数据
    tx_agg = db.aggregate_transactions(user_id)
    credit = db.get_credit_info(user_id)

    # 新用户判断：
    # - 将 is_new_user_no_purchase 定义为交易笔数 == 0（严格未消费过）
    is_new_user_no_purchase = (tx_agg['tx_count'] == 0)
    is_new_user = is_new_user_no_purchase

    user_profile = {
        'total_consume': tx_agg['total_consume'],
        'tx_count': tx_agg['tx_count'],
        'avg_tx': tx_agg['avg_tx'],
        'total_limit': credit['total_limit'],
        'available_limit': credit['available_limit'],
        'is_new_user_no_purchase': is_new_user_no_purchase,
        'is_new_user': is_new_user
    }

    rules_hit = evaluate_user_rules(user_profile)

    # 3) 对每个 reward 计算最终 weight
    weighted_rewards = []
    for r in rewards:
        base = float(r.get('base_prob') or 0.0)
        if base <= 0:
            # 跳过基础概率为 0 的奖品
            weighted = 0.0
        else:
            total_multiplier = 1.0
            # 若该 reward 标注 new_user_only 且用户不满足 is_new_user，则权重为 0（直接无资格）
            if r.get('new_user_only', 0) == 1 and not user_profile['is_new_user']:
                total_multiplier = 0.0
            else:
                # 对该 reward.type 检查对应规则
                rules_for_type = PRIZE_RULE_MAPPING.get(r.get('type'), [])
                for rule_name in rules_for_type:
                    if rules_hit.get(rule_name):
                        total_multiplier *= RULE_MULTIPLIER  # 统一乘子 1.3

                # 最大倍数上限保护
                if total_multiplier > MAX_MULTIPLIER:
                    total_multiplier = MAX_MULTIPLIER

            weighted = base * total_multiplier

        r_copy = r.copy()
        r_copy['weight'] = weighted
        weighted_rewards.append(r_copy)

    return weighted_rewards


def normalize_prob_list(weighted_rewards):
    """
    从 weighted_rewards 列表计算概率 map，并返回 { reward_id: prob }
    """
    total = sum([r['weight'] for r in weighted_rewards])
    if total <= 0:
        # fallback: 均匀分配（剔除权重为0的项）
        non_zero = [r for r in weighted_rewards if r['weight'] > 0]
        if not non_zero:
            return {}
        n = len(non_zero)
        return {r['id']: 1.0/n for r in non_zero}

    return {r['id']: (r['weight']/total) for r in weighted_rewards}


def weighted_choice(prob_map):
    """
    prob_map: { reward_id: probability }
    返回选中的 reward_id
    """
    r = random.random()
    acc = 0.0
    for k, p in prob_map.items():
        acc += p
        if r <= acc:
            return k
    return list(prob_map.keys())[-1]


def draw_four_with_reduction(db, user_id):
    """
    抽四张卡（放回抽样，但每次某奖品被抽中后其后续权重降低 40%）
    返回 list of reward_row dict（可能重复）
    """
    # 1) 初始权重
    weighted = compute_weights(db, user_id)
    # 用 id->entry 映射加方便修改权重
    id_to_reward = {r['id']: r for r in weighted}

    results = []
    for draw_i in range(4):
        probs = normalize_prob_list(list(id_to_reward.values()))
        if not probs:
            break
        chosen_id = weighted_choice(probs)
        chosen_reward = id_to_reward.get(chosen_id)
        results.append(chosen_reward.copy() if chosen_reward else None)

        # 对被选中的奖品进行权重衰减（乘以 0.6，即降低40%）
        if chosen_id in id_to_reward and id_to_reward[chosen_id]['weight'] > 0:
            id_to_reward[chosen_id]['weight'] *= 0.6  # 每被抽出一次，其后续权重乘以0.6
            # 如果权重过小可选去除：这里保留，但若希望完全移除可 pop
            # if id_to_reward[chosen_id]['weight'] < 1e-6:
            #     id_to_reward.pop(chosen_id, None)

    return results
