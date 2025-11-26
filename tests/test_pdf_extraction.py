"""
测试PDF提取功能
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.pdf_service import PDFService


def test_pdf_extraction():
    """测试PDF提取功能"""
    print("\n" + "="*80)
    print("测试PDF提取功能")
    print("="*80)
    
    pdf_service = PDFService()
    
    # 创建模拟的交易数据
    print("\n创建模拟交易数据...")
    
    mock_transactions = [
        {'date': '20250801', 'amount': 10000.0, 'balance': 15000.0, 'type': 'income', 'category': 'salary'},
        {'date': '20250805', 'amount': 500.0, 'balance': 14500.0, 'type': 'expense', 'category': 'atm_withdrawal'},
        {'date': '20250810', 'amount': 2000.0, 'balance': 12500.0, 'type': 'expense', 'category': 'pos_spending'},
        {'date': '20250815', 'amount': 3000.0, 'balance': 15500.0, 'type': 'income', 'category': 'transfer'},
        {'date': '20250820', 'amount': 1500.0, 'balance': 14000.0, 'type': 'expense', 'category': 'pos_spending'},
        {'date': '20250825', 'amount': 800.0, 'balance': 13200.0, 'type': 'expense', 'category': 'atm_withdrawal'},
        {'date': '20250901', 'amount': 10000.0, 'balance': 23200.0, 'type': 'income', 'category': 'salary'},
        {'date': '20250905', 'amount': 600.0, 'balance': 22600.0, 'type': 'expense', 'category': 'atm_withdrawal'},
        {'date': '20250910', 'amount': 2500.0, 'balance': 20100.0, 'type': 'expense', 'category': 'pos_spending'},
        {'date': '20250915', 'amount': 1000.0, 'balance': 19100.0, 'type': 'expense', 'category': 'pos_spending'},
    ]
    
    # 测试格式化交易列表
    print("\n测试格式化交易列表...")
    formatted = pdf_service._format_transactions_for_display(mock_transactions)
    
    print(f"\n格式化后的交易列表 (共{len(formatted)}笔):")
    print("-" * 80)
    print(f"{'日期':<12} {'类型':<8} {'分类':<12} {'金额':<12} {'余额':<12}")
    print("-" * 80)
    
    for trans in formatted:
        print(f"{trans['date']:<12} {trans['type']:<8} {trans['category']:<12} "
              f"¥{trans['amount']:<11,.2f} ¥{trans['balance']:<11,.2f}")
    
    # 测试详细统计
    print("\n\n测试详细统计计算...")
    stats = pdf_service._calculate_detailed_statistics(mock_transactions)
    
    print("\n统计结果:")
    print("-" * 80)
    print(f"总收入:           ¥{stats['total_income']:,.2f}")
    print(f"总支出:           ¥{stats['total_expense']:,.2f}")
    print(f"当前余额:         ¥{stats['current_balance']:,.2f}")
    print(f"交易笔数:         {stats['total_transactions']}")
    print(f"\n核心指标:")
    print(f"  3个月平均收入:  ¥{stats['avg_income_3m']:,.2f}")
    print(f"  收入方差:       ¥{stats['income_variance_3m']:,.2f}")
    print(f"  平均月消费:     ¥{stats['avg_monthly_consumption']:,.2f}")
    print(f"  大额支出均值:   ¥{stats['avg_large_spending']:,.2f}")
    print(f"  12月最低余额:   ¥{stats['min_balance_12m']:,.2f}")
    print(f"  大额取现比例:   {stats['large_withdrawal_ratio']:.2%}")
    
    print("\n" + "="*80)
    print("✅ 测试完成")
    print("="*80 + "\n")
    
    return True


def test_feature_engineering():
    """测试特征工程"""
    print("\n" + "="*80)
    print("测试特征工程")
    print("="*80)
    
    from services.feature_engineering_service import FeatureEngineeringService
    
    feature_service = FeatureEngineeringService()
    
    # 模拟PDF数据
    pdf_data = {
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
    }
    
    # 提取特征
    features = feature_service.extract_features_from_pdf_data(pdf_data, credit_amount=10000.0)
    
    print("\n提取的13个特征:")
    print("-" * 80)
    for i, (key, value) in enumerate(features.items(), 1):
        print(f"{i:2d}. {key:<30} = {value:>15,.2f}")
    
    print("\n" + "="*80)
    print("✅ 特征工程测试完成")
    print("="*80 + "\n")
    
    return True


if __name__ == "__main__":
    print("\n" + "="*80)
    print("开始测试PDF提取和特征工程")
    print("="*80)
    
    results = []
    
    # 运行测试
    results.append(("PDF提取", test_pdf_extraction()))
    results.append(("特征工程", test_feature_engineering()))
    
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

