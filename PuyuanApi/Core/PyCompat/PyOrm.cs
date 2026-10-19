using System.Globalization;
using System.Text;
using System.Text.RegularExpressions;

namespace PuyuanApi.Core.PyCompat;

/// <summary>
/// Python 內建行為相容工具（truthiness、str()、float repr、float()/int() 解析），
/// 對應 FastAPI + pydantic v1 + SQLAlchemy ORM 的程式路徑。User / Account 模組使用。
/// <para>
/// 與 <see cref="Py"/> 的差異：<see cref="FloatRepr"/> 遇到 NaN/Inf 會丟出
/// <see cref="PyValueError"/>（FastAPI JSON 輸出的 "Out of range float values are not JSON compliant"），
/// <see cref="Str"/> 對 bytes 以 UTF-8 解碼，且不處理 DBNull。Journal / Else 請用 <see cref="Py"/>。
/// </para>
/// </summary>
public static class PyOrm
{
    private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

    /// <summary>Python 的 bool(x)</summary>
    public static bool Truthy(object? v) => v switch
    {
        null => false,
        bool b => b,
        long l => l != 0,
        int i => i != 0,
        double d => d != 0,
        string s => s.Length > 0,
        byte[] bytes => bytes.Length > 0,
        _ => true,
    };

    /// <summary>Python 的 <c>x or fallback</c></summary>
    public static object Or(object? v, object fallback) => Truthy(v) ? v! : fallback;

    /// <summary>Python 的 repr(float)，例如 0.0、170.5、1e+16；NaN/Inf 丟出 PyValueError（JSON 不相容）</summary>
    public static string FloatRepr(double d)
    {
        if (double.IsNaN(d) || double.IsInfinity(d))
            throw new PyValueError("Out of range float values are not JSON compliant");
        if (d == 0) return double.IsNegative(d) ? "-0.0" : "0.0";

        // 取得最短可還原的有效數字與指數
        var r = d.ToString("R", Inv);
        var sign = "";
        if (r.StartsWith('-')) { sign = "-"; r = r[1..]; }
        var exp = 0;
        var ePos = r.IndexOfAny(['E', 'e']);
        if (ePos >= 0) { exp = int.Parse(r[(ePos + 1)..], Inv); r = r[..ePos]; }
        var dot = r.IndexOf('.');
        var intLen = dot >= 0 ? dot : r.Length;
        var digits = r.Replace(".", "");
        var decpt = intLen + exp; // 數值 = 0.digits × 10^decpt
        var lead = digits.Length - digits.TrimStart('0').Length;
        digits = digits.TrimStart('0');
        decpt -= lead;
        digits = digits.TrimEnd('0');
        if (digits.Length == 0) digits = "0";

        string body;
        if (decpt > -4 && decpt <= 16)
        {
            if (decpt <= 0) body = "0." + new string('0', -decpt) + digits;
            else if (decpt >= digits.Length) body = digits + new string('0', decpt - digits.Length) + ".0";
            else body = digits[..decpt] + "." + digits[decpt..];
        }
        else
        {
            var e = decpt - 1;
            body = digits[..1] + (digits.Length > 1 ? "." + digits[1..] : "")
                   + "e" + (e < 0 ? "-" : "+") + Math.Abs(e).ToString("00", Inv);
        }
        return sign + body;
    }

    /// <summary>Python 的 str(x)（只處理 sqlite 會回傳的型別）</summary>
    public static string Str(object? v) => v switch
    {
        null => "None",
        string s => s,
        double d => FloatRepr(d),
        long l => l.ToString(Inv),
        int i => i.ToString(Inv),
        bool b => b ? "True" : "False",
        byte[] bytes => Encoding.UTF8.GetString(bytes),
        _ => Convert.ToString(v, Inv) ?? "",
    };

    /// <summary>Python 的 float(str)：允許前後空白、數字間底線、inf / nan</summary>
    public static bool TryParseFloat(string s, out double value)
    {
        value = 0;
        s = s.Trim();
        var lower = s.ToLowerInvariant().TrimStart('+');
        var negative = lower.StartsWith('-');
        var word = negative ? lower[1..] : lower;
        if (word is "inf" or "infinity") { value = negative ? double.NegativeInfinity : double.PositiveInfinity; return true; }
        if (word is "nan") { value = double.NaN; return true; }

        s = Regex.Replace(s, "(?<=[0-9])_(?=[0-9])", "");
        if (!Regex.IsMatch(s, @"\A[+-]?([0-9]+\.?[0-9]*|\.[0-9]+)([eE][+-]?[0-9]+)?\z")) return false;
        return double.TryParse(s, NumberStyles.Float, Inv, out value);
    }

    /// <summary>Python 的 int(str)：允許前後空白、正負號、數字間底線</summary>
    public static bool TryParseInt(string s, out long value)
    {
        value = 0;
        s = Regex.Replace(s.Trim(), "(?<=[0-9])_(?=[0-9])", "");
        return Regex.IsMatch(s, @"\A[+-]?[0-9]+\z") && long.TryParse(s, NumberStyles.AllowLeadingSign, Inv, out value);
    }

    /// <summary>SQLAlchemy 在 SQLite 中儲存 DateTime 的格式（例如 2025-12-16 20:29:53.000000）</summary>
    public static string SqlaDateTime(DateTime dt) => dt.ToString("yyyy-MM-dd HH:mm:ss.ffffff", Inv);

    /// <summary>台灣時間（含微秒），對應 datetime.now(TAIWAN_TZ).replace(tzinfo=None)</summary>
    public static DateTime TaiwanNowPrecise() => DateTime.SpecifyKind(DateTime.UtcNow + TimeUtil.TaiwanOffset, DateTimeKind.Unspecified);

    /// <summary>Python repr(str)（用於錯誤訊息）</summary>
    public static string Repr(string s) => s.Contains('\'') && !s.Contains('"') ? $"\"{s}\"" : $"'{s.Replace("'", "\\'")}'";
}
