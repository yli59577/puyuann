using System.Data;
using Dapper;
using PuyuanApi.Core;
using PuyuanApi.Core.PyCompat;

namespace PuyuanApi.Modules.Else;

/// <summary>最新消息、分享業務邏輯（對應 app/_else/module.py）</summary>
public class ElseModule(Database db, ILogger logger)
{
    // ==================== 最新消息 ====================

    /// <summary>獲取最新消息列表（失敗時回傳空列表）</summary>
    public List<NewsItem> GetNewsList(int limit = 20)
    {
        try
        {
            using var conn = db.Open();
            var rows = Rows(conn, """
                SELECT id, member_id, "group", title, message, pushed_at, created_at, updated_at
                FROM News ORDER BY created_at DESC LIMIT @limit
                """, new { limit });

            return rows.Select(n =>
            {
                // ORM 載入時解析 DateTime，再 str()（None → "None"）
                var pushedAt = Py.OrmDateTimeStr(n["pushed_at"]);
                var createdAt = Py.OrmDateTimeStr(n["created_at"]) ?? "None";
                var updatedAt = Py.OrmDateTimeStr(n["updated_at"]) ?? "None";
                return new NewsItem(
                    Id: Py.Int(n["id"]),
                    MemberId: Py.Truthy(n["member_id"]) ? Py.Int(n["member_id"]) : 0,
                    Group: Py.Truthy(n["group"]) ? Py.Int(n["group"]) : 0,
                    Title: RequiredStr(n["title"]),
                    Message: RequiredStr(n["message"]),
                    PushedAt: pushedAt ?? createdAt,
                    CreatedAt: createdAt,
                    UpdatedAt: updatedAt);
            }).ToList();
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "查詢最新消息失敗: {Message}", ex.Message);
            return [];
        }
    }

    // ==================== 分享 ====================

    /// <summary>創建分享記錄（Python 的 _check_record_exists 目前一律回傳 True）</summary>
    public bool CreateShare(int recordId, int dataType, int relationType, int userId)
    {
        try
        {
            // TODO: 根據 data_type 查詢對應的資料表確認記錄存在（Python 版也尚未實作）
            var now = TimeUtil.TaiwanNow().ToString("yyyy-MM-dd HH:mm:ss.ffffff");
            using var conn = db.Open();
            conn.Execute("""
                INSERT INTO Share (fid, data_type, relation_type, user_id, created_at, updated_at)
                VALUES (@recordId, @dataType, @relationType, @userId, @now, @now)
                """, new { recordId, dataType, relationType, userId, now });
            return true;
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "創建分享記錄失敗: {Message}", ex.Message);
            return false;
        }
    }

    /// <summary>獲取分享給當前用戶（shared_with_user_id）的記錄列表</summary>
    public List<ShareRecord> GetSharedRecords(int dataType, int userId)
    {
        try
        {
            using var conn = db.Open();
            var shares = Rows(conn, """
                SELECT id, fid, data_type, relation_type, user_id, shared_with_user_id, created_at, updated_at
                FROM Share
                WHERE data_type = @dataType AND shared_with_user_id = @userId
                """, new { dataType, userId });

            // ORM 載入時會解析 DateTime 欄位
            foreach (var s in shares)
            {
                _ = Py.OrmDateTimeStr(s["created_at"]);
                _ = Py.OrmDateTimeStr(s["updated_at"]);
            }

            logger.LogDebug("查詢到 {Count} 筆分享記錄 (data_type={DataType}, shared_with_user_id={UserId})",
                shares.Count, dataType, userId);

            var records = new List<ShareRecord>();
            foreach (var share in shares)
            {
                var record = GetHealthRecord(conn, share["fid"], dataType, share["user_id"], share["relation_type"]);
                if (record is not null) records.Add(record);
            }
            return records;
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "查詢分享記錄失敗: {Message}", ex.Message);
            return [];
        }
    }

    /// <summary>獲取健康記錄詳情（任何錯誤 → null，該筆分享會被略過）</summary>
    private ShareRecord? GetHealthRecord(IDbConnection conn, object? recordId, int dataType, object? sharerUserId, object? relationType)
    {
        try
        {
            // 查詢分享者的用戶資訊
            var profile = Rows(conn, """
                SELECT name, created_at, updated_at FROM UserProfile WHERE user_id = @sharerUserId LIMIT 1
                """, new { sharerUserId }).FirstOrDefault();
            var auth = Rows(conn, """
                SELECT account, token_expire_at, created_at, updated_at, verification_expires_at
                FROM UserAuth WHERE id = @sharerUserId LIMIT 1
                """, new { sharerUserId }).FirstOrDefault();
            ParseDates(profile, "created_at", "updated_at");
            ParseDates(auth, "token_expire_at", "created_at", "updated_at", "verification_expires_at");

            // UserInfo 的欄位都是必填 str / int，None 會讓 pydantic 驗證失敗
            var userInfo = new UserInfo(
                Id: Py.Int(Required(sharerUserId)),
                Name: profile is not null ? RequiredStr(profile["name"]) : "未知用戶",
                Account: auth is not null ? RequiredStr(auth["account"]) : "");

            var relType = Py.Int(Required(relationType));
            var relId = userInfo.Id;

            switch (dataType)
            {
                case 0: // 血壓
                {
                    var r = Rows(conn, """
                        SELECT id, user_id, systolic, diastolic, pulse, recorded_at, created_at, updated_at
                        FROM BloodPressure WHERE id = @recordId AND user_id = @sharerUserId LIMIT 1
                        """, new { recordId, sharerUserId }).FirstOrDefault();
                    if (r is null)
                    {
                        logger.LogWarning("找不到血壓記錄: id={RecordId}, user_id={UserId}", recordId, sharerUserId);
                        return null;
                    }
                    var (recordedAt, createdAt) = RecordTimes(r, "recorded_at");
                    return new ShareRecord
                    {
                        Id = Py.Int(Required(r["id"])),
                        UserId = Py.Int(Required(r["user_id"])),
                        Systolic = OptInt(r["systolic"]),
                        Diastolic = OptInt(r["diastolic"]),
                        Pulse = Py.Truthy(r["pulse"]) ? Py.Int(r["pulse"]) : 0,
                        RelationType = relType,
                        RelationId = relId,
                        Type = dataType,
                        RecordedAt = recordedAt,
                        CreatedAt = createdAt,
                        User = userInfo,
                    };
                }
                case 1: // 體重
                {
                    var r = Rows(conn, """
                        SELECT id, user_id, weight, bmi, body_fat, recorded_at, created_at, updated_at
                        FROM Weight WHERE id = @recordId AND user_id = @sharerUserId LIMIT 1
                        """, new { recordId, sharerUserId }).FirstOrDefault();
                    if (r is null)
                    {
                        logger.LogWarning("找不到體重記錄: id={RecordId}, user_id={UserId}", recordId, sharerUserId);
                        return null;
                    }
                    var (recordedAt, createdAt) = RecordTimes(r, "recorded_at");
                    return new ShareRecord
                    {
                        Id = Py.Int(Required(r["id"])),
                        UserId = Py.Int(Required(r["user_id"])),
                        Weight = r["weight"] is null ? null : Py.Float(r["weight"]),
                        BodyFat = Py.Truthy(r["body_fat"]) ? Py.Float(r["body_fat"]) : 0.0,
                        Bmi = Py.Truthy(r["bmi"]) ? Py.Float(r["bmi"]) : 0.0,
                        RelationType = relType,
                        RelationId = relId,
                        Type = dataType,
                        RecordedAt = recordedAt,
                        CreatedAt = createdAt,
                        User = userInfo,
                    };
                }
                case 2: // 血糖
                {
                    var r = Rows(conn, """
                        SELECT id, user_id, sugar, timeperiod, recorded_at, created_at, updated_at
                        FROM BloodSugar WHERE id = @recordId AND user_id = @sharerUserId LIMIT 1
                        """, new { recordId, sharerUserId }).FirstOrDefault();
                    if (r is null)
                    {
                        logger.LogWarning("找不到血糖記錄: id={RecordId}, user_id={UserId}", recordId, sharerUserId);
                        return null;
                    }
                    var (recordedAt, createdAt) = RecordTimes(r, "recorded_at");
                    return new ShareRecord
                    {
                        Id = Py.Int(Required(r["id"])),
                        UserId = Py.Int(Required(r["user_id"])),
                        Sugar = Py.Float(Required(r["sugar"])),
                        Timeperiod = OptInt(r["timeperiod"]),
                        RelationType = relType,
                        RelationId = relId,
                        Type = dataType,
                        RecordedAt = recordedAt,
                        CreatedAt = createdAt,
                        User = userInfo,
                    };
                }
                case 3: // 飲食 (DiaryDiet)
                {
                    var r = Rows(conn, """
                        SELECT id, user_id, description, meal, tag, image, lat, lng, recorded_at, created_at, updated_at
                        FROM DiaryDiet WHERE id = @recordId AND user_id = @sharerUserId LIMIT 1
                        """, new { recordId, sharerUserId }).FirstOrDefault();
                    if (r is null)
                    {
                        logger.LogWarning("找不到飲食記錄: id={RecordId}, user_id={UserId}", recordId, sharerUserId);
                        return null;
                    }
                    var (recordedAt, createdAt) = RecordTimes(r, "recorded_at");

                    // 處理標籤（Python 以逗號切割原始字串）
                    var tagList = new List<string>();
                    if (Py.Truthy(r["tag"]))
                    {
                        var tag = Py.Str(r["tag"]);
                        tagList = tag.Contains(',') ? [.. tag.Split(',')] : [tag];
                    }

                    // 處理圖片：根據圖片數量生成圖片 URL
                    var imageList = new List<string>();
                    if (Py.Truthy(r["image"]) && Py.Int(r["image"]) > 0)
                    {
                        var count = Py.Int(r["image"]);
                        for (var i = 0; i < count; i++)
                            imageList.Add($"/uploads/diet_images/{Py.Str(r["id"])}_{i}.jpg");
                    }

                    // 處理位置
                    var location = new LocationData(
                        Lat: Py.Truthy(r["lat"]) ? Py.Str(r["lat"]) : "0",
                        Lng: Py.Truthy(r["lng"]) ? Py.Str(r["lng"]) : "0");

                    return new ShareRecord
                    {
                        // DiaryDiet.id 是 VARCHAR：UUID / NULL 無法轉成 int → 驗證失敗 → 略過
                        Id = Py.Int(Required(r["id"])),
                        UserId = Py.Int(Required(r["user_id"])),
                        Meal = Py.Truthy(r["meal"]) ? Py.Int(r["meal"]) : 0,
                        Tag = tagList,
                        Image = imageList,
                        Location = location,
                        RelationType = relType,
                        RelationId = relId,
                        Message = Py.Truthy(r["description"]) ? Py.Str(r["description"]) : "",
                        Type = dataType,
                        RecordedAt = recordedAt,
                        CreatedAt = createdAt,
                        User = userInfo,
                    };
                }
                default: // 其他類型 (4)
                    logger.LogWarning("不支援的資料類型: {DataType}", dataType);
                    return null;
            }
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "獲取健康記錄失敗: {Message}", ex.Message);
            return null;
        }
    }

    // ==================== 工具 ====================

    /// <summary>recorded_at / created_at：ORM 解析後 str()，空值 → ""</summary>
    private static (string RecordedAt, string CreatedAt) RecordTimes(IDictionary<string, object?> r, string recordedCol)
    {
        var recorded = Py.OrmDateTimeStr(r[recordedCol]);
        var created = Py.OrmDateTimeStr(r["created_at"]);
        _ = Py.OrmDateTimeStr(r["updated_at"]);
        return (recorded ?? "", created ?? "");
    }

    private static void ParseDates(IDictionary<string, object?>? row, params string[] cols)
    {
        if (row is null) return;
        foreach (var c in cols) _ = Py.OrmDateTimeStr(row[c]);
    }

    /// <summary>pydantic 必填欄位：None → 驗證失敗</summary>
    private static object Required(object? v) =>
        v ?? throw new InvalidOperationException("none is not an allowed value");

    /// <summary>pydantic v1 的 str 欄位：None → 失敗，其他型別轉成字串</summary>
    private static string RequiredStr(object? v) => Py.Str(Required(v));

    private static long? OptInt(object? v) => v is null ? null : Py.Int(v);

    private static List<IDictionary<string, object?>> Rows(IDbConnection conn, string sql, object param) =>
        conn.Query(sql, param).Select(r => (IDictionary<string, object?>)r).ToList();
}
