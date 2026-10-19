namespace PuyuanApi.Core;

/// <summary>所有 API 共用的基本回應：status "0" = 成功、"1" = 失敗</summary>
public record BaseResponse(string Status, string Message)
{
    public static BaseResponse Ok(string message = "ok") => new("0", message);
    public static BaseResponse Fail(string message = "失敗") => new("1", message);
}
