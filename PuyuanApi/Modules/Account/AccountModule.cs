using System.Data;
using Dapper;
using PuyuanApi.Core;
using PuyuanApi.Core.PyCompat;
using PuyuanApi.Modules.User;

namespace PuyuanApi.Modules.Account;

/// <summary>帳號模組 - 處理註冊、登入、密碼管理（對應 app/account/module.py 的 AccountModule）</summary>
public class AccountModule(Database db, Security security, EmailService emailService, ILogger logger)
{
    /// <summary>根據 email 查詢用戶（SQLAlchemy 的 .first()，DateTime 欄位格式錯誤會丟例外）</summary>
    private static UserAuthRow? GetUserByEmail(IDbConnection conn, string email, IDbTransaction? tx = null)
    {
        var user = conn.QueryFirstOrDefault<UserAuthRow>(UserAuthRow.SelectSql + " WHERE email = @email LIMIT 1", new { email }, tx);
        user?.ParseDates();
        return user;
    }

    /// <summary>
    /// 用戶註冊 - 支持未驗證帳號重新註冊
    /// - 帳號已驗證 → 「帳號已經存在」
    /// - 帳號未驗證 → 允許重新註冊（更新密碼和驗證過期時間，刪除舊驗證碼）
    /// - 帳號不存在 → 創建新帳號
    /// </summary>
    public (bool Success, string Message) RegisterUser(string email, string password)
    {
        try
        {
            using var conn = db.Open();
            using var tx = conn.BeginTransaction();

            // 驗證過期時間（5分鐘後，台灣時間，保留微秒與 Python 相同）
            var verificationExpiresAt = PyOrm.SqlaDateTime(PyOrm.TaiwanNowPrecise().AddMinutes(5));

            // 1. 檢查 email 是否已存在
            var existingUser = GetUserByEmail(conn, email, tx);
            if (existingUser is not null)
            {
                if (PyOrm.Truthy(existingUser.Verified))
                {
                    logger.LogInformation("帳號 {Email} 已驗證，拒絕重新註冊", email);
                    return (false, "帳號已經存在");
                }

                logger.LogInformation("帳號 {Email} 未驗證，允許重新註冊", email);

                // 1.1 刪除舊的驗證碼
                var deleted = conn.Execute("DELETE FROM verification_codes WHERE email = @email", new { email }, tx);
                logger.LogDebug("已刪除 {Count} 條舊驗證碼", deleted);

                // 1.2 更新帳號密碼和驗證過期時間，清除舊驗證碼
                conn.Execute(
                    """
                    UPDATE UserAuth SET password = @password, verification_expires_at = @verificationExpiresAt,
                                        code = NULL, updated_at = @now
                    WHERE id = @id
                    """,
                    new
                    {
                        password = Security.HashPassword(password), verificationExpiresAt,
                        now = PyOrm.SqlaDateTime(TimeUtil.TaiwanNow()), id = existingUser.Id,
                    }, tx);
                tx.Commit();

                logger.LogInformation("帳號 {Email} 已更新密碼和驗證過期時間: {ExpiresAt}", email, verificationExpiresAt);
                return (true, "註冊成功");
            }

            // 2. 帳號不存在，創建新帳號（預設未驗證）
            logger.LogInformation("帳號 {Email} 不存在，創建新帳號", email);
            var account = email.Split('@')[0];
            var created = PyOrm.SqlaDateTime(TimeUtil.TaiwanNow());
            var newUserId = conn.ExecuteScalar<long>(
                """
                INSERT INTO UserAuth (account, email, password, verified, privacy_policy, must_change_password,
                                      login_times, verification_expires_at, created_at, updated_at)
                VALUES (@account, @email, @password, 0, 0, 0, 0, @verificationExpiresAt, @created, @created);
                SELECT last_insert_rowid();
                """,
                new { account, email, password = Security.HashPassword(password), verificationExpiresAt, created }, tx);

            // 2.4 檢查是否已有 UserProfile，沒有才創建
            var hasProfile = conn.ExecuteScalar<long?>(
                "SELECT id FROM UserProfile WHERE user_id = @newUserId LIMIT 1", new { newUserId }, tx) is not null;
            if (!hasProfile)
            {
                conn.Execute(
                    "INSERT INTO UserProfile (user_id, name, badge, created_at, updated_at) VALUES (@newUserId, @account, 0, @created, @created)",
                    new { newUserId, account, created }, tx);
            }

            // 2.5 提交交易
            tx.Commit();

            logger.LogInformation("用戶 {Email} 已註冊，驗證過期時間: {ExpiresAt}", email, verificationExpiresAt);
            return (true, "註冊成功");
        }
        catch (Exception e)
        {
            logger.LogError(e, "註冊時發生錯誤: {Message}", e.Message);
            return (false, $"註冊失敗: {e.Message}");
        }
    }

    /// <summary>用戶登入，成功回傳 JWT，失敗回傳 null</summary>
    public string? LoginUser(string email, string password)
    {
        try
        {
            logger.LogInformation("--- 登入流程開始 ---");
            using var conn = db.Open();

            // 1. 查詢用戶
            var user = GetUserByEmail(conn, email);
            if (user is null)
            {
                logger.LogWarning("結果: 找不到用戶 {Email}。", email);
                return null;
            }

            // 2. 檢查是否已驗證
            if (!PyOrm.Truthy(user.Verified))
            {
                logger.LogWarning("結果: 帳號尚未驗證。");
                return null;
            }

            // 3. 驗證密碼
            if (!Security.VerifyPassword(password, user.Password))
            {
                logger.LogWarning("結果: 密碼驗證失敗。");
                return null;
            }

            // 4. 生成 Token
            var token = security.CreateAccessToken((int)user.Id);
            logger.LogInformation("--- 登入流程成功結束 ---");
            return token;
        }
        catch (Exception e)
        {
            logger.LogError(e, "登入流程中發生嚴重錯誤: {Message}", e.Message);
            return null;
        }
    }

    /// <summary>重設密碼（不需要舊密碼，透過 Token 驗證身份）</summary>
    public bool ResetPassword(long userId, string newPassword)
    {
        try
        {
            using var conn = db.Open();

            // 1. 查詢用戶
            if (UserModule.GetUser(conn, userId) is null) return false;

            // 2. 更新密碼（SQLAlchemy 只有值改變時才 UPDATE 並更新 updated_at）
            conn.Execute(
                """
                UPDATE UserAuth SET password = @password, must_change_password = 0, updated_at = @now
                WHERE id = @userId
                  AND (password IS NOT @password OR must_change_password IS NULL OR must_change_password != 0)
                """,
                new { password = Security.HashPassword(newPassword), now = PyOrm.SqlaDateTime(TimeUtil.TaiwanNow()), userId });

            logger.LogInformation("用戶 {UserId} 密碼已更新", userId);
            return true;
        }
        catch (Exception e)
        {
            logger.LogError(e, "重設密碼錯誤: {Message}", e.Message);
            return false;
        }
    }

    /// <summary>忘記密碼 - 產生 6 位數臨時密碼取代原密碼，並寄到信箱</summary>
    public bool ForgotPasswordSendTemp(string email)
    {
        try
        {
            logger.LogInformation("開始處理: {Email}", email);
            using var conn = db.Open();

            // 1. 查詢用戶
            var user = GetUserByEmail(conn, email);
            if (user is null)
            {
                logger.LogWarning("用戶不存在: {Email}", email);
                return false;
            }

            // 2. 生成 6 位數臨時密碼
            var tempPassword = GenerateCode();

            // 3. 用臨時密碼取代原本的密碼，並標記需要更改密碼
            conn.Execute(
                "UPDATE UserAuth SET password = @password, must_change_password = 1, updated_at = @now WHERE id = @id",
                new { password = Security.HashPassword(tempPassword), now = PyOrm.SqlaDateTime(TimeUtil.TaiwanNow()), id = user.Id });
            logger.LogDebug("已更新密碼為臨時密碼");

            // 4. 發送臨時密碼到郵件（發送失敗仍視為成功）
            if (emailService.SendTempPassword(email, tempPassword))
                logger.LogInformation("臨時密碼郵件發送成功");
            else
                logger.LogWarning("郵件發送失敗，但臨時密碼已設定: {TempPassword}", tempPassword);

            return true;
        }
        catch (Exception e)
        {
            logger.LogError(e, "錯誤: {Message}", e.Message);
            return false;
        }
    }

    /// <summary>檢查註冊狀態（查詢失敗視為不存在）</summary>
    public (bool Exists, bool Verified) CheckRegisterStatus(string email)
    {
        try
        {
            using var conn = db.Open();
            var user = GetUserByEmail(conn, email);
            return user is null ? (false, false) : (true, PyOrm.Truthy(user.Verified));
        }
        catch (Exception e)
        {
            logger.LogError(e, "檢查註冊狀態錯誤: {Message}", e.Message);
            return (false, false);
        }
    }

    // ========== 驗證碼相關功能 ==========

    /// <summary>生成 6 位數驗證碼（100000 ~ 999999）</summary>
    public static string GenerateCode() => Random.Shared.Next(100000, 1000000).ToString();

    /// <summary>發送驗證碼：存到 verification_codes 表並寄信，成功回傳驗證碼，失敗回傳 null</summary>
    public string? SendVerificationCode(string email)
    {
        try
        {
            logger.LogInformation("開始發送驗證碼到: {Email}", email);

            // 1. 生成驗證碼
            var code = GenerateCode();

            // 2. 存到 verification_codes 表（expires_at 使用伺服器本地時間 datetime.now()，與 Python 相同）
            using (var conn = db.Open())
            {
                conn.Execute(
                    """
                    INSERT INTO verification_codes (email, code, created_at, is_used, expires_at)
                    VALUES (@email, @code, @created, 0, @expiresAt)
                    """,
                    new
                    {
                        email, code,
                        created = PyOrm.SqlaDateTime(TimeUtil.TaiwanNow()),
                        expiresAt = PyOrm.SqlaDateTime(DateTime.Now.AddMinutes(10)),
                    });
            }
            logger.LogDebug("已儲存到資料庫");

            // 3. 發送郵件（發送失敗仍回傳成功）
            if (emailService.SendVerificationCode(email, code))
                logger.LogInformation("郵件發送成功");
            else
                logger.LogWarning("郵件發送失敗，但驗證碼已儲存: {Code}", code);

            return code;
        }
        catch (Exception e)
        {
            logger.LogError(e, "發送失敗: {Message}", e.Message);
            return null;
        }
    }

    /// <summary>
    /// 驗證驗證碼：
    /// 1. 先比對 UserAuth.code
    /// 2. 再查 verification_codes 表（未使用、未過期的最新一筆），成功後標記已使用並將用戶設為已驗證
    /// </summary>
    public bool VerifyCode(string email, string code)
    {
        try
        {
            logger.LogDebug("開始驗證 - Email: {Email}, Code: {Code}", email, code);
            using var conn = db.Open();
            using var tx = conn.BeginTransaction();
            var now = PyOrm.SqlaDateTime(TimeUtil.TaiwanNow());

            // 1. 先檢查 UserAuth.code（已註冊用戶）
            var user = GetUserByEmail(conn, email, tx);
            if (user is not null)
            {
                var dbCode = PyOrm.Truthy(user.Code) ? PyOrm.Str(user.Code).Trim() : null;
                var inputCode = code.Length > 0 ? code.Trim() : null;
                if (!string.IsNullOrEmpty(dbCode) && !string.IsNullOrEmpty(inputCode) && dbCode == inputCode)
                {
                    logger.LogInformation("從 UserAuth.code 驗證成功");
                    conn.Execute("UPDATE UserAuth SET verified = 1, code = NULL, updated_at = @now WHERE id = @id",
                        new { now, id = user.Id }, tx);
                    tx.Commit();
                    return true;
                }
                logger.LogDebug("UserAuth.code 不匹配，繼續檢查 verification_codes 表");
            }
            else
            {
                logger.LogDebug("用戶不存在，檢查 verification_codes 表");
            }

            // 2. 再檢查 verification_codes 表
            var verification = conn.QueryFirstOrDefault(
                """
                SELECT id, created_at, expires_at FROM verification_codes
                WHERE email = @email AND code = @code AND is_used = 0
                ORDER BY created_at DESC LIMIT 1
                """, new { email, code }, tx) as IDictionary<string, object?>;

            if (verification is null)
            {
                logger.LogWarning("驗證碼不存在或已使用 - Email: {Email}, Code: {Code}", email, code);
                return false;
            }

            // 3. 檢查是否過期（naive 本地時間比較；有時區的值在 Python 會 TypeError → 失敗）
            PyOrmDateTime.FromDb(verification["created_at"]);
            var expiresAt = PyOrmDateTime.FromDb(verification["expires_at"]);
            if (expiresAt is { } exp)
            {
                if (exp.IsAware) throw new InvalidOperationException("can't compare offset-naive and offset-aware datetimes");
                if (DateTime.Now > exp.Value)
                {
                    logger.LogWarning("驗證碼已過期 - Email: {Email}, Code: {Code}", email, code);
                    return false;
                }
            }

            // 4. 標記為已使用
            conn.Execute("UPDATE verification_codes SET is_used = 1 WHERE id = @id", new { id = verification["id"] }, tx);

            // 5. 將用戶標記為已驗證，並清除驗證過期時間（有變動才 UPDATE / 更新 updated_at）
            if (user is not null)
            {
                conn.Execute(
                    """
                    UPDATE UserAuth SET verified = 1, verification_expires_at = NULL, updated_at = @now
                    WHERE id = @id AND (verified IS NULL OR verified = 0 OR verification_expires_at IS NOT NULL)
                    """, new { now, id = user.Id }, tx);
            }

            tx.Commit();
            logger.LogInformation("Email: {Email}, Code: {Code}, 用戶已驗證", email, code);
            return true;
        }
        catch (Exception e)
        {
            logger.LogError(e, "驗證驗證碼錯誤: {Message}", e.Message);
            return false;
        }
    }
}
