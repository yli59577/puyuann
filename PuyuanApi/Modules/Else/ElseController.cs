using Microsoft.AspNetCore.Mvc;
using PuyuanApi.Core;
using PuyuanApi.Core.PyCompat;

namespace PuyuanApi.Modules.Else;

/// <summary>
/// 其他 API（對應 app/_else/api.py，掛在 /api）。
/// 註：Python 的 PUT /api/user/badge 會被 _user 模組先註冊的同路徑路由蓋掉（永遠不會執行），
///     因此這裡不註冊，交由 User 模組處理，避免路由衝突。
/// </summary>
[ApiController]
[Tags("其他")]
public class ElseController(Database db, Security security, ILogger<ElseController> logger) : ControllerBase
{
    private readonly ElseModule _module = new(db, logger);

    /// <summary>最新消息（不需要 Token）</summary>
    [HttpGet("api/news")]
    public ActionResult<NewsResponse> GetNews()
    {
        try
        {
            var newsList = _module.GetNewsList();
            if (newsList.Count == 0)
                return Ok(new NewsResponse("0", "目前沒有最新消息", []));

            return Ok(new NewsResponse("0", "ok", newsList));
        }
        catch (Exception ex)
        {
            return Ok(new NewsResponse("1", $"查詢失敗: {ex.Message}", []));
        }
    }

    /// <summary>分享：將健康記錄（血壓/體重/血糖/飲食）分享給親友或糖友</summary>
    [HttpPost("api/share")]
    [HttpBearerActionFilter]
    public ActionResult<BaseResponse> ShareContent([FromBody] ShareRequest request)
    {
        try
        {
            var currentUserId = PyAuth.ParseUserId(HttpContext, security);
            if (currentUserId is null)
                return Ok(BaseResponse.Fail("身份驗證失敗"));

            var success = _module.CreateShare(request.Id, request.Type, request.RelationType, currentUserId.Value);
            return success
                ? Ok(BaseResponse.Ok("ok"))
                : Ok(BaseResponse.Fail("記錄不存在或分享失敗"));
        }
        catch (Exception ex)
        {
            return Ok(BaseResponse.Fail($"分享失敗: {ex.Message}"));
        }
    }

    /// <summary>查看分享：根據類型查詢分享給自己的健康記錄</summary>
    [HttpGet("api/share/{type}")]
    [HttpBearerActionFilter]
    public ActionResult<ShareRecordsResponse> ViewShareByType([FromRoute] int type)
    {
        try
        {
            // 驗證 type 範圍
            if (type < 0 || type > 4)
                return Ok(new ShareRecordsResponse("1", "無效的記錄類型", []));

            var currentUserId = PyAuth.ParseUserId(HttpContext, security);
            if (currentUserId is null)
                return Ok(new ShareRecordsResponse("1", "身份驗證失敗", []));

            logger.LogDebug("查詢分享記錄: type={Type}, user_id={UserId}", type, currentUserId);

            var records = _module.GetSharedRecords(type, currentUserId.Value);
            return Ok(new ShareRecordsResponse("0", "ok", records));
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "查詢分享記錄失敗: {Message}", ex.Message);
            return Ok(new ShareRecordsResponse("1", $"查詢失敗: {ex.Message}", []));
        }
    }
}
