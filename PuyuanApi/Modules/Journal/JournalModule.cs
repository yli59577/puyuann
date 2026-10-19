using System.Globalization;
using System.Text.Json;
using System.Text.Json.Nodes;
using Dapper;
using PuyuanApi.Core;
using PuyuanApi.Core.PyCompat;

namespace PuyuanApi.Modules.Journal;

/// <summary>日記模組 - 提供可重用的業務邏輯（對應 app/_journal/module.py）</summary>
public class JournalModule(Database db, ILogger logger)
{
    /// <summary>查詢用戶是否存在（UserAuth）</summary>
    public bool UserExists(int userId)
    {
        using var conn = db.Open();
        return conn.ExecuteScalar<long?>("SELECT id FROM UserAuth WHERE id = @userId LIMIT 1", new { userId }) is not null;
    }

    /// <summary>獲取指定日期的日記列表（任何錯誤都回傳空列表，與 Python 相同）</summary>
    public List<DiaryRecord> GetDiaryList(int userId, string date)
    {
        try
        {
            logger.LogDebug("開始查詢日記列表: user_id={UserId}, date={Date}", userId, date);

            // datetime.strptime(date, '%Y-%m-%d') → str(date) 會正規化成 yyyy-MM-dd
            if (!DateTime.TryParseExact(date, ["yyyy-M-d"], CultureInfo.InvariantCulture, DateTimeStyles.None, out var target))
                throw new FormatException($"time data '{date}' does not match format '%Y-%m-%d'");
            var queryDate = target.ToString("yyyy-MM-dd");

            var diaryList = new List<DiaryRecord>();
            using var conn = db.Open();

            // 查詢血壓記錄（Python 使用 sqlite3 原始查詢，時間字串原樣輸出）
            foreach (var r in Rows(conn, """
                SELECT id, user_id, systolic, diastolic, pulse, measured_at
                FROM blood_pressure_records
                WHERE user_id = @userId AND DATE(measured_at) = @queryDate
                """, new { userId, queryDate }))
            {
                diaryList.Add(new DiaryRecord
                {
                    Id = Py.Truthy(r["id"]) ? Py.Int(r["id"]) : 0,
                    UserId = Py.Truthy(r["user_id"]) ? Py.Int(r["user_id"]) : 0,
                    Systolic = Py.Truthy(r["systolic"]) ? Py.Int(r["systolic"]) : 0,
                    Diastolic = Py.Truthy(r["diastolic"]) ? Py.Int(r["diastolic"]) : 0,
                    Pulse = Py.Truthy(r["pulse"]) ? Py.Int(r["pulse"]) : 0,
                    RecordedAt = Py.Truthy(r["measured_at"]) ? Py.Str(r["measured_at"]) : "",
                    Type = "blood_pressure",
                });
            }

            // 查詢體重記錄
            foreach (var r in Rows(conn, """
                SELECT id, user_id, weight, bmi, body_fat, measured_at
                FROM weight_records
                WHERE user_id = @userId AND DATE(measured_at) = @queryDate
                """, new { userId, queryDate }))
            {
                diaryList.Add(new DiaryRecord
                {
                    Id = Py.Truthy(r["id"]) ? Py.Int(r["id"]) : 0,
                    UserId = Py.Truthy(r["user_id"]) ? Py.Int(r["user_id"]) : 0,
                    Weight = Py.Truthy(r["weight"]) ? Py.Float(r["weight"]) : 0.0,
                    BodyFat = Py.Truthy(r["body_fat"]) ? Py.Float(r["body_fat"]) : 0.0,
                    Bmi = Py.Truthy(r["bmi"]) ? Py.Float(r["bmi"]) : 0.0,
                    RecordedAt = Py.Truthy(r["measured_at"]) ? Py.Str(r["measured_at"]) : "",
                    Type = "weight",
                });
            }

            // 查詢血糖記錄
            foreach (var r in Rows(conn, """
                SELECT id, user_id, glucose, meal_time, measured_at
                FROM blood_sugar_records
                WHERE user_id = @userId AND DATE(measured_at) = @queryDate
                """, new { userId, queryDate }))
            {
                diaryList.Add(new DiaryRecord
                {
                    Id = Py.Truthy(r["id"]) ? Py.Int(r["id"]) : 0,
                    UserId = Py.Truthy(r["user_id"]) ? Py.Int(r["user_id"]) : 0,
                    Sugar = Py.Truthy(r["glucose"]) ? Py.Float(r["glucose"]) : 0.0,
                    Timeperiod = Py.Truthy(r["meal_time"]) ? Py.Int(r["meal_time"]) : 0,
                    RecordedAt = Py.Truthy(r["measured_at"]) ? Py.Str(r["measured_at"]) : "",
                    Type = "blood_sugar",
                });
            }

            // 查詢飲食記錄（Python 用 ORM，DateTime 欄位會被解析再 str()）
            // 註：Python 原始碼寫成 db.func.date(...)，Session 沒有 func 屬性，
            //     會讓整個日記列表回傳空陣列；這裡依原意實作 func.date(recorded_at) == date
            var dietRows = Rows(conn, """
                SELECT id, user_id, description, meal, tag, image, lat, lng, recorded_at, created_at, updated_at
                FROM DiaryDiet
                WHERE user_id = @userId AND date(recorded_at) = @queryDate
                """, new { userId, queryDate });
            logger.LogDebug("查詢到 {Count} 筆飲食記錄", dietRows.Count);

            foreach (var r in dietRows)
            {
                // ORM 載入時會解析所有 DateTime 欄位，格式錯誤會丟例外
                var recordedAt = Py.OrmDateTimeStr(r["recorded_at"]);
                _ = Py.OrmDateTimeStr(r["created_at"]);
                _ = Py.OrmDateTimeStr(r["updated_at"]);

                // 解析 location - Swift 期望 Dictionary，不能是 null
                var location = Py.Truthy(r["lat"]) && Py.Truthy(r["lng"])
                    ? new Dictionary<string, string> { ["lat"] = Py.Str(r["lat"]), ["lng"] = Py.Str(r["lng"]) }
                    : new Dictionary<string, string> { ["lat"] = "0", ["lng"] = "0" };

                diaryList.Add(new DiaryRecord
                {
                    Id = DietRecordId(r["id"]),
                    UserId = Py.Truthy(r["user_id"]) ? Py.Int(r["user_id"]) : 0,
                    Description = Py.Truthy(r["description"]) ? Py.Str(r["description"]) : "",
                    Meal = r["meal"] is null ? 0 : Py.Int(r["meal"]),
                    Tag = ParseTags(r["tag"]),
                    Image = Py.Truthy(r["image"]) ? [Py.Str(r["image"])] : [],
                    Location = location,
                    RecordedAt = recordedAt ?? "",
                    Type = "diet",
                });
            }

            logger.LogDebug("總共查詢到 {Count} 筆日記記錄", diaryList.Count);
            return diaryList;
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "獲取日記列表錯誤: {Message}", ex.Message);
            return [];
        }
    }

    /// <summary>
    /// 飲食記錄 id 是 VARCHAR（UUID 或 NULL），Swift 期望 Int：
    /// NULL → 0；純數字 → int；其他 → 雜湊（Python 用 hash()，每次重啟都不同，這裡改用穩定雜湊）
    /// </summary>
    private static long DietRecordId(object? id)
    {
        if (!Py.Truthy(id)) return 0;
        var s = Py.Str(id);
        if (s.All(char.IsAsciiDigit) && long.TryParse(s, out var n)) return n;
        return Py.StableHash(s);
    }

    /// <summary>
    /// 解析 tag 欄位（JSON 字串，例如 '["早餐"]'）。
    /// DiaryRecord.tag 宣告為 List[Dict]，直接放字串清單會讓 pydantic 驗證失敗，
    /// 因此沿用先前可運作版本的格式：[{"name": [...tags], "message": "ok"}]
    /// </summary>
    private static List<Dictionary<string, object?>> ParseTags(object? tag)
    {
        if (!Py.Truthy(tag) || tag is not string s) return [];
        try
        {
            var node = JsonNode.Parse(s);
            var truthy = node switch
            {
                null => false,
                JsonArray a => a.Count > 0,
                JsonObject o => o.Count > 0,
                JsonValue v when v.GetValueKind() == JsonValueKind.String => v.GetValue<string>().Length > 0,
                JsonValue v when v.GetValueKind() == JsonValueKind.Number => v.GetValue<double>() != 0,
                _ => node.GetValueKind() == JsonValueKind.True,
            };
            return truthy ? [new() { ["name"] = node, ["message"] = "ok" }] : [];
        }
        catch (JsonException)
        {
            return [];
        }
    }

    /// <summary>上傳飲食日記</summary>
    public bool UploadDiet(int userId, string description, int meal, List<string> tags, int image,
        double? lat, double? lng, string recordedAt)
    {
        try
        {
            logger.LogDebug("upload_diet called with tags: {Tags}", string.Join(",", tags));

            // 將 tags 轉換為 JSON 字串（ensure_ascii=False 保留中文）
            var tagJson = Py.JsonDumpsStrList(tags);

            // datetime.strptime(recorded_at, '%Y-%m-%d %H:%M:%S')
            if (!DateTime.TryParseExact(recordedAt, ["yyyy-M-d H:m:s"], CultureInfo.InvariantCulture, DateTimeStyles.None, out var recorded))
                throw new FormatException($"time data '{recordedAt}' does not match format '%Y-%m-%d %H:%M:%S'");

            // SQLAlchemy 在 SQLite 的 DateTime 儲存格式：yyyy-MM-dd HH:mm:ss.ffffff
            var now = TimeUtil.TaiwanNow().ToString("yyyy-MM-dd HH:mm:ss.ffffff");

            // 與 Python 相同：不指定 id（DiaryDiet.id 是 VARCHAR 主鍵，實際會存成 NULL）
            using var conn = db.Open();
            conn.Execute("""
                INSERT INTO DiaryDiet (user_id, description, meal, tag, image, lat, lng, recorded_at, created_at, updated_at)
                VALUES (@userId, @description, @meal, @tagJson, @image, @lat, @lng, @recordedAt, @now, @now)
                """, new
            {
                userId, description, meal, tagJson, image, lat, lng,
                recordedAt = recorded.ToString("yyyy-MM-dd HH:mm:ss.ffffff"),
                now,
            });

            logger.LogInformation("Diet record uploaded successfully for user {UserId}", userId);
            return true;
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "上傳飲食日記錯誤: {Message}", ex.Message);
            return false;
        }
    }

    /// <summary>刪除日記記錄（只刪除屬於該用戶的記錄，找不到的 id 直接略過）</summary>
    public bool DeleteRecords(int userId, Dictionary<string, List<long>> deleteObject)
    {
        using var conn = db.Open();
        using var tx = conn.BeginTransaction();
        try
        {
            (string Key, string Table)[] targets =
            [
                ("blood_pressures", "blood_pressure_records"),
                ("weights", "weight_records"),
                ("blood_sugars", "blood_sugar_records"),
                ("diets", "DiaryDiet"),
            ];

            foreach (var (key, table) in targets)
            {
                if (!deleteObject.TryGetValue(key, out var ids)) continue;
                foreach (var id in ids)
                    conn.Execute($"DELETE FROM {table} WHERE id = @id AND user_id = @userId", new { id, userId }, tx);
            }

            tx.Commit();
            return true;
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "刪除記錄錯誤: {Message}", ex.Message);
            tx.Rollback();
            return false;
        }
    }

    /// <summary>執行查詢並以「欄位名 → 原始值」字典回傳（模擬 sqlite3 的動態型別）</summary>
    private static List<IDictionary<string, object?>> Rows(System.Data.IDbConnection conn, string sql, object param) =>
        conn.Query(sql, param).Select(r => (IDictionary<string, object?>)r).ToList();
}
