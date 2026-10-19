using Microsoft.AspNetCore.Mvc;
using PuyuanApi.Core;
using PuyuanApi.Modules.User;

namespace PuyuanApi.Modules.Account;

/// <summary>用戶身份 API（對應 app/account/api.py，掛在 /api）</summary>
[ApiController]
[Tags("用戶身份")]
public class AccountController(Database db, Security security, EmailService emailService, ILogger<AccountController> logger)
    : ControllerBase
{
    private readonly AccountModule _module = new(db, security, emailService, logger);

    private static readonly BaseResponse InvalidData = BaseResponse.Fail("The given data was invalid.");

    /// <summary>用戶註冊</summary>
    [HttpPost("api/register")]
    public IActionResult RegisterUser([FromBody] UserRegister? request)
    {
        if (request is null) return Ok(InvalidData);

        var (success, message) = _module.RegisterUser(request.Email, request.Password);
        return Ok(success ? BaseResponse.Ok("成功") : BaseResponse.Fail(message));
    }

    /// <summary>
    /// 檢查帳號是否可以註冊（?email=）
    /// - "0" = 帳號可以註冊（不存在或未驗證）
    /// - "1" = 帳號已存在且已驗證
    /// </summary>
    [HttpGet("api/register/check")]
    public IActionResult CheckRegister()
    {
        // 直接讀 Query：與 FastAPI 相同，?email= 空字串視為有效值，重複參數取最後一個
        if (!Request.Query.TryGetValue("email", out var values)) return Ok(InvalidData);
        var email = values[^1] ?? "";

        try
        {
            var (exists, verified) = _module.CheckRegisterStatus(email);
            BaseResponse response;
            if (!exists)
            {
                response = BaseResponse.Ok("帳號可以註冊");
                logger.LogDebug("帳號不存在，允許註冊");
            }
            else if (verified)
            {
                response = BaseResponse.Fail("帳號已存在");
                logger.LogDebug("帳號已驗證，不允許註冊");
            }
            else
            {
                response = BaseResponse.Ok("帳號未驗證，可以重新註冊");
                logger.LogDebug("帳號未驗證，允許重新註冊");
            }
            return Ok(response);
        }
        catch (Exception e)
        {
            logger.LogError(e, "check_register 錯誤: {Message}", e.Message);
            return Ok(BaseResponse.Fail("查詢失敗"));
        }
    }

    /// <summary>用戶登入：成功 {"status":"0","token":...}；失敗 {"status":"1","message":...}</summary>
    [HttpPost("api/auth")]
    public IActionResult LoginUser([FromBody] UserLogin? request)
    {
        if (request is null) return Ok(InvalidData);

        var token = _module.LoginUser(request.Email, request.Password);
        return token is not null
            ? Ok(new TokenSuccessResponse("0", token))
            : Ok(new TokenErrorResponse("1", "登入失敗，帳號或密碼錯誤"));
    }

    /// <summary>重設密碼（需要 Bearer Token，只需要新密碼）</summary>
    [HttpPost("api/password/reset")]
    public IActionResult ResetPassword([FromBody] PasswordReset? request)
    {
        if (request is null) return Ok(InvalidData);

        // 1. 解析 Token 獲取用戶 ID
        var userId = UserModule.ParseUserIdFromToken(Request.Headers.Authorization.FirstOrDefault(), security, logger);
        if (userId is null) return Ok(BaseResponse.Fail("失敗"));

        // 2. 直接重設密碼（不需要舊密碼）
        return Ok(_module.ResetPassword(userId.Value, request.Password) ? BaseResponse.Ok("成功") : BaseResponse.Fail("失敗"));
    }

    /// <summary>忘記密碼 - 發送臨時密碼到郵件</summary>
    [HttpPost("api/password/forgot")]
    public IActionResult ForgotPassword([FromBody] PasswordForgot? request)
    {
        if (request is null) return Ok(InvalidData);

        return Ok(_module.ForgotPasswordSendTemp(request.Email) ? BaseResponse.Ok("成功") : BaseResponse.Fail("失敗"));
    }

    /// <summary>發送驗證碼到郵箱：成功 {"status":"0","code":"089682","message":"成功"}</summary>
    [HttpPost("api/verification/send")]
    public IActionResult SendVerification([FromBody] VerificationSend? request)
    {
        if (request is null) return Ok(InvalidData);

        var code = _module.SendVerificationCode(request.Email);
        return code is not null
            ? Ok(new VerificationSendResponse("0", code, "成功"))
            : Ok(new VerificationSendResponse("1", null, "失敗"));
    }

    /// <summary>檢查驗證碼是否正確</summary>
    [HttpPost("api/verification/check")]
    public IActionResult CheckVerification([FromBody] VerificationCheck? request)
    {
        if (request is null) return Ok(InvalidData);

        return Ok(_module.VerifyCode(request.Email, request.Code) ? BaseResponse.Ok("成功") : BaseResponse.Fail("失敗"));
    }
}
