using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.AspNetCore.Diagnostics;
using Microsoft.AspNetCore.Mvc;
using PuyuanApi.Core;

// 載入 .env（先找專案資料夾，再找上一層的 Python 專案根目錄）
DotEnv.Load(".env", Path.Combine("..", ".env"));

var builder = WebApplication.CreateBuilder(args);

var host = DotEnv.Get("API_HOST", "0.0.0.0");
var port = DotEnv.GetInt("API_PORT", 8000);
builder.WebHost.UseUrls($"http://{host}:{port}");

// 資料庫：預設為 PuyuanApi/Data/Puyuan.db（可用 appsettings 的 Database:Path 覆寫）
var dbPath = builder.Configuration["Database:Path"] ?? Path.Combine("Data", "Puyuan.db");
builder.Services.AddSingleton(new Database(Path.Combine(builder.Environment.ContentRootPath, dbPath)));
builder.Services.AddSingleton<Security>();
builder.Services.AddSingleton<EmailService>();
builder.Services.AddHostedService<CleanupService>();

builder.Services
    .AddControllers()
    .ConfigureApiBehaviorOptions(o =>
    {
        // 不輸出 ProblemDetails，讓 415 等錯誤交給下方 UseStatusCodePages 統一轉成 status "1"
        o.SuppressMapClientErrors = true;

        // 驗證錯誤（缺欄位、型別錯誤）一律回 200 + status "1"，讓 App 能解析 JSON
        o.InvalidModelStateResponseFactory = ctx =>
        {
            var logger = ctx.HttpContext.RequestServices.GetRequiredService<ILogger<Program>>();
            logger.LogWarning("捕捉到驗證錯誤: {Errors}",
                string.Join("; ", ctx.ModelState.Where(e => e.Value?.Errors.Count > 0)
                    .Select(e => $"{e.Key}: {string.Join(",", e.Value!.Errors.Select(x => x.ErrorMessage))}")));
            return new OkObjectResult(BaseResponse.Fail("The given data was invalid."));
        };
    })
    .AddJsonOptions(o =>
    {
        o.JsonSerializerOptions.PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower;
        o.JsonSerializerOptions.PropertyNameCaseInsensitive = false; // pydantic 欄位名稱區分大小寫
        o.JsonSerializerOptions.NumberHandling = JsonNumberHandling.AllowReadingFromString;
        o.JsonSerializerOptions.Converters.Add(new LenientStringConverter());
        o.JsonSerializerOptions.Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping;
    });

builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(c =>
{
    c.SwaggerDoc("v1", new() { Title = "普元後端 API", Description = "普元 IoT 專案後端 API 服務", Version = "1.0.0" });
    c.CustomSchemaIds(t => t.FullName); // 不同模組可有同名 DTO
});

builder.Services.AddCors(o => o.AddDefaultPolicy(p => p.AllowAnyOrigin().AllowAnyMethod().AllowAnyHeader()));

var app = builder.Build();

// 全域例外處理：所有錯誤都回 200 + status "1"，防止 App 崩潰
app.UseExceptionHandler(errorApp => errorApp.Run(async ctx =>
{
    var ex = ctx.Features.Get<IExceptionHandlerFeature>()?.Error;
    app.Logger.LogError(ex, "捕捉到未預期錯誤: {Message}", ex?.Message);
    ctx.Response.StatusCode = StatusCodes.Status200OK;
    await ctx.Response.WriteAsJsonAsync(BaseResponse.Fail($"伺服器內部錯誤: {ex?.Message}"));
}));

// 404 / 405 等 HTTP 錯誤也轉成 200 + status "1"
app.UseStatusCodePages(async ctx =>
{
    var res = ctx.HttpContext.Response;
    var message = res.StatusCode switch
    {
        404 => "Not Found",
        405 => "Method Not Allowed",
        401 => "Not authenticated",
        415 => "The given data was invalid.",
        _ => $"HTTP {res.StatusCode}",
    };
    app.Logger.LogWarning("捕捉到 HTTP 錯誤: {Message}", message);
    res.StatusCode = StatusCodes.Status200OK;
    await res.WriteAsJsonAsync(BaseResponse.Fail(message));
});

// FastAPI 沒有 Content-Type 也會當 JSON 解析；ASP.NET 會回 415，這裡補上預設值
app.Use((ctx, next) =>
{
    if (string.IsNullOrEmpty(ctx.Request.ContentType) && (ctx.Request.ContentLength > 0 || ctx.Request.Headers.TransferEncoding.Count > 0))
        ctx.Request.ContentType = "application/json";
    return next(ctx);
});

app.UseCors();

app.UseSwagger();
app.UseSwaggerUI(c =>
{
    c.RoutePrefix = "docs"; // 與 FastAPI 相同：/docs
    c.SwaggerEndpoint("/swagger/v1/swagger.json", "普元後端 API v1");
});

app.MapControllers();

app.MapGet("/", () => new { message = "普元後端 API 服務正在運行", version = "1.0.0" });

app.Logger.LogInformation("資料庫: {Path}", app.Services.GetRequiredService<Database>().DbPath);
app.Logger.LogInformation("訪問 API 文檔: http://{Host}:{Port}/docs", host, port);

try
{
    app.Run();
}
catch (System.Net.Sockets.SocketException ex) when (ex.SocketErrorCode is System.Net.Sockets.SocketError.AccessDenied or System.Net.Sockets.SocketError.AddressAlreadyInUse)
{
    // 10013：埠號落在 Windows 保留範圍（Hyper-V / WSL）；10048：埠號已被其他程式使用
    // host 啟動失敗後 logger 已被釋放，直接寫到 stderr
    Console.Error.WriteLine(
        $"無法使用埠號 {port}（{ex.SocketErrorCode}）。請修改 .env 的 API_PORT。" +
        "可用 `netsh int ipv4 show excludedportrange protocol=tcp` 查看 Windows 保留的埠號範圍。");
    Environment.ExitCode = 1;
}
