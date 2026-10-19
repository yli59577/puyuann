using Microsoft.AspNetCore.Mvc;
using PuyuanApi.Core;

namespace PuyuanApi.Modules.Care;

/// <summary>
/// 關懷諮詢（對應 app/care/api.py，掛在 /api/user）。
/// 與其他模組不同：Python 用 Header(None) 而非 HTTPBearer，所以沒有 "Not authenticated" 回應。
/// </summary>
[ApiController]
[Tags("關懷諮詢")]
public class CareController(Database db, Security security, ILogger<CareController> logger) : ControllerBase
{
    private readonly CareModule _module = new(db, security, logger);

    private int? CurrentUserId() =>
        _module.ParseUserIdFromToken(Request.Headers.Authorization.FirstOrDefault());

    /// <summary>獲取關懷諮詢列表</summary>
    [HttpGet("/api/user/care")]
    public CareListResponse GetCareList()
    {
        try
        {
            // 未通過驗證時 user_id 為 null，查詢結果為空列表，仍回傳 status "0"（與 Python 相同）
            var cares = _module.GetCareList(CurrentUserId());
            return new("0", "ok", cares);
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "獲取關懷諮詢列表錯誤: {Message}", ex.Message);
            return new("1", "失敗", []);
        }
    }

    /// <summary>上傳關懷諮詢</summary>
    [HttpPost("/api/user/care")]
    public BaseResponse UploadCareMessage([FromBody] CareMessageUpload data)
    {
        try
        {
            _module.UploadCareMessage(CurrentUserId(), data);
            return BaseResponse.Ok("成功");
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "上傳關懷諮詢錯誤: {Message}", ex.Message);
            return BaseResponse.Fail("失敗");
        }
    }
}
