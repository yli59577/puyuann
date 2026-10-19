using Dapper;
using PuyuanApi.Core;
using PuyuanApi.Core.PyCompat;

namespace PuyuanApi.Modules.Care;

/// <summary>關懷諮詢模組（對應 app/care/module.py，資料表 UserCare）。錯誤一律往外拋，由 controller 轉成「失敗」。</summary>
public class CareModule(Database db, Security security, ILogger logger)
{
    /// <summary>從 Authorization Header 解析用戶 ID（"Bearer xxx" → split(' ')[1]，大小寫須完全相同）</summary>
    public int? ParseUserIdFromToken(string? authorization)
    {
        if (string.IsNullOrEmpty(authorization) || !authorization.StartsWith("Bearer ")) return null;
        return security.VerifyToken(authorization.Split(' ')[1]);
    }

    private static CareRecord ToRecord(IDictionary<string, object?> row) => new(
        PyCoerce.Int(row["id"], "id"),
        PyCoerce.Int(row["user_id"], "user_id"),
        PyCoerce.OptionalInt(row["member_id"], "member_id"),
        PyCoerce.OptionalInt(row["reply_id"], "reply_id"),
        PyCoerce.Str(row["message"], "message"),
        PyCoerce.Str(row["updated_at"], "updated_at"),
        PyCoerce.Str(row["created_at"], "created_at"));

    /// <summary>
    /// 獲取使用者的關懷諮詢紀錄列表。
    /// 注意：Python 未驗證時 user_id 為 None → WHERE user_id = NULL → 永遠是空列表（不會回錯誤）。
    /// </summary>
    public List<CareRecord> GetCareList(int? userId)
    {
        using var conn = db.Open();
        return conn.Query("SELECT * FROM UserCare WHERE user_id = @userId ORDER BY created_at DESC", new { userId })
            .Select(r => ToRecord((IDictionary<string, object?>)r))
            .ToList();
    }

    /// <summary>上傳關懷訊息（user_id 為 null 時違反 NOT NULL → 拋出例外）</summary>
    public CareRecord UploadCareMessage(int? userId, CareMessageUpload data)
    {
        // Python 用 datetime.now()（伺服器本地時間）
        var now = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");
        using var conn = db.Open();
        var recordId = conn.ExecuteScalar<long>(
            """
            INSERT INTO UserCare (user_id, message, created_at, updated_at)
            VALUES (@userId, @message, @now, @now);
            SELECT last_insert_rowid();
            """, new { userId, message = data.Message, now });

        // 獲取並返回創建的記錄
        var row = (IDictionary<string, object?>)conn.QueryFirst("SELECT * FROM UserCare WHERE id = @recordId", new { recordId });
        logger.LogInformation("關懷訊息已儲存: id={Id}, user_id={UserId}", recordId, userId);
        return ToRecord(row);
    }
}
