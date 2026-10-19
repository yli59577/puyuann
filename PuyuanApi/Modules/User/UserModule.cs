using System.Data;
using System.Text.Json;
using Dapper;
using PuyuanApi.Core;
using PuyuanApi.Core.PyCompat;

namespace PuyuanApi.Modules.User;

/// <summary>個人資訊模組（對應 app/_user/module.py 的 UserModule）</summary>
public class UserModule(Database db, ILogger logger)
{
    /// <summary>
    /// 從 Authorization Header 中解析用戶 ID（與 Python 版相同：必須剛好是 "Bearer &lt;token&gt;"）。
    /// 解析失敗或 id 為 0 回傳 null。
    /// </summary>
    public static int? ParseUserIdFromToken(string? authorization, Security security, ILogger logger)
    {
        if (string.IsNullOrEmpty(authorization))
        {
            logger.LogWarning("缺少 Authorization header");
            return null;
        }

        var parts = authorization.Split(' ');
        if (parts.Length != 2)
        {
            logger.LogError("Token 處理錯誤: Authorization 格式錯誤");
            return null;
        }
        if (parts[0] != "Bearer")
        {
            logger.LogWarning("Token 類型錯誤: {TokenType}", parts[0]);
            return null;
        }

        var userId = security.VerifyToken(parts[1]);
        if (userId is null)
        {
            logger.LogWarning("Token 解析失敗: 簽名驗證失敗或格式錯誤");
            return null;
        }
        return userId == 0 ? null : userId; // Python 端以 `if not user_id` 判斷
    }

    /// <summary>
    /// 查詢用戶基本認證資料（SQLAlchemy 載入時會解析 DateTime，格式錯誤丟出 ValueError，這裡照做）
    /// </summary>
    public static UserAuthRow? GetUser(IDbConnection conn, long userId, IDbTransaction? tx = null)
    {
        var user = conn.QueryFirstOrDefault<UserAuthRow>(UserAuthRow.SelectSql + " WHERE id = @userId LIMIT 1", new { userId }, tx);
        user?.ParseDates();
        return user;
    }

    /// <summary>查詢用戶基本認證資料</summary>
    public UserAuthRow? GetUser(long userId)
    {
        using var conn = db.Open();
        return GetUser(conn, userId);
    }

    /// <summary>創建或更新用戶個人資料（update_data 包含所有欄位，未提供的會被設成 NULL）</summary>
    public bool CreateOrUpdateProfile(long userId, UserProfileUpdate data, double? height, double? weight)
    {
        try
        {
            var birthday = ToBirthdayValue(data.Birthday);
            logger.LogDebug("開始更新，user_id={UserId}", userId);

            using var conn = db.Open();
            using var tx = conn.BeginTransaction();

            var profileId = conn.ExecuteScalar<long?>(
                "SELECT id FROM UserProfile WHERE user_id = @userId LIMIT 1", new { userId }, tx);

            if (profileId is null)
            {
                logger.LogDebug("找不到現有 profile，創建新的");
                var now = PyOrm.SqlaDateTime(TimeUtil.TaiwanNow());
                profileId = conn.ExecuteScalar<long>(
                    """
                    INSERT INTO UserProfile (user_id, badge, created_at, updated_at) VALUES (@userId, 0, @now, @now);
                    SELECT last_insert_rowid();
                    """, new { userId, now }, tx);
            }
            else
            {
                logger.LogDebug("找到現有 profile，id={ProfileId}", profileId);
            }

            var parameters = new DynamicParameters(new
            {
                data.Name, data.Gender, height, weight,
                data.Phone, data.Address, data.Avatar, data.FcmId,
                now = PyOrm.SqlaDateTime(TimeUtil.TaiwanNow()), profileId,
            });
            // birthday 依實際型別綁定（int / float / str），由 SQLite 的 TEXT affinity 轉成文字，與 Python 相同
            parameters.Add("birthday", birthday);

            conn.Execute(
                """
                UPDATE UserProfile
                SET name = @Name, gender = @Gender, birthday = @birthday, height = @height, weight = @weight,
                    phone = @Phone, address = @Address, avatar = @Avatar, fcm_id = @FcmId, updated_at = @now
                WHERE id = @profileId
                """, parameters, tx);

            tx.Commit();
            logger.LogDebug("成功提交");
            return true;
        }
        catch (Exception e)
        {
            logger.LogError(e, "更新個人資料錯誤: {Message}", e.Message);
            return false;
        }
    }

    /// <summary>創建或更新用戶設定（只更新有提供的欄位；只有 after_recording / no_recording_for_a_day 是實際欄位）</summary>
    public bool CreateOrUpdateSettings(long userId, UserSettingsUpdate data)
    {
        try
        {
            using var conn = db.Open();
            using var tx = conn.BeginTransaction();

            var settings = conn.QueryFirstOrDefault(
                "SELECT id, after_recording, no_recording_for_a_day FROM UserSettings WHERE user_id = @userId LIMIT 1",
                new { userId }, tx) as IDictionary<string, object?>;

            if (settings is null)
            {
                // 新建：未提供的布林欄位預設 False (0)
                var now = PyOrm.SqlaDateTime(TimeUtil.TaiwanNow());
                conn.Execute(
                    """
                    INSERT INTO UserSettings (user_id, after_recording, no_recording_for_a_day, over_max_or_under_min,
                                              after_meal, unit_of_sugar, unit_of_weight, unit_of_height, created_at, updated_at)
                    VALUES (@userId, @afterRecording, @noRecording, 0, 0, 0, 0, 0, @now, @now)
                    """,
                    new
                    {
                        userId,
                        afterRecording = data.AfterRecordingSet ? data.AfterRecording : false,
                        noRecording = data.NoRecordingForADaySet ? data.NoRecordingForADay : false,
                        now,
                    }, tx);
            }
            else
            {
                // SQLAlchemy 只在值有變動時才發出 UPDATE（並觸發 updated_at 的 onupdate）
                static bool? AsBool(object? v) => v is null ? null : PyOrm.Truthy(v);
                var sets = new List<string>();
                if (data.AfterRecordingSet && AsBool(settings["after_recording"]) != data.AfterRecording)
                    sets.Add("after_recording = @AfterRecording");
                if (data.NoRecordingForADaySet && AsBool(settings["no_recording_for_a_day"]) != data.NoRecordingForADay)
                    sets.Add("no_recording_for_a_day = @NoRecordingForADay");

                if (sets.Count > 0)
                {
                    conn.Execute(
                        $"UPDATE UserSettings SET {string.Join(", ", sets)}, updated_at = @now WHERE id = @id",
                        new
                        {
                            data.AfterRecording, data.NoRecordingForADay,
                            now = PyOrm.SqlaDateTime(TimeUtil.TaiwanNow()), id = settings["id"],
                        }, tx);
                }
            }

            tx.Commit();
            return true;
        }
        catch (Exception e)
        {
            logger.LogError(e, "更新設定錯誤: {Message}", e.Message);
            return false;
        }
    }

    /// <summary>
    /// 獲取用戶所有相關資料，組合成一個字典（與 Python 版 get_user_complete_data 相同的 key 與值）。
    /// 發生任何錯誤（包含 DateTime 解析失敗）回傳 null。
    /// </summary>
    public Dictionary<string, object?>? GetUserCompleteData(long userId)
    {
        try
        {
            logger.LogDebug("開始獲取用戶資料，user_id={UserId}", userId);
            using var conn = db.Open();

            var userAuth = GetUser(conn, userId);
            if (userAuth is null)
            {
                logger.LogWarning("找不到 UserAuth，user_id={UserId}", userId);
                return null;
            }
            var (authCreated, authUpdated) = userAuth.ParseDates();

            var profile = QueryRow(conn,
                "SELECT phone, name, gender, birthday, height, weight, address, invite_code, badge, avatar, created_at, updated_at FROM UserProfile WHERE user_id = @userId LIMIT 1",
                userId);
            if (profile is null) logger.LogWarning("找不到 UserProfile，user_id={UserId}", userId);

            // 獲取用戶預設值
            var defaults = QueryRow(conn, "SELECT * FROM UserDefaults WHERE user_id = @userId LIMIT 1", userId);
            object D(string col) => defaults?[col] ?? 0L;
            var defaultData = new Dictionary<string, object?>
            {
                ["id"] = defaults?["id"] ?? 0L,
                ["user_id"] = userId,
                ["sugar_morning_max"] = D("sugar_morning_max"),
                ["sugar_morning_min"] = D("sugar_morning_min"),
                ["sugar_evening_max"] = D("sugar_evening_max"),
                ["sugar_evening_min"] = D("sugar_evening_min"),
                ["sugar_before_max"] = D("sugar_before_max"),
                ["sugar_before_min"] = D("sugar_before_min"),
                ["sugar_after_max"] = D("sugar_after_max"),
                ["sugar_after_min"] = D("sugar_after_min"),
                ["systolic_max"] = D("systolic_max"),
                ["systolic_min"] = D("systolic_min"),
                ["diastolic_max"] = D("diastolic_max"),
                ["diastolic_min"] = D("diastolic_min"),
                ["pulse_max"] = D("pulse_max"),
                ["pulse_min"] = D("pulse_min"),
                ["weight_max"] = D("weight_max"),
                ["weight_min"] = D("weight_min"),
                ["bmi_max"] = D("bmi_max"),
                ["bmi_min"] = D("bmi_min"),
                ["body_fat_max"] = D("body_fat_max"),
                ["body_fat_min"] = D("body_fat_min"),
                ["created_at"] = IsoOrEmpty(defaults, "created_at"),
                ["updated_at"] = IsoOrEmpty(defaults, "updated_at"),
            };

            // 獲取用戶設定（所有欄位使用預設值，避免 Swift 解析失敗）
            var settings = QueryRow(conn, "SELECT * FROM UserSettings WHERE user_id = @userId LIMIT 1", userId);
            long S(string col) => settings is not null && PyOrm.Truthy(settings[col]) ? 1 : 0;
            var settingData = new Dictionary<string, object?>
            {
                ["id"] = settings?["id"] ?? 0L,
                ["user_id"] = userId,
                ["after_recording"] = S("after_recording"),
                ["no_recording_for_a_day"] = S("no_recording_for_a_day"),
                ["over_max_or_under_min"] = S("over_max_or_under_min"),
                ["after_meal"] = S("after_meal"),
                ["unit_of_sugar"] = S("unit_of_sugar"),
                ["unit_of_weight"] = S("unit_of_weight"),
                ["unit_of_height"] = S("unit_of_height"),
                ["created_at"] = IsoOrEmpty(settings, "created_at"),
                ["updated_at"] = IsoOrEmpty(settings, "updated_at"),
            };

            // 找不到 UserProfile 時，所有欄位視為 None
            object? P(string col) => profile?[col];

            var userData = new Dictionary<string, object?>
            {
                // 從 UserAuth 獲取
                ["id"] = userAuth.Id,
                ["account"] = PyOrm.Or(userAuth.Account, ""),
                ["email"] = PyOrm.Or(userAuth.Email, ""),
                ["phone"] = PyOrm.Or(P("phone"), ""),
                ["google_id"] = PyOrm.Or(userAuth.GoogleId, ""),
                ["apple_id"] = PyOrm.Or(userAuth.AppleId, ""),
                ["login_times"] = PyOrm.Or(userAuth.LoginTimes, 0L),
                ["verified"] = PyOrm.Truthy(userAuth.Verified) ? 1L : 0L,
                ["privacy_policy"] = PyOrm.Truthy(userAuth.PrivacyPolicy) ? 1L : 0L,
                ["must_change_password"] = PyOrm.Truthy(userAuth.MustChangePassword) ? 1L : 0L,

                // 從 UserProfile 獲取
                ["name"] = PyOrm.Or(P("name"), ""),
                ["gender"] = P("gender") ?? 0L,
                ["birthday"] = PyOrm.Or(P("birthday"), ""),
                ["height"] = PyOrm.Or(P("height"), 0.0),
                ["weight"] = PyOrm.Or(P("weight"), 0.0),
                ["address"] = PyOrm.Or(P("address"), ""),
                ["invite_code"] = PyOrm.Or(P("invite_code"), ""),
                // Python 版另有 "inviteCode"，但 UserProfileData 沒有此欄位，輸出時會被 pydantic 丟掉
                ["badge"] = PyOrm.Or(P("badge"), 0L),
                ["avatar"] = PyOrm.Or(P("avatar"), ""),

                // 固定或暫時性欄位
                ["group"] = "",
                ["unread_records"] = new List<long> { 0, 0, 0 },
                ["status"] = "0",
                ["vip"] = new Dictionary<string, object?>
                {
                    ["id"] = 0L,
                    ["user_id"] = userId,
                    ["level"] = 0L,
                    ["started_at"] = "",
                    ["ended_at"] = "",
                    ["remark"] = 0.0,
                    ["created_at"] = "",
                    ["updated_at"] = "",
                },

                // 時間戳欄位
                ["created_at"] = authCreated?.IsoFormat() ?? "",
                ["updated_at"] = authUpdated?.IsoFormat() ?? "",

                ["default"] = defaultData,
                ["setting"] = settingData,
            };

            logger.LogDebug("成功組合用戶資料");
            return userData;
        }
        catch (Exception e)
        {
            logger.LogError(e, "發生錯誤: {Message}", e.Message);
            return null;
        }
    }

    /// <summary>查詢單列並解析其 created_at / updated_at（SQLAlchemy 載入時就會解析）</summary>
    private static IDictionary<string, object?>? QueryRow(IDbConnection conn, string sql, long userId)
    {
        var row = conn.QueryFirstOrDefault(sql, new { userId }) as IDictionary<string, object?>;
        if (row is not null)
        {
            PyOrmDateTime.FromDb(row["created_at"]);
            PyOrmDateTime.FromDb(row["updated_at"]);
        }
        return row;
    }

    private static string IsoOrEmpty(IDictionary<string, object?>? row, string col) =>
        row is null ? "" : PyOrmDateTime.FromDb(row[col])?.IsoFormat() ?? "";

    // ==================== PATCH /api/user 的值轉換（對應 api.py 中的處理）====================

    /// <summary>height / weight：空字串或 None → None；否則 float(value)，失敗 → None</summary>
    public static double? ToFloatOrNone(JsonElement? value)
    {
        if (value is not { } v) return null;
        return v.ValueKind switch
        {
            JsonValueKind.Number => v.GetDouble(),
            JsonValueKind.True => 1.0,
            JsonValueKind.False => 0.0,
            JsonValueKind.String when v.GetString() is { Length: > 0 } s && PyOrm.TryParseFloat(s, out var d) => d,
            _ => null, // null、""、無法解析的字串、物件、陣列
        };
    }

    /// <summary>
    /// birthday：空字串或 None → None；其他值原樣寫入 String 欄位（數字 / 布林由 SQLite 轉成文字）。
    /// 物件或陣列在 Python 端會在寫入時失敗（Error binding parameter）。
    /// </summary>
    public static object? ToBirthdayValue(JsonElement? value)
    {
        if (value is not { } v) return null;
        return v.ValueKind switch
        {
            JsonValueKind.Null => null,
            JsonValueKind.String => v.GetString() is { Length: > 0 } s ? s : null,
            JsonValueKind.True => 1L,
            JsonValueKind.False => 0L,
            // 注意要轉成 object，否則三元運算會把 long 提升成 double
            JsonValueKind.Number => v.GetRawText().IndexOfAny(['.', 'e', 'E']) < 0
                ? (v.TryGetInt64(out var l) ? (object)l : throw new OverflowException("Python int too large to convert to SQLite INTEGER"))
                : (object)v.GetDouble(),
            _ => throw new InvalidOperationException("Error binding parameter - probably unsupported type."),
        };
    }
}
