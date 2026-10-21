using System.Text.Json;
using Dapper;
using PuyuanApi.Core;
using PuyuanApi.Core.PyCompat;

namespace PuyuanApi.Modules.Measurement;

/// <summary>測量上傳模組 - 提供可重用的業務邏輯（對應 app/measurement/module.py）</summary>
public class MeasurementModule(Database db, Security security, ILogger logger)
{
    /// <summary>從 Authorization Header 解析用戶 ID（"Bearer xxx" → split(' ')[1]）</summary>
    public int? ParseUserIdFromToken(string authorization)
    {
        if (string.IsNullOrEmpty(authorization) || !authorization.StartsWith("Bearer ")) return null;
        var parts = authorization.Split(' ');
        return security.VerifyToken(parts[1]);
    }

    /// <summary>查詢用戶是否存在（UserAuth）</summary>
    public bool UserExists(int userId)
    {
        using var conn = db.Open();
        return conn.ExecuteScalar<long?>("SELECT 1 FROM UserAuth WHERE id = @userId", new { userId }) is not null;
    }

    /// <summary>上傳血壓測量結果</summary>
    public long? UploadBloodPressure(int userId, int systolic, int diastolic, int? pulse, string measuredAt) =>
        Insert("血壓", measuredAt,
            """
            INSERT INTO BloodPressure (user_id, systolic, diastolic, pulse, recorded_at, created_at, updated_at)
            VALUES (@userId, @systolic, @diastolic, @pulse, @measured, @now, @now);
            SELECT last_insert_rowid();
            """,
            m => new { userId, systolic, diastolic, pulse, measured = m, now = PyDateTime.ToSqlAlchemy(TimeUtil.TaiwanNow()) },
            userId);

    /// <summary>上傳體重測量結果</summary>
    public long? UploadWeight(int userId, double weight, double? bmi, double? bodyFat, string measuredAt) =>
        Insert("體重", measuredAt,
            """
            INSERT INTO Weight (user_id, weight, bmi, body_fat, recorded_at, created_at, updated_at)
            VALUES (@userId, @weight, @bmi, @bodyFat, @measured, @now, @now);
            SELECT last_insert_rowid();
            """,
            m => new { userId, weight, bmi, bodyFat, measured = m, now = PyDateTime.ToSqlAlchemy(TimeUtil.TaiwanNow()) },
            userId);

    /// <summary>上傳血糖測量結果</summary>
    public long? UploadBloodSugar(int userId, int glucose, int mealTime, string measuredAt) =>
        Insert("血糖", measuredAt,
            """
            INSERT INTO BloodSugar (user_id, sugar, timeperiod, recorded_at, created_at, updated_at)
            VALUES (@userId, @glucose, @mealTime, @measured, @now, @now);
            SELECT last_insert_rowid();
            """,
            m => new { userId, glucose, mealTime, measured = m, now = PyDateTime.ToSqlAlchemy(TimeUtil.TaiwanNow()) },
            userId);

    private long? Insert(string kind, string measuredAt, string sql, Func<string, object> param, int userId)
    {
        try
        {
            // 解析測量時間（datetime.fromisoformat(measured_at.replace('Z', '+00:00'))），時區資訊捨棄、只存牆上時間
            if (!PyDateTime.TryFromIsoFormat(measuredAt.Replace("Z", "+00:00"), out var measured, out _))
                throw new FormatException($"Invalid isoformat string: '{measuredAt}'");

            using var conn = db.Open();
            var id = conn.ExecuteScalar<long>(sql, param(PyDateTime.ToSqlAlchemy(measured)));
            logger.LogInformation("{Kind}記錄已儲存: id={Id}, user_id={UserId}", kind, id, userId);
            return id;
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "上傳{Kind}記錄錯誤: {Message}", kind, ex.Message);
            return null;
        }
    }

    /// <summary>
    /// 創建測量記錄上傳記錄。record_type / record_id 原樣寫入（Python 端未驗證型別），
    /// 例如 null 會違反 NOT NULL、物件/陣列無法綁定 → 回傳 false。
    /// </summary>
    public bool CreateMeasurementRecord(int userId, JsonElement recordType, JsonElement recordId)
    {
        try
        {
            var type = ToSqliteValue(recordType);
            var rid = ToSqliteValue(recordId);
            using var conn = db.Open();
            conn.Execute(
                "INSERT INTO measurement_records (user_id, record_type, record_id, uploaded_at) VALUES (@userId, @recordType, @recordId, @now)",
                new { userId, recordType = type, recordId = rid, now = PyDateTime.ToSqlAlchemy(TimeUtil.TaiwanNow()) });
            return true;
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "創建測量記錄錯誤: {Message}", ex.Message);
            return false;
        }
    }

    /// <summary>JSON 值 → sqlite3 綁定值（bool 存成 1/0；物件、陣列無法綁定）</summary>
    private static object? ToSqliteValue(JsonElement e) => e.ValueKind switch
    {
        JsonValueKind.Number => e.TryGetInt64(out var l) ? l : e.GetDouble(),
        JsonValueKind.String => e.GetString(),
        JsonValueKind.True => 1L,
        JsonValueKind.False => 0L,
        JsonValueKind.Null => null,
        _ => throw new InvalidOperationException($"Error binding parameter: type '{e.ValueKind}' is not supported"),
    };

    /// <summary>獲取最後上傳時間（uploaded_at.isoformat()）</summary>
    public string? GetLastUploadTime(int userId)
    {
        try
        {
            using var conn = db.Open();
            var found = conn.Query<string?>(
                "SELECT uploaded_at FROM measurement_records WHERE user_id = @userId ORDER BY uploaded_at DESC LIMIT 1",
                new { userId }).ToList();
            if (found.Count == 0) return null;

            // uploaded_at 為 NULL 或無法解析時，Python 會拋例外並被 except 吃掉 → None
            if (!PyDateTime.TryFromIsoFormat(found[0], out var dt, out var offset))
                throw new FormatException($"Invalid isoformat string: '{found[0]}'");
            return PyDateTime.IsoFormat(dt, offset);
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "查詢最後上傳時間錯誤: {Message}", ex.Message);
            return null;
        }
    }
}
