# credit_limit_service.py
"""
信用额度预测服务 - 增强版
集成Home Credit的PD模型、利用率模型和EV优化器
"""
import joblib
import numpy as np
import os
from services.feature_engineering_service import FeatureEngineeringService
from services.pd_model_service import PDModelService
from services.utilization_model_service import UtilizationModelService
from services.credit_optimizer_service import CreditOptimizerService


class CreditLimitService:
    """
    信用额度预测服务 - 增强版

    使用Home Credit的完整模型系统：
    1. 特征工程：将PDF数据转换为13个核心指标
    2. PD模型：预测违约概率
    3. 利用率模型：预测额度利用率
    4. 优化器：基于EV最大化原则计算最优额度
    """

    def __init__(self,
                 pd_model_path='models/hc_pd_model.pkl',
                 util_model_path='models/hc_utilization_model.pkl'):
        """
        初始化服务

        Args:
            pd_model_path: PD模型文件路径
            util_model_path: 利用率模型文件路径
        """
        print("\n" + "="*80)
        print("初始化信用额度预测服务（增强版）")
        print("="*80)

        # 初始化各个组件
        self.feature_service = FeatureEngineeringService()
        self.pd_model = PDModelService(pd_model_path)
        self.util_model = UtilizationModelService(util_model_path)
        self.optimizer = CreditOptimizerService(self.pd_model, self.util_model)

        print("="*80)
        print("✅ 信用额度预测服务初始化完成")
        print("="*80 + "\n")
    

    def predict_credit_limit(self, total_income, balance, pdf_data=None):
        """
        预测用户信用额度（增强版）

        使用完整的Home Credit模型系统进行预测

        Args:
            total_income: 总收入
            balance: 账户余额
            pdf_data: PDF提取的详细数据（可选，如果提供则使用增强特征）

        Returns:
            dict: {
                'success': bool,
                'credit_limit': float,
                'risk_level': str,
                'pd_prob': float,
                'expected_value': float,
                'message': str
            }
        """
        try:
            print(f"\n{'='*60}")
            print(f"开始预测信用额度")
            print(f"{'='*60}")
            print(f"输入数据: 收入=¥{total_income:,.2f}, 余额=¥{balance:,.2f}")

            # 如果有PDF详细数据，使用增强特征
            if pdf_data is not None and isinstance(pdf_data, dict):
                print("✓ 使用PDF详细数据进行特征工程")
                features = self.feature_service.extract_features_from_pdf_data(
                    pdf_data,
                    credit_amount=balance * 2.0  # 初始候选额度
                )
            else:
                print("⚠️ 未提供PDF详细数据，使用基础特征")
                # 构建基础特征
                features = self._build_basic_features(total_income, balance)

            # 转换为DataFrame格式
            features_df = self.feature_service.prepare_features_for_model(features)

            print(f"✓ 特征工程完成，共{len(features_df.columns)}个特征")

            # 使用优化器计算最优额度
            print("\n开始优化额度...")
            optimization_result = self.optimizer.optimize_limit(
                features_df,
                base_amount=balance
            )

            optimal_limit = optimization_result['optimal_limit']
            max_ev = optimization_result['max_ev']
            pd_prob = optimization_result['pd_prob']
            risk_level = optimization_result['risk_level']
            base_amount = optimization_result.get('base_amount', balance)

            # 🔧 输出和test_pdf_features.py一致的最终结果格式
            print(f"\n{'='*70}")
            print(f"  最终预测结果")
            print(f"{'='*70}")

            print(f"\n📊 基础数据:")
            print(f"  总收入: ¥{total_income:,.2f}")
            if pdf_data:
                print(f"  总支出: ¥{pdf_data.get('total_expense', 0):,.2f}")
            print(f"  当前余额: ¥{balance:,.2f}")

            print(f"\n🎯 模型预测:")
            print(f"  违约概率 (PD): {pd_prob:.2%}")
            print(f"  额度利用率: {optimization_result['utilization']:.2%}")
            print(f"  风险等级: {risk_level}")

            print(f"\n💰 额度优化:")
            print(f"  最优额度: ¥{optimal_limit:,.2f}")
            print(f"  预期价值 (EV): ¥{max_ev:,.2f}")

            if optimal_limit == 0:
                print(f"\n⚠️  拒绝授信原因:")
                print(f"  - 违约概率过高 ({pd_prob:.2%})")
                print(f"  - 所有候选额度的预期价值均为负")
            else:
                print(f"\n✅ 建议授信额度: ¥{optimal_limit:,.2f}")
                print(f"  额度/余额比: {optimal_limit / base_amount:.1f}x")

            print(f"{'='*70}\n")

            return {
                'success': True,
                'credit_limit': float(round(optimal_limit, 2)),
                'risk_level': risk_level,
                'pd_prob': float(pd_prob),
                'expected_value': float(max_ev),
                'balance': float(balance),
                'total_income': float(total_income),
                'utilization': float(optimization_result['utilization']),
                'message': f'预测成功 - {risk_level}，授信额度¥{optimal_limit:,.2f}，预期价值¥{max_ev:,.2f}'
            }

        except Exception as e:
            print(f"❌ 额度预测错误: {str(e)}")
            import traceback
            traceback.print_exc()

            # 返回错误信息
            return {
                'success': False,
                'credit_limit': 0,
                'risk_level': '预测失败',
                'pd_prob': 0,
                'expected_value': 0,
                'balance': float(balance),
                'total_income': float(total_income),
                'utilization': 0,
                'message': f'预测失败: {str(e)}'
            }

    def _build_basic_features(self, total_income, balance):
        """
        构建基础特征（当没有PDF详细数据时）

        Args:
            total_income: 总收入
            balance: 账户余额

        Returns:
            dict: 特征字典
        """
        # 估算月收入
        monthly_income = total_income / 6.0

        # 估算月消费（假设为收入的70%）
        monthly_consumption = monthly_income * 0.7

        # 构建基础特征
        features = {
            # 收入能力
            'avg_income_3m': monthly_income,
            'income_variance_3m': monthly_income * 0.1,
            'total_income': total_income,

            # 支出能力
            'avg_large_spending': monthly_consumption * 0.2,
            'avg_monthly_consumption': monthly_consumption,
            'income_consumption_ratio': 1.0 / 0.7,  # 收入/消费比

            # 偿还能力
            'current_balance': balance,
            'balance_income_ratio': balance / (monthly_income + 1),
            'min_balance_12m': balance * 0.3,
            'payday_plus_5_drop': 0.0,
            'large_withdrawal_ratio': 0.25,

            # 额度相关（初始值）
            'credit_amount': balance * 2.0,
            'credit_to_income_ratio': (balance * 2.0) / (total_income + 1),
        }

        return features

    def get_default_credit_limit(self):
        """
        获取默认额度（当没有用户数据时）

        Returns:
            dict: 默认预测结果
        """
        return {
            'success': False,
            'credit_limit': 0,
            'risk_level': '无数据',
            'pd_prob': 0,
            'expected_value': 0,
            'balance': 0,
            'total_income': 0,
            'utilization': 0,
            'message': '无用户数据，无法预测额度'
        }

    def predict_with_pdf_data(self, pdf_data):
        """
        使用PDF数据进行预测（便捷方法）

        Args:
            pdf_data: PDF服务返回的数据字典

        Returns:
            dict: 预测结果
        """
        total_income = pdf_data.get('total_income', 50000.0)
        balance = pdf_data.get('current_balance') or pdf_data.get('balance', 5000.0)

        return self.predict_credit_limit(total_income, balance, pdf_data=pdf_data)

