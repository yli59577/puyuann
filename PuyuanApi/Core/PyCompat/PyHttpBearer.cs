using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.Filters;

namespace PuyuanApi.Core.PyCompat;

// FastAPI HTTPBearer() 的兩種移植。兩者的錯誤訊息與執行時機不同（各自對過 Python 版），不可互換。

/// <summary>
/// 模擬 FastAPI 的 HTTPBearer()（auto_error=True），以「授權過濾器」實作，所以會在 body 驗證之前執行。
/// 缺少 Authorization、scheme 不是 bearer（不分大小寫）或沒有 credentials（會 strip）時，
/// 一律回 {"status":"1","message":"Not authenticated"}。
/// 用 <see cref="GetCredentials"/> 取得 credentials。Measurement / A1c / Medicine 模組使用。
/// </summary>
[AttributeUsage(AttributeTargets.Class | AttributeTargets.Method)]
public sealed class HttpBearerAuthFilterAttribute : Attribute, IAuthorizationFilter
{
    private const string ItemKey = "HttpBearer.Credentials";

    public void OnAuthorization(AuthorizationFilterContext context)
    {
        var header = context.HttpContext.Request.Headers.Authorization.FirstOrDefault();
        var (scheme, credentials) = PartitionScheme(header);
        if (string.IsNullOrEmpty(header) || scheme.Length == 0 || credentials.Length == 0
            || !scheme.Equals("bearer", StringComparison.OrdinalIgnoreCase))
        {
            context.Result = new OkObjectResult(BaseResponse.Fail("Not authenticated"));
            return;
        }
        context.HttpContext.Items[ItemKey] = credentials;
    }

    /// <summary>取得 HTTPBearer 解析出的 credentials（對應 credentials.credentials）</summary>
    public static string GetCredentials(HttpContext ctx) => ctx.Items[ItemKey] as string ?? "";

    /// <summary>對應 starlette 的 get_authorization_scheme_param：partition(" ") 後 strip</summary>
    private static (string Scheme, string Param) PartitionScheme(string? header)
    {
        if (string.IsNullOrEmpty(header)) return ("", "");
        var idx = header.IndexOf(' ');
        return idx < 0 ? (header, "") : (header[..idx], header[(idx + 1)..].Trim());
    }
}

/// <summary>
/// 模擬 FastAPI 的 HTTPBearer()（auto_error=True），以「動作過濾器」實作（Order -3000，早於 ModelStateInvalidFilter 的 -2000）。
/// 沒有 Authorization header 或 credentials（不 strip）→ "Not authenticated"；scheme 不是 bearer → "Invalid authentication credentials"。
/// 通過後把 credentials 放進 HttpContext.Items，供 controller 以 <see cref="PyAuth.ParseUserId"/> 取得使用者 id。
/// Journal / Else 模組使用。
/// </summary>
[AttributeUsage(AttributeTargets.Class | AttributeTargets.Method)]
public sealed class HttpBearerActionFilterAttribute : Attribute, IActionFilter, IOrderedFilter
{
    public const string ItemKey = "py_bearer_credentials";

    // ModelStateInvalidFilter 的 Order 是 -2000，這裡要比它更早
    public int Order => -3000;

    public void OnActionExecuting(ActionExecutingContext context)
    {
        var header = context.HttpContext.Request.Headers.Authorization.ToString();

        // get_authorization_scheme_param: scheme, _, param = header.partition(" ")
        string scheme = "", credentials = "";
        if (!string.IsNullOrEmpty(header))
        {
            var idx = header.IndexOf(' ');
            scheme = idx < 0 ? header : header[..idx];
            credentials = idx < 0 ? "" : header[(idx + 1)..];
        }

        if (string.IsNullOrEmpty(header) || scheme.Length == 0 || credentials.Length == 0)
        {
            context.Result = new OkObjectResult(BaseResponse.Fail("Not authenticated"));
            return;
        }
        if (!scheme.Equals("bearer", StringComparison.OrdinalIgnoreCase))
        {
            context.Result = new OkObjectResult(BaseResponse.Fail("Invalid authentication credentials"));
            return;
        }

        context.HttpContext.Items[ItemKey] = credentials;
    }

    public void OnActionExecuted(ActionExecutedContext context) { }
}

/// <summary>
/// 對應 Python 各模組的 parse_user_id_from_token(f"Bearer {credentials.credentials}")。
/// 搭配 <see cref="HttpBearerActionFilterAttribute"/> 使用。
/// </summary>
public static class PyAuth
{
    public static int? ParseUserId(HttpContext http, Security security)
    {
        if (http.Items[HttpBearerActionFilterAttribute.ItemKey] is not string credentials) return null;

        // authorization.split(' ')[1]
        var parts = $"Bearer {credentials}".Split(' ');
        var userId = security.VerifyToken(parts[1]);

        // Python: `if not user_id` → 0 也視為失敗
        return userId is null or 0 ? null : userId;
    }
}
