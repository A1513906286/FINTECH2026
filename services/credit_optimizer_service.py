"""
信贷额度优化服务 - 跨境信用卡版（月度模型）
基于预期价值(EV)最大化原则优化授信额度

月度业务模式：
- 收入来源：
  * MDR收入 = 月度GMV × 0.5%
  * 利息收入 = 分期额度(额度×50%) × 月化利率(8%/12)
- 成本来源：
  * 违约损失 = Next Exposure × 月化PD(PD/12) × LGD(50%)
  * 资金成本 = 月度GMV × 月化资金成本(2.28%/12)
- 风险敞口：Next Exposure = max(0, 月度GMV - 本金 - 还款额)
  * 还款额 = 月度GMV × 还款率

还款率(repayment_rate)超参数说明：
- 基于学术研究和行业数据设定默认值为50%
- 参考文献：
  1. Journal of Financial Economics (2018): "Minimum payments and debt paydown in consumer credit cards"
     - 研究发现29%的账户定期支付接近最低还款额(2-3%)
     - 约40-50%的用户为全额还款者(Transactors)
  2. CFPB Consumer Credit Card Market Report:
     - 信用卡用户分为Transactors(全额还款)和Revolvers(循环余额)
     - 平均还款率介于30%-70%之间
  3. 纽约联储消费者信贷数据:
     - 循环信用用户通常每月偿还部分余额
- 50%作为中位数假设，适用于混合用户群体
- 可根据具体用户群体特征调整：
  * 高信用用户群体：可设置为60%-80%
  * 普通用户群体：50%（默认值）
  * 高风险用户群体：可设置为30%-40%
"""
import pandas as pd
import numpy as np


class CreditOptimizerService:
    """信贷额度优化器 - 跨境信用卡版"""

    def __init__(self, pd_model, utilization_model,
                 lgd_ratio=0.8,
                 apr=0.08,
                 mdr=0.005,
                 revolving_ratio=0.3,
                 funding_cost=0.0228,
                 repayment_rate=0.5):
        """
        初始化优化器（月度模型）

        Args:
            pd_model: 违约概率模型服务
            utilization_model: 周转率模型服务（复用利用率模型）
            lgd_ratio: 违约损失率（默认80%，假设可追回20%）
            apr: 年化利率（默认8%）
            mdr: 商户手续费率（默认0.5%）
            revolving_ratio: 分期比例（默认30%）
            funding_cost: 年化资金成本（默认2.28%）
            repayment_rate: 还款率（默认50%）
                - 基于学术研究设定，表示用户每月偿还GMV的比例
                - 参考: Journal of Financial Economics (2018), CFPB报告
                - 取值范围: 0.0-1.0
                - 典型值: 0.3(保守) / 0.5(中性) / 0.7(乐观)
        """
        self.pd_model = pd_model
        self.utilization_model = utilization_model
        self.lgd_ratio = lgd_ratio
        self.apr = apr
        self.mdr = mdr
        self.revolving_ratio = revolving_ratio
        self.funding_cost = funding_cost
        self.repayment_rate = repayment_rate

        # 候选额度倍数（从1x到10x余额）
        self.candidate_multipliers = [1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]

        # 额度范围限制
        self.min_credit_limit = 5000
        self.max_credit_limit = 500000
    
    def calculate_expected_value(self, credit_limit, pd_prob, velocity, initial_balance=0):
        """
        计算预期价值 (Expected Value) - 跨境信用卡版（月度模型）

        月度跨境信用卡业务模型：
        1. 月交易额 (GMV) = 授信额度 × 使用率
        2. 收入模型（月度）：
           - MDR收入 = 月度GMV × 0.5%
           - 利息收入 = 分期额度(额度×50%) × 月化利率(8%/12)
           - 总收入 = MDR收入 + 利息收入
        3. 成本模型（月度）：
           - 还款额 = 月度GMV × 还款率(repayment_rate)
             * 还款率默认50%，基于学术研究设定
             * 参考: Journal of Financial Economics (2018), CFPB报告
           - 下期风险敞口 (Next Exposure) = max(0, 月度GMV - 本金 - 还款额)
             * 本金 = 用户初始余额（还款能力）
             * 逻辑：用户可用余额+还款额还款，超出部分才是真实风险敞口
           - 违约损失 = Next Exposure × 月化PD(PD/12) × LGD(80%)
           - 资金成本 = 月度GMV × 月化资金成本(2.28%/12)
           - 总成本 = 违约损失 + 资金成本
        4. 预期价值 = 总收入 - 总成本

        Args:
            credit_limit: 授信额度
            pd_prob: 违约概率（年度，会自动月化）
            velocity: 使用率（月交易额/授信额度）
            initial_balance: 用户初始余额（本金，默认0）

        Returns:
            tuple: (expected_value, total_revenue, total_cost, gmv, mdr_revenue, interest_revenue, expected_loss, funding_cost_amount)
        """
        # 1. 计算月交易额 (GMV) = 额度 × 使用率
        monthly_gmv = credit_limit * velocity

        # 2. 收入计算（月度）
        # 2.1 MDR收入 = 月度GMV × MDR
        mdr_revenue = monthly_gmv * self.mdr

        # 2.2 利息收入 = 分期额度(额度×30%) × 月化利率(8%/12)
        revolving_balance = credit_limit * self.revolving_ratio
        interest_revenue = revolving_balance * (self.apr / 12)   # 月化利率

        # 2.3 总收入（月度）
        total_revenue = mdr_revenue + interest_revenue

        # 3. 成本计算（月度）
        # 3.1 计算还款额 = 月度GMV × 还款率
        # 还款率(repayment_rate)基于学术研究设定，默认50%
        # 参考: Journal of Financial Economics (2018) - 29%用户只付最低还款
        #       CFPB报告 - 约40-50%用户为全额还款者
        repayment_amount = monthly_gmv * self.repayment_rate

        # 3.2 下期风险敞口 (Next Exposure) = max(0, 月度GMV - 本金 - 还款额)
        # 逻辑：用户可用余额(initial_balance) + 还款额(repayment_amount)来偿还
        # 超出部分才是真实风险敞口
        next_exposure = max(0, monthly_gmv - initial_balance - repayment_amount)

        # 3.3 违约损失（月度）= Next Exposure × 月化PD × LGD
        monthly_pd = pd_prob / 12  # 年度PD月化
        expected_loss = next_exposure * monthly_pd * self.lgd_ratio

        # 3.4 资金成本（月度）= 月度GMV × 月化资金成本
        monthly_funding_cost = self.funding_cost / 12
        funding_cost_amount = monthly_gmv * monthly_funding_cost

        # 3.5 总成本（月度）
        total_cost = expected_loss + funding_cost_amount

        # 4. 预期价值（月度）
        expected_value = total_revenue - total_cost

        return (expected_value, total_revenue, total_cost, monthly_gmv,
                mdr_revenue, interest_revenue, expected_loss, funding_cost_amount)

    def evaluate_single_limit(self, credit_limit, features, initial_balance=0):
        """
        评估单个候选额度（改进版）

        Args:
            credit_limit: 候选额度
            features: 特征字典
            initial_balance: 用户初始余额（本金，默认0）

        Returns:
            dict: 评估结果
        """
        # 更新特征中的额度
        features_copy = features.copy()
        features_copy['credit_amount'] = credit_limit

        # 计算杠杆率
        total_income = features_copy.get('total_income', 50000)
        leverage_ratio = credit_limit / (total_income + 1)
        features_copy['credit_to_income_ratio'] = leverage_ratio

        # 预测PD和周转率
        pd_prob = self.pd_model.predict(features_copy)
        velocity = self.utilization_model.predict(features_copy)

        # 计算EV（传入initial_balance）
        ev, total_revenue, total_cost, gmv, mdr_revenue, interest_revenue, expected_loss, funding_cost = \
            self.calculate_expected_value(credit_limit, pd_prob, velocity, initial_balance)

        return {
            'credit_limit': credit_limit,
            'pd': pd_prob,
            'velocity': velocity,
            'gmv': gmv,
            'ev': ev,
            'total_revenue': total_revenue,
            'total_cost': total_cost,
            'mdr_revenue': mdr_revenue,
            'interest_revenue': interest_revenue,
            'expected_loss': expected_loss,
            'funding_cost': funding_cost,
        }

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

            # 预测PD和周转率
            pd_prob = self.pd_model.predict_proba(user_features_with_limit)
            if isinstance(pd_prob, np.ndarray):
                pd_prob = pd_prob[0]

            velocity = self.utilization_model.predict(user_features_with_limit)
            if isinstance(velocity, np.ndarray):
                velocity = velocity[0]

            # 计算EV（跨境信用卡版 - 改进模型）
            # 传入base_amount作为initial_balance（用户余额）
            (ev, total_revenue, total_cost, gmv,
             mdr_revenue, interest_revenue, expected_loss, funding_cost_amount) = \
                self.calculate_expected_value(limit, pd_prob, velocity, initial_balance=base_amount)

            results.append({
                'limit': limit,
                'pd': pd_prob,
                'velocity': velocity,
                'gmv': gmv,
                'mdr_revenue': mdr_revenue,
                'interest_revenue': interest_revenue,
                'total_revenue': total_revenue,
                'expected_loss': expected_loss,
                'funding_cost': funding_cost_amount,
                'total_cost': total_cost,
                'expected_value': ev
            })
        
        # 转换为DataFrame
        results_df = pd.DataFrame(results)

        # 🔧 打印详细的候选额度评估表格（跨境信用卡版）
        print("\n所有候选额度的评估结果（跨境信用卡版）:")
        print("-" * 140)
        print(f"{'倍数':<6} {'额度':>12} {'PD':>8} {'周转率':>8} {'GMV':>12} {'MDR收入':>10} {'利息收入':>10} {'总收入':>10} {'违约损失':>10} {'资金成本':>10} {'总成本':>10} {'EV':>12}")
        print("-" * 140)

        for idx, row in results_df.iterrows():
            multiplier = row['limit'] / base_amount
            print(f"{multiplier:>5.1f}x  "
                  f"¥{row['limit']:>10,.0f}  "
                  f"{row['pd']:>7.2%}  "
                  f"{row['velocity']:>7.2%}  "
                  f"¥{row['gmv']:>10,.0f}  "
                  f"¥{row['mdr_revenue']:>8,.0f}  "
                  f"¥{row['interest_revenue']:>8,.0f}  "
                  f"¥{row['total_revenue']:>8,.0f}  "
                  f"¥{row['expected_loss']:>8,.0f}  "
                  f"¥{row['funding_cost']:>8,.0f}  "
                  f"¥{row['total_cost']:>8,.0f}  "
                  f"¥{row['expected_value']:>10,.0f}")

        print("-" * 140)

        # 找到最优额度
        max_ev_idx = results_df['expected_value'].idxmax()
        optimal_limit = results_df.loc[max_ev_idx, 'limit']
        max_ev = results_df.loc[max_ev_idx, 'expected_value']
        optimal_pd = results_df.loc[max_ev_idx, 'pd']
        optimal_velocity = results_df.loc[max_ev_idx, 'velocity']
        optimal_gmv = results_df.loc[max_ev_idx, 'gmv']
        optimal_total_revenue = results_df.loc[max_ev_idx, 'total_revenue']
        optimal_total_cost = results_df.loc[max_ev_idx, 'total_cost']

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
            'velocity': float(optimal_velocity),
            'gmv': float(optimal_gmv),
            'total_revenue': float(optimal_total_revenue),
            'total_cost': float(optimal_total_cost),
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

