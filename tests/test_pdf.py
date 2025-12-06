#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PDF测试工具 - 调试和测试PDF提取功能
"""

import sys
import os

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

import pdfplumber
from services.pdf_service import PDFService
from services.credit_limit_service import CreditLimitService

def debug_pdf_structure(pdf_path):
    """调试PDF结构"""
    print("\n" + "="*70)
    print(f"📄 调试PDF: {pdf_path}")
    print("="*70)

    with pdfplumber.open(pdf_path) as pdf:
        print(f"总页数: {len(pdf.pages)}\n")

        # 只看第一页
        page = pdf.pages[0]

        # 1. 提取文本
        text = page.extract_text()
        if text:
            lines = text.split('\n')
            print(f"📝 文本内容 (前20行):")
            print("-"*70)
            for i, line in enumerate(lines[:20], 1):
                print(f"{i:2d}: {line}")
            print("-"*70)

            # 分析RMB金额
            print(f"\n🔍 分析前5行交易数据:")
            import re
            for i, line in enumerate(lines[12:17], 1):  # 从第13行开始是交易数据
                rmb_amounts = re.findall(r'RMB\s+([\d,]+\.?\d*)', line)
                print(f"  行{i}: 找到{len(rmb_amounts)}个RMB金额: {rmb_amounts}")
                if rmb_amounts:
                    print(f"       原文: {line[:80]}...")

def test_extraction(pdf_path):
    """测试提取功能"""
    print("\n" + "="*70)
    print("🧪 测试PDF提取")
    print("="*70)

    pdf_service = PDFService()

    # 测试银行流水提取
    result = pdf_service.extract_bank_statement(pdf_path)

    print(f"\n✅ {result['message']}")

    # 新版本返回详细统计数据
    if 'total_income' in result:
        print(f"\n📊 详细统计:")
        print(f"  📈 总收入: ¥{result['total_income']:,.2f}")
        print(f"  📉 总支出: ¥{result['total_expense']:,.2f}")
        print(f"  💵 当前余额: ¥{result.get('current_balance', result.get('balance', 0)):,.2f}")
        print(f"  📝 交易总数: {result['total_transactions']}")
        print(f"  📅 3个月平均收入: ¥{result.get('avg_income_3m', 0):,.2f}")
        print(f"  💰 平均月消费: ¥{result.get('avg_monthly_consumption', 0):,.2f}")
        print(f"  📊 最低余额(12个月): ¥{result.get('min_balance_12m', 0):,.2f}")

    # 测试信用额度预测
    print("\n" + "="*70)
    print("💳 测试信用额度预测")
    print("="*70)

    credit_service = CreditLimitService()

    # 使用新的API：传递total_income, balance和pdf_data
    total_income = result.get('total_income', 74707.66)
    balance = result.get('current_balance', result.get('balance', 4204.74))

    credit_result = credit_service.predict_credit_limit(
        total_income=total_income,
        balance=balance,
        pdf_data=result  # 传递完整的PDF数据
    )

    print(f"\n💳 预测结果:")
    print(f"  授信额度: ¥{credit_result['credit_limit']:,.2f}")
    print(f"  违约概率 (PD): {credit_result.get('pd_prob', 0):.2%}")
    print(f"  周转率 (Velocity): {credit_result.get('velocity', credit_result.get('utilization', 0)):.2%}")
    print(f"  风险等级: {credit_result['risk_level']}")
    print(f"  预期价值 (EV): ¥{credit_result.get('expected_value', 0):,.2f}")

    if 'gmv' in credit_result:
        print(f"\n💰 跨境信用卡业务指标:")
        print(f"  月交易额 (GMV): ¥{credit_result['gmv']:,.2f}")
        print(f"  总收入: ¥{credit_result.get('total_revenue', 0):,.2f}")
        print(f"  总成本: ¥{credit_result.get('total_cost', 0):,.2f}")

def main():
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        # 查找PDF文件
        pdf_files = [f for f in os.listdir('.') if f.endswith('.pdf')]
        if not pdf_files:
            print("❌ 未找到PDF文件")
            print("使用方法: python test_pdf.py <PDF文件路径>")
            return
        pdf_path = pdf_files[0]
        print(f"使用: {pdf_path}")
    
    if not os.path.exists(pdf_path):
        print(f"❌ 文件不存在: {pdf_path}")
        return
    
    # 1. 调试PDF结构
    debug_pdf_structure(pdf_path)
    
    # 2. 测试提取
    test_extraction(pdf_path)

if __name__ == "__main__":
    main()

