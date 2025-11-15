import sqlite3
from datetime import datetime
import os
import json

class Database:
    """数据库操作类，管理所有数据库相关的增删改查操作"""

    def __init__(self, db_path='instance/fintech.db'):
        """初始化数据库连接"""
        self.db_path = db_path
    
    def get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 支持按列名访问
        return conn
    
    # ==================== 用户WECoin操作 ====================
    
    def get_user_wecoin(self, user_id):
        """
        获取用户当前的WECoin余额
        
        Args:
            user_id: 用户ID
            
        Returns:
            int: 用户的WECoin余额
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT wecoin FROM user WHERE id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        return result['wecoin'] if result else 0
    
    def deduct_wecoin(self, user_id, amount):
        """
        消耗用户的WECoin（抽奖/刷新消耗）
        
        Args:
            user_id: 用户ID
            amount: 消耗的WECoin数量
            
        Returns:
            bool: 是否成功扣除（如果余额不足则返回False）
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 检查余额是否足够
        current_wecoin = self.get_user_wecoin(user_id)
        if current_wecoin < amount:
            conn.close()
            return False
        
        # 更新WECoin
        cursor.execute('''
            UPDATE user
            SET wecoin = wecoin - ?
            WHERE id = ?
        ''', (amount, user_id))
        
        conn.commit()
        conn.close()
        return True
    
    def add_wecoin(self, user_id, amount):
        """
        增加用户的WECoin（奖励或返还）
        
        Args:
            user_id: 用户ID
            amount: 增加的WECoin数量
            
        Returns:
            bool: 是否成功增加
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE user
            SET wecoin = wecoin + ?
            WHERE id = ?
        ''', (amount, user_id))
        
        conn.commit()
        conn.close()
        return True
    
    # ==================== 奖品操作 ====================
    
    def get_reward(self, reward_id):
        """
        获取奖品信息
        
        Args:
            reward_id: 奖品ID
            
        Returns:
            dict: 奖品信息
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM reward WHERE id = ?', (reward_id,))
        result = cursor.fetchone()
        conn.close()
        
        return dict(result) if result else None
    
    def get_user_rewards(self, user_id, is_used=0):
        """
        获取用户的奖品包
        
        Args:
            user_id: 用户ID
            is_used: 是否已使用（0=未使用, 1=已使用, None=全部）
            
        Returns:
            list: 用户拥有的奖品列表
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if is_used is None:
            cursor.execute('''
                SELECT reward.*, user_reward.obtained_date, user_reward.is_used
                FROM reward
                JOIN user_reward ON reward.id = user_reward.reward_id
                WHERE user_reward.user_id = ?
                ORDER BY user_reward.obtained_date DESC
            ''', (user_id,))
        else:
            cursor.execute('''
                SELECT reward.*, user_reward.obtained_date, user_reward.is_used
                FROM reward
                JOIN user_reward ON reward.id = user_reward.reward_id
                WHERE user_reward.user_id = ? AND user_reward.is_used = ?
                ORDER BY user_reward.obtained_date DESC
            ''', (user_id, is_used))
        
        results = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in results]
    
    def mark_reward_as_used(self, user_id, reward_id):
        """
        标记奖品为已使用
        
        Args:
            user_id: 用户ID
            reward_id: 奖品ID
            
        Returns:
            bool: 是否成功标记
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE user_reward
            SET is_used = 1
            WHERE user_id = ? AND reward_id = ?
        ''', (user_id, reward_id))
        
        conn.commit()
        conn.close()
        return cursor.rowcount > 0
    
    # ==================== 抽奖次数 =====================
    def get_user_redeem_count(self, user_id):
        """
        获取用户今日可兑换（抽奖）次数
        
        Args:
            user_id: 用户ID
            
        Returns:
            int: 当前用户的可兑换次数，若未找到用户则返回0
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT redeem_today_count FROM user WHERE id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result['redeem_today_count'] if result else 0


    def deduct_redeem_count(self, user_id, amount=1):
        """
        扣除用户的抽奖次数
        
        Args:
            user_id: 用户ID
            amount: 扣除的次数（默认1）
            
        Returns:
            bool: 是否成功扣除（如果次数不足则返回False）
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        current_count = self.get_user_redeem_count(user_id)
        if current_count < amount:
            conn.close()
            return False
        
        cursor.execute('''
            UPDATE user
            SET redeem_today_count = redeem_today_count - ?
            WHERE id = ?
        ''', (amount, user_id))
        
        conn.commit()
        conn.close()
        return True


    def add_redeem_count(self, user_id, amount=1):
        """
        增加用户的抽奖次数（预留接口，用于后续活动奖励等）
        
        Args:
            user_id: 用户ID
            amount: 增加的次数（默认1）
            
        Returns:
            bool: 是否操作成功
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE user
            SET redeem_today_count = redeem_today_count + ?
            WHERE id = ?
        ''', (amount, user_id))
        conn.commit()
        conn.close()
        return True

    
    # ==================== 消费记录操作 ====================
    
    def add_transaction(self, user_id, amount, currency, converted_amount, rate, wecoin_earned=0):
        """
        添加消费记录
        
        Args:
            user_id: 用户ID
            amount: 消费金额
            currency: 消费币种
            converted_amount: 折算后的金额
            rate: 汇率
            wecoin_earned: 获得的WECoin
            
        Returns:
            bool: 是否成功添加
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO transactions (user_id, amount, currency, converted_amount, rate, wecoin_earned, spend_time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, amount, currency, converted_amount, rate, wecoin_earned, datetime.now()))
            
            # 如果产生WECoin奖励，增加用户WECoin
            if wecoin_earned > 0:
                self.add_wecoin(user_id, wecoin_earned)
            
            conn.commit()
            return True
        
        except Exception as e:
            conn.rollback()
            print(f'添加消费记录失败: {str(e)}')
            return False
        
        finally:
            conn.close()
    
    # ==================== 额度操作 ====================
    
    def update_available_limit(self, user_id, new_limit):
        """
        更新用户可用额度
        
        Args:
            user_id: 用户ID
            new_limit: 新的可用额度
            
        Returns:
            bool: 是否成功更新
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE credit
            SET available_limit = ?, updated_at = ?
            WHERE user_id = ?
        ''', (new_limit, datetime.now(), user_id))
        
        conn.commit()
        conn.close()
        return cursor.rowcount > 0
    
    # ==================== 通知操作 ====================
    
    def add_message(self, user_id, text, message_type='info'):
        """
        添加用户通知消息
        
        Args:
            user_id: 用户ID
            text: 消息文本
            message_type: 消息类型（promotion/bill/rate/info等）
            
        Returns:
            bool: 是否成功添加
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO message (user_id, text, type, is_read, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, text, message_type, 0, datetime.now()))
        
        conn.commit()
        conn.close()
        return True
    
    def get_user_messages(self, user_id):
        """
        获取用户的所有消息通知
        Args:
            user_id: 用户ID
        Returns:
            list[dict]: 包含消息的字典列表
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, text, type, is_read, created_at
            FROM message
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (user_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]


    def list_all_rewards(self):
            """
            列出所有 reward 表中的奖品（用于抽奖时读取基础概率与规则标记）
            返回 list of dict
            """
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT id, type, title, details, base_prob, new_user_only, code, extra_info FROM reward')
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]


    def get_reward_by_id(self, reward_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM reward WHERE id = ?', (reward_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None


    # ---- 授信相关 ----
    def get_credit_info(self, user_id):
        """
        获取用户授信信息（取最新一条）
        返回 dict: { 'total_limit': float, 'available_limit': float }
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT total_limit, available_limit
            FROM credit
            WHERE user_id = ?
            ORDER BY updated_at DESC
            LIMIT 1
        ''', (user_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return {'total_limit': 0.0, 'available_limit': 0.0}
        return {'total_limit': row['total_limit'] or 0.0, 'available_limit': row['available_limit'] or 0.0}


    # ---- 交易相关 ----
    def list_transactions(self, user_id):
        """
        返回用户的所有 transactions 列表（按时间降序）
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, amount, currency, converted_amount, rate, wecoin_earned, spend_time
            FROM transactions
            WHERE user_id = ?
            ORDER BY spend_time DESC
        ''', (user_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def aggregate_transactions(self, user_id):
        """
        计算交易汇总统计：
        - total_consume: 所有消费金额之和, 使用原始 amount
        - tx_count: 交易笔数
        - avg_tx: 平均单笔消费
        返回 dict
        """
        txs = self.list_transactions(user_id)
        if not txs:
            return {'total_consume': 0.0, 'tx_count': 0, 'avg_tx': 0.0}

        total = 0.0
        count = 0
        for t in txs:
            # 使用 amount
            val = t.get('amount') or 0.0
            total += float(val)
            count += 1

        avg = total / count if count > 0 else 0.0
        return {'total_consume': total, 'tx_count': count, 'avg_tx': avg}

    # ==================== Face ID 相关操作 ====================

    def update_user_face_encoding(self, user_id, face_encoding, face_image_path):
        """
        更新用户的人脸特征编码

        Args:
            user_id: 用户ID
            face_encoding: 人脸特征编码（128维向量的list）
            face_image_path: 人脸照片存储路径

        Returns:
            bool: 是否成功
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # 将编码转换为JSON字符串存储
            encoding_json = json.dumps(face_encoding)

            cursor.execute('''
                UPDATE user
                SET face_encoding = ?,
                    face_image_path = ?,
                    face_registered_at = ?
                WHERE id = ?
            ''', (encoding_json, face_image_path, datetime.now(), user_id))

            conn.commit()
            success = cursor.rowcount > 0
            conn.close()
            return success

        except Exception as e:
            conn.close()
            print(f"更新人脸编码失败: {e}")
            return False

    def get_user_face_encoding(self, user_id):
        """
        获取用户的人脸特征编码

        Args:
            user_id: 用户ID

        Returns:
            list or None: 人脸特征编码（128维向量）
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT face_encoding FROM user WHERE id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()

        if result and result['face_encoding']:
            try:
                return json.loads(result['face_encoding'])
            except:
                return None
        return None

    def get_all_face_encodings(self):
        """
        获取所有已注册Face ID的用户的人脸特征

        Returns:
            list: [
                {'user_id': 1, 'encoding': [...]},
                {'user_id': 2, 'encoding': [...]},
                ...
            ]
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, face_encoding
            FROM user
            WHERE face_encoding IS NOT NULL AND face_encoding != ''
        ''')

        results = cursor.fetchall()
        conn.close()

        encodings = []
        for row in results:
            try:
                encoding = json.loads(row['face_encoding'])
                encodings.append({
                    'user_id': row['id'],
                    'encoding': encoding
                })
            except:
                continue

        return encodings

    def check_user_has_face_id(self, user_id):
        """
        检查用户是否已注册Face ID

        Args:
            user_id: 用户ID

        Returns:
            bool: 是否已注册
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT face_encoding
            FROM user
            WHERE id = ? AND face_encoding IS NOT NULL AND face_encoding != ''
        ''', (user_id,))

        result = cursor.fetchone()
        conn.close()

        return result is not None

    def add_face_login_log(self, user_id, similarity_score, login_success, ip_address=''):
        """
        添加Face ID登录日志

        Args:
            user_id: 用户ID
            similarity_score: 相似度分数
            login_success: 是否登录成功（1成功，0失败）
            ip_address: IP地址
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO face_login_logs
            (user_id, similarity_score, login_success, ip_address)
            VALUES (?, ?, ?, ?)
        ''', (user_id, similarity_score, login_success, ip_address))

        conn.commit()
        conn.close()