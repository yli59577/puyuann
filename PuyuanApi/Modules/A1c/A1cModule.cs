using Dapper;
using PuyuanApi.Core;
using PuyuanApi.Core.PyCompat;

namespace PuyuanApi.Modules.A1c;

/// <summary>糖化血色素模組 - 提供可重用的業務邏輯（對應 app/a1c/module.py，資料表 HbA1c）</summary>
public class A1cModule(Database db, Security security, ILogger logger)
{
    /// <summary>從 Authorization Header 解析用戶 ID（"Bearer xxx" → split(' ')[1]）</summary>
    public int? ParseUserIdFromToken(string authorization)
    {
        if (string.IsNullOrEmpty(authorization) || !authorization.StartsWith("Bearer ")) return null;
        return security.VerifyToken(authorization.Split(' ')[1]);
    }

    /// <summary>上傳糖化血色素記錄</summary>
    public bool UploadA1c(int userId, string a1c, string recordedAt)
    {
        try
        {
            logger.LogDebug("上傳糖化血色素: user_id={UserId}, a1c={A1c}, recorded_at={RecordedAt}", userId, a1c, recordedAt);

            // Python 用 datetime.now()（伺服器本地時間）
            var now = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");
            using var conn = db.Open();
            conn.Execute(
                """
                INSERT INTO HbA1c (user_id, a1c, recorded_at, created_at, updated_at)
                VALUES (@userId, @a1c, @recordedAt, @now, @now)
                """, new { userId, a1c, recordedAt, now });

            logger.LogInformation("糖化血色素上傳成功");
            return true;
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "上傳糖化血色素錯誤: {Message}", ex.Message);
            return false;
        }
    }

    /// <summary>
    /// 獲取用戶的所有糖化血色素記錄。資料庫錯誤時回傳空列表；
    /// 欄位型別不符（例如 NULL）時 Python 在建立回應模型時才失敗 → 拋出 PyValidationException（變成伺服器內部錯誤）。
    /// </summary>
    public List<A1cRecord> GetA1cList(int userId)
    {
        List<IDictionary<string, object?>> rows;
        try
        {
            logger.LogDebug("查詢糖化血色素列表: user_id={UserId}", userId);
            using var conn = db.Open();
            rows = conn.Query(
                """
                SELECT id, user_id, a1c, recorded_at, created_at, updated_at
                FROM HbA1c
                WHERE user_id = @userId
                ORDER BY recorded_at DESC
                """, new { userId })
                .Select(r => (IDictionary<string, object?>)r).ToList();
            logger.LogDebug("查詢到 {Count} 筆糖化血色素記錄", rows.Count);
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "查詢糖化血色素列表錯誤: {Message}", ex.Message);
            return [];
        }

        return rows.Select(r => new A1cRecord(
            PyCoerce.Int(r["id"], "id"),
            PyCoerce.Str(r["a1c"], "a1c"),
            PyCoerce.Str(r["recorded_at"], "recorded_at"),
            PyCoerce.Str(r["updated_at"], "updated_at"),
            PyCoerce.Str(r["created_at"], "created_at"),
            PyCoerce.Int(r["user_id"], "user_id"))).ToList();
    }

    /// <summary>刪除糖化血色素記錄（只能刪除自己的記錄）</summary>
    public bool DeleteA1cRecords(int userId, List<int> ids)
    {
        try
        {
            logger.LogDebug("刪除糖化血色素記錄: user_id={UserId}, ids={Ids}", userId, ids);
            if (ids.Count == 0)
            {
                logger.LogDebug("沒有要刪除的記錄");
                return true;
            }

            using var conn = db.Open();
            var deleted = conn.Execute("DELETE FROM HbA1c WHERE user_id = @userId AND id IN @ids", new { userId, ids });
            logger.LogInformation("成功刪除 {Count} 筆糖化血色素記錄", deleted);
            return true;
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "刪除糖化血色素記錄錯誤: {Message}", ex.Message);
            return false;
        }
    }
}
