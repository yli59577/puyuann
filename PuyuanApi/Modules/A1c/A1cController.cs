using Microsoft.AspNetCore.Mvc;
using PuyuanApi.Core;
using PuyuanApi.Core.PyCompat;

namespace PuyuanApi.Modules.A1c;

/// <summary>糖化血色素（對應 app/a1c/api.py，掛在 /api/user）</summary>
[ApiController]
[HttpBearerAuthFilter]
[Tags("糖化血色素")]
public class A1cController(Database db, Security security, ILogger<A1cController> logger) : ControllerBase
{
    private readonly A1cModule _module = new(db, security, logger);

    private int? CurrentUserId() =>
        _module.ParseUserIdFromToken($"Bearer {HttpBearerAuthFilterAttribute.GetCredentials(HttpContext)}");

    /// <summary>上傳糖化血色素</summary>
    [HttpPost("/api/user/a1c")]
    public BaseResponse UploadA1c([FromBody] A1cUpload request)
    {
        var userId = CurrentUserId();
        if (userId is null or 0) return BaseResponse.Fail("身份驗證失敗");

        return _module.UploadA1c(userId.Value, request.A1c, request.RecordedAt)
            ? BaseResponse.Ok("成功")
            : BaseResponse.Fail("失敗");
    }

    /// <summary>獲取糖化血色素</summary>
    [HttpGet("/api/user/a1c")]
    public A1cListResponse GetA1cList()
    {
        var userId = CurrentUserId();
        if (userId is null or 0) return new("1", "身份驗證失敗", []);

        // get_a1c_list 失敗時回傳 []（不是 None），因此 Python 的「失敗」分支實際上不會發生
        return new("0", "ok", _module.GetA1cList(userId.Value));
    }

    /// <summary>刪除糖化血色素（JSON body: {"ids[]": [52]}）</summary>
    [HttpDelete("/api/user/a1c")]
    public BaseResponse DeleteA1c([FromBody] A1cDeleteRequest request)
    {
        var userId = CurrentUserId();
        if (userId is null or 0) return BaseResponse.Fail("身份驗證失敗");

        return _module.DeleteA1cRecords(userId.Value, request.Ids)
            ? BaseResponse.Ok("ok")
            : BaseResponse.Fail("失敗");
    }
}
