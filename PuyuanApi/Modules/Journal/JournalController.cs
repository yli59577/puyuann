using Microsoft.AspNetCore.Mvc;
using PuyuanApi.Core;
using PuyuanApi.Core.PyCompat;

namespace PuyuanApi.Modules.Journal;

/// <summary>日記 API（對應 app/_journal/api.py，掛在 /api/user）</summary>
[ApiController]
[HttpBearerActionFilter]
[Tags("日記")]
public class JournalController(Database db, Security security, ILogger<JournalController> logger) : ControllerBase
{
    private readonly JournalModule _module = new(db, logger);

    /// <summary>獲取日記列表資料</summary>
    [HttpGet("api/user/diary")]
    public ActionResult<DiaryListResponse> GetDiaryList([FromQuery(Name = "date")] string? date)
    {
        // date 為必填（Query(...)）；空字串仍算有傳
        if (!Request.Query.ContainsKey("date"))
            return Ok(BaseResponse.Fail("The given data was invalid."));
        date ??= "";

        // 1. 解析 Token
        var userId = PyAuth.ParseUserId(HttpContext, security);
        logger.LogDebug("Parsed user_id: {UserId}", userId);
        if (userId is null)
            return Ok(new DiaryListResponse("1", "身份驗證失敗", []));

        // 2. 檢查用戶是否存在
        if (!_module.UserExists(userId.Value))
            return Ok(new DiaryListResponse("1", "用戶不存在", []));

        // 3. 獲取日記列表（Python 的 get_diary_list 失敗時也回傳 []，所以永遠是 "ok"）
        var diaryList = _module.GetDiaryList(userId.Value, date);
        logger.LogDebug("get_diary_list returned {Count} records", diaryList.Count);
        return Ok(new DiaryListResponse("0", "ok", diaryList));
    }

    /// <summary>上傳飲食日記</summary>
    [HttpPost("api/user/diet")]
    public ActionResult<DietUploadResponse> UploadDiet([FromBody] DietUpload request)
    {
        // 1. 解析 Token
        var userId = PyAuth.ParseUserId(HttpContext, security);
        if (userId is null)
            return Ok(new DietUploadResponse("1", "身份驗證失敗", null));

        // 2. 檢查用戶是否存在
        if (!_module.UserExists(userId.Value))
            return Ok(new DietUploadResponse("1", "用戶不存在", null));

        // 3. 記錄接收到的 tag
        logger.LogDebug("Received tag: {Tag}", string.Join(",", request.Tag));

        // 4. 上傳飲食日記
        var success = _module.UploadDiet(userId.Value, request.Description, request.Meal, request.Tag,
            request.Image, request.Lat, request.Lng, request.RecordedAt);

        return success
            ? Ok(new DietUploadResponse("0", "ok", "")) // TODO: 實作圖片上傳功能後返回圖片 URL
            : Ok(new DietUploadResponse("1", "失敗", null));
    }

    /// <summary>刪除日記記錄</summary>
    [HttpDelete("api/user/records")]
    public ActionResult<BaseResponse> DeleteRecords([FromBody] DeleteRecordsRequest request)
    {
        // 1. 解析 Token
        var userId = PyAuth.ParseUserId(HttpContext, security);
        if (userId is null)
            return Ok(BaseResponse.Fail("身份驗證失敗"));

        // 2. 檢查用戶是否存在
        if (!_module.UserExists(userId.Value))
            return Ok(BaseResponse.Fail("用戶不存在"));

        // 3. 刪除記錄
        return _module.DeleteRecords(userId.Value, request.DeleteObject)
            ? Ok(BaseResponse.Ok("ok"))
            : Ok(BaseResponse.Fail("失敗"));
    }
}
