using Microsoft.AspNetCore.Mvc;
using PuyuanApi.Core;
using PuyuanApi.Core.PyCompat;

namespace PuyuanApi.Modules.User;

/// <summary>個人資訊 API（對應 app/_user/api.py，掛在 /api/user）</summary>
[ApiController]
[Tags("個人資訊")]
public class UserController(Database db, Security security, ILogger<UserController> logger) : ControllerBase
{
    private readonly UserModule _module = new(db, logger);

    private int? ParseUserId() =>
        UserModule.ParseUserIdFromToken(Request.Headers.Authorization.FirstOrDefault(), security, logger);

    /// <summary>更新個人資料（未提供的欄位會被設為 null，與 Python 版相同）</summary>
    [HttpPatch("api/user")]
    public IActionResult UpdateUserProfile([FromBody] UserProfileUpdate? request)
    {
        if (request is null) return Ok(BaseResponse.Fail("The given data was invalid."));

        // 1. 解析 Token
        var userId = ParseUserId();
        logger.LogDebug("解析後 user_id={UserId}", userId);
        if (userId is null)
        {
            logger.LogWarning("Token 解析失敗");
            return Ok(BaseResponse.Fail("authentication failed"));
        }

        // 2. 檢查用戶是否存在
        if (_module.GetUser(userId.Value) is null)
        {
            logger.LogWarning("用戶不存在");
            return Ok(BaseResponse.Fail("user not found"));
        }

        // 3. 處理空字串和類型轉換（birthday 在 module 中處理）
        var height = UserModule.ToFloatOrNone(request.Height);
        var weight = UserModule.ToFloatOrNone(request.Weight);

        var success = _module.CreateOrUpdateProfile(userId.Value, request, height, weight);
        logger.LogDebug("更新結果: success={Success}", success);

        return Ok(success ? BaseResponse.Ok("success") : BaseResponse.Fail("failed"));
    }

    /// <summary>獲取個人資料</summary>
    [HttpGet("api/user")]
    public IActionResult GetUserProfile()
    {
        // 1. 解析 Token
        var userId = ParseUserId();
        if (userId is null) return Ok(new UserProfileResponse("1", "authentication failed", null));

        // 2. 獲取用戶完整資料
        var userData = _module.GetUserCompleteData(userId.Value);
        if (userData is null) return Ok(new UserProfileResponse("1", "user not found", null));

        // 3. 按照 App 預期的格式回傳（驗證失敗時回傳帶有 status 的錯誤訊息，防止 App 崩潰）
        try
        {
            var validated = UserProfileData.FromDict(userData);
            return Ok(new UserProfileResponse("0", "success", validated));
        }
        catch (PyValidationError e)
        {
            logger.LogError(e, "資料驗證失敗: {Message}", e.Message);
            return Ok(new UserProfileResponse("1", $"data format error: {e.Message}", null));
        }
    }

    /// <summary>更新個人設定（只更新提供的欄位）</summary>
    [HttpPatch("api/user/setting")]
    public IActionResult UpdateUserSettings([FromBody] UserSettingsUpdate? request)
    {
        if (request is null) return Ok(BaseResponse.Fail("The given data was invalid."));

        var userId = ParseUserId();
        if (userId is null) return Ok(BaseResponse.Fail("authentication failed"));

        if (_module.GetUser(userId.Value) is null) return Ok(BaseResponse.Fail("user not found"));

        var success = _module.CreateOrUpdateSettings(userId.Value, request);
        return Ok(success ? BaseResponse.Ok("success") : BaseResponse.Fail("failed"));
    }

    /// <summary>更新用戶徽章（TODO: 徽章計算邏輯，目前直接回成功）</summary>
    [HttpPut("api/user/badge")]
    public IActionResult UpdateUserBadge()
    {
        var userId = ParseUserId();
        if (userId is null) return Ok(BaseResponse.Fail("authentication failed"));

        if (_module.GetUser(userId.Value) is null) return Ok(BaseResponse.Fail("user not found"));

        return Ok(BaseResponse.Ok("success"));
    }
}
