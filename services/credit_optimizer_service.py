"""
信贷额度优化服务 - 适配自Fintech/hc_credit_optimizer.py
基于预期价值(EV)最大化原则优化授信额度
"""
import pandas as pd
import numpy as np


class CreditOptimizerService:
    """信贷额度优化器"""
    
    def __init__(self, pd_model, utilization_model,
                 lgd_ratio=0.8, apr=0.36, ead_ratio=0.6):
        """
        初始化优化器

        Args:
            pd_model: 违约概率模型服务
            utilization_model: 利用率模型服务
            lgd_ratio: 违约损失率（默认80%）
            apr: 年化利率（默认36%，小额信贷通常为36%-100%）
            ead_ratio: 违约风险敞口比率（默认60%）
        """
        self.pd_model = pd_model
        self.utilization_model = utilization_model
        self.lgd_ratio = lgd_ratio
        self.apr = apr
        self.ead_ratio = ead_ratio



        # 候选额度倍数（从1x到10x余额）
        self.candidate_multipliers = [1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]

        # 额度范围限制
        self.min_credit_limit = 5000
        self.max_credit_limit = 500000
    
    def calculate_expected_value(self, credit_limit, pd_prob, utilization):
        """
        计算预期价值 (Expected Value) - 本金回收模型

        完整的信贷经济学模型：
        1. 风险敞口 (EAD) = 授信额度 × 利用率（用户实际使用的金额）
        2. 利息收入 = 风险敞口 × 年化利率
        3. 本金回收：
           - 不违约（概率 1-PD）：收回全部本金 = 风险敞口
           - 违约（概率 PD）：收回部分本金 = 风险敞口 × (1 - LGD)
        4. 预期本金回收 = 风险敞口 × (1-PD) + 风险敞口 × PD × (1-LGD)
                        = 风险敞口 × (1 - PD × LGD)
        5. 预期损失 = 风险敞口 - 预期本金回收 = 风险敞口 × PD × LGD
        6. 预期收益 = 利息收入 + 预期本金回收 - 风险敞口
                   = 利息收入 - 预期损失

        关键点：
        - 考虑了本金回收，不仅仅是利息
        - 违约时可以收回部分本金（1-LGD）
        - 额度越大不一定收益越大，因为违约风险也增加

        Args:
            credit_limit: 授信额度
            pd_prob: 违约概率
            utilization: 利用率（实际使用额度的比例）

        Returns:
            tuple: (expected_value, expected_revenue, expected_loss)
        """
        # 1. 风险敞口 = 实际使用的额度
        exposure = credit_limit * utilization

        # 2. 利息收入 = 风险敞口 × 年化利率
        interest_income = exposure * self.apr

        # 3. 预期损失 = 风险敞口 × 违约概率 × 损失率
        expected_loss = exposure * pd_prob * self.lgd_ratio

        # 4. 预期收益 = 利息收入 - 预期损失
        expected_revenue = interest_income - expected_loss

        # 5. 预期价值 = 预期收益
        expected_value = expected_revenue

        return expected_value, expected_revenue, expected_loss
    
    def optimize_limit(self, user_features, base_amount=None):
        """
        为单个用户优化信贷额度
        
        Args:
            user_features: 用户特征（DataFrame或dict）
            base_amount: 基准金额（如果为None，则使用当前余额）
        
        Returns:
            dict: {
                'optimal_limit': 最优额度,
                'max_ev': 最大预期价值,
                'pd_prob': 违约概率,
                'utilization': 利用率,
                'risk_level': 风险等级,
                'analysis': 详细分析结果DataFrame
            }
        """
        # 确保是DataFrame格式
        if isinstance(user_features, dict):
            user_features = pd.DataFrame([user_features])
        
        # 如果没有提供基准金额，使用当前余额作为基准
        if base_amount is None:
            if 'current_balance' in user_features.columns:
                base_amount = float(user_features['current_balance'].iloc[0])
                print(f"✓ 从特征中获取余额: ¥{base_amount:,.2f}")
                # 如果余额为0或过小，设置最小基准金额
                if base_amount < self.min_credit_limit:
                    print(f"⚠️ 余额过小，调整为最小额度: ¥{self.min_credit_limit:,.2f}")
                    base_amount = self.min_credit_limit
            else:
                # 如果没有余额特征，使用默认值
                print(f"⚠️ 未找到current_balance特征，使用默认值: ¥50,000")
                base_amount = 50000
        else:
            print(f"✓ 使用传入的基准金额: ¥{base_amount:,.2f}")

        print(f"\n基准额度（余额）: ¥{base_amount:,.2f}")
        print(f"候选额度倍数: {self.candidate_multipliers}")

        # 生成候选额度（从余额的1x到10x，不受min_credit_limit限制）
        candidate_limits = [
            base_amount * multiplier
            for multiplier in self.candidate_multipliers
        ]
        # 只限制最大额度，不限制最小额度
        candidate_limits = [
            min(limit, self.max_credit_limit)
            for limit in candidate_limits
        ]

        print(f"候选额度范围: ¥{candidate_limits[0]:,.2f} - ¥{candidate_limits[-1]:,.2f}")
        print(f"共{len(candidate_limits)}个候选额度\n")
        
        # 评估每个候选额度
        results = []
        
        for idx, limit in enumerate(candidate_limits):
            # 创建包含额度的特征副本
            user_features_with_limit = user_features.copy()
            user_features_with_limit['credit_amount'] = limit

            # 计算额度/收入比（杠杆率）
            if 'total_income' in user_features_with_limit.columns:
                total_income = user_features_with_limit['total_income'].iloc[0]
                user_features_with_limit['credit_to_income_ratio'] = limit / (total_income + 1)

            # 预测PD和利用率
            pd_prob = self.pd_model.predict_proba(user_features_with_limit)
            if isinstance(pd_prob, np.ndarray):
                pd_prob = pd_prob[0]

            utilization = self.utilization_model.predict(user_features_with_limit)
            if isinstance(utilization, np.ndarray):
                utilization = utilization[0]

            # 计算EV
            ev, revenue, loss = self.calculate_expected_value(limit, pd_prob, utilization)
            
            results.append({
                'limit': limit,
                'pd': pd_prob,
                'utilization': utilization,
                'expected_revenue': revenue,
                'expected_loss': loss,
                'expected_value': ev
            })
        
        # 转换为DataFrame
        results_df = pd.DataFrame(results)

        # 🔧 打印详细的候选额度评估表格（和test_pdf_features.py一致）
        print("\n所有候选额度的评估结果:")
        print("-" * 100)
        print(f"{'倍数':<6} {'额度':>15} {'违约概率':>12} {'利用率':>10} {'预期损失':>15} {'预期收益':>15} {'预期价值':>15}")
        print("-" * 100)

        for idx, row in results_df.iterrows():
            multiplier = row['limit'] / base_amount
            print(f"{multiplier:>5.1f}x  ¥{row['limit']:>13,.2f}  {row['pd']:>11.2%}  {row['utilization']:>9.2%}  "
                  f"¥{row['expected_loss']:>13,.2f}  ¥{row['expected_revenue']:>13,.2f}  ¥{row['expected_value']:>13,.2f}")

        print("-" * 100)

        # 找到最优额度
        max_ev_idx = results_df['expected_value'].idxmax()
        optimal_limit = results_df.loc[max_ev_idx, 'limit']
        max_ev = results_df.loc[max_ev_idx, 'expected_value']
        optimal_pd = results_df.loc[max_ev_idx, 'pd']
        optimal_util = results_df.loc[max_ev_idx, 'utilization']

        # 熔断机制：如果所有EV都为负，拒绝授信
        if max_ev < 0:
            optimal_limit = 0
            max_ev = 0
            risk_level = "拒绝授信"
        else:
            # 根据违约概率判断风险等级
            if optimal_pd < 0.10:
                risk_level = "低风险"
            elif optimal_pd < 0.20:
                risk_level = "中等风险"
            elif optimal_pd < 0.30:
                risk_level = "较高风险"
            else:
                risk_level = "高风险"

        return {
            'optimal_limit': float(optimal_limit),
            'max_ev': float(max_ev),
            'pd_prob': float(optimal_pd),
            'utilization': float(optimal_util),
            'risk_level': risk_level,
            'analysis': results_df,
            'base_amount': float(base_amount)  # 添加基准额度，用于计算倍数
        }

    def get_risk_assessment(self, pd_prob, credit_limit, total_income):
        """
        获取风险评估

        Args:
            pd_prob: 违约概率
            credit_limit: 授信额度
            total_income: 总收入

        Returns:
            dict: 风险评估结果
        """
        # 计算杠杆率
        leverage_ratio = credit_limit / (total_income + 1)

        # 风险等级
        if pd_prob < 0.10:
            risk_level = "低风险"
            risk_score = 1
        elif pd_prob < 0.20:
            risk_level = "中等风险"
            risk_score = 2
        elif pd_prob < 0.30:
            risk_level = "较高风险"
            risk_score = 3
        else:
            risk_level = "高风险"
            risk_score = 4

        # 杠杆率评估
        if leverage_ratio < 0.5:
            leverage_assessment = "杠杆率低，风险可控"
        elif leverage_ratio < 1.0:
            leverage_assessment = "杠杆率适中"
        elif leverage_ratio < 2.0:
            leverage_assessment = "杠杆率较高，需关注"
        else:
            leverage_assessment = "杠杆率过高，风险较大"

        return {
            'risk_level': risk_level,
            'risk_score': risk_score,
            'pd_prob': float(pd_prob),
            'leverage_ratio': float(leverage_ratio),
            'leverage_assessment': leverage_assessment
        }

