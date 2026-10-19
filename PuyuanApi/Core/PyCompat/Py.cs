using System.Globalization;
using System.Text;
using System.Text.RegularExpressions;

namespace PuyuanApi.Core.PyCompat;

/// <summary>
/// Python 內建行為相容工具（str()/float repr/int()/float()/datetime 解析/json.dumps），
/// 針對 sqlite3 原始查詢結果（含 DBNull）設計。Journal / Else 模組使用。
/// <para>
/// 與 <see cref="PyOrm"/> 的差異：<see cref="FloatRepr"/> 對 NaN/Inf 回傳 "nan"/"inf"（真正的 Python repr），
/// <see cref="Str"/> 對 bytes 輸出 b'...'，且 DBNull 視同 None。User / Account 請用 <see cref="PyOrm"/>。
/// </para>
/// </summary>
public static class Py
{
    // Python 3.7 datetime.fromisoformat（SQLAlchemy 2.0 的 SQLite DATETIME 預設解析方式）
    private static readonly Regex IsoRegex = new(
        @"^(\d{4})-(\d{2})-(\d{2})(?:.(\d{2})(?::(\d{2})(?::(\d{2})(?:\.(\d{3}|\d{6}))?)?)?([+-]\d{2}:\d{2}(?::\d{2}(?:\.\d{6})?)?)?)?$",
        RegexOptions.Compiled | RegexOptions.Singleline);

    /// <summary>
    /// 模擬 SQLAlchemy 讀取 DateTime 欄位後再 str(datetime)：
    /// "2025-12-15 13:03:53.000000" → "2025-12-15 13:03:53"；有微秒才輸出 .ffffff。
    /// null → null；無法解析時丟出例外（與 SQLAlchemy 相同）。
    /// </summary>
    public static string? OrmDateTimeStr(object? value)
    {
        if (value is null || value is DBNull) return null;
        if (value is not string s) throw new InvalidOperationException($"Invalid isoformat string: {value}");

        var m = IsoRegex.Match(s);
        if (!m.Success) throw new FormatException($"Invalid isoformat string: '{s}'");

        int year = int.Parse(m.Groups[1].Value), month = int.Parse(m.Groups[2].Value), day = int.Parse(m.Groups[3].Value);
        int hour = m.Groups[4].Success ? int.Parse(m.Groups[4].Value) : 0;
        int minute = m.Groups[5].Success ? int.Parse(m.Groups[5].Value) : 0;
        int second = m.Groups[6].Success ? int.Parse(m.Groups[6].Value) : 0;
        int micro = 0;
        if (m.Groups[7].Success)
            micro = m.Groups[7].Value.Length == 3 ? int.Parse(m.Groups[7].Value) * 1000 : int.Parse(m.Groups[7].Value);

        // 驗證日期時間是否合法（例如 2月30日 → 例外）
        _ = new DateTime(year, month, day, hour, minute, second);

        var sb = new StringBuilder($"{year:D4}-{month:D2}-{day:D2} {hour:D2}:{minute:D2}:{second:D2}");
        if (micro != 0) sb.Append('.').Append(micro.ToString("D6"));
        if (m.Groups[8].Success) sb.Append(m.Groups[8].Value[..6]);
        return sb.ToString();
    }

    /// <summary>Python 的 str(x)（用於 sqlite3 原始查詢結果）</summary>
    public static string Str(object? value) => value switch
    {
        null or DBNull => "None",
        string s => s,
        double d => FloatRepr(d),
        float f => FloatRepr(f),
        bool b => b ? "True" : "False",
        byte[] bytes => "b'" + Encoding.Latin1.GetString(bytes) + "'",
        IFormattable f => f.ToString(null, CultureInfo.InvariantCulture),
        _ => value.ToString() ?? "",
    };

    /// <summary>Python 的真值判斷（None / 0 / 0.0 / "" 為 False）</summary>
    public static bool Truthy(object? value) => value switch
    {
        null or DBNull => false,
        string s => s.Length > 0,
        long l => l != 0,
        int i => i != 0,
        double d => d != 0,
        bool b => b,
        byte[] bytes => bytes.Length > 0,
        _ => true,
    };

    /// <summary>Python 的 int(x)</summary>
    public static long Int(object? value) => value switch
    {
        long l => l,
        int i => i,
        double d => (long)Math.Truncate(d),
        bool b => b ? 1 : 0,
        string s => long.Parse(s.Trim().Replace("_", ""), NumberStyles.AllowLeadingSign, CultureInfo.InvariantCulture),
        _ => throw new InvalidCastException($"int() argument must be a string or a number, not '{value?.GetType().Name ?? "NoneType"}'"),
    };

    /// <summary>Python 的 float(x)</summary>
    public static double Float(object? value) => value switch
    {
        double d => d,
        long l => l,
        int i => i,
        bool b => b ? 1 : 0,
        string s => double.Parse(s.Trim(), NumberStyles.Float, CultureInfo.InvariantCulture),
        _ => throw new InvalidCastException($"float() argument must be a string or a number, not '{value?.GetType().Name ?? "NoneType"}'"),
    };

    /// <summary>Python repr(float)：50.0 → "50.0"、1e-05 → "1e-05"、1e16 → "1e+16"、NaN → "nan"</summary>
    public static string FloatRepr(double d)
    {
        if (double.IsNaN(d)) return "nan";
        if (double.IsPositiveInfinity(d)) return "inf";
        if (double.IsNegativeInfinity(d)) return "-inf";
        if (d == 0) return double.IsNegative(d) ? "-0.0" : "0.0";

        var r = d.ToString("R", CultureInfo.InvariantCulture);
        var neg = r.StartsWith('-');
        if (neg) r = r[1..];

        // 拆成「有效數字」與「小數點位置」
        int exp = 0;
        var eIdx = r.IndexOfAny(['E', 'e']);
        if (eIdx >= 0)
        {
            exp = int.Parse(r[(eIdx + 1)..], CultureInfo.InvariantCulture);
            r = r[..eIdx];
        }
        var dot = r.IndexOf('.');
        var digits = dot < 0 ? r : r.Remove(dot, 1);
        var point = (dot < 0 ? r.Length : dot) + exp;
        var lead = digits.Length - digits.TrimStart('0').Length;
        digits = digits.TrimStart('0');
        point -= lead;
        digits = digits.TrimEnd('0');
        if (digits.Length == 0) digits = "0";

        var sciExp = point - 1;
        string body;
        if (sciExp >= -4 && sciExp < 16)
        {
            if (point <= 0) body = "0." + new string('0', -point) + digits;
            else if (point >= digits.Length) body = digits + new string('0', point - digits.Length) + ".0";
            else body = digits[..point] + "." + digits[point..];
        }
        else
        {
            body = digits[..1] + (digits.Length > 1 ? "." + digits[1..] : "")
                   + "e" + (sciExp < 0 ? "-" : "+") + Math.Abs(sciExp).ToString("D2");
        }
        return neg ? "-" + body : body;
    }

    /// <summary>json.dumps(list_of_str, ensure_ascii=False)：'["a", "b"]'</summary>
    public static string JsonDumpsStrList(IEnumerable<string?> items)
    {
        var sb = new StringBuilder("[");
        var first = true;
        foreach (var item in items)
        {
            if (!first) sb.Append(", ");
            first = false;
            if (item is null) { sb.Append("null"); continue; }
            sb.Append('"');
            foreach (var c in item)
            {
                switch (c)
                {
                    case '"': sb.Append("\\\""); break;
                    case '\\': sb.Append("\\\\"); break;
                    case '\n': sb.Append("\\n"); break;
                    case '\r': sb.Append("\\r"); break;
                    case '\t': sb.Append("\\t"); break;
                    case '\b': sb.Append("\\b"); break;
                    case '\f': sb.Append("\\f"); break;
                    default:
                        if (c < 0x20) sb.Append("\\u").Append(((int)c).ToString("x4"));
                        else sb.Append(c);
                        break;
                }
            }
            sb.Append('"');
        }
        return sb.Append(']').ToString();
    }

    /// <summary>穩定的字串雜湊（取代 Python 每次啟動都不同的 hash(str)），結果介於 0 ~ 2147483646</summary>
    public static long StableHash(string s)
    {
        uint h = 2166136261;
        foreach (var b in Encoding.UTF8.GetBytes(s))
        {
            h ^= b;
            h *= 16777619;
        }
        return h % 2147483647L;
    }
}
