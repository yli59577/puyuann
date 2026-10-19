using System.Globalization;
using Dapper;
using PuyuanApi.Core;

namespace PuyuanApi.Modules.Friend;

/// <summary>控糖團好友模組（對應 app/friend/module.py）</summary>
public class FriendModule(Database db, Security security, ILogger logger)
{
    /// <summary>
    /// 從 Authorization Header 解析用戶 ID。
    /// 模擬 HTTPBearer(auto_error=False)：scheme 不分大小寫，取第一個空白後的內容當 token，
    /// 再照 Python 的 authorization.split(' ')[1] 取 token。
    /// </summary>
    public int? ParseUserIdFromToken(HttpRequest request)
    {
        var header = request.Headers.Authorization.ToString();
        if (string.IsNullOrEmpty(header)) return null;

        var space = header.IndexOf(' ');
        if (space < 0) return null;
        var scheme = header[..space];
        var param = header[(space + 1)..];
        if (!scheme.Equals("bearer", StringComparison.OrdinalIgnoreCase) || param.Length == 0) return null;

        var token = param.Split(' ')[0];
        return security.VerifyToken(token);
    }

    /// <summary>獲取好友列表</summary>
    public List<FriendInfo> GetFriendList(int userId)
    {
        using var conn = db.Open();
        logger.LogDebug("查詢好友列表，user_id={UserId}", userId);

        // 查詢已接受的好友關係
        var rows = conn.Query(
            """
            SELECT f.friend_id as id, u.name, fr.type as relation_type
            FROM Friendship f
            JOIN UserProfile u ON f.friend_id = u.user_id
            JOIN friend_requests fr ON (fr.user_id = @userId AND fr.relation_id = f.friend_id)
               OR (fr.relation_id = @userId AND fr.user_id = f.friend_id)
            WHERE f.user_id = @userId AND f.status = 1 AND fr.status = 1
            ORDER BY f.created_at DESC
            """, new { userId }).Cast<IDictionary<string, object?>>().ToList();
        logger.LogDebug("查詢到 {Count} 位好友", rows.Count);

        return rows.Select(r => new FriendInfo(
            PyInt(r["id"]),
            OrEmpty(r["name"]),
            PyInt(r["relation_type"]))).ToList();
    }

    /// <summary>獲取用戶的邀請碼（沒有就自動生成 6 位數字）</summary>
    public string? GetInviteCode(int userId)
    {
        try
        {
            using var conn = db.Open();

            // 先查詢是否有邀請碼
            var existing = conn.ExecuteScalar<object?>(
                "SELECT invite_code FROM UserProfile WHERE user_id = @userId", new { userId });
            if (Truthy(existing))
                return PyStr(existing);

            // 如果沒有邀請碼，自動生成一個 6 位數字邀請碼
            var inviteCode = Random.Shared.Next(100000, 1000000).ToString(CultureInfo.InvariantCulture);

            // 更新到資料庫（UserProfile 不存在時不會更新，但仍回傳生成的邀請碼，與 Python 相同）
            conn.Execute("UPDATE UserProfile SET invite_code = @inviteCode WHERE user_id = @userId",
                new { inviteCode, userId });

            logger.LogDebug("為用戶 {UserId} 生成邀請碼: {InviteCode}", userId, inviteCode);
            return inviteCode;
        }
        catch (Exception e)
        {
            logger.LogError(e, "get_invite_code 錯誤: {Message}", e.Message);
            return null;
        }
    }

    /// <summary>獲取好友邀請列表（別人寄給我的邀請）</summary>
    public List<FriendRequest> GetFriendRequests(int userId)
    {
        using var conn = db.Open();
        logger.LogDebug("查詢好友邀請列表，user_id={UserId}", userId);

        var rows = conn.Query(
            """
            SELECT fr.*, u.name, ua.account
            FROM friend_requests fr
            JOIN UserProfile u ON fr.user_id = u.user_id
            JOIN UserAuth ua ON fr.user_id = ua.id
            WHERE fr.relation_id = @userId AND fr.status = 0
            ORDER BY fr.created_at DESC
            """, new { userId }).Cast<IDictionary<string, object?>>().ToList();
        logger.LogDebug("查詢到 {Count} 筆邀請", rows.Count);

        return rows.Select(r => new FriendRequest(
            PyInt(r["id"]),
            PyInt(r["user_id"]),
            PyInt(r["relation_id"]),
            PyInt(r["type"]),
            PyInt(r["read"]),
            PyInt(r["status"]),
            PyStr(r["created_at"]),
            PyStr(r["updated_at"]),
            new UserInfo(PyInt(r["user_id"]), OrEmpty(r["name"]), PyStr(r["account"])))).ToList();
    }

    /// <summary>送出好友邀請</summary>
    public bool SendFriendInvite(int userId, SendInviteRequest data)
    {
        try
        {
            using var conn = db.Open();

            // 根據邀請碼查找目標用戶
            var target = conn.QueryFirstOrDefault<long?>(
                "SELECT user_id FROM UserProfile WHERE invite_code = @code", new { code = data.InviteCode });
            if (target is null)
            {
                logger.LogWarning("邀請碼無效: {InviteCode}", data.InviteCode);
                return false;
            }
            var targetUserId = target.Value;

            // 不能邀請自己
            if (targetUserId == userId)
            {
                logger.LogWarning("不能邀請自己");
                return false;
            }

            // 檢查是否已經是好友
            if (conn.QueryFirstOrDefault<long?>(
                    "SELECT id FROM Friendship WHERE user_id = @userId AND friend_id = @targetUserId",
                    new { userId, targetUserId }) is not null)
            {
                logger.LogWarning("已經是好友");
                return false;
            }

            // 檢查是否已有待處理的邀請
            if (conn.QueryFirstOrDefault<long?>(
                    """
                    SELECT id FROM friend_requests
                    WHERE ((user_id = @userId AND relation_id = @targetUserId) OR (user_id = @targetUserId AND relation_id = @userId))
                    AND status = 0
                    """, new { userId, targetUserId }) is not null)
            {
                logger.LogWarning("已有待處理的邀請");
                return false;
            }

            var now = TimeUtil.TaiwanNowString();

            // 創建好友邀請
            conn.Execute(
                """
                INSERT INTO friend_requests
                (user_id, relation_id, type, read, status, created_at, updated_at)
                VALUES (@userId, @targetUserId, @type, 0, 0, @now, @now)
                """, new { userId, targetUserId, type = data.Type, now });

            logger.LogInformation("邀請已發送: {UserId} -> {TargetUserId}", userId, targetUserId);
            return true;
        }
        catch (Exception e)
        {
            logger.LogError(e, "send_friend_invite 錯誤: {Message}", e.Message);
            return false;
        }
    }

    /// <summary>接受好友邀請（與 Python 相同：不檢查邀請狀態，重複接受會再新增一組 Friendship）</summary>
    public bool AcceptFriendInvite(int userId, int inviteId)
    {
        try
        {
            using var conn = db.Open();
            using var tx = conn.BeginTransaction();
            var now = TimeUtil.TaiwanNowString();

            // 獲取邀請資訊
            var inviter = conn.QueryFirstOrDefault<long?>(
                "SELECT user_id FROM friend_requests WHERE id = @inviteId AND relation_id = @userId",
                new { inviteId, userId }, tx);
            if (inviter is null)
                return false;

            // 更新邀請狀態為已接受
            conn.Execute("UPDATE friend_requests SET status = 1, read = 1, updated_at = @now WHERE id = @inviteId",
                new { now, inviteId }, tx);

            // 添加雙向好友關係
            const string insert =
                """
                INSERT INTO Friendship (user_id, friend_id, status, created_at, updated_at)
                VALUES (@a, @b, 1, @now, @now)
                """;
            conn.Execute(insert, new { a = (long)userId, b = inviter.Value, now }, tx);
            conn.Execute(insert, new { a = inviter.Value, b = (long)userId, now }, tx);

            tx.Commit();
            return true;
        }
        catch (Exception e)
        {
            logger.LogError(e, "accept_friend_invite 錯誤: {Message}", e.Message);
            return false;
        }
    }

    /// <summary>拒絕好友邀請</summary>
    public bool RefuseFriendInvite(int userId, int inviteId)
    {
        try
        {
            using var conn = db.Open();
            var now = TimeUtil.TaiwanNowString();

            // 更新邀請狀態為已拒絕
            var affected = conn.Execute(
                """
                UPDATE friend_requests
                SET status = 2, read = 1, updated_at = @now
                WHERE id = @inviteId AND relation_id = @userId
                """, new { now, inviteId, userId });
            return affected > 0;
        }
        catch (Exception e)
        {
            logger.LogError(e, "refuse_friend_invite 錯誤: {Message}", e.Message);
            return false;
        }
    }

    /// <summary>刪除好友（雙向）</summary>
    public bool RemoveFriends(int userId, List<long> friendIds)
    {
        if (friendIds.Count == 0)
            return false;

        try
        {
            using var conn = db.Open();
            using var tx = conn.BeginTransaction();

            // 刪除雙向好友關係
            conn.Execute("DELETE FROM Friendship WHERE user_id = @userId AND friend_id IN @friendIds",
                new { userId, friendIds }, tx);
            conn.Execute("DELETE FROM Friendship WHERE friend_id = @userId AND user_id IN @friendIds",
                new { userId, friendIds }, tx);

            tx.Commit();
            return true;
        }
        catch (Exception e)
        {
            logger.LogError(e, "remove_friends 錯誤: {Message}", e.Message);
            return false;
        }
    }

    /// <summary>獲取好友結果列表（我送出的邀請的狀態）— 只返回未讀的，並標記為已讀</summary>
    public List<FriendResult> GetFriendResults(int userId)
    {
        using var conn = db.Open();
        logger.LogDebug("查詢好友結果列表，user_id={UserId}", userId);

        // 只查詢未讀的結果 (read = 0)
        var rows = conn.Query(
            """
            SELECT fr.*, u.name, ua.account
            FROM friend_requests fr
            JOIN UserProfile u ON fr.relation_id = u.user_id
            JOIN UserAuth ua ON fr.relation_id = ua.id
            WHERE fr.user_id = @userId AND fr.status != 0 AND fr.read = 0
            ORDER BY fr.updated_at DESC
            """, new { userId }).Cast<IDictionary<string, object?>>().ToList();
        logger.LogDebug("查詢到 {Count} 筆未讀結果", rows.Count);

        // 標記為已讀（與 Python 相同：先 commit 再組回應，組回應失敗也已標記）
        if (rows.Count > 0)
        {
            conn.Execute("UPDATE friend_requests SET read = 1 WHERE user_id = @userId AND status != 0 AND read = 0",
                new { userId });
            logger.LogDebug("已標記 {Count} 筆結果為已讀", rows.Count);
        }

        return rows.Select(r => new FriendResult(
            PyInt(r["id"]),
            PyInt(r["user_id"]),
            PyInt(r["relation_id"]),
            PyInt(r["type"]),
            PyInt(r["status"]),
            PyInt(r["read"]),
            PyStr(r["created_at"]),
            PyStr(r["updated_at"]),
            new RelationInfo(PyInt(r["relation_id"]), OrEmpty(r["name"]), PyStr(r["account"])))).ToList();
    }

    // ---- 模擬 pydantic v1 的欄位轉型：None 對必填欄位會丟出驗證錯誤 ----

    private static long PyInt(object? v) => v switch
    {
        null or DBNull => throw new InvalidOperationException("none is not an allowed value"),
        long l => l,
        double d => (long)d, // pydantic v1 int(1.5) = 1
        string s => long.Parse(s.Trim(), CultureInfo.InvariantCulture),
        _ => Convert.ToInt64(v, CultureInfo.InvariantCulture),
    };

    private static string PyStr(object? v) => v switch
    {
        null or DBNull => throw new InvalidOperationException("none is not an allowed value"),
        string s => s,
        double d => d == Math.Floor(d) && Math.Abs(d) < 1e16
            ? d.ToString("F1", CultureInfo.InvariantCulture) // Python str(1.0) = "1.0"
            : d.ToString("R", CultureInfo.InvariantCulture),
        _ => Convert.ToString(v, CultureInfo.InvariantCulture)!,
    };

    /// <summary>Python 的 `x or ''`</summary>
    private static string OrEmpty(object? v) => Truthy(v) ? PyStr(v) : "";

    private static bool Truthy(object? v) => v switch
    {
        null or DBNull => false,
        string s => s.Length > 0,
        long l => l != 0,
        double d => d != 0,
        byte[] b => b.Length > 0,
        _ => true,
    };
}
