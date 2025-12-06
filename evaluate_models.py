"""
模型性能评估脚本
评估PD模型和利用率模型的性能指标
"""
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, r2_score, mean_squared_error, classification_report, confusion_matrix
import joblib
import os

def evaluate_pd_model(model_path='models/hc_pd_model.pkl', test_data_path=None):
    """
    评估PD模型性能
    
    Args:
        model_path: 模型文件路径
        test_data_path: 测试数据路径（如果有的话）
    
    Returns:
        dict: 评估指标
    """
    print("="*80)
    print("📊 PD模型性能评估")
    print("="*80)
    
    if not os.path.exists(model_path):
        print(f"❌ 模型文件不存在: {model_path}")
        return None
    
    # 加载模型
    model_data = joblib.load(model_path)
    model = model_data['model']
    feature_names = model_data['feature_names']
    
    print(f"✅ 模型加载成功")
    print(f"   特征数量: {len(feature_names)}")
    print(f"   特征列表: {feature_names[:5]}... (显示前5个)")
    
    # 如果没有测试数据，返回模型信息
    if test_data_path is None or not os.path.exists(test_data_path):
        print("\n⚠️ 未提供测试数据，无法计算AUC等指标")
        print("\n💡 建议：")
        print("   1. 准备测试数据集（CSV格式）")
        print("   2. 包含所有特征列 + 'target'列（0=正常，1=违约）")
        print("   3. 运行: python evaluate_models.py --test-data test.csv")
        return {
            'model_type': 'PD Model (XGBoost Classifier)',
            'features': len(feature_names),
            'status': 'No test data provided'
        }
    
    # 加载测试数据
    test_df = pd.read_csv(test_data_path)
    print(f"\n✅ 测试数据加载成功: {len(test_df)} 条记录")
    
    # 分离特征和标签
    X_test = test_df[feature_names]
    y_test = test_df['target']
    
    # 预测
    y_pred_proba = model.predict_proba(X_test)[:, 1]  # 违约概率
    y_pred = (y_pred_proba >= 0.5).astype(int)  # 二分类预测
    
    # 计算AUC
    auc = roc_auc_score(y_test, y_pred_proba)
    
    # 计算混淆矩阵
    cm = confusion_matrix(y_test, y_pred)
    
    # 计算其他指标
    from sklearn.metrics import precision_score, recall_score, f1_score
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    
    # 打印结果
    print("\n" + "="*80)
    print("📈 PD模型评估结果")
    print("="*80)
    print(f"\n🎯 核心指标:")
    print(f"   AUC (ROC曲线下面积): {auc:.4f}")
    
    # 评价AUC
    if auc >= 0.80:
        auc_rating = "优秀 (Excellent) ⭐⭐⭐"
    elif auc >= 0.75:
        auc_rating = "良好 (Good) ⭐⭐"
    elif auc >= 0.70:
        auc_rating = "一般 (Fair) ⭐"
    else:
        auc_rating = "较差 (Poor) ❌"
    
    print(f"   评价: {auc_rating}")
    print(f"\n📊 分类指标:")
    print(f"   Precision (精确率): {precision:.4f}")
    print(f"   Recall (召回率): {recall:.4f}")
    print(f"   F1 Score: {f1:.4f}")
    
    print(f"\n📋 混淆矩阵:")
    print(f"   TN={cm[0,0]}, FP={cm[0,1]}")
    print(f"   FN={cm[1,0]}, TP={cm[1,1]}")
    
    print(f"\n✅ 行业基准对比:")
    print(f"   传统银行标准: AUC ≥ 0.75")
    print(f"   互联网金融标准: AUC ≥ 0.70")
    print(f"   巴塞尔III要求: AUC ≥ 0.70")
    print(f"   你的模型: AUC = {auc:.4f}")
    
    return {
        'auc': auc,
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'confusion_matrix': cm
    }


def evaluate_utilization_model(model_path='models/hc_utilization_model.pkl', test_data_path=None):
    """
    评估利用率模型性能
    
    Args:
        model_path: 模型文件路径
        test_data_path: 测试数据路径
    
    Returns:
        dict: 评估指标
    """
    print("\n" + "="*80)
    print("📊 利用率模型性能评估")
    print("="*80)
    
    if not os.path.exists(model_path):
        print(f"❌ 模型文件不存在: {model_path}")
        return None
    
    # 加载模型
    model_data = joblib.load(model_path)
    model = model_data['model']
    feature_names = model_data['feature_names']
    
    print(f"✅ 模型加载成功")
    print(f"   特征数量: {len(feature_names)}")
    
    # 如果没有测试数据
    if test_data_path is None or not os.path.exists(test_data_path):
        print("\n⚠️ 未提供测试数据，无法计算R²、RMSE等指标")
        return {
            'model_type': 'Utilization Model (XGBoost Regressor)',
            'features': len(feature_names),
            'status': 'No test data provided'
        }
    
    # 加载测试数据
    test_df = pd.read_csv(test_data_path)
    print(f"\n✅ 测试数据加载成功: {len(test_df)} 条记录")
    
    # 分离特征和标签
    X_test = test_df[feature_names]
    y_test = test_df['utilization']  # 真实利用率
    
    # 预测
    y_pred = model.predict(X_test)
    
    # 计算R²
    r2 = r2_score(y_test, y_pred)
    
    # 计算RMSE
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    
    # 计算相对RMSE
    mean_utilization = y_test.mean()
    relative_rmse = rmse / mean_utilization
    
    # 打印结果
    print("\n" + "="*80)
    print("📈 利用率模型评估结果")
    print("="*80)
    print(f"\n🎯 核心指标:")
    print(f"   R² (决定系数): {r2:.4f}")
    
    # 评价R²
    if r2 >= 0.50:
        r2_rating = "优秀 (Excellent) ⭐⭐⭐"
    elif r2 >= 0.35:
        r2_rating = "良好 (Good) ⭐⭐"
    elif r2 >= 0.25:
        r2_rating = "一般 (Fair) ⭐"
    else:
        r2_rating = "较差 (Poor) ❌"
    
    print(f"   评价: {r2_rating}")
    
    print(f"\n📊 误差指标:")
    print(f"   RMSE (均方根误差): {rmse:.4f}")
    print(f"   相对RMSE: {relative_rmse:.2%}")
    print(f"   平均利用率: {mean_utilization:.4f}")
    
    # 评价相对RMSE
    if relative_rmse < 0.15:
        rmse_rating = "优秀 ⭐⭐⭐"
    elif relative_rmse < 0.25:
        rmse_rating = "良好 ⭐⭐"
    elif relative_rmse < 0.35:
        rmse_rating = "一般 ⭐"
    else:
        rmse_rating = "较差 ❌"
    
    print(f"   相对RMSE评价: {rmse_rating}")
    
    print(f"\n✅ 行业基准对比:")
    print(f"   信用卡利用率标准: R² ≥ 0.30, 相对RMSE ≤ 25%")
    print(f"   你的模型: R² = {r2:.4f}, 相对RMSE = {relative_rmse:.2%}")
    
    return {
        'r2': r2,
        'rmse': rmse,
        'relative_rmse': relative_rmse,
        'mean_utilization': mean_utilization
    }


if __name__ == '__main__':
    print("🚀 开始模型性能评估...\n")
    
    # 评估PD模型
    pd_metrics = evaluate_pd_model()
    
    # 评估利用率模型
    util_metrics = evaluate_utilization_model()
    
    print("\n" + "="*80)
    print("✅ 评估完成！")
    print("="*80)

