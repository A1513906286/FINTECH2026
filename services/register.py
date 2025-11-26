# register.py
import sqlite3
import random
from datetime import datetime
from utils.database import Database

class RegistrationManager:
    """注册管理器，处理用户注册相关逻辑"""
    
    def __init__(self, db_path='instance/fintech.db'):
        self.db_path = db_path
        self.database = Database(db_path)
    
    def generate_card_prefix(self):
        """生成不重复的8位卡号前缀"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        while True:
            # 生成8位随机数字
            prefix = ''.join([str(random.randint(0, 9)) for _ in range(8)])
            
            # 检查是否已存在
            cursor.execute('SELECT id FROM user WHERE card_number LIKE ?', (f"{prefix}%",))
            if not cursor.fetchone():
                conn.close()
                return prefix
        
        conn.close()
    
    def get_next_user_id(self):
        """获取下一个可用的用户ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 查找最大用户ID
        cursor.execute('SELECT MAX(id) as max_id FROM user')
        result = cursor.fetchone()
        next_user_id = max(100001, (result['max_id'] or 0) + 1)
        
        conn.close()
        return next_user_id
    
    def complete_registration(self, card_suffix, expected_return_day, username='Yogurt', credit_limit=100000):
        """
        完成注册流程，创建新用户

        Args:
            card_suffix: 用户定制的后8位卡号
            expected_return_day: 返程日期 (YYYY-MM-DD格式)
            username: 用户名（默认为Yogurt）
            credit_limit: 预测的信用额度（默认100000）

        Returns:
            dict: 包含注册结果的字典
        """
        conn = None
        try:
            # 验证卡号后缀（必须是8位数字）
            card_suffix_clean = card_suffix.replace(' ', '')  # 移除空格
            if len(card_suffix_clean) != 8 or not card_suffix_clean.isdigit():
                return {
                    'success': False,
                    'message': '卡号后缀必须是8位数字'
                }

            # 生成完整卡号 - 保持4+4格式
            card_prefix = self.generate_card_prefix()
            # 将前8位也格式化为4+4格式
            formatted_prefix = f"{card_prefix[:4]} {card_prefix[4:]}"
            # 将后8位格式化为4+4格式
            formatted_suffix = f"{card_suffix_clean[:4]} {card_suffix_clean[4:]}"
            # 完整卡号：前8位(4+4) + 后8位(4+4)
            full_card_number = f"{formatted_prefix} {formatted_suffix}"

            # 用户信息（使用传入的用户名）
            avatar_initial = username[0].upper() if username else 'Y'
            fixed_user_info = {
                'username': username,
                'region': 'United Arab Emirates',
                'location_city': 'Abu Dhabi',
                'avatar_initial': avatar_initial,
                'landmark_image': 'halifata.png',
                'phone': '+971-50-1234567',
                'email': f'{username.lower()}@example.com'
            }
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建新用户 - 让数据库自动生成ID
            cursor.execute('''
                INSERT INTO user (username, card_number, region, location_city, 
                                avatar_initial, landmark_image, phone, email, 
                                wecoin, redeem_today_count, expected_return_day, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                fixed_user_info['username'],
                full_card_number,
                fixed_user_info['region'],
                fixed_user_info['location_city'],
                fixed_user_info['avatar_initial'],
                fixed_user_info['landmark_image'],
                fixed_user_info['phone'],
                fixed_user_info['email'],
                50,  # 初始WECoin
                5,    # 初始抽奖次数
                expected_return_day,
                datetime.now()
            ))
            
            # 获取新创建的用户ID
            new_user_id = cursor.lastrowid
            
            # 创建授信额度记录（使用预测的额度）
            cursor.execute('''
                INSERT INTO credit (user_id, total_limit, available_limit, updated_at)
                VALUES (?, ?, ?, ?)
            ''', (new_user_id, credit_limit, credit_limit, datetime.now()))
            
            # 创建初始汇率记录
            cursor.execute('''
                INSERT INTO exchange_rate (pair, value, updated_at)
                VALUES (?, ?, ?)
            ''', ("UAE/HKD", 1.97, datetime.now()))
            
            conn.commit()
            
            return {
                'success': True,
                'message': '注册成功',
                'data': {
                    'user_id': new_user_id,
                    'username': fixed_user_info['username'],
                    'card_number': full_card_number,
                    'credit_limit': credit_limit
                }
            }
            
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"注册失败错误: {str(e)}")  # 添加详细错误日志
            return {
                'success': False,
                'message': f'注册失败: {str(e)}'
            }
        finally:
            if conn:
                conn.close()

# 创建全局实例
registration_manager = RegistrationManager()