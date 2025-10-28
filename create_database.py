import sqlite3

conn = sqlite3.connect("Puyuan.db")

cursor = conn.cursor()
cursor.execute("DROP TABLE IF EXISTS UserAuth")
cursor.execute(
    """
CREATE TABLE IF NOT EXISTS UserAuth(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account TEXT,  -- 移除 NOT NULL
    password TEXT NOT NULL,
    phone TEXT UNIQUE,  -- 移除 NOT NULL
    email TEXT NOT NULL UNIQUE,
    code TEXT,
    verified BOOLEAN DEFAULT false,
    privacy_policy BOOLEAN DEFAULT false,
    must_change_password BOOLEAN DEFAULT false,
    login_token TEXT, -- 存放登入 Token
    password_reset_token TEXT, -- 存放重設密碼 Token
    token_expire_at DATETIME, -- 存放 Token 的過期時間
    created_at DATETIME,
    updated_at DATETIME
);
"""
)


cursor.execute(
    """
CREATE TABLE IF NOT EXISTS UserProfile(
    id INTEGER PRIMARY KEY, 
    name TEXT,
    birthday DATE,
    height FLOAT,
    weight FLOAT,
    gender BOOLEAN,
    address TEXT,
    invitCode TEXT,
    badge INT,
    created_at DATETIME,
    updated_at DATETIME,
    FOREIGN KEY(id) REFERENCES UserAuth(id)
);                      
"""
)

cursor.execute(
    """
CREATE TABLE IF NOT EXISTS Friendship(
    id INTEGER PRIMARY KEY, 
    user_id INTEGER,
    friend_id INTEGER,
    status INT,
    created_at DATETIME,
    updated_at DATETIME,
    FOREIGN KEY(user_id) REFERENCES UserAuth(id), 
    FOREIGN KEY(friend_id) REFERENCES UserAuth(id)  
);                      
"""
)

cursor.execute(
    """
CREATE TABLE IF NOT EXISTS News (
    id INTEGER PRIMARY KEY AUTOINCREMENT, -- 唯一識別新聞的 ID
    member_id INTEGER,                    -- 發佈新聞的會員 ID
    `group` INTEGER,                      -- 分組 ID
    title TEXT NOT NULL,                  -- 消息標題
    message TEXT NOT NULL,                -- 消息內容
    pushed_at DATETIME,                   -- 消息推送時間
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- 消息建時間
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP  -- 消息更新時間
);                     
"""
)

cursor.execute(
    """
CREATE TABLE IF NOT EXISTS Share (
    id INTEGER PRIMARY KEY AUTOINCREMENT,        -- 分享記錄的唯一 ID
    fid VARCHAR(50) NOT NULL,                    -- 外部 ID (紀錄 ID)
    data_type INTEGER NOT NULL,                  -- 種類 (0:血壓; 1:體重; 2:血糖; 3:飲食; 4)
    relation_type INTEGER NOT NULL,              -- 關係類型 (1:親友; 2:糖友)
    user_id INTEGER,                             -- 分享者的使用者 ID
    shared_with_user_id INTEGER,                 -- 被分享對象的使用者 ID (選建)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- 分享建立時間
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- 分享更新時間
    FOREIGN KEY(user_id) REFERENCES UserAuth(id)
);
"""
)

cursor.execute(
    """
CREATE TABLE IF NOT EXISTS BloodPressure (
    id VARCHAR(50) PRIMARY KEY,               -- 唯一識別 ID
    user_id INTEGER NOT NULL,                 -- 使用者 ID
    systolic FLOAT NOT NULL,                  -- 收縮壓
    diastolic FLOAT NOT NULL,                 -- 舒張壓
    pulse FLOAT NOT NULL,                     -- 心跳
    recorded_at DATETIME NOT NULL,            -- 記錄時間
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- 創建時間
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- 更新時間
    FOREIGN KEY(user_id) REFERENCES UserAuth(id)
);
"""
)

cursor.execute(
    """
CREATE TABLE IF NOT EXISTS Weight (
    id VARCHAR(50) PRIMARY KEY,               -- 唯一識別 ID
    user_id INTEGER NOT NULL,                 -- 使用者 ID
    weight FLOAT NOT NULL,                    -- 體重
    body_fat FLOAT,                           -- 體脂肪
    bmi FLOAT,                                -- BMI
    recorded_at DATETIME NOT NULL,            -- 記錄時間
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- 創建時間
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- 更新時間
    FOREIGN KEY(user_id) REFERENCES UserAuth(id)
);
"""
)

cursor.execute(
    """
CREATE TABLE IF NOT EXISTS BloodSugar (
    id VARCHAR(50) PRIMARY KEY,               -- 唯一識別 ID
    user_id INTEGER NOT NULL,                 -- 使用者 ID
    sugar INTEGER NOT NULL,                   -- 血糖值
    timeperiod INTEGER NOT NULL,              -- 時段
    recorded_at DATETIME NOT NULL,            -- 記錄時間
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- 創建時間
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- 更新時間
    FOREIGN KEY(user_id) REFERENCES UserAuth(id)
);
"""
)

cursor.execute(
    """
CREATE TABLE IF NOT EXISTS DiaryDiet (
    id INTEGER PRIMARY KEY AUTOINCREMENT,     -- 唯一識別 ID (自動遞增)
    user_id INTEGER NOT NULL,                 -- 使用者 ID
    description VARCHAR(100),                 -- 描述
    meal INTEGER,                             -- 餐次
    tag VARCHAR(100),                         -- 標籤 (JSON 格式)
    image INTEGER,                            -- 照片數量
    lat REAL,                                 -- 緯度
    lng REAL,                                 -- 經度
    recorded_at DATETIME NOT NULL,            -- 記錄時間
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- 創建時間
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- 更新時間
    FOREIGN KEY(user_id) REFERENCES UserAuth(id)
);
"""
)

# ==================== 測量上傳相關資料表 ====================

cursor.execute(
    """
CREATE TABLE IF NOT EXISTS blood_pressure_records(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    systolic INTEGER NOT NULL,  -- 收縮壓
    diastolic INTEGER NOT NULL,  -- 舒張壓
    pulse INTEGER,  -- 脈搏
    measured_at DATETIME NOT NULL,  -- 測量時間
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES UserAuth(id)
);
"""
)

cursor.execute(
    """
CREATE TABLE IF NOT EXISTS weight_records(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    weight FLOAT NOT NULL,  -- 體重 (kg)
    bmi FLOAT,  -- BMI
    body_fat FLOAT,  -- 體脂率 (%)
    measured_at DATETIME NOT NULL,  -- 測量時間
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES UserAuth(id)
);
"""
)

cursor.execute(
    """
CREATE TABLE IF NOT EXISTS blood_sugar_records(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    glucose INTEGER NOT NULL,  -- 血糖值 (mg/dL)
    meal_time INTEGER NOT NULL,  -- 測量時段 (0:早上, 1:中午, 2:晚上)
    measured_at DATETIME NOT NULL,  -- 測量時間
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES UserAuth(id)
);
"""
)

cursor.execute(
    """
CREATE TABLE IF NOT EXISTS measurement_records(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    record_type INTEGER NOT NULL,  -- 記錄類型 (0:血壓, 1:體重, 2:血糖)
    record_id INTEGER NOT NULL,  -- 對應記錄的 ID
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,  -- 上傳時間
    FOREIGN KEY(user_id) REFERENCES UserAuth(id)
);
"""
)


conn.commit()

conn.close()

