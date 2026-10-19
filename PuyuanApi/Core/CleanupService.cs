using Dapper;

namespace PuyuanApi.Core;

/// <summary>每分鐘清理過期未驗證帳號（對應 app/core/cleanup.py）</summary>
public class CleanupService(Database db, ILogger<CleanupService> logger) : BackgroundService
{
    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        logger.LogInformation("已啟動過期帳號清理任務（每分鐘檢查一次）");
        while (!stoppingToken.IsCancellationRequested)
        {
            try
            {
                CleanupExpiredUnverifiedUsers();
            }
            catch (Exception ex)
            {
                logger.LogError(ex, "清理任務出錯: {Message}", ex.Message);
            }
            try
            {
                await Task.Delay(TimeSpan.FromMinutes(1), stoppingToken);
            }
            catch (OperationCanceledException)
            {
                break; // 程式關閉時正常結束
            }
        }
    }

    public int CleanupExpiredUnverifiedUsers()
    {
        using var conn = db.Open();
        using var tx = conn.BeginTransaction();

        var now = TimeUtil.TaiwanNowString();
        var expired = conn.Query<(long Id, string Email, string ExpiresAt)>(
            """
            SELECT id, email, verification_expires_at FROM UserAuth
            WHERE (verified = 0 OR verified IS NULL)
              AND verification_expires_at IS NOT NULL
              AND verification_expires_at <= @now
            """, new { now }, tx).ToList();

        foreach (var u in expired)
        {
            logger.LogInformation("刪除過期未驗證帳號: {Email} (過期時間: {ExpiresAt})", u.Email, u.ExpiresAt);
            conn.Execute("DELETE FROM UserProfile WHERE user_id = @Id", new { u.Id }, tx);
            conn.Execute("DELETE FROM UserAuth WHERE id = @Id", new { u.Id }, tx);
        }

        tx.Commit();
        if (expired.Count > 0)
            logger.LogInformation("成功刪除 {Count} 個過期未驗證帳號", expired.Count);
        return expired.Count;
    }
}
