using System.ComponentModel.DataAnnotations;
using System.Text.Json.Serialization;
using PuyuanApi.Core.PyCompat;

namespace PuyuanApi.Modules.Account;

// ==================== 請求模型（對應 app/account/models.py 的 pydantic 模型）====================
// EmailStr 欄位使用 EmailStrConverter：反序列化時驗證並正規化（例如網域轉小寫），不合法即為驗證錯誤。

/// <summary>用戶註冊請求</summary>
public class UserRegister
{
    [JsonConverter(typeof(EmailStrConverter))]
    public string Email { get; set; } = null!; // 缺少欄位 → null → 必填驗證失敗

    /// <summary>密碼（至少6位）</summary>
    [PyMinLength(6)]
    public string Password { get; set; } = null!; // 缺少欄位 → null → 必填驗證失敗
}

/// <summary>用戶登入請求</summary>
public class UserLogin
{
    [JsonConverter(typeof(EmailStrConverter))]
    public string Email { get; set; } = null!; // 缺少欄位 → null → 必填驗證失敗

    /// <summary>密碼（pydantic 允許空字串）</summary>
    [Required(AllowEmptyStrings = true)]
    public string Password { get; set; } = null!; // 缺少欄位 → null → 必填驗證失敗
}

/// <summary>重設密碼請求（只需要新密碼）</summary>
public class PasswordReset
{
    /// <summary>新密碼（至少6位）</summary>
    [PyMinLength(6)]
    public string Password { get; set; } = null!; // 缺少欄位 → null → 必填驗證失敗
}

/// <summary>忘記密碼請求</summary>
public class PasswordForgot
{
    [JsonConverter(typeof(EmailStrConverter))]
    public string Email { get; set; } = null!; // 缺少欄位 → null → 必填驗證失敗
}

/// <summary>發送驗證碼請求</summary>
public class VerificationSend
{
    [JsonConverter(typeof(EmailStrConverter))]
    public string Email { get; set; } = null!; // 缺少欄位 → null → 必填驗證失敗
}

/// <summary>檢查驗證碼請求</summary>
public class VerificationCheck
{
    [JsonConverter(typeof(EmailStrConverter))]
    public string Email { get; set; } = null!; // 缺少欄位 → null → 必填驗證失敗

    /// <summary>驗證碼（pydantic 允許空字串）</summary>
    [Required(AllowEmptyStrings = true)]
    public string Code { get; set; } = null!; // 缺少欄位 → null → 必填驗證失敗
}

// ==================== 回應模型 ====================
// 一般成功 / 失敗使用 Core 的 BaseResponse(status, message)

/// <summary>登入成功回應：{"status":"0","token":"..."}</summary>
public record TokenSuccessResponse(string Status, string Token);

/// <summary>登入失敗回應：{"status":"1","message":"..."}</summary>
public record TokenErrorResponse(string Status, string Message);

/// <summary>發送驗證碼回應（response_model_exclude_none：失敗時不輸出 code）</summary>
public record VerificationSendResponse(
    string Status,
    [property: JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)] string? Code,
    string Message);
