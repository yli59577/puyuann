using System.Text.Json;
using Microsoft.AspNetCore.Mvc;
using PuyuanApi.Core;
using PuyuanApi.Core.PyCompat;

namespace PuyuanApi.Modules.Measurement;

/// <summary>測量上傳（對應 app/measurement/api.py，掛在 /api/user）</summary>
[ApiController]
[HttpBearerAuthFilter]
[Tags("測量上傳")]
public class MeasurementController(Database db, Security security, ILogger<MeasurementController> logger) : ControllerBase
{
    private readonly MeasurementModule _module = new(db, security, logger);

    /// <summary>對應 f"Bearer {credentials.credentials}" 再交給 parse_user_id_from_token</summary>
    private int? CurrentUserId() =>
        _module.ParseUserIdFromToken($"Bearer {HttpBearerAuthFilterAttribute.GetCredentials(HttpContext)}");

    /// <summary>上傳血壓測量結果（Python 宣告為 /blood/pressure/，兩種寫法都接受）</summary>
    [HttpPost("/api/user/blood/pressure/")]
    public MeasurementUploadResponse UploadBloodPressure([FromBody] BloodPressureUpload request)
    {
        var userId = CurrentUserId();
        if (userId is null or 0) return new("1", "身份驗證失敗", null);
        if (!_module.UserExists(userId.Value)) return new("1", "用戶不存在", null);

        var recordId = _module.UploadBloodPressure(userId.Value, request.Systolic, request.Diastolic, request.Pulse, request.MeasuredAt);
        return recordId is { } id && id != 0
            ? new("0", "上傳成功", new MeasurementUploadData(id))
            : new("1", "上傳失敗", null);
    }

    /// <summary>上傳體重測量結果</summary>
    [HttpPost("/api/user/weight")]
    public MeasurementUploadResponse UploadWeight([FromBody] WeightUpload request)
    {
        var userId = CurrentUserId();
        if (userId is null or 0) return new("1", "身份驗證失敗", null);
        if (!_module.UserExists(userId.Value)) return new("1", "用戶不存在", null);

        var recordId = _module.UploadWeight(userId.Value, request.Weight, request.Bmi, request.BodyFat, request.RecordedAt);
        return recordId is { } id && id != 0
            ? new("0", "上傳成功", new MeasurementUploadData(id))
            : new("1", "上傳失敗", null);
    }

    /// <summary>上傳血糖測量結果</summary>
    [HttpPost("/api/user/blood/sugar")]
    public MeasurementUploadResponse UploadBloodSugar([FromBody] BloodSugarUpload request)
    {
        var userId = CurrentUserId();
        if (userId is null or 0) return new("1", "身份驗證失敗", null);
        if (!_module.UserExists(userId.Value)) return new("1", "用戶不存在", null);

        var recordId = _module.UploadBloodSugar(userId.Value, request.Glucose, request.MealTime, request.MeasuredAt);
        return recordId is { } id && id != 0
            ? new("0", "上傳成功", new MeasurementUploadData(id))
            : new("1", "上傳失敗", null);
    }

    /// <summary>最後上傳時間</summary>
    [HttpGet("/api/user/last-upload")]
    public LastUploadResponse GetLastUpload()
    {
        var userId = CurrentUserId();
        if (userId is null or 0) return new("1", "身份驗證失敗", null);
        if (!_module.UserExists(userId.Value)) return new("1", "用戶不存在", null);

        var lastTime = _module.GetLastUploadTime(userId.Value);
        return string.IsNullOrEmpty(lastTime)
            ? new("0", "尚無上傳記錄", null)
            : new("0", "成功", lastTime);
    }

    /// <summary>
    /// 上傳/查詢記錄。body 為任意 JSON 物件（Body(default={})）：
    /// {"record_type": 0, "record_id": 123} → 上傳記錄；{"diet": 0} 或其他 → 回傳 Swift 期望的預設格式。
    /// </summary>
    [HttpPost("/api/user/records")]
    public async Task<IActionResult> UploadRecord()
    {
        // FastAPI 先解析 body（失敗 → 驗證錯誤），之後才在函式內驗證 token
        Dictionary<string, JsonElement> request;
        try
        {
            using var reader = new StreamReader(Request.Body);
            var raw = await reader.ReadToEndAsync();
            request = string.IsNullOrWhiteSpace(raw)
                ? []
                : JsonSerializer.Deserialize<Dictionary<string, JsonElement>>(raw) ?? throw new JsonException("body 為 null");
        }
        catch (JsonException ex)
        {
            logger.LogWarning("捕捉到驗證錯誤: {Message}", ex.Message);
            return Ok(BaseResponse.Fail("The given data was invalid."));
        }

        var userId = CurrentUserId();
        if (userId is null or 0) return Ok(BaseResponse.Fail("身份驗證失敗"));
        if (!_module.UserExists(userId.Value)) return Ok(BaseResponse.Fail("用戶不存在"));

        if (request.Count > 0 && request.ContainsKey("diet"))
            return Ok(RecordsDefaultResponse.Create(userId.Value));

        if (request.Count > 0
            && request.TryGetValue("record_type", out var recordType)
            && request.TryGetValue("record_id", out var recordId))
        {
            return Ok(_module.CreateMeasurementRecord(userId.Value, recordType, recordId)
                ? BaseResponse.Ok("上傳成功")
                : BaseResponse.Fail("上傳失敗"));
        }

        return Ok(RecordsDefaultResponse.Create(userId.Value));
    }
}
