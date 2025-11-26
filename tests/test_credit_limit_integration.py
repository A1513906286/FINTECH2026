"""
测试信用额度预测系统集成
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.pdf_service import PDFService
from services.credit_limit_service import CreditLimitService


def test_basic_prediction():
    """测试基础预测（不使用PDF数据）"""
    print("\n" + "="*80)
    print("测试1: 基础预测（不使用PDF数据）")
    print("="*80)
    
    credit_service = CreditLimitService()
    
    # 测试数据
    total_income = 74707.66
    balance = 4204.74
    
    result = credit_service.predict_credit_limit(total_income, balance)
    
    print("\n预测结果:")
    print(f"  成功: {result['success']}")
    print(f"  授信额度: ¥{result['credit_limit']:,.2f}")
    print(f"  风险等级: {result['risk_level']}")
    print(f"  违约概率: {result.get('pd_prob', 0):.2%}")
    print(f"  预期价值: ¥{result.get('expected_value', 0):,.2f}")
    print(f"  消息: {result['message']}")
    
    return result['success']


def test_pdf_prediction():
    """测试使用PDF数据的预测"""
    print("\n" + "="*80)
    print("测试2: 使用PDF数据的预测")
    print("="*80)
    
    credit_service = CreditLimitService()
    
    # 模拟PDF数据（使用默认数据）
    pdf_data = {
        'success': True,
        'total_income': 74707.66,
        'total_expense': 70698.55,
        'current_balance': 4204.74,
        'total_transactions': 653,
        'avg_income_3m': 24902.55,
        'income_variance_3m': 1500000.0,
        'avg_large_spending': 5000.0,
        'avg_monthly_consumption': 5891.55,
        'min_balance_12m': 1000.0,
        'large_withdrawal_ratio': 0.25,
        'atm_withdrawal_total': 15000.0,
        'pos_spending_total': 45000.0,
        'transaction_count_3m': 180,
        'transaction_count_12m': 653,
    }
    
    result = credit_service.predict_with_pdf_data(pdf_data)
    
    print("\n预测结果:")
    print(f"  成功: {result['success']}")
    print(f"  授信额度: ¥{result['credit_limit']:,.2f}")
    print(f"  风险等级: {result['risk_level']}")
    print(f"  违约概率: {result.get('pd_prob', 0):.2%}")
    print(f"  预期价值: ¥{result.get('expected_value', 0):,.2f}")
    print(f"  利用率: {result.get('utilization', 0):.2%}")
    print(f"  消息: {result['message']}")
    
    return result['success']


def test_high_income_user():
    """测试高收入用户"""
    print("\n" + "="*80)
    print("测试3: 高收入用户")
    print("="*80)
    
    credit_service = CreditLimitService()
    
    # 高收入用户数据
    total_income = 200000.0
    balance = 50000.0
    
    result = credit_service.predict_credit_limit(total_income, balance)
    
    print("\n预测结果:")
    print(f"  成功: {result['success']}")
    print(f"  授信额度: ¥{result['credit_limit']:,.2f}")
    print(f"  风险等级: {result['risk_level']}")
    print(f"  违约概率: {result.get('pd_prob', 0):.2%}")
    print(f"  预期价值: ¥{result.get('expected_value', 0):,.2f}")
    
    return result['success']


def test_low_income_user():
    """测试低收入用户"""
    print("\n" + "="*80)
    print("测试4: 低收入用户")
    print("="*80)
    
    credit_service = CreditLimitService()
    
    # 低收入用户数据
    total_income = 30000.0
    balance = 1000.0
    
    result = credit_service.predict_credit_limit(total_income, balance)
    
    print("\n预测结果:")
    print(f"  成功: {result['success']}")
    print(f"  授信额度: ¥{result['credit_limit']:,.2f}")
    print(f"  风险等级: {result['risk_level']}")
    print(f"  违约概率: {result.get('pd_prob', 0):.2%}")
    print(f"  预期价值: ¥{result.get('expected_value', 0):,.2f}")
    
    return result['success']


if __name__ == "__main__":
    print("\n" + "="*80)
    print("开始测试信用额度预测系统集成")
    print("="*80)
    
    results = []
    
    # 运行所有测试
    results.append(("基础预测", test_basic_prediction()))
    results.append(("PDF数据预测", test_pdf_prediction()))
    results.append(("高收入用户", test_high_income_user()))
    results.append(("低收入用户", test_low_income_user()))
    
    # 汇总结果
    print("\n" + "="*80)
    print("测试结果汇总")
    print("="*80)
    
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name}: {status}")
    
    all_passed = all(success for _, success in results)
    
    print("\n" + "="*80)
    if all_passed:
        print("✅ 所有测试通过！")
    else:
        print("❌ 部分测试失败")
    print("="*80 + "\n")

