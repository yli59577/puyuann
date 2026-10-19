using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using System.Security.Cryptography;
using System.Text;
using Microsoft.IdentityModel.Tokens;

namespace PuyuanApi.Core;

/// <summary>JWT 與密碼工具（對應 app/core/security.py）</summary>
public class Security
{
    private readonly SymmetricSecurityKey _key;
    private readonly int _expireHours;

    public Security()
    {
        var secret = DotEnv.Get("SECRET_KEY");
        if (string.IsNullOrEmpty(secret))
            throw new InvalidOperationException("錯誤：找不到 SECRET_KEY，請檢查您的 .env 檔案。");

        _key = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(secret));
        _expireHours = DotEnv.GetInt("ACCESS_TOKEN_EXPIRE_HOURS", 24);
    }

    /// <summary>暫時停用密碼加密，直接返回明文密碼（與 Python 版相同）</summary>
    public static string HashPassword(string password) => password;

    /// <summary>暫時停用密碼驗證，直接比對明文密碼（與 Python 版相同）</summary>
    public static bool VerifyPassword(string plain, string? hashed) => plain == hashed;

    /// <summary>建立 JWT（HS256，sub = 使用者 id，與 Python 版發出的 token 互通）</summary>
    public string CreateAccessToken(int userId, TimeSpan? expiresDelta = null)
    {
        var handler = new JwtSecurityTokenHandler();
        var token = new JwtSecurityToken(
            claims: [new Claim(JwtRegisteredClaimNames.Sub, userId.ToString())],
            expires: DateTime.UtcNow + (expiresDelta ?? TimeSpan.FromHours(_expireHours)),
            signingCredentials: new SigningCredentials(_key, SecurityAlgorithms.HmacSha256));
        return handler.WriteToken(token);
    }

    /// <summary>驗證 JWT，成功回傳 sub（使用者 id），失敗回傳 null</summary>
    public int? VerifyToken(string token)
    {
        try
        {
            var handler = new JwtSecurityTokenHandler { MapInboundClaims = false };
            var principal = handler.ValidateToken(token, new TokenValidationParameters
            {
                ValidateIssuer = false,
                ValidateAudience = false,
                ValidateLifetime = true,
                ClockSkew = TimeSpan.Zero,
                IssuerSigningKey = _key,
                ValidAlgorithms = [SecurityAlgorithms.HmacSha256],
            }, out _);

            var sub = principal.FindFirst(JwtRegisteredClaimNames.Sub)?.Value;
            return int.TryParse(sub, out var id) ? id : null;
        }
        catch
        {
            return null;
        }
    }

    /// <summary>從 Authorization: Bearer xxx 解析使用者 id（對應各模組的 parse_user_id_from_token）</summary>
    public int? GetUserId(HttpRequest request)
    {
        var header = request.Headers.Authorization.ToString();
        // FastAPI HTTPBearer 對 scheme 不分大小寫
        if (string.IsNullOrEmpty(header) || !header.StartsWith("Bearer ", StringComparison.OrdinalIgnoreCase)) return null;
        return VerifyToken(header["Bearer ".Length..].Trim());
    }

    /// <summary>生成 6 位數驗證碼</summary>
    public static string GenerateVerificationCode() =>
        RandomNumberGenerator.GetInt32(0, 1_000_000).ToString("D6");
}
