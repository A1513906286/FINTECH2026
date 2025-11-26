import random
from datetime import datetime
import sqlite3
from utils.database import Database
from services.lottery_prob import draw_four_with_reduction


class LotteryMachine:
    """
    抽奖机类，管理盲盒抽奖的整个流程
    """
    
    WECOIN_COST_PER_FLIP = 10  # 每次翻卡消耗的WECoin
    CARDS_PER_DRAW = 4  # 每次刷新显示的卡片数量
    
    def __init__(self, db_path='instance/fintech.db'):
        """初始化抽奖机"""
        self.db = Database(db_path)
        self.db_path = db_path
    
    # ==================== 第一步：初始化抽奖卡片 ====================
    
    def generate_blind_box_cards(self, user_id):
        """
        为用户生成新的盲盒卡片（基于概率规则与权重调整，返回最多4张卡）
        
        说明：
        - 使用外部模块 lottery_prob.draw_four_with_reduction(db, user_id)
        计算并抽取 4 张奖品（放回抽样，但每次抽中某个奖品后，该奖品的后续权重会乘以0.6）
        - 不在此方法内扣除用户的 WECoin 或 抽奖次数（这些应由调用方在业务流程中先行处理）
        - 返回结构保持与你原来定义的一致，前端无需改动
        
        返回:
        {
        'success': bool,
        'message': str,
        'data': [ card_obj, ... ]  # card_obj 与之前结构一致
        }
        """
        try:
            # 1) 使用我们封装好的抽奖算法从 reward 表中抽取最多 4 个奖品（允许重复）
            #    draw_four_with_reduction 会返回 reward 行的 dict 列表（长度最多为4，可能包含 None）
            drawn_rewards = draw_four_with_reduction(self.db, user_id)

            if not drawn_rewards:
                return {
                    'success': False,
                    'message': '可用奖品不足或权重配置导致无法抽取',
                    'data': None
                }

            # 2) 生成卡片信息（和之前兼容）
            timestamp = int(datetime.now().timestamp() * 1000)  # 毫秒级时间戳
            cards = []
            index = 0

            for reward in drawn_rewards:
                # 如果抽取结果里出现 None（比如所有权重为0），跳过
                if not reward:
                    continue

                # 保证 reward 中有 id 与 type 字段（你在 reward 表里已有 id/type）
                reward_id = reward['id']
                reward_type = reward['type']
                if reward_id is None:
                    # 安全兜底：若数据异常则跳过此项
                    continue

                # 卡片唯一ID：保持原格式 {user_id}_{timestamp}_{index}
                card_id = f"{user_id}_{timestamp}_{index}"
                is_star = (reward_type == 'star')

                cards.append({
                    'id': card_id,
                    'index': index,
                    'flipped': False,
                    'reward_id': reward_id,
                    'reward_type': reward_type,
                    'is_star_card': bool(is_star)
                })

                # 如果已经达到了期望的卡片数（self.CARDS_PER_DRAW），可以提前退出
                if index >= getattr(self, 'CARDS_PER_DRAW', 4):
                    break

            if not cards:
                return {
                    'success': False,
                    'message': '未生成任何卡片（可能是所有奖品均被过滤或权重为0）',
                    'data': None
                }

            return {
                'success': True,
                'message': '卡片生成成功',
                'data': cards
            }

        except Exception as e:
            # 捕获并返回错误信息，便于前端/调试定位
            return {
                'success': False,
                'message': f'生成卡片异常: {str(e)}',
                'data': None
            }
    
    # ==================== 第二步：翻开卡片并消耗WECoin ====================
    
    def flip_card(self, user_id, card_id, reward_id):
        """
        用户翻开一张卡片，消耗WECoin并获取奖品
        
        调用时机：
        - 用户点击翻卡片
        
        Args:
            user_id: 用户ID
            card_id: 卡片唯一ID
            reward_id: 卡片背后的奖品ID
            
        Returns:
            dict: 包含翻卡结果的字典
                {
                    'success': bool,
                    'message': str,
                    'data': {
                        'user_id': int,
                        'card_id': str,
                        'reward_id': int,
                        'reward_title': str,
                        'reward_type': str,
                        'reward_details': str,
                        'current_wecoin': int,  # 翻卡后的WECoin余额
                        'flip_time': str
                    } if success else None
                }
        """
        try:
            # 1&2. 检查余额和消耗WECoin
            consume_result = self.consume_wecoin_for_flip(user_id)
            if not consume_result['success']:
                return consume_result
            
            # 3. 获取奖品信息
            reward_info = self.db.get_reward(reward_id)
            if not reward_info:
                return {
                    'success': False,
                    'message': '奖品不存在',
                    'data': None
                }
            
            # 4. 记录抽奖历史
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO blind_box_draw (user_id, draw_date, wecoin_cost, wecoin_returned, item)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, datetime.now(), self.WECOIN_COST_PER_FLIP, 0, reward_info['title']))
            
            # 5. 添加奖品到用户奖品包
            cursor.execute('''
                INSERT INTO user_reward (user_id, reward_id, obtained_date, is_used)
                VALUES (?, ?, ?, ?)
            ''', (user_id, reward_id, datetime.now(), 0))
            
            conn.commit()
            conn.close()
            
            # 6. 获取更新后的WECoin余额
            updated_wecoin = self.db.get_user_wecoin(user_id)
            
            return {
                'success': True,
                'message': '翻卡成功',
                'data': {
                    'user_id': user_id,
                    'card_id': card_id,
                    'reward_id': reward_id,
                    'reward_title': reward_info['title'],  # 奖品标题
                    'reward_type': reward_info['type'],  # 奖品类型
                    'reward_details': reward_info['details'],  # 奖品详情
                    'current_wecoin': updated_wecoin,  # 翻卡后的WECoin余额
                    'flip_time': datetime.now().isoformat()
                }
            }
        
        except Exception as e:
            return {
                'success': False,
                'message': f'翻卡失败: {str(e)}',
                'data': None
            }
        
    # 消耗WECoin
    def consume_wecoin_for_flip(self, user_id):
        """
        消耗用户的WECoin（抽奖/刷新消耗）
        """
        try:
            # 1. 检查用户WECoin余额
            current_wecoin = self.db.get_user_wecoin(user_id)
            if current_wecoin < self.WECOIN_COST_PER_FLIP:
                return {
                    'success': False,
                    'message': f'WECoin不足，需要{self.WECOIN_COST_PER_FLIP}个，当前余额为{current_wecoin}',
                    'data': None
                }
                
            # 2. 消耗WECoin
            if not self.db.deduct_wecoin(user_id, self.WECOIN_COST_PER_FLIP):
                return {
                    'success': False,
                    'message': 'WECoin扣除失败',
                    'data': None
                }
            return {
                'success': True,
                'message': 'WECoin扣除成功',
                'data': {
                    'current_wecoin': self.db.get_user_wecoin(user_id)
                }
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'WECoin扣除失败: {str(e)}',
                'data': None
            }

    # 消耗抽奖次数
    def consume_redeem_for_draw(self, user_id):
        """
        消耗用户的抽奖次数（每次抽奖或刷新消耗一次）
        
        Returns:
            dict: {
                'success': bool,
                'message': str,
                'data': { 'current_redeem_count': int } 或 None
            }
        """
        try:
            # 1. 获取用户当前抽奖次数
            current_redeem = self.db.get_user_redeem_count(user_id)
            if current_redeem <= 0:
                return {
                    'success': False,
                    'message': '今日抽奖次数已用完，请明日再试或通过任务增加次数',
                    'data': None
                }

            # 2. 扣除一次抽奖次数
            if not self.db.deduct_redeem_count(user_id, 1):
                return {
                    'success': False,
                    'message': '扣除抽奖次数失败，可能次数不足',
                    'data': None
                }

            # 3. 获取最新次数
            new_count = self.db.get_user_redeem_count(user_id)
            return {
                'success': True,
                'message': '抽奖次数扣除成功',
                'data': {
                    'current_redeem_count': new_count
                }
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'抽奖次数扣除出错: {str(e)}',
                'data': None
            }



    # ==================== 辅助方法 ====================
    
    def get_blind_box_data(self, user_id):
        """
        获取用户的盲盒相关数据
        
        Args:
            user_id: 用户ID
            
        Returns:
            dict: 包含盲盒数据的字典
                {
                    'current_wecoin': int,
                    'blind_box_history': [...]
                }
        """
        try:
            # 获取用户当前WECoin
            current_wecoin = self.db.get_user_wecoin(user_id)
            
            # 获取盲盒抽奖历史
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT draw_date, item, wecoin_returned
                FROM blind_box_draw
                WHERE user_id = ?
                ORDER BY draw_date DESC
            ''', (user_id,))
            history = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return {
                'current_wecoin': current_wecoin,
                'blind_box_history': history
            }
        
        except Exception as e:
            return {
                'current_wecoin': 0,
                'blind_box_history': []
            }
    
    def validate_card(self, card_id, reward_id):
        """
        验证卡片信息的合法性（可选的安全校验）
        
        Args:
            card_id: 卡片ID
            reward_id: 奖品ID
            
        Returns:
            bool: 卡片是否有效
        """
        # 这里可以添加额外的验证逻辑
        # 例如：检查卡片是否已被翻开、卡片是否过期等
        
        reward = self.db.get_reward(reward_id)
        return reward is not None
