# credit_limit_service.py
import joblib
import numpy as np
import os

class CreditLimitService:
    """信用额度预测服务 - 使用XGBoost简化模型（只需收入和余额）"""

    def __init__(self, model_path='models/xgboost_simple_model.pkl'):
        """
        初始化服务

        Args:
            model_path: XGBoost模型文件路径
        """
        self.model_path = model_path
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """加载XGBoost模型"""
        try:
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
                print(f"✅ XGBoost模型加载成功: {self.model_path}")
            else:
                print(f"⚠️ 模型文件不存在: {self.model_path}")
                print("将使用默认规则计算额度")
        except Exception as e:
            print(f"❌ 模型加载失败: {str(e)}")
            print("将使用默认规则计算额度")
            self.model = None
    

    
    def predict_credit_limit(self, total_income, balance):
        """
        预测用户信用额度（回归模型：直接预测额度）

        Args:
            total_income: 总收入
            balance: 账户余额

        Returns:
            dict: {
                'success': bool,
                'credit_limit': float,
                'risk_level': str,
                'message': str
            }
        """
        try:
            # 构建特征向量 (2个特征: 总收入, 余额)
            features_array = np.array([[total_income, balance]])

            # 如果模型存在，使用模型直接预测额度
            if self.model is not None:
                try:
                    # 直接预测信用额度（回归模型）
                    credit_limit = float(self.model.predict(features_array)[0])
                    print(f"✅ 模型预测额度: ¥{credit_limit:,.2f}")
                except Exception as e:
                    print(f"❌ 模型预测失败: {str(e)}")
                    # 使用规则计算默认额度
                    credit_limit = self._calculate_default_limit(total_income, balance)
            else:
                # 使用规则计算默认额度
                credit_limit = self._calculate_default_limit(total_income, balance)

            # 根据额度判断风险等级
            if credit_limit >= balance * 3:
                risk_level = "低风险"
            elif credit_limit >= balance * 1.5:
                risk_level = "中等风险"
            else:
                risk_level = "高风险"

            return {
                'success': True,
                'credit_limit': float(round(credit_limit, 2)),
                'risk_level': risk_level,
                'balance': float(balance),
                'total_income': float(total_income),
                'message': f'预测成功 - {risk_level}，授信额度¥{credit_limit:,.2f}'
            }

        except Exception as e:
            print(f"额度预测错误: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'message': f'额度预测失败: {str(e)}'
            }

    def _calculate_default_limit(self, total_income, balance):
        """
        使用规则计算默认额度

        Args:
            total_income: 总收入
            balance: 账户余额

        Returns:
            float: 信用额度
        """
        # 收入余额比
        income_balance_ratio = total_income / balance if balance > 0 else 0

        # 根据收入余额比确定倍数
        if income_balance_ratio >= 15:
            multiplier = 4.0  # 收入远大于余额，低风险
        elif income_balance_ratio >= 10:
            multiplier = 3.0
        elif income_balance_ratio >= 5:
            multiplier = 2.0
        elif income_balance_ratio >= 2:
            multiplier = 1.5
        else:
            multiplier = 1.0  # 收入低，高风险

        credit_limit = balance * multiplier
        print(f"📊 规则计算: 收入¥{total_income:,.2f}, 余额¥{balance:,.2f}, 倍数{multiplier}x, 额度¥{credit_limit:,.2f}")

        return credit_limit
    
    def get_default_credit_limit(self, balance=4204.74, total_income=74707.66):
        """
        获取默认信用额度（当没有足够数据时使用）

        Args:
            balance: 账户余额
            total_income: 总收入

        Returns:
            dict: 信用额度信息
        """
        # 使用规则计算默认额度
        credit_limit = self._calculate_default_limit(total_income, balance)

        return {
            'success': True,
            'credit_limit': float(round(credit_limit, 2)),
            'risk_level': "中等风险",
            'balance': float(balance),
            'total_income': float(total_income),
            'message': '使用默认额度计算'
        }

