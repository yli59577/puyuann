-- 將 Puyuan.db 調整為規格書「資料庫設計v2」的資料表 / 欄位命名
-- 舊表資料會搬到 V2 表，再刪除舊表與未使用的重複表。只需執行一次。
-- 為了維持 API 回傳的 JSON 不變，主鍵沿用 INTEGER 自動編號、數值欄位沿用原本型別。
-- 不在 V2 但 API 需要的表保留：verification_codes、News、measurement_records

PRAGMA foreign_keys = OFF;
BEGIN;

-- ---- 血壓 BloodPressure（原 blood_pressure_records，measured_at → recorded_at）----
DROP TABLE IF EXISTS BloodPressure;
CREATE TABLE BloodPressure (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    systolic INTEGER NOT NULL,
    diastolic INTEGER NOT NULL,
    pulse INTEGER,
    recorded_at DATETIME NOT NULL,
    created_at DATETIME,
    updated_at DATETIME
);
INSERT INTO BloodPressure (id, user_id, systolic, diastolic, pulse, recorded_at, created_at, updated_at)
SELECT id, user_id, systolic, diastolic, pulse, measured_at, created_at, updated_at FROM blood_pressure_records;
CREATE INDEX ix_BloodPressure_user_id ON BloodPressure (user_id);

-- ---- 體重 Weight（原 weight_records）----
DROP TABLE IF EXISTS Weight;
CREATE TABLE Weight (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    weight FLOAT NOT NULL,
    body_fat FLOAT,
    bmi FLOAT,
    recorded_at DATETIME NOT NULL,
    created_at DATETIME,
    updated_at DATETIME
);
INSERT INTO Weight (id, user_id, weight, body_fat, bmi, recorded_at, created_at, updated_at)
SELECT id, user_id, weight, body_fat, bmi, measured_at, created_at, updated_at FROM weight_records;
CREATE INDEX ix_Weight_user_id ON Weight (user_id);

-- ---- 血糖 BloodSugar（原 blood_sugar_records，glucose → sugar、meal_time → timeperiod）----
DROP TABLE IF EXISTS BloodSugar;
CREATE TABLE BloodSugar (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    sugar INTEGER NOT NULL,
    timeperiod INTEGER NOT NULL,
    recorded_at DATETIME NOT NULL,
    created_at DATETIME,
    updated_at DATETIME
);
INSERT INTO BloodSugar (id, user_id, sugar, timeperiod, recorded_at, created_at, updated_at)
SELECT id, user_id, glucose, meal_time, measured_at, created_at, updated_at FROM blood_sugar_records;
CREATE INDEX ix_BloodSugar_user_id ON BloodSugar (user_id);

-- ---- 糖化血色素 HbA1c（原 a1c_records）----
DROP TABLE IF EXISTS HbA1c;
CREATE TABLE HbA1c (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    a1c VARCHAR(50) NOT NULL,
    recorded_at DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO HbA1c (id, user_id, a1c, recorded_at, created_at, updated_at)
SELECT id, user_id, a1c, recorded_at, created_at, updated_at FROM a1c_records;
CREATE INDEX ix_HbA1c_user_id ON HbA1c (user_id);

-- ---- 就醫資訊 MedicalInfo（原 medical_info）----
DROP TABLE IF EXISTS MedicalInfo;
CREATE TABLE MedicalInfo (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE,
    oad INTEGER DEFAULT 0,
    insulin INTEGER DEFAULT 0,
    anti_hypertensives INTEGER DEFAULT 0,
    diabetes_type INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO MedicalInfo (id, user_id, oad, insulin, anti_hypertensives, diabetes_type, created_at, updated_at)
SELECT id, user_id, oad, insulin, anti_hypertensives, diabetes_type, created_at, updated_at FROM medical_info;

-- ---- 藥物資訊 DrugInfo（原 drug_used，name → drugname、type → drug_type）----
DROP TABLE IF EXISTS DrugInfo;
CREATE TABLE DrugInfo (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    drugname VARCHAR(100) NOT NULL,
    drug_type INTEGER NOT NULL,
    recorded_at DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO DrugInfo (id, user_id, drugname, drug_type, recorded_at, created_at, updated_at)
SELECT id, user_id, name, type, recorded_at, created_at, updated_at FROM drug_used;
CREATE INDEX ix_DrugInfo_user_id ON DrugInfo (user_id);

-- ---- 個人預設值 Default、個人設定 Setting（原 UserDefaults、UserSettings，欄位相同）----
INSERT INTO "Default" SELECT * FROM UserDefaults WHERE user_id NOT IN (SELECT user_id FROM "Default");
INSERT INTO Setting SELECT * FROM UserSettings WHERE user_id NOT IN (SELECT user_id FROM Setting);

-- ---- 用戶個資 UserProfile（invite_code → inviteCode）----
ALTER TABLE UserProfile RENAME COLUMN invite_code TO inviteCode;

-- ---- 控糖團 Friend（原 friend_requests，user_id → userId、relation_id → relationId、type → friend_type）----
DROP TABLE IF EXISTS Friend;
CREATE TABLE Friend (
    id INTEGER PRIMARY KEY,
    userId INTEGER NOT NULL,
    relationId INTEGER NOT NULL,
    friend_type INTEGER NOT NULL,
    status INTEGER DEFAULT 0,
    read INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO Friend (id, userId, relationId, friend_type, status, read, created_at, updated_at)
SELECT id, user_id, relation_id, type, status, read, created_at, updated_at FROM friend_requests;
CREATE INDEX ix_Friend_userId ON Friend (userId);
CREATE INDEX ix_Friend_relationId ON Friend (relationId);

-- ---- 親友團通知 Notification（V2 新增）----
CREATE TABLE IF NOT EXISTS Notification (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    member_id INTEGER,
    reply_id INTEGER,
    message VARCHAR(100),
    created_at DATETIME,
    updated_at DATETIME
);

-- ---- 刪除舊表與未使用的重複表 ----
DROP TABLE blood_pressure_records;
DROP TABLE weight_records;
DROP TABLE blood_sugar_records;
DROP TABLE a1c_records;
DROP TABLE medical_info;
DROP TABLE drug_used;
DROP TABLE UserDefaults;
DROP TABLE UserSettings;
DROP TABLE friend_requests;
DROP TABLE cares;
DROP TABLE care_info;
DROP TABLE DiaryDietImage;
DROP TABLE alembic_version;

COMMIT;
PRAGMA foreign_keys = ON;
VACUUM;
