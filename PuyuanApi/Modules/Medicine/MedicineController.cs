using Microsoft.AspNetCore.Mvc;
using PuyuanApi.Core;
using PuyuanApi.Core.PyCompat;

namespace PuyuanApi.Modules.Medicine;

/// <summary>就醫、藥物資訊（對應 app/medicine/api.py，掛在 /api/user）</summary>
[ApiController]
[HttpBearerAuthFilter]
[Tags("就醫、藥物資訊")]
public class MedicineController(Database db, Security security, ILogger<MedicineController> logger) : ControllerBase
{
    private readonly MedicineModule _module = new(db, security, logger);

    private int? CurrentUserId() =>
        _module.ParseUserIdFromToken($"Bearer {HttpBearerAuthFilterAttribute.GetCredentials(HttpContext)}");

    /// <summary>獲取就醫資訊（永遠回傳 medical_info 物件，避免 Swift 解析失敗）</summary>
    [HttpGet("/api/user/medical")]
    public MedicalInfoResponse GetMedicalInfo()
    {
        var userId = CurrentUserId();
        if (userId is null or 0)
            return new("1", "authentication failed", MedicalInfo.Default(0));

        var info = _module.GetMedicalInfo(userId.Value);
        return new("0", "ok", info ?? MedicalInfo.Default(userId.Value));
    }

    /// <summary>更新就醫資訊</summary>
    [HttpPatch("/api/user/medical")]
    public BaseResponse UpdateMedicalInfo([FromBody] MedicalInfoUpdate request)
    {
        var userId = CurrentUserId();
        if (userId is null or 0) return BaseResponse.Fail("authentication failed");

        return _module.UpdateMedicalInfo(userId.Value, request.Oad, request.Insulin, request.AntiHypertensives, request.DiabetesType)
            ? BaseResponse.Ok("success")
            : BaseResponse.Fail("failed");
    }

    /// <summary>獲取所有藥物資訊</summary>
    [HttpGet("/api/user/drug-used")]
    public DrugUsedListResponse GetDrugUsedList()
    {
        var userId = CurrentUserId();
        if (userId is null or 0) return new("1", "authentication failed", []);

        // get_drug_used_list 失敗時回傳 []（不是 None），因此 Python 的 "failed" 分支實際上不會發生
        return new("0", "ok", _module.GetDrugUsedList(userId.Value));
    }

    /// <summary>上傳藥物資訊</summary>
    [HttpPost("/api/user/drug-used")]
    public BaseResponse UploadDrugUsed([FromBody] DrugUsedUpload request)
    {
        var userId = CurrentUserId();
        if (userId is null or 0) return BaseResponse.Fail("authentication failed");

        return _module.UploadDrugUsed(userId.Value, request.Type, request.Name, request.RecordedAt)
            ? BaseResponse.Ok("success")
            : BaseResponse.Fail("failed");
    }

    /// <summary>刪除藥物資訊（JSON body: {"ids[]": [1, 2]}）</summary>
    [HttpDelete("/api/user/drug-used")]
    public BaseResponse DeleteDrugUsed([FromBody] DrugUsedDeleteRequest request)
    {
        var userId = CurrentUserId();
        if (userId is null or 0) return BaseResponse.Fail("authentication failed");

        return _module.DeleteDrugUsedRecords(userId.Value, request.Ids)
            ? BaseResponse.Ok("ok")
            : BaseResponse.Fail("failed");
    }
}
