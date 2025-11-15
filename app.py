from flask import Flask, render_template, request, jsonify, session
import sqlite3
from datetime import datetime
import random
import os
import base64
from utils.database import Database
from services.lottery import LotteryMachine
from services.register import registration_manager
from services.face_service import FaceRecognitionService
from services.pdf_service import PDFService
from services.credit_limit_service import CreditLimitService
from services.abu_dhabi_service import AbuDhabiService

# 告诉 Flask 你的 static 文件夹在 'templates/static'
app = Flask(__name__, static_folder='templates/static', static_url_path='/static')
app.secret_key = 'anappleadaythedoctorkeepsalway'  # 用于session加密

# 数据库路径
DB_PATH = 'instance/fintech.db'

# 初始化数据库操作类和抽奖机
db = Database(DB_PATH)
lottery_machine = LotteryMachine(DB_PATH)
face_service = FaceRecognitionService()
pdf_service = PDFService()
credit_limit_service = CreditLimitService()
# 阿布扎比推荐服务
# 参数说明:
#   use_proxy=True: 启用代理（需要Clash等代理工具运行）
#   use_proxy=False: 不使用代理（直连）
#   proxy_url: 代理地址（默认Clash端口7890）
abu_dhabi_service = AbuDhabiService(
    model_name="llama3.2:3b",
    use_proxy=True,  # 改为False可禁用代理
    proxy_url="http://127.0.0.1:7890"  # Clash默认端口
)

# 创建上传文件夹
UPLOAD_FOLDER = 'uploads/faces'
PDF_UPLOAD_FOLDER = 'uploads/pdfs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PDF_UPLOAD_FOLDER, exist_ok=True)

# 用于存储注册过程中的临时数据
registration_temp_data = {}

# 增加用户ID获取
def get_current_user_id():
    """获取当前登录用户的ID，如果没有登录则使用默认用户ID=1"""
    return session.get('user_id', 1)  # 默认使用用户ID=1

# 定义一个路由：当用户访问主页 ("/") 时，执行这个函数
@app.route('/')
def home():
    """
    提供主页并传入动态数据。
    """
    # 当前用户 ID，通过会话管理进行动态获取
    current_user_id = get_current_user_id()
    
    # 连接数据库
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 使用 Row 对象，支持按列名访问
    cursor = conn.cursor()

    # 查询用户数据
    cursor.execute('''
        SELECT username, card_number, region, location_city, avatar_initial, landmark_image
        FROM user
        WHERE id = ?
    ''', (current_user_id,))
    user_row = cursor.fetchone()


    # 如果用户不存在，使用默认值
    if not user_row:
        user_data = {
            "name": "Guest",
            "avatar_initial": "G",
            "balance": "0.00",
            "card_number": "未设置",
            "region": "未设置",
            "landmark_image": "default.png",
            "location_city": "未设置",
            "wecoin": 0
        }
    else:
        # 查询授信余额 - 添加默认值处理
        cursor.execute('''
            SELECT available_limit
            FROM credit
            WHERE user_id = ?
        ''', (current_user_id,))
        credit_row = cursor.fetchone()
        available_limit = credit_row['available_limit'] if credit_row else 0

        user_data = {
            "name": user_row['username'],  # 用户名
            "avatar_initial": user_row['avatar_initial'],  # 头像首字母
            "balance": f"{available_limit:,.2f}",  # 当前信用卡授信余额
            "card_number": user_row['card_number'],  # 信用卡号
            "region": user_row['region'],  # 用户所在地区
            "landmark_image": user_row['landmark_image'],  # 地标图片文件名
            "location_city": user_row['location_city'],  # 用户所在城市
            "wecoin": db.get_user_wecoin(current_user_id) or 0  # 添加默认值
        }

    # 查询汇率数据 - 添加默认值处理
    cursor.execute('''
        SELECT pair, value
        FROM exchange_rate
        ORDER BY updated_at DESC
        LIMIT 1
    ''')
    rate_row = cursor.fetchone()
    rate_data = {
        "pair": rate_row['pair'] if rate_row else "USD/CNY",  # 默认汇率对
        "value": f"{rate_row['value']:.2f}" if rate_row else "7.20"  # 默认汇率值
    }

    # 查询账单数据
    cursor.execute('''
        SELECT amount, currency, converted_amount
        FROM transactions
        WHERE user_id = ?
        ORDER BY spend_time DESC
        LIMIT 1
    ''', (current_user_id,))
    bill_row = cursor.fetchone()
    bill_data = {
        "last_spend": f"{bill_row['amount']:.2f}" if bill_row else "0.00",  # 上次消费金额
        "last_spend_currency": bill_row['currency'] if bill_row else "USD",  # 上次消费币种
        "converted_spend": f"{bill_row['converted_amount']:.2f}" if bill_row else "0.00"  # 经过汇率折算后的消费金额
    }

    # 查询授信额度数据
    cursor.execute('''
        SELECT total_limit
        FROM credit
        WHERE user_id = ?
    ''', (current_user_id,))
    limit_row = cursor.fetchone()
    total_limit = limit_row['total_limit'] if limit_row else 0 # 
    limit_data = {
        "current_limit": f"{int(total_limit):,}"  # 当前信用卡授信额度
    }

    # 查询消息通知
    raw_messages = db.get_user_messages(current_user_id) or []

    messages = []
    for msg in raw_messages:
        messages.append({
            "text": msg["text"],
            "long": len(msg["text"]) > 20,  # 保留原本long字段
            "type": msg.get("type", "default")  # 给前端点击跳转用
        })


    # 查询活动数据（计算公式：  saved_value = sum(单笔消费 * (用户初始汇率 - 用户消费时汇率))）
    # 暂时使用模拟数据，计算规则待明确
    activity_data = {
        "saved_value": 15,  # 已经节省的外币金额
        "saved_currency": "USD",  # 已经节省的外币币种
        "saved_rmb": 30  # 已经节省的人民币金额
    }

    # 获取用户数据抽奖相关信息
    cursor.execute('SELECT wecoin, redeem_today_count FROM user WHERE id = ?', (current_user_id,))
    user_info = cursor.fetchone()

    # 查询盲盒兑换历史
    cursor.execute('''
        SELECT draw_date, item
        FROM blind_box_draw
        WHERE user_id = ?
        ORDER BY draw_date DESC
    ''', (current_user_id,))
    blind_box_history = cursor.fetchall()

    # 
    wecoin_balance = user_info['wecoin'] if user_info else 0
    redeem_count = user_info['redeem_today_count'] if user_info else 0

    blind_box_data = {
        "wecoin_returned": wecoin_balance,  # 从数据库获取
        "redeem_today_count": redeem_count,  # 从数据库获取
        "game_rules": "点击拉绳消耗 10 WECoin 刷新盲盒。AI 将根据您的消费偏好和活跃度为您抽取惊喜奖励，包括汇率优惠、消费券及稀有星星卡。",
        "redeem_history": [
            {"date": row['draw_date'], "item": row['item']} for row in blind_box_history
        ]
    }

    # blind_box_data = {
    #     "wecoin_returned": user_info['wecoin'],  # 从数据库获取
    #     "redeem_today_count": user_info['redeem_today_count'],  # 从数据库获取
    #     "game_rules": "点击拉绳消耗 10 WECoin 刷新盲盒。AI 将根据您的消费偏好和活跃度为您抽取惊喜奖励，包括汇率优惠、消费券及稀有星星卡。",
    #     "redeem_history": [
    #         {"date": row['draw_date'], "item": row['item']} for row in blind_box_history
    #     ]
    # }


    # 查询用户奖品包（用于"我的奖券包"弹窗），只有优惠券类型的奖品会出现在这里
    cursor.execute('''
        SELECT reward.type, reward.title, reward.details
        FROM reward
        JOIN user_reward ON reward.id = user_reward.reward_id
        WHERE user_reward.user_id = ? AND user_reward.is_used = 0
    ''', (current_user_id,))
    coupons_data = [
        {"type": row['type'], "title": row['title'], "details": row['details']} for row in cursor.fetchall()
    ]

    # 模拟的探索趋势数据（这部分会从AI获取，数据库暂不做考量）
    trends_data = [
        {"platform": "xiaohongshu", "text": "小红书博主推荐：阿布扎比 5 个小众拍照圣地"},
        {"platform": "sale", "text": "Atalas Shopping Mall 正在进行 30% 折扣活动，最高可享30% discount"},
        {"platform": "hotel", "text": "合作酒店推广：XX 酒店海景房套餐，入住即送 WECoin"}
    ]

    conn.close()

    # 将所有数据打包传入 render_template
    return render_template(
        'index.html',
        user=user_data,
        rate=rate_data,
        bill=bill_data,
        limit=limit_data,
        messages=messages,
        activity=activity_data,
        blind_box=blind_box_data, 
        coupons=coupons_data,
        trends=trends_data,
        current_user_id=current_user_id
    )


# ==================== 抽奖相关接口 ====================

@app.route('/api/generate_blind_box', methods=['POST'])
def generate_blind_box():
    """
    生成新的盲盒卡片（随机选择4个奖品）
    
    前端请求参数:
    {
        'user_id': int
    }
    
    响应数据:
    {
        'success': bool,
        'message': str,
        'data': [
            {
                'id': str,
                'index': int,
                'flipped': bool,
                'reward_id': int,
                'reward_type': str,
                'is_star_card': bool
            },
            ...
        ]
    }
    """
    try:
        data = request.get_json()
        user_id = data.get('user_id', get_current_user_id()) #
        
        result = lottery_machine.generate_blind_box_cards(user_id)
        return jsonify(result), 200 if result['success'] else 400
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'生成盲盒失败: {str(e)}',
            'data': None
        }), 500


@app.route('/api/flip_card', methods=['POST'])
def flip_card():
    """
    用户翻开一张卡片，消耗WECoin并获取奖品
    
    前端请求参数:
    {
        'user_id': int,
        'card_id': str,
        'reward_id': int
    }
    
    响应数据:
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
            'current_wecoin': int,
            'flip_time': str
        }
    }
    """
    try:
        data = request.get_json()
        user_id = data.get('user_id', get_current_user_id()) #
        card_id = data.get('card_id')
        reward_id = data.get('reward_id')
        
        # 验证必要参数
        if not card_id or not reward_id:
            return jsonify({
                'success': False,
                'message': '缺少必要参数（card_id 或 reward_id）',
                'data': None
            }), 400
        
        result = lottery_machine.flip_card(user_id, card_id, reward_id)
        return jsonify(result), 200 if result['success'] else 400
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'翻卡失败: {str(e)}',
            'data': None
        }), 500


@app.route('/api/get_blind_box_data/<int:user_id>', methods=['GET'])
def get_blind_box_data(user_id):
    """
    获取用户的盲盒相关数据（WECoin余额和历史记录）
    
    响应数据:
    {
        'success': bool,
        'data': {
            'current_wecoin': int,
            'blind_box_history': [...]
        }
    }
    """
    try:
        result = lottery_machine.get_blind_box_data(user_id)
        return jsonify({
            'success': True,
            'data': result
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取数据失败: {str(e)}'
        }), 500


# 消耗用户 WECoin 的接口
@app.route('/api/consume_wecoin_for_flip', methods=['POST'])
def consume_wecoin_for_flip():
    """
    消耗用户的WECoin（抽奖/刷新消耗）
    请求 body: { "user_id": 1 }
    响应:
    {
      'success': bool,
      'message': str,
      'data': { 'current_wecoin': int } 或 null
    }
    """
    try:
        data = request.get_json(force=True, silent=True)
        if not data or 'user_id' not in data:
            return jsonify({
                'success': False,
                'message': '缺失 user_id',
                'data': None
            }), 400

        user_id = int(data['user_id'])
        result = lottery_machine.consume_wecoin_for_flip(user_id)

        # 返回状态: 若业务失败返回 400 更明确（可按需调整为 200 并用 success 字段区分）
        return jsonify(result), 200 if result.get('success') else 400

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'消耗WECoin失败: {str(e)}',
            'data': None
        }), 500


@app.route('/api/get_user_wecoin/<int:user_id>', methods=['GET'])
def get_user_wecoin(user_id):
    """
    获取用户当前的WECoin余额
    
    响应数据:
    {
        'success': bool,
        'data': {
            'user_id': int,
            'wecoin': int
        }
    }
    """
    try:
        wecoin = db.get_user_wecoin(user_id)
        return jsonify({
            'success': True,
            'data': {
                'user_id': user_id,
                'wecoin': wecoin
            }
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取WECoin失败: {str(e)}'
        }), 500


@app.route('/api/get_user_rewards/<int:user_id>', methods=['GET'])
def get_user_rewards_api(user_id):
    """
    获取用户的奖品包（未使用的奖品）
    
    响应数据:
    {
        'success': bool,
        'data': [
            {
                'id': int,
                'type': str,
                'title': str,
                'details': str,
                'obtained_date': str
            },
            ...
        ]
    }
    """
    try:
        rewards = db.get_user_rewards(user_id, is_used=0)
        return jsonify({
            'success': True,
            'data': rewards
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取奖品包失败: {str(e)}'
        }), 500


@app.route('/api/get_blind_box_history/<int:user_id>', methods=['GET'])
def get_blind_box_history(user_id):
    """
    获取用户的盲盒抽奖历史
    
    响应数据:
    {
        'success': bool,
        'data': [
            {
                'draw_date': str,
                'item': str,
                'wecoin_returned': int
            },
            ...
        ]
    }
    """
    try:
        conn = sqlite3.connect(DB_PATH)
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
        
        return jsonify({
            'success': True,
            'data': history
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取历史记录失败: {str(e)}'
        }), 500
    
@app.route('/api/consume_redeem_for_draw', methods=['POST'])
def consume_redeem_for_draw():
    """
    消耗用户的抽奖次数
    
    请求:
        { "user_id": 1 }
    
    响应:
        {
            "success": bool,
            "message": str,
            "data": {
                "current_redeem_count": int
            } 或 None
        }
    """
    try:
        data = request.get_json(force=True, silent=True)
        if not data or 'user_id' not in data:
            return jsonify({
                'success': False,
                'message': '缺少 user_id',
                'data': None
            }), 400

        user_id = int(data['user_id'])
        result = lottery_machine.consume_redeem_for_draw(user_id)
        return jsonify(result), 200 if result['success'] else 400

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'消耗抽奖次数失败: {str(e)}',
            'data': None
        }), 500



# --- (修改) 为登录页面添加路由 ---
@app.route('/login')
def login():
    """
    提供登录/注册页面。
    """
    # [新增] 模拟一个用户数据，至少包含名字
    user_data = {
        "name": "Yogurt",
        "avatar_initial": "Y",
        "balance": "18,234.50",
        "card_number": "5210 7132 0767 1316",
        "region": "United Arab Emirates",
        "landmark_image": "halifata.png",
        "location_city": "Abu Dhabi"
    }
    
    # [修改] 将 user_name 传递给模板
    return render_template('login.html', user_name=user_data['name'], location_city=user_data['location_city'])
# --- 结束 修改 ---

# 模拟的全局用户数据 (方便多页面使用)
MOCK_USER_DATA = {
    "name": "Yogurt",
    "avatar_initial": "Y",
    "balance": "18,234.50",
    "card_number": "5210 7132 0767 1316",
    "region": "United Arab Emirates",
    "landmark_image": "halifata.png",
    "location_city": "Abu Dhabi"
}

# --- (新增) 为注册页面添加路由 ---
@app.route('/register')
def register():
    """
    提供新的注册页面。
    """
    # 注册页面也需要用户名 (Hi, Yogurt)
    return render_template(
        'register.html', 
        user_name=MOCK_USER_DATA['name']
    )


@app.route('/api/complete_registration', methods=['POST'])
def complete_registration():
    """
    完成注册流程，创建新用户
    请求参数:
    {
        "username": "用户名",  # 新增
        "card_suffix": "后8位卡号",  # 用户定制的后8位
        "expected_return_day": "返程日期",  # YYYY-MM-DD格式
        "face_image": "base64编码的人脸图片"  # 可选
    }
    """
    try:
        data = request.get_json()

        # 验证必要参数
        if not data.get('username') or not data.get('card_suffix') or not data.get('expected_return_day'):
            return jsonify({
                'success': False,
                'message': '缺少必要参数'
            }), 400

        # 获取预测的信用额度
        session_id = session.get('temp_registration_id')
        credit_limit = 100000  # 默认额度

        if session_id and session_id in registration_temp_data:
            credit_limit = registration_temp_data[session_id].get('predicted_credit_limit', 100000)
            print(f"使用预测额度: {credit_limit}")
        else:
            print("使用默认额度: 100000")

        # 使用注册管理器处理注册
        result = registration_manager.complete_registration(
            data['card_suffix'],
            data['expected_return_day'],
            data.get('username'),  # 传递用户名
            credit_limit  # 传递预测的额度
        )

        if result['success']:
            # 注册成功，设置session为当前用户
            user_id = result['data']['user_id']
            session['user_id'] = user_id
            print(f"注册成功，用户ID: {user_id}")

            # 如果有Face ID数据，注册Face ID
            face_image = data.get('face_image')
            if face_image:
                try:
                    # 提取人脸特征
                    face_result = face_service.register_face(face_image)

                    if face_result['success']:
                        # 保存人脸照片
                        image_data = base64.b64decode(face_image)
                        image_filename = f'user_{user_id}_face.jpg'
                        image_path = os.path.join(UPLOAD_FOLDER, image_filename)

                        with open(image_path, 'wb') as f:
                            f.write(image_data)

                        # 保存人脸特征到数据库
                        db.update_user_face_encoding(
                            user_id=user_id,
                            face_encoding=face_result['encoding'],
                            face_image_path=image_path
                        )
                        print(f"Face ID注册成功，用户ID: {user_id}")
                    else:
                        print(f"Face ID注册失败: {face_result['message']}")

                except Exception as e:
                    print(f"Face ID处理失败: {str(e)}")
                    # Face ID失败不影响注册流程

        status_code = 200 if result['success'] else 400
        return jsonify(result), status_code

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'注册失败: {str(e)}'
        }), 500
# --- 结束 新增 ---


# ==================== Face ID 相关API ====================

@app.route('/test_face_id')
def test_face_id():
    """Face ID测试页面"""
    return render_template('test_face_id.html')


@app.route('/api/register_face', methods=['POST'])
def register_face():
    """
    注册人脸

    请求体: {
        "image": "base64编码的图片",
        "user_id": 用户ID
    }
    """
    try:
        data = request.get_json()
        image_base64 = data.get('image')
        user_id = data.get('user_id')

        if not image_base64 or not user_id:
            return jsonify({
                'success': False,
                'message': '缺少必要参数'
            }), 400

        # 检查用户是否已注册Face ID
        if db.check_user_has_face_id(user_id):
            return jsonify({
                'success': False,
                'message': '该用户已注册Face ID'
            }), 400

        # 提取人脸特征
        result = face_service.register_face(image_base64)

        if not result['success']:
            return jsonify(result), 400

        # 保存人脸照片
        image_data = base64.b64decode(image_base64)
        image_filename = f'user_{user_id}_face.jpg'
        image_path = os.path.join(UPLOAD_FOLDER, image_filename)

        with open(image_path, 'wb') as f:
            f.write(image_data)

        # 保存人脸特征到数据库
        success = db.update_user_face_encoding(
            user_id=user_id,
            face_encoding=result['encoding'],
            face_image_path=image_path
        )

        if success:
            return jsonify({
                'success': True,
                'message': 'Face ID注册成功！'
            })
        else:
            return jsonify({
                'success': False,
                'message': '保存人脸数据失败'
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'注册失败: {str(e)}'
        }), 500


@app.route('/api/login_with_face', methods=['POST'])
def login_with_face():
    """
    Face ID登录

    请求体: {
        "image": "base64编码的图片"
    }
    """
    try:
        # 检查face_recognition库是否可用
        try:
            import face_recognition
        except ImportError:
            return jsonify({
                'success': False,
                'message': 'Face ID功能未启用，请先安装依赖: pip install face_recognition'
            }), 503

        data = request.get_json()
        image_base64 = data.get('image')

        if not image_base64:
            return jsonify({
                'success': False,
                'message': '缺少图片数据'
            }), 400

        print(f"[Face ID] 收到登录请求，图片大小: {len(image_base64)} bytes")

        # 获取所有已注册用户的人脸特征
        all_encodings = db.get_all_face_encodings()

        if not all_encodings:
            print("[Face ID] 暂无已注册用户")
            return jsonify({
                'success': False,
                'message': '暂无已注册Face ID的用户，请先注册'
            }), 400

        print(f"[Face ID] 找到 {len(all_encodings)} 个已注册用户")

        # 搜索匹配的人脸
        result = face_service.search_face(image_base64, all_encodings)

        if result['success']:
            user_id = result['user_id']
            similarity = result['similarity']

            print(f"[Face ID] 匹配成功 - 用户ID: {user_id}, 相似度: {similarity:.1f}%")

            # 记录登录日志
            db.add_face_login_log(
                user_id=user_id,
                similarity_score=similarity,
                login_success=1,
                ip_address=request.remote_addr
            )

            # 创建session
            session['user_id'] = user_id

            return jsonify({
                'success': True,
                'user_id': user_id,
                'similarity': similarity,
                'message': result['message']
            })
        else:
            print(f"[Face ID] 匹配失败: {result['message']}")

            # 记录失败日志
            db.add_face_login_log(
                user_id=None,
                similarity_score=0,
                login_success=0,
                ip_address=request.remote_addr
            )

            return jsonify(result), 401

    except Exception as e:
        print(f"[Face ID] 错误: {str(e)}")
        import traceback
        traceback.print_exc()

        return jsonify({
            'success': False,
            'message': f'Face ID登录失败: {str(e)}'
        }), 500


@app.route('/api/check_face_id/<int:user_id>', methods=['GET'])
def check_face_id(user_id):
    """
    检查用户是否已注册Face ID
    """
    try:
        has_face_id = db.check_user_has_face_id(user_id)

        return jsonify({
            'success': True,
            'has_face_id': has_face_id
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


# ==================== 用户设置相关API ====================

@app.route('/api/update_username', methods=['POST'])
def update_username():
    """
    修改用户名
    请求体: {
        "username": "新用户名"
    }
    """
    try:
        user_id = get_current_user_id()
        data = request.get_json()
        new_username = data.get('username', '').strip()

        if not new_username:
            return jsonify({
                'success': False,
                'message': '用户名不能为空'
            }), 400

        if len(new_username) < 2:
            return jsonify({
                'success': False,
                'message': '用户名至少2个字符'
            }), 400

        # 更新数据库
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('UPDATE user SET username = ? WHERE id = ?', (new_username, user_id))
        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'message': '用户名修改成功'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'修改失败: {str(e)}'
        }), 500


@app.route('/api/update_password', methods=['POST'])
def update_password():
    """
    修改密码（目前为占位符，实际项目需要密码加密）
    请求体: {
        "password": "新密码"
    }
    """
    try:
        user_id = get_current_user_id()
        data = request.get_json()
        new_password = data.get('password', '').strip()

        if not new_password:
            return jsonify({
                'success': False,
                'message': '密码不能为空'
            }), 400

        if len(new_password) < 6:
            return jsonify({
                'success': False,
                'message': '密码至少6个字符'
            }), 400

        # TODO: 实际项目中应该加密密码
        # 这里只是占位符，暂时不实际保存密码

        return jsonify({
            'success': True,
            'message': '密码修改成功'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'修改失败: {str(e)}'
        }), 500


# ==================== PDF上传和额度预测API ====================

@app.route('/api/upload_bank_statement', methods=['POST'])
def upload_bank_statement():
    """
    上传银行流水PDF
    """
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': '没有上传文件'
            }), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({
                'success': False,
                'message': '文件名为空'
            }), 400

        # 保存文件
        filename = f'bank_statement_{datetime.now().strftime("%Y%m%d%H%M%S")}.pdf'
        filepath = os.path.join(PDF_UPLOAD_FOLDER, filename)
        file.save(filepath)

        # 提取流水信息
        result = pdf_service.extract_bank_statement(filepath)

        # 存储到临时数据（使用session ID作为key）
        session_id = session.get('temp_registration_id', str(datetime.now().timestamp()))
        session['temp_registration_id'] = session_id

        if session_id not in registration_temp_data:
            registration_temp_data[session_id] = {}

        registration_temp_data[session_id]['total_income'] = result['total_income']
        registration_temp_data[session_id]['total_expense'] = result['total_expense']

        return jsonify({
            'success': True,
            'message': result['message'],
            'data': {
                'total_income': result['total_income'],
                'total_expense': result['total_expense'],
                'total_transactions': result['total_transactions']
            }
        })

    except Exception as e:
        print(f"银行流水上传错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'上传失败: {str(e)}'
        }), 500


@app.route('/api/upload_balance_proof', methods=['POST'])
def upload_balance_proof():
    """
    上传余额证明PDF
    """
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': '没有上传文件'
            }), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({
                'success': False,
                'message': '文件名为空'
            }), 400

        # 保存文件
        filename = f'balance_proof_{datetime.now().strftime("%Y%m%d%H%M%S")}.pdf'
        filepath = os.path.join(PDF_UPLOAD_FOLDER, filename)
        file.save(filepath)

        # 提取余额信息
        result = pdf_service.extract_balance_proof(filepath)

        # 存储到临时数据
        session_id = session.get('temp_registration_id', str(datetime.now().timestamp()))
        session['temp_registration_id'] = session_id

        if session_id not in registration_temp_data:
            registration_temp_data[session_id] = {}

        registration_temp_data[session_id]['balance'] = result['balance']
        registration_temp_data[session_id]['currency'] = result['currency']

        return jsonify({
            'success': True,
            'message': result['message'],
            'data': {
                'balance': result['balance'],
                'currency': result['currency']
            }
        })

    except Exception as e:
        print(f"余额证明上传错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'上传失败: {str(e)}'
        }), 500


@app.route('/api/predict_credit_limit', methods=['POST'])
def predict_credit_limit():
    """
    预测信用额度（简化版：只需总收入和余额）
    """
    try:
        # 从临时数据中获取信息
        session_id = session.get('temp_registration_id')

        if not session_id or session_id not in registration_temp_data:
            # 如果没有数据，使用默认值
            result = credit_limit_service.get_default_credit_limit()
        else:
            temp_data = registration_temp_data[session_id]

            total_income = temp_data.get('total_income', 74707.66)
            balance = temp_data.get('balance', 4204.74)

            # 预测额度
            result = credit_limit_service.predict_credit_limit(
                total_income=total_income,
                balance=balance
            )

        if result['success']:
            # 存储预测结果
            if session_id and session_id in registration_temp_data:
                registration_temp_data[session_id]['predicted_credit_limit'] = result['credit_limit']

        return jsonify(result)

    except Exception as e:
        print(f"额度预测错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'预测失败: {str(e)}'
        }), 500


@app.route('/logout')
def logout():
    """退出登录"""
    session.clear()
    return render_template('login.html', user_name='Guest', location_city='Abu Dhabi')


# ==================== 阿布扎比推荐API ====================

@app.route('/api/abu_dhabi_recommendations', methods=['GET'])
def get_abu_dhabi_recommendations():
    """
    获取阿布扎比推荐信息
    """
    try:
        recommendations = abu_dhabi_service.generate_recommendations()
        return jsonify({
            'success': True,
            'recommendations': recommendations,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        print(f"获取推荐失败: {str(e)}")
        # 返回默认推荐
        return jsonify({
            'success': True,
            'recommendations': abu_dhabi_service._get_default_recommendations(),
            'timestamp': datetime.now().isoformat()
        })





# 确保当你直接运行这个脚本时，服务器会启动
if __name__ == '__main__':
    app.run(debug=True)
