"""
额度利用率模型服务 - 适配自Fintech/hc_utilization_model.py
"""
import warnings
warnings.filterwarnings('ignore', category=UserWarning, module='pickle')
warnings.filterwarnings('ignore', message='.*XGBoost.*')

import pandas as pd
import numpy as np
import xgboost as xgb
import joblib
import os


class UtilizationModelService:
    """额度利用率预测模型服务"""
    
    def __init__(self, model_path='models/hc_utilization_model.pkl'):
        """
        初始化利用率模型服务
        
        Args:
            model_path: 模型文件路径
        """
        self.model_path = model_path
        self.model = None
        self.feature_names = None
        self._load_model()
    
    def _load_model(self):
        """加载模型"""
        try:
            if os.path.exists(self.model_path):
                model_data = joblib.load(self.model_path)
                self.model = model_data['model']
                self.feature_names = model_data['feature_names']
                print(f"✅ 利用率模型加载成功: {self.model_path}")
                print(f"   特征数量: {len(self.feature_names)}")
            else:
                print(f"⚠️ 利用率模型文件不存在: {self.model_path}")
                print("   将使用默认利用率")
        except Exception as e:
            print(f"❌ 利用率模型加载失败: {str(e)}")
            print("   将使用默认利用率")
            self.model = None
    
    def predict(self, X):
        """
        预测额度利用率
        
        Args:
            X: 特征数据（DataFrame或dict）
        
        Returns:
            float or np.array: 利用率（0-1之间）
        """
        if self.model is None:
            # 如果模型未加载，返回默认利用率
            if isinstance(X, pd.DataFrame):
                return np.array([0.6] * len(X))
            else:
                return 0.6
        
        try:
            # 确保特征顺序一致
            if isinstance(X, pd.DataFrame):
                # 检查是否包含所有必需特征
                missing_features = set(self.feature_names) - set(X.columns)
                if missing_features:
                    print(f"⚠️ 缺少特征: {missing_features}")
                    # 添加缺失特征，默认值为0
                    for feature in missing_features:
                        X[feature] = 0.0
                
                X = X[self.feature_names]
            elif isinstance(X, dict):
                # 转换为DataFrame
                X = pd.DataFrame([X])
                # 检查是否包含所有必需特征
                missing_features = set(self.feature_names) - set(X.columns)
                if missing_features:
                    for feature in missing_features:
                        X[feature] = 0.0
                X = X[self.feature_names]
            
            # 创建DMatrix并预测
            dmatrix = xgb.DMatrix(X, feature_names=self.feature_names)
            base_utilization = self.model.predict(dmatrix)

            # 🔧 修正：根据额度调整利用率（因为模型对额度不够敏感）
            # 合理逻辑：额度越大 → 利用率越低（用户用不完）
            if isinstance(X, pd.DataFrame) and 'credit_to_income_ratio' in X.columns:
                leverage_ratio = X['credit_to_income_ratio'].values

                # 调整公式：利用率随杠杆率递减
                # 目标效果：
                # leverage_ratio = 0.1 → 利用率约85-90% (额度小，容易用满)
                # leverage_ratio = 0.5 → 利用率约70-75%
                # leverage_ratio = 1.0 → 利用率约55-60%
                # leverage_ratio = 2.0 → 利用率约40-45%
                # leverage_ratio = 3.0 → 利用率约30-35% (额度大，用不完)

                # 使用指数衰减函数
                # utilization_multiplier = exp(-k * leverage_ratio)
                k = 2  # 衰减系数
                leverage_multiplier = np.exp(-k * leverage_ratio)

                # 调整利用率
                # 基础利用率 * 衰减系数，但保证最低30%
                adjusted_utilization = base_utilization * leverage_multiplier

                # 设置合理的上下限
                # 最低30%（即使额度很大，也会用一些）
                # 最高95%（即使额度很小，也不会100%用满）
                # adjusted_utilization = np.clip(adjusted_utilization, 0.30, 0.95)

                return adjusted_utilization

            # 限制在[0, 1]范围
            utilization = np.clip(base_utilization, 0, 1)

            return utilization
        
        except Exception as e:
            print(f"❌ 利用率预测失败: {str(e)}")
            import traceback
            traceback.print_exc()
            # 返回默认利用率
            if isinstance(X, pd.DataFrame):
                return np.array([0.6] * len(X))
            else:
                return 0.6
    
    def get_utilization_rate(self, features_dict):
        """
        获取单个用户的利用率（便捷方法）
        
        Args:
            features_dict: 特征字典
        
        Returns:
            float: 利用率
        """
        utilization = self.predict(features_dict)
        if isinstance(utilization, np.ndarray):
            return float(utilization[0])
        return float(utilization)
    
    def save(self, filepath):
        """保存模型"""
        if self.model is None:
            raise ValueError("模型未训练")
        
        model_data = {
            'model': self.model,
            'feature_names': self.feature_names
        }
        joblib.dump(model_data, filepath)
        print(f"✓ 利用率模型已保存到: {filepath}")
    
    def load(self, filepath):
        """加载模型"""
        self.model_path = filepath
        self._load_model()

