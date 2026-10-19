using System.ComponentModel.DataAnnotations;
using System.Globalization;

namespace PuyuanApi.Core.PyCompat;

/// <summary>模擬 Python 的 ValueError（訊息格式與 Python 相同，交給全域例外處理輸出）</summary>
public class PyValueError(string message) : Exception(message);

/// <summary>
/// pydantic v1 驗證錯誤（str(e) 格式與 pydantic v1 相同：「N validation error(s) for Model」+ 每欄位訊息）。
/// User 模組使用。
/// </summary>
public class PyValidationError(string model, IReadOnlyList<(string Field, string Message)> errors)
    : Exception($"{errors.Count} validation error{(errors.Count > 1 ? "s" : "")} for {model}\n"
                + string.Join("\n", errors.Select(e => $"{e.Field}\n  {e.Message}")));

/// <summary>
/// pydantic v2 單一欄位型別驗證錯誤（「1 validation error: field Input should be a valid ...」）。
/// 由 <see cref="PyCoerce"/> 丟出；A1c / Medicine / Care 模組使用。
/// </summary>
public sealed class PyValidationException(string field, string type, object? value)
    : Exception($"1 validation error: {field} Input should be a valid {(type == "int" ? "integer" : "string")} [input_value={value ?? "None"}]");

/// <summary>
/// 模擬 pydantic v2（lax 模式）對 sqlite 讀出值的型別驗證：
/// 驗證失敗時丟出 <see cref="PyValidationException"/>，對應 Python 端的 ValidationError。
/// </summary>
public static class PyCoerce
{
    public static long Int(object? v, string field) => v switch
    {
        long l => l,
        int i => i,
        double d when double.IsFinite(d) && d == Math.Floor(d) => (long)d,
        string s when long.TryParse(s.Trim(), NumberStyles.AllowLeadingSign, CultureInfo.InvariantCulture, out var l) => l,
        _ => throw new PyValidationException(field, "int", v),
    };

    public static long? OptionalInt(object? v, string field) => v is null ? null : Int(v, field);

    public static string Str(object? v, string field) =>
        v as string ?? throw new PyValidationException(field, "str", v);
}

/// <summary>pydantic 的 min_length：以 Unicode code point 計算長度（與 Python len() 相同）</summary>
[AttributeUsage(AttributeTargets.Property)]
public sealed class PyMinLengthAttribute(int length) : ValidationAttribute
{
    public override bool IsValid(object? value) => value is not string s || s.EnumerateRunes().Count() >= length;
}
