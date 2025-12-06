"""
特征工程服务 - 将PDF提取的数据转换为模型所需的13个核心指标
"""
import numpy as np
import pandas as pd


class FeatureEngineeringService:
    """
    特征工程服务
    
    将PDF提取的银行流水数据转换为Home Credit模型所需的13个核心指标：
    
    【收入能力】3个指标
    1. avg_income_3m - 过去3个月平均入账
    2. income_variance_3m - 3个月入账方差
    3. total_income - 总收入
    
    【支出能力】3个指标
    4. avg_large_spending - 大额单笔平均支出
    5. avg_monthly_consumption - 平均月消费
    6. income_consumption_ratio - 收入/消费比
    
    【偿还能力】5个指标
    7. current_balance - 当前余额
    8. balance_income_ratio - 余额/收入比
    9. min_balance_12m - 月度余额最低点
    10. payday_plus_5_drop - Payday+5压力测试（可选，默认0）
    11. large_withdrawal_ratio - 大额提现比例
    
    【额度相关】2个指标（在预测时动态计算）
    12. credit_amount - 申请/候选额度
    13. credit_to_income_ratio - 额度/收入比
    """
    
    def __init__(self):
        pass
    
    def extract_features_from_pdf_data(self, pdf_data, credit_amount=None):
        """
        从PDF提取的数据中计算13个核心特征
        
        Args:
            pdf_data: PDF服务返回的数据字典
            credit_amount: 申请额度（可选，如果不提供则使用余额的2倍作为基准）
        
        Returns:
            dict: 包含13个特征的字典
        """
        # 提取基础数据
        total_income = pdf_data.get('total_income', 0.0)
        total_expense = pdf_data.get('total_expense', 0.0)
        current_balance = pdf_data.get('current_balance', 0.0) or pdf_data.get('balance', 0.0)
        
        # 如果没有提供申请额度，使用余额的2倍作为基准
        if credit_amount is None:
            credit_amount = current_balance * 2.0
        
        # 确保数值有效
        if total_income <= 0:
            total_income = 50000.0  # 默认收入
        if current_balance <= 0:
            current_balance = 5000.0  # 默认余额
        
        # 计算月收入（假设total_income是6个月或12个月的总收入）
        # 这里假设是6个月的数据
        monthly_income = total_income / 6.0
        
        # 构建特征字典
        features = {
            # 【收入能力】
            'avg_income_3m': pdf_data.get('avg_income_3m', monthly_income),
            'income_variance_3m': pdf_data.get('income_variance_3m', monthly_income * 0.1),
            'total_income': total_income,
            
            # 【支出能力】
            'avg_large_spending': pdf_data.get('avg_large_spending', total_expense * 0.15),
            'avg_monthly_consumption': pdf_data.get('avg_monthly_consumption', total_expense / 6.0),
            'income_consumption_ratio': 0.0,  # 稍后计算
            
            # 【偿还能力】
            'current_balance': current_balance,
            'balance_income_ratio': 0.0,  # 稍后计算
            'min_balance_12m': pdf_data.get('min_balance_12m', current_balance * 0.2),
            'payday_plus_5_drop': 0.0,  # 默认值（需要分期付款数据，这里设为0）
            'large_withdrawal_ratio': pdf_data.get('large_withdrawal_ratio', 0.25),
            
            # 【额度相关】
            'credit_amount': credit_amount,
            'credit_to_income_ratio': 0.0,  # 稍后计算
        }
        
        # 计算衍生特征
        # 指标6: 收入/消费比
        avg_consumption = features['avg_monthly_consumption']
        features['income_consumption_ratio'] = (
            features['avg_income_3m'] / (avg_consumption + 1.0)
        )
        
        # 指标8: 余额/收入比
        features['balance_income_ratio'] = (
            current_balance / (monthly_income + 1.0)
        )
        
        # 指标13: 额度/收入比（杠杆率）
        features['credit_to_income_ratio'] = (
            credit_amount / (total_income + 1.0)
        )
        
        return features
    
    def prepare_features_for_model(self, features_dict):
        """
        将特征字典转换为模型输入格式（DataFrame）
        
        Args:
            features_dict: 特征字典
        
        Returns:
            pd.DataFrame: 单行DataFrame，包含所有特征
        """
        # 确保特征顺序一致
        feature_names = [
            'avg_income_3m',
            'income_variance_3m',
            'total_income',
            'avg_large_spending',
            'avg_monthly_consumption',
            'income_consumption_ratio',
            'current_balance',
            'balance_income_ratio',
            'min_balance_12m',
            'payday_plus_5_drop',
            'large_withdrawal_ratio',
            'credit_amount',
            'credit_to_income_ratio',
        ]
        
        # 构建DataFrame
        df = pd.DataFrame([features_dict])
        
        # 确保所有特征都存在
        for feature in feature_names:
            if feature not in df.columns:
                df[feature] = 0.0
        
        # 只保留需要的特征，并按顺序排列
        df = df[feature_names]
        
        return df

