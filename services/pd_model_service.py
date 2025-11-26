"""
违约概率(PD)模型服务 - 适配自Fintech/hc_pd_model.py
"""
import warnings
warnings.filterwarnings('ignore', category=UserWarning, module='pickle')
warnings.filterwarnings('ignore', message='.*XGBoost.*')

import pandas as pd
import numpy as np
import xgboost as xgb
import joblib
import os


class PDModelService:
    """违约概率预测模型服务"""
    
    def __init__(self, model_path='models/hc_pd_model.pkl'):
        """
        初始化PD模型服务
        
        Args:
            model_path: 模型文件路径
        """
        self.model_path = model_path
        self.model = None
        self.feature_names = None
        self.threshold = 0.5
        self._load_model()
    
    def _load_model(self):
        """加载模型"""
        try:
            if os.path.exists(self.model_path):
                model_data = joblib.load(self.model_path)
                self.model = model_data['model']
                self.feature_names = model_data['feature_names']
                self.threshold = model_data.get('threshold', 0.5)
                print(f"✅ PD模型加载成功: {self.model_path}")
                print(f"   特征数量: {len(self.feature_names)}")
            else:
                print(f"⚠️ PD模型文件不存在: {self.model_path}")
                print("   将使用默认违约概率")
        except Exception as e:
            print(f"❌ PD模型加载失败: {str(e)}")
            print("   将使用默认违约概率")
            self.model = None
    
    def predict_proba(self, X):
        """
        预测违约概率
        
        Args:
            X: 特征数据（DataFrame或dict）
        
        Returns:
            float or np.array: 违约概率
        """
        if self.model is None:
            # 如果模型未加载，返回默认违约概率
            if isinstance(X, pd.DataFrame):
                return np.array([0.15] * len(X))
            else:
                return 0.15
        
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
            base_proba = self.model.predict(dmatrix)

            # 🔧 修正：根据额度调整违约概率（因为模型对额度不够敏感）
            # 使用额度/收入比来调整违约概率
            if isinstance(X, pd.DataFrame) and 'credit_to_income_ratio' in X.columns:
                leverage_ratio = X['credit_to_income_ratio'].values

                # 策略：先缩小base_proba，再用指数函数放大
                # 这样可以保留指数增长特性，同时避免过早触及上限
                #
                # PD_adjusted = (base_PD * scale_factor) * exp(k * leverage_ratio)
                #
                # 目标效果（k=1.0，强指数增长）：
                # leverage_ratio = 0.1 → PD增加约11%
                # leverage_ratio = 0.5 → PD增加约65%
                # leverage_ratio = 1.0 → PD增加约172%
                # leverage_ratio = 2.0 → PD增加约639%
                # leverage_ratio = 3.0 → PD增加约1900%

                # 第一步：缩小base_proba到合理范围
                # 如果base_proba很高（>0.5），需要更大幅度缩小

                scaled_base_proba = base_proba * 0.7

                # 第二步：使用强指数函数放大
                k = 1.0  # 指数调整系数（从0.5提高到1.0，增长更快）
                leverage_multiplier = np.exp(k * leverage_ratio)

                # 调整违约概率
                adjusted_proba = scaled_base_proba * leverage_multiplier

                # 确保概率在[0, 1]范围内，上限设为70%
                adjusted_proba = np.clip(adjusted_proba, 0.0, 0.70)

                return adjusted_proba

            return base_proba
        
        except Exception as e:
            print(f"❌ PD预测失败: {str(e)}")
            import traceback
            traceback.print_exc()
            # 返回默认违约概率
            if isinstance(X, pd.DataFrame):
                return np.array([0.15] * len(X))
            else:
                return 0.15
    
    def predict(self, X):
        """
        预测违约类别（0=正常，1=违约）
        
        Args:
            X: 特征数据
        
        Returns:
            int or np.array: 违约类别
        """
        proba = self.predict_proba(X)
        return (proba >= self.threshold).astype(int)
    
    def get_default_probability(self, features_dict):
        """
        获取单个用户的违约概率（便捷方法）
        
        Args:
            features_dict: 特征字典
        
        Returns:
            float: 违约概率
        """
        proba = self.predict_proba(features_dict)
        if isinstance(proba, np.ndarray):
            return float(proba[0])
        return float(proba)
    
    def save(self, filepath):
        """保存模型"""
        if self.model is None:
            raise ValueError("模型未训练")
        
        model_data = {
            'model': self.model,
            'feature_names': self.feature_names,
            'threshold': self.threshold
        }
        joblib.dump(model_data, filepath)
        print(f"✓ 模型已保存到: {filepath}")
    
    def load(self, filepath):
        """加载模型"""
        self.model_path = filepath
        self._load_model()

