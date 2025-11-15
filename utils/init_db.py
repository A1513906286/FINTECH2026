import sqlite3
from datetime import datetime, timedelta
import os

# 数据库文件夹和文件名
DB_DIR = os.path.join(os.path.dirname(__file__), 'instance')
DB_NAME = os.path.join(DB_DIR, 'fintech.db')

# 如果 instance 文件夹不存在则创建
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

# 连接数据库
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# 1. 用户表
cursor.execute('''
CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    card_number TEXT,
    region TEXT,
    location_city TEXT,
    avatar_initial TEXT,
    landmark_image TEXT,
    phone TEXT,
    email TEXT,
    wecoin INTEGER DEFAULT 0,
    redeem_today_count INTEGER DEFAULT 5,
    expected_return_day TEXT,
    created_at DATETIME,
    face_encoding TEXT,
    face_image_path TEXT,
    face_registered_at DATETIME
)
''')

# 2. 授信额度表
cursor.execute('''
CREATE TABLE IF NOT EXISTS credit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    total_limit REAL,
    available_limit REAL,
    updated_at DATETIME,
    FOREIGN KEY(user_id) REFERENCES user(id)
)
''')

# 3. 消费记录表
cursor.execute('''
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    amount REAL,
    currency TEXT,
    converted_amount REAL,
    rate REAL,
    wecoin_earned INTEGER,
    spend_time DATETIME,
    FOREIGN KEY(user_id) REFERENCES user(id)
)
''')

# 4. 抽奖/盲盒记录表
cursor.execute('''
CREATE TABLE IF NOT EXISTS blind_box_draw (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    draw_date DATETIME,
    wecoin_cost INTEGER,
    wecoin_returned INTEGER,
    item TEXT,
    FOREIGN KEY(user_id) REFERENCES user(id)
)
''')

# 5. 奖品表（reward）
cursor.execute('''
CREATE TABLE IF NOT EXISTS reward (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT,            -- 奖品类型（coupon / merchant / rate / star）
    title TEXT,           -- 奖品名称
    details TEXT,         -- 奖品描述
    base_prob REAL,       -- 基础概率（实验阶段用于调试）
    new_user_only INTEGER, -- 新用户专享标记（1=仅新用户，0=所有用户）
    code TEXT,            -- 奖品业务编码，用于识别奖品具体逻辑
    extra_info TEXT       -- 额外信息（如汇率券的关键字占位等）
)
''')


# 6. 用户奖品包
cursor.execute('''
CREATE TABLE IF NOT EXISTS user_reward (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    reward_id INTEGER,
    obtained_date DATETIME,
    is_used INTEGER,
    FOREIGN KEY(user_id) REFERENCES user(id),
    FOREIGN KEY(reward_id) REFERENCES reward(id)
)
''')

# 7. 汇率表
cursor.execute('''
CREATE TABLE IF NOT EXISTS exchange_rate (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pair TEXT,
    value REAL,
    updated_at DATETIME
)
''')

# 8. 消息通知表
cursor.execute('''
CREATE TABLE IF NOT EXISTS message (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    text TEXT,
    type TEXT,
    is_read INTEGER,
    created_at DATETIME,
    FOREIGN KEY(user_id) REFERENCES user(id)
)
''')

# 9. Face ID登录日志表
cursor.execute('''
CREATE TABLE IF NOT EXISTS face_login_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    similarity_score REAL,
    login_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    login_success INTEGER,
    ip_address TEXT,
    FOREIGN KEY (user_id) REFERENCES user(id)
)
''')

# 插入模拟用户数据
cursor.execute('''
INSERT INTO user (username, card_number, region, location_city, avatar_initial, landmark_image, wecoin, redeem_today_count, created_at)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
''', (
    "Yogurt", "5210 7132 0767 1316", "United Arab Emirates", "Abu Dhabi", "Y", "halifata.png", 200, 10, datetime.now()
))
user_id = cursor.lastrowid

# 插入授信额度
cursor.execute('''
INSERT INTO credit (user_id, total_limit, available_limit, updated_at)
VALUES (?, ?, ?, ?)
''', (user_id, 100000, 95000.00, datetime.now()- timedelta(days=30)) )

# 插入汇率
cursor.execute('''
INSERT INTO exchange_rate (pair, value, updated_at)
VALUES (?, ?, ?)
''', ("UAE/HKD", 1.97, datetime.now()))

# 插入账单（消费记录）
cursor.execute('''
INSERT INTO transactions (user_id, amount, currency, converted_amount, rate, wecoin_earned, spend_time)
VALUES (?, ?, ?, ?, ?, ?, ?)
''', (user_id, 188, "UAE", 401.50, 1.97, 10, datetime.now()))

# small_transactions = [
#         # 小额多笔消费，平均约150
#         (user_id, 120, "UAE", 120, 1.0, 6, datetime.now() - timedelta(days=5)),
#         (user_id, 180, "UAE", 180, 1.0, 9, datetime.now() - timedelta(days=10)),
#         (user_id, 90, "UAE", 90, 1.0, 4, datetime.now() - timedelta(days=15)),
#         (user_id, 210, "UAE", 210, 1.0, 10, datetime.now() - timedelta(days=20)),
#     ]
# cursor.executemany('''
# INSERT INTO transactions (user_id, amount, currency, converted_amount, rate, wecoin_earned, spend_time)
# VALUES (?, ?, ?, ?, ?, ?, ?)
# ''', small_transactions)

# 插入盲盒抽奖记录
blind_box_history = [
    (user_id, "2025-11-11", 10, 200, "满10-1 消费券"),
    (user_id, "2025-11-10", 10, 0, "汇率 1.96 优惠"),
    (user_id, "2025-11-09", 10, 0, "星星卡 x1")
]
cursor.executemany('''
INSERT INTO blind_box_draw (user_id, draw_date, wecoin_cost, wecoin_returned, item)
VALUES (?, ?, ?, ?, ?)
''', blind_box_history)

# 插入奖品
# 奖品有四种类型：消费券(spend)、汇率(rate)、合作商户通用券(partner)、星星卡(star)
default_rewards = [
    # type, title, details, base_prob, new_user_only, code, extra_info
    ("coupon", "新用户满10-10 消费券", "新用户可用", 0.10, 1, "coupon_new_10_10", None),
    ("coupon", "新用户满50-25 消费券", "新用户可用", 0.15, 1, "coupon_new_50_25", None),
    ("coupon", "新用户满100-30 消费券", "新用户可用", 0.20, 1, "coupon_new_100_30", None),
    ("coupon", "满100-20 消费券", "满减券", 0.15, 0, "coupon_100_20", None),
    ("coupon", "满50-10 消费券", "满减券", 0.10, 0, "coupon_50_10", None),
    ("merchant", "合作商户通用八折券", "八折券", 0.20, 0, "merchant_80", None),
    ("rate", "汇率券", "模型动态生成汇率", 0.10, 0, "rate_dynamic", "rate_dynamic"),
    ("star", "星星卡", "稀有卡片", 0.30, 0, "star_card", None),
]

cursor.executemany('''
INSERT INTO reward(type, title, details, base_prob, new_user_only, code, extra_info)
VALUES (?, ?, ?, ?, ?, ?, ?)
''', default_rewards)



# 插入用户奖品包（假设全部未使用）
for i in range(1, 7):
    cursor.execute('''
    INSERT INTO user_reward (user_id, reward_id, obtained_date, is_used)
    VALUES (?, ?, ?, ?)
    ''', (user_id, i, datetime.now(), 0))

# 插入消息通知
messages = [
    (user_id, "迪拜 Atalas Shopping Mall多家品牌联合折扣，最高可享30% discount", "recommend", 0, datetime.now()),
    (user_id, "您的账单已生成，请及时查看。", "bill", 0, datetime.now()),
    (user_id, "新汇率提醒: UAE/HKD 1.96", "rate", 0, datetime.now())
]
cursor.executemany('''
INSERT INTO message (user_id, text, type, is_read, created_at)
VALUES (?, ?, ?, ?, ?)
''', messages)

conn.commit()
conn.close()

print("数据库创建并初始化数据成功！")
