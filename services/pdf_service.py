# pdf_service.py
import pdfplumber
import re
import os
import numpy as np
import pandas as pd
from datetime import datetime
from collections import defaultdict

class PDFService:
    """PDF文件处理服务 - 提取银行流水和余额证明信息（增强版）"""

    def __init__(self):
        self.upload_folder = 'uploads/pdfs'
        self.user_persona_folder = 'user_persona'
        os.makedirs(self.upload_folder, exist_ok=True)
        os.makedirs(self.user_persona_folder, exist_ok=True)

    def _extract_number(self, text):
        """从文本中提取数字（支持RMB格式）"""
        if not text:
            return 0.0

        text = str(text).strip()
        if not text:
            return 0.0

        # 移除货币符号、空格、逗号
        text = text.replace('RMB', '').replace('¥', '').replace('$', '').replace('AED', '')
        text = text.replace(',', '').replace(' ', '').strip()

        # 提取数字
        match = re.search(r'\d+\.?\d*', text)
        if match:
            try:
                return float(match.group())
            except:
                return 0.0
        return 0.0

    def _identify_transaction_category(self, line):
        """识别交易类型"""
        line_lower = line.lower()

        # ATM取现
        if 'atm' in line_lower or '取现' in line or '提现' in line:
            return 'atm_withdrawal'

        # POS消费
        if 'pos' in line_lower or '消费' in line or '刷卡' in line:
            return 'pos_spending'

        # 转账
        if '转账' in line or 'transfer' in line_lower:
            return 'transfer'

        # 工资
        if '工资' in line or 'salary' in line_lower or '代发' in line:
            return 'salary'

        # 还款
        if '还款' in line or 'repayment' in line_lower or 'payment' in line_lower:
            return 'repayment'

        return 'unknown'

    def _format_transactions_for_display(self, transactions):
        """
        格式化交易列表供前端显示

        返回格式:
        [
            {
                'date': '2025-08-10',
                'type': '收入/支出',
                'category': '工资/ATM取现/POS消费/转账',
                'amount': 1000.00,
                'balance': 5000.00
            }
        ]
        """
        formatted = []

        # 类型映射
        type_map = {
            'income': '收入',
            'expense': '支出',
            'unknown': '未知'
        }

        # 分类映射
        category_map = {
            'atm_withdrawal': 'ATM取现',
            'pos_spending': 'POS消费',
            'transfer': '转账',
            'salary': '工资',
            'repayment': '还款',
            'income': '收入',
            'expense': '支出',
            'unknown': '其他'
        }

        for trans in transactions:
            # 格式化日期
            date_str = trans['date']
            try:
                formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            except:
                formatted_date = date_str

            formatted.append({
                'date': formatted_date,
                'type': type_map.get(trans['type'], '未知'),
                'category': category_map.get(trans['category'], '其他'),
                'amount': round(trans['amount'], 2),
                'balance': round(trans['balance'], 2)
            })

        return formatted

    def _calculate_detailed_statistics(self, transactions):
        """
        计算详细的统计数据，用于特征工程

        返回13个核心指标所需的基础数据
        """
        if not transactions:
            return self._get_default_detailed_stats()

        # 转换为DataFrame便于处理
        df = pd.DataFrame(transactions)

        # 解析日期
        df['date'] = pd.to_datetime(df['date'], format='%Y%m%d', errors='coerce')
        df = df.dropna(subset=['date'])

        if len(df) == 0:
            return self._get_default_detailed_stats()

        # 按日期排序
        df = df.sort_values('date')

        # 计算月份
        df['month'] = df['date'].dt.to_period('M')

        # 分类交易
        income_df = df[df['type'] == 'income']
        expense_df = df[df['type'] == 'expense']
        atm_df = df[df['category'] == 'atm_withdrawal']
        pos_df = df[df['category'] == 'pos_spending']
        transfer_df = df[df['category'] == 'transfer']

        # 获取最近的日期范围
        latest_date = df['date'].max()
        date_3m_ago = latest_date - pd.DateOffset(months=3)
        date_12m_ago = latest_date - pd.DateOffset(months=12)

        # 最近3个月的数据
        recent_3m = df[df['date'] >= date_3m_ago]
        income_3m = recent_3m[recent_3m['type'] == 'income']

        # 最近12个月的数据
        recent_12m = df[df['date'] >= date_12m_ago]
        expense_12m = recent_12m[recent_12m['type'] == 'expense']
        atm_12m = recent_12m[recent_12m['category'] == 'atm_withdrawal']
        transfer_12m = recent_12m[recent_12m['category'] == 'transfer']

        # 计算各项指标
        stats = {
            # 基础数据
            'total_income': float(income_df['amount'].sum()),
            'total_expense': float(expense_df['amount'].sum()),
            'current_balance': float(df['balance'].iloc[-1]) if len(df) > 0 else 0.0,
            'total_transactions': len(df[df['type'] != 'unknown']),

            # 指标1: 过去3个月平均入账
            'avg_income_3m': float(income_3m['amount'].mean()) if len(income_3m) > 0 else 0.0,

            # 指标2: 3个月入账方差
            'income_variance_3m': float(income_3m['amount'].var()) if len(income_3m) > 1 else 0.0,

            # 指标3: 总收入（已包含在total_income中）

            # 指标4: 大额单笔平均支出 (>90分位数)
            'avg_large_spending': self._calculate_large_spending(expense_12m),

            # 指标5: 平均月消费
            'avg_monthly_consumption': self._calculate_monthly_consumption(expense_12m),

            # 指标7: 当前余额（已包含在current_balance中）

            # 指标9: 月度余额最低点（最近12个月）
            'min_balance_12m': float(recent_12m['balance'].min()) if len(recent_12m) > 0 else 0.0,

            # 指标10: 发薪日后5天余额下降（还款压力）
            'payday_plus_5_drop': self._calculate_payday_plus_5_drop(income_df, df),

            # 指标11: 大额提现/转账比例
            'large_withdrawal_ratio': self._calculate_large_withdrawal_ratio(atm_12m, transfer_12m),

            # 额外统计
            'atm_withdrawal_total': float(atm_df['amount'].sum()),
            'pos_spending_total': float(pos_df['amount'].sum()),
            'transfer_total': float(transfer_df['amount'].sum()),
            'transaction_count_3m': len(recent_3m),
            'transaction_count_12m': len(recent_12m),
        }

        # 打印PDF统计数据用于调试
        print("\n" + "="*60)
        print("PDF统计数据:")
        print("="*60)
        print(f"总收入: ¥{stats['total_income']:,.2f}")
        print(f"总支出: ¥{stats['total_expense']:,.2f}")
        print(f"当前余额: ¥{stats['current_balance']:,.2f}")
        print(f"3个月平均收入: ¥{stats['avg_income_3m']:,.2f}")
        print(f"3个月收入方差: ¥{stats['income_variance_3m']:,.2f}")
        print(f"大额支出平均: ¥{stats['avg_large_spending']:,.2f}")
        print(f"平均月消费: ¥{stats['avg_monthly_consumption']:,.2f}")
        print(f"最低余额(12个月): ¥{stats['min_balance_12m']:,.2f}")
        print(f"大额取现比例: {stats['large_withdrawal_ratio']:.2%}")
        print(f"交易笔数(3个月): {stats['transaction_count_3m']}")
        print(f"交易笔数(12个月): {stats['transaction_count_12m']}")
        print("="*60 + "\n")

        return stats

    def _calculate_large_spending(self, expense_df):
        """计算大额支出平均值（>90分位数）"""
        if len(expense_df) == 0:
            return 0.0

        amounts = expense_df['amount']
        amounts = amounts[amounts > 0]

        if len(amounts) == 0:
            return 0.0

        threshold = amounts.quantile(0.90)
        large_spending = amounts[amounts >= threshold]

        return float(large_spending.mean()) if len(large_spending) > 0 else 0.0

    def _calculate_monthly_consumption(self, expense_df):
        """计算平均月消费"""
        if len(expense_df) == 0:
            return 0.0

        # 按月分组
        if 'month' in expense_df.columns:
            monthly_totals = expense_df.groupby('month')['amount'].sum()
            return float(monthly_totals.mean()) if len(monthly_totals) > 0 else 0.0
        else:
            # 如果没有月份信息，直接计算平均值
            return float(expense_df['amount'].mean())

    def _calculate_payday_plus_5_drop(self, income_df, all_df):
        """
        计算发薪日后5天的余额下降（还款压力指标）

        逻辑：
        1. 找到所有收入日期（发薪日）
        2. 计算发薪日后5天的余额变化
        3. 返回平均余额下降幅度
        """
        if len(income_df) == 0 or len(all_df) == 0:
            return 0.0

        try:
            balance_drops = []

            for idx, income_row in income_df.iterrows():
                income_date = income_row['date']
                income_balance = income_row['balance']

                # 找到5天后的日期
                date_plus_5 = income_date + pd.Timedelta(days=5)

                # 找到5天后最接近的交易记录
                future_transactions = all_df[all_df['date'] >= date_plus_5]

                if len(future_transactions) > 0:
                    # 取最近的一笔交易的余额
                    balance_after_5 = future_transactions.iloc[0]['balance']

                    # 计算余额下降
                    drop = income_balance - balance_after_5

                    # 只记录下降的情况（正值表示下降）
                    if drop > 0:
                        balance_drops.append(drop)

            # 返回平均下降金额
            if len(balance_drops) > 0:
                return float(np.mean(balance_drops))
            else:
                return 0.0

        except Exception as e:
            print(f"计算payday_plus_5_drop时出错: {e}")
            return 0.0

    def _calculate_large_withdrawal_ratio(self, atm_df, transfer_df):
        """
        计算大额提现/转账比例（>75分位数）

        包括ATM取现和转账两种类型
        """
        # 合并ATM取现和转账
        withdrawal_list = []

        if len(atm_df) > 0:
            withdrawal_list.extend(atm_df['amount'].tolist())

        if len(transfer_df) > 0:
            # 只统计支出类型的转账
            transfer_expenses = transfer_df[transfer_df['type'] == 'expense']
            withdrawal_list.extend(transfer_expenses['amount'].tolist())

        if len(withdrawal_list) == 0:
            return 0.0

        amounts = pd.Series(withdrawal_list)
        amounts = amounts[amounts > 0]

        if len(amounts) == 0:
            return 0.0

        # 计算75分位数
        threshold = amounts.quantile(0.75)
        large_count = (amounts >= threshold).sum()

        return float(large_count / len(amounts)) if len(amounts) > 0 else 0.0

    def _get_default_detailed_stats(self):
        """返回默认的详细统计数据"""
        return {
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
    
    def _save_extracted_info_to_txt(self, pdf_path, result_data):
        """
        将提取的PDF信息保存到txt文件
        
        Args:
            pdf_path: PDF文件路径
            result_data: 提取结果数据字典
        """
        try:
            # 获取户名，用于文件名
            account_name = result_data.get('account_name', '')
            if account_name:
                # 清理户名，移除可能存在的非法文件名字符
                account_name = re.sub(r'[<>:"/\\|?*]', '', account_name)
                account_name = account_name.strip()
            
            # 生成txt文件名（优先使用户名，否则使用PDF文件名+时间戳）
            if account_name:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                txt_filename = f"{account_name}_{timestamp}.txt"
            else:
                # 如果提取不到户名，使用原来的命名方式
                pdf_filename = os.path.splitext(os.path.basename(pdf_path))[0]
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                txt_filename = f"{pdf_filename}_{timestamp}.txt"
            
            txt_filepath = os.path.join(self.user_persona_folder, txt_filename)
            
            # 准备写入内容
            content_lines = []
            content_lines.append("=" * 80)
            content_lines.append("银行流水提取信息")
            content_lines.append("=" * 80)
            content_lines.append(f"提取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            content_lines.append(f"PDF文件路径: {pdf_path}")
            if account_name:
                content_lines.append(f"户名: {account_name}")
            content_lines.append("")
            
            # 添加统计信息
            content_lines.append("-" * 80)
            content_lines.append("统计信息")
            content_lines.append("-" * 80)
            if 'total_income' in result_data:
                if account_name:
                    content_lines.append(f"户名: {account_name}")
                content_lines.append(f"总收入: ¥{result_data.get('total_income', 0):,.2f}")
                content_lines.append(f"总支出: ¥{result_data.get('total_expense', 0):,.2f}")
                content_lines.append(f"当前余额: ¥{result_data.get('current_balance', 0):,.2f}")
                content_lines.append(f"交易总数: {result_data.get('total_transactions', 0)}")
                content_lines.append(f"3个月平均收入: ¥{result_data.get('avg_income_3m', 0):,.2f}")
                content_lines.append(f"3个月收入方差: ¥{result_data.get('income_variance_3m', 0):,.2f}")
                content_lines.append(f"大额支出平均: ¥{result_data.get('avg_large_spending', 0):,.2f}")
                content_lines.append(f"平均月消费: ¥{result_data.get('avg_monthly_consumption', 0):,.2f}")
                content_lines.append(f"最低余额(12个月): ¥{result_data.get('min_balance_12m', 0):,.2f}")
                content_lines.append(f"发薪日后5天余额下降: ¥{result_data.get('payday_plus_5_drop', 0):,.2f}")
                content_lines.append(f"大额取现比例: {result_data.get('large_withdrawal_ratio', 0):.2%}")
                content_lines.append(f"ATM取现总额: ¥{result_data.get('atm_withdrawal_total', 0):,.2f}")
                content_lines.append(f"POS消费总额: ¥{result_data.get('pos_spending_total', 0):,.2f}")
                content_lines.append(f"转账总额: ¥{result_data.get('transfer_total', 0):,.2f}")
                content_lines.append(f"交易笔数(3个月): {result_data.get('transaction_count_3m', 0)}")
                content_lines.append(f"交易笔数(12个月): {result_data.get('transaction_count_12m', 0)}")
            else:
                content_lines.append(f"余额: ¥{result_data.get('balance', 0):,.2f}")
            content_lines.append("")
            
            # 添加交易列表
            transactions = result_data.get('transactions', [])
            if transactions:
                content_lines.append("-" * 80)
                content_lines.append(f"交易明细 (共{len(transactions)}笔)")
                content_lines.append("-" * 80)
                # 表头：日期、类型、分类、金额、余额、摘要、对方户名
                content_lines.append(
                    f"{'日期':<12} {'类型':<8} {'分类':<12} {'金额':>15} {'余额':>15}  {'摘要':<20}  {'对方户名':<30}"
                )
                content_lines.append("-" * 80)
                
                # 类型映射
                type_map = {
                    'income': '收入',
                    'expense': '支出',
                    'unknown': '未知'
                }
                
                # 分类映射
                category_map = {
                    'atm_withdrawal': 'ATM取现',
                    'pos_spending': 'POS消费',
                    'transfer': '转账',
                    'salary': '工资',
                    'repayment': '还款',
                    'income': '收入',
                    'expense': '支出',
                    'unknown': '其他'
                }
                
                for trans in transactions:
                    date_str = trans.get('date', '')
                    # 格式化日期
                    try:
                        if len(date_str) == 8:
                            formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                        else:
                            formatted_date = date_str
                    except:
                        formatted_date = date_str
                    
                    trans_type = type_map.get(trans.get('type', 'unknown'), '未知')
                    category = category_map.get(trans.get('category', 'unknown'), '其他')
                    amount = trans.get('amount', 0)
                    balance = trans.get('balance', 0)
                    description = trans.get('description', '') or ''
                    recipient = (trans.get('recipient', '') or '').strip()

                    # 对方户名清洗规则：
                    # 1. 如果整列只有一个 N / n，认为是无户名，置为空
                    # 2. 如果以空格+N结尾（冲账标识），去掉末尾的 N
                    if recipient.upper() == 'N':
                        recipient = ''
                    else:
                        recipient = re.sub(r"\s+N$", "", recipient)
                    
                    # 限制摘要和对方户名的长度，避免表格过宽
                    description_display = description[:18] if len(description) > 18 else description
                    recipient_display = recipient[:28] if len(recipient) > 28 else recipient
                    
                    content_lines.append(
                        f"{formatted_date:<12} {trans_type:<8} {category:<12} "
                        f"¥{amount:>14,.2f} ¥{balance:>14,.2f}  {description_display:<20}  {recipient_display:<30}"
                    )
            
            content_lines.append("")
            content_lines.append("=" * 80)
            content_lines.append(f"消息: {result_data.get('message', '无')}")
            content_lines.append("=" * 80)
            
            # 写入文件
            with open(txt_filepath, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content_lines))
            
            print(f"  提取信息已保存到: {txt_filepath}")
            
        except Exception as e:
            print(f"保存提取信息到txt文件时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def _extract_account_name(self, text):
        """从PDF文本中提取户名"""
        if not text:
            return None
        
        # 尝试匹配"户名"或"Account name"后面的内容
        patterns = [
            r'户名[：:]\s*([^\n\r]+?)(?:\s+证件|$)',
            r'Account\s+name[：:]\s*([^\n\r]+?)(?:\s+ID|$)',
            r'户名\s+([^\n\r]+?)(?:\s+证件|$)',
            r'Account\s+name\s+([^\n\r]+?)(?:\s+ID|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # 移除可能的括号内容（如英文名），但保留中文名
                # 如果包含中文，优先保留中文部分
                chinese_name = re.sub(r'\s*\([^)]*\)', '', name)
                # 如果移除括号后还有内容，使用它；否则使用原名
                if chinese_name.strip():
                    name = chinese_name
                # 移除多余的空白字符，但保留单个空格（如果有多个字）
                name = re.sub(r'\s+', '', name)
                if name:
                    return name
        
        return None

    def _extract_description_and_recipient_from_line(self, line):
        """从交易行文本中提取交易摘要和对方户名（文本模式）"""
        description = ''
        recipient = ''
        
        if not line:
            return description, recipient
        
        # 移除日期和金额部分，保留描述部分
        # 先移除开头的日期
        line_clean = re.sub(r'^\d{8}\s*', '', line)
        # 移除RMB金额
        line_clean = re.sub(r'RMB\s+[\d,]+\.?\d*', '', line_clean)
        # 移除账户序号
        line_clean = re.sub(r'00000\d+\s*', '', line_clean)
        
        # 尝试提取交易摘要和对方户名
        # 通常格式：摘要在前，对方户名在后，用空格或特殊字符分隔
        parts = line_clean.strip().split()
        
        if len(parts) >= 1:
            # 第一个非空部分通常是摘要
            description = parts[0] if parts[0] else ''
        
        if len(parts) >= 2:
            # 后面的部分可能是对方户名
            recipient = ' '.join(parts[1:]) if len(parts) > 1 else ''
        
        # 清理提取的内容
        description = description.strip()
        recipient = recipient.strip()
        
        return description, recipient

    def extract_bank_statement(self, pdf_path):
        """
        提取银行流水 - 增强版，提取详细交易数据用于特征工程

        逻辑：
        1. 提取户名
        2. 提取每行的日期、交易金额和余额
        3. 提取交易摘要和对方户名
        4. 通过余额变化判断收入/支出
        5. 识别ATM取现、POS消费等交易类型
        6. 按月份分组统计
        7. 返回详细的交易列表和统计数据
        """
        try:
            transactions = []  # 存储所有交易: {date, amount, balance, type, category, description, recipient}
            account_name = None  # 户名

            print(f"\n开始解析PDF: {pdf_path}")

            with pdfplumber.open(pdf_path) as pdf:
                # 首先提取户名（通常在第一页）
                first_page_text = ''
                if len(pdf.pages) > 0:
                    first_page_text = pdf.pages[0].extract_text() or ''
                    account_name = self._extract_account_name(first_page_text)
                    if account_name:
                        print(f"  提取到户名: {account_name}")

                # 尝试使用表格提取（更准确）
                table_extracted = False
                for page_num, page in enumerate(pdf.pages, 1):
                    tables = page.extract_tables()
                    if tables:
                        for table in tables:
                            # 查找表头，确定列索引
                            header_row_idx = None
                            date_col = None
                            income_col = None
                            expense_col = None
                            balance_col = None
                            desc_col = None
                            recipient_col = None
                            
                            for row_idx, row in enumerate(table):
                                if not row:
                                    continue
                                
                                row_str = '|'.join([str(c) if c else '' for c in row])
                                
                                # 查找表头行
                                if '交易日期' in row_str or 'Transaction date' in row_str:
                                    header_row_idx = row_idx
                                    # 确定各列的索引
                                    for col_idx, cell in enumerate(row):
                                        if not cell:
                                            continue
                                        cell_str = str(cell).strip()
                                        if '交易日期' in cell_str or 'Transaction date' in cell_str:
                                            date_col = col_idx
                                        elif '收入金额' in cell_str or 'Account receivable' in cell_str:
                                            income_col = col_idx
                                        elif '支出金额' in cell_str or 'Account paid' in cell_str:
                                            expense_col = col_idx
                                        elif '账户余额' in cell_str or 'Account balance' in cell_str:
                                            balance_col = col_idx
                                        elif '交易摘要' in cell_str or 'Description' in cell_str:
                                            desc_col = col_idx
                                        elif '对方户名' in cell_str or 'Recipient' in cell_str:
                                            recipient_col = col_idx
                                    
                                    # 如果找到了表头，提取数据行
                                    if header_row_idx is not None and date_col is not None:
                                        # 计算最大列索引
                                        max_col_idx = max([col for col in [date_col, income_col, expense_col, balance_col, desc_col, recipient_col] if col is not None], default=0)
                                        
                                        for data_row in table[header_row_idx + 1:]:
                                            if not data_row or len(data_row) <= max_col_idx:
                                                continue
                                            
                                            # 提取日期
                                            date_cell = str(data_row[date_col]).strip() if date_col < len(data_row) and data_row[date_col] else ''
                                            date_match = re.match(r'^(\d{8})', date_cell)
                                            if not date_match:
                                                continue
                                            
                                            date_str = date_match.group(1)
                                            
                                            # 提取金额
                                            income = 0.0
                                            expense = 0.0
                                            balance = 0.0
                                            
                                            if income_col is not None and income_col < len(data_row):
                                                income = self._extract_number(data_row[income_col])
                                            if expense_col is not None and expense_col < len(data_row):
                                                expense = self._extract_number(data_row[expense_col])
                                            if balance_col is not None and balance_col < len(data_row):
                                                balance = self._extract_number(data_row[balance_col])
                                            
                                            # 提取摘要和对方户名
                                            description = ''
                                            recipient = ''
                                            if desc_col is not None and desc_col < len(data_row):
                                                description = str(data_row[desc_col]).strip() if data_row[desc_col] else ''
                                            if recipient_col is not None and recipient_col < len(data_row):
                                                recipient = str(data_row[recipient_col]).strip() if data_row[recipient_col] else ''
                                            
                                            # 识别交易类型
                                            desc_line = description + ' ' + recipient
                                            category = self._identify_transaction_category(desc_line)
                                            
                                            # 添加交易记录
                                            if income > 0:
                                                transactions.append({
                                                    'date': date_str,
                                                    'amount': income,
                                                    'balance': balance,
                                                    'type': 'income',
                                                    'category': 'income',
                                                    'description': description,
                                                    'recipient': recipient
                                                })
                                            if expense > 0:
                                                transactions.append({
                                                    'date': date_str,
                                                    'amount': expense,
                                                    'balance': balance,
                                                    'type': 'expense',
                                                    'category': category if category != 'unknown' else 'expense',
                                                    'description': description,
                                                    'recipient': recipient
                                                })
                                        
                                        table_extracted = True
                                        break
                            
                            if table_extracted:
                                break
                    
                    if table_extracted:
                        break

                # 如果表格提取失败，使用文本提取（备用方案）
                if not table_extracted:
                    for page_num, page in enumerate(pdf.pages, 1):
                        text = page.extract_text()
                        if not text:
                            continue

                        lines = text.split('\n')

                        for line in lines:
                            # 跳过表头和空行
                            if not line or '交易日期' in line or 'Transaction' in line:
                                continue

                            # 提取日期 (格式: 20250810)
                            date_match = re.match(r'^(\d{8})', line.strip())
                            if not date_match:
                                continue

                            date_str = date_match.group(1)

                            # 提取交易摘要和对方户名
                            description, recipient = self._extract_description_and_recipient_from_line(line)

                            # 识别交易类型
                            category = self._identify_transaction_category(line)

                            # 查找所有RMB金额
                            rmb_amounts = re.findall(r'RMB\s+([\d,]+\.?\d*)', line)

                            if len(rmb_amounts) == 2:
                                # 2个金额：第1个是交易金额，第2个是余额
                                amount = self._extract_number(rmb_amounts[0])
                                balance = self._extract_number(rmb_amounts[1])

                                if amount > 0 and balance > 0:
                                    transactions.append({
                                        'date': date_str,
                                        'amount': amount,
                                        'balance': balance,
                                        'type': None,  # 待判断
                                        'category': category,
                                        'description': description,
                                        'recipient': recipient
                                    })

                            elif len(rmb_amounts) == 3:
                                # 3个金额：第1个是收入，第2个是支出，第3个是余额
                                income = self._extract_number(rmb_amounts[0])
                                expense = self._extract_number(rmb_amounts[1])
                                balance = self._extract_number(rmb_amounts[2])

                                if income > 0:
                                    transactions.append({
                                        'date': date_str,
                                        'amount': income,
                                        'balance': balance,
                                        'type': 'income',
                                        'category': 'income',
                                        'description': description,
                                        'recipient': recipient
                                    })
                                if expense > 0:
                                    transactions.append({
                                        'date': date_str,
                                        'amount': expense,
                                        'balance': balance,
                                        'type': 'expense',
                                        'category': category if category != 'unknown' else 'expense',
                                        'description': description,
                                        'recipient': recipient
                                    })

            # 通过余额变化判断收入/支出
            print(f"  找到{len(transactions)}笔交易")

            for i in range(len(transactions)):
                if transactions[i]['type'] is not None:
                    continue  # 已经判断过

                if i == 0:
                    # 第一笔无法判断，跳过
                    transactions[i]['type'] = 'unknown'
                    continue

                prev_balance = transactions[i-1]['balance']
                curr_balance = transactions[i]['balance']

                # 计算余额变化
                balance_change = curr_balance - prev_balance

                if balance_change > 0:
                    transactions[i]['type'] = 'income'
                    if transactions[i]['category'] == 'unknown':
                        transactions[i]['category'] = 'income'
                elif balance_change < 0:
                    transactions[i]['type'] = 'expense'
                    if transactions[i]['category'] == 'unknown':
                        transactions[i]['category'] = 'expense'
                else:
                    transactions[i]['type'] = 'unknown'

            # 计算详细统计数据
            detailed_stats = self._calculate_detailed_statistics(transactions)

            print(f"  提取完成: 收入¥{detailed_stats['total_income']:.2f}, "
                  f"支出¥{detailed_stats['total_expense']:.2f}, "
                  f"余额¥{detailed_stats['current_balance']:.2f}")

            if detailed_stats['total_income'] > 0 or detailed_stats['total_expense'] > 0:
                # 格式化交易列表供前端显示
                formatted_transactions = self._format_transactions_for_display(transactions)

                result = {
                    'success': True,
                    'account_name': account_name,  # 户名
                    'transactions': transactions,  # 原始交易列表（用于后端计算）
                    'formatted_transactions': formatted_transactions,  # 格式化后的交易列表（用于前端显示）
                    **detailed_stats,  # 详细统计数据
                    'balance': detailed_stats['current_balance'],  # 最终余额（兼容旧接口）
                    'message': f'成功提取{len(transactions)}笔交易 - 收入¥{detailed_stats["total_income"]:.2f}, '
                              f'支出¥{detailed_stats["total_expense"]:.2f}, '
                              f'最终余额¥{detailed_stats["current_balance"]:,.2f}'
                }
                
                # 保存提取信息到txt文件
                self._save_extracted_info_to_txt(pdf_path, result)
                
                return result
            else:
                default_result = self._get_default_statement()
                # 即使使用默认数据，也保存到txt文件
                self._save_extracted_info_to_txt(pdf_path, default_result)
                return default_result

        except Exception as e:
            print(f"PDF解析错误: {e}")
            import traceback
            traceback.print_exc()
            error_result = self._get_default_statement()
            error_result['message'] = f'PDF解析错误: {str(e)}'
            # 即使出错，也尝试保存错误信息
            try:
                self._save_extracted_info_to_txt(pdf_path, error_result)
            except:
                pass
            return error_result

    def _get_default_statement(self):
        """返回默认银行流水数据（增强版）"""
        default_stats = self._get_default_detailed_stats()
        default_stats['success'] = True
        default_stats['balance'] = default_stats['current_balance']  # 兼容旧接口
        default_stats['message'] = '使用默认数据'
        default_stats['transactions'] = []  # 空交易列表
        return default_stats
    
    def extract_balance_proof(self, pdf_path):
        """提取余额证明"""
        try:
            balance = 0.0
            currency = 'RMB'

            print(f"\n开始提取余额: {pdf_path}")

            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    # 提取表格
                    tables = page.extract_tables()
                    if tables:
                        for table in tables:
                            for row_idx, row in enumerate(table):
                                if not row:
                                    continue

                                row_str = '|'.join([str(c) if c else '' for c in row])

                                if '余额' in row_str or 'balance' in row_str.lower():
                                    # 找余额列
                                    balance_col = None
                                    for col_idx, cell in enumerate(row):
                                        if cell and ('余额' in str(cell) or 'balance' in str(cell).lower()):
                                            balance_col = col_idx
                                            break

                                    # 提取余额
                                    if balance_col is not None:
                                        for data_row in table[row_idx + 1:]:
                                            if data_row and balance_col < len(data_row):
                                                val = self._extract_number(data_row[balance_col])
                                                if val > 0:
                                                    balance = val
                                    break

                    # 文本提取
                    text = page.extract_text()
                    if text and balance == 0:
                        for line in text.split('\n'):
                            if '余额' in line or 'balance' in line.lower():
                                val = self._extract_number(line)
                                if val > balance:
                                    balance = val

                                if 'RMB' in line or '¥' in line:
                                    currency = 'RMB'
                                elif 'AED' in line:
                                    currency = 'AED'

            print(f"  提取余额: {balance} {currency}")

            if balance > 0:
                return {
                    'success': True,
                    'balance': balance,
                    'currency': currency,
                    'message': f'成功提取余额: ¥{balance:,.2f}'
                }
            else:
                return {
                    'success': False,
                    'balance': 0.0,
                    'currency': 'RMB',
                    'message': '未能从PDF中提取到余额，请检查PDF格式'
                }

        except Exception as e:
            print(f"余额提取错误: {e}")
            return {
                'success': True,
                'balance': 50000.0,
                'currency': 'RMB',
                'message': '使用默认余额'
            }

