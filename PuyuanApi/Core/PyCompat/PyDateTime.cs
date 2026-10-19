using System.Globalization;
using System.Text.RegularExpressions;

namespace PuyuanApi.Core.PyCompat;

/// <summary>
/// Python datetime 相關的相容工具（Python 3.11+ 的 datetime.fromisoformat 規則，用於解析請求中的時間字串）。
/// Measurement / Medicine 模組使用。讀取 SQLAlchemy 存在資料庫的 DateTime 欄位（Python 3.7 規則）請用 <see cref="PyOrmDateTime"/>。
/// </summary>
public static partial class PyDateTime
{
    // date: YYYY-MM-DD 或 YYYYMMDD；分隔符可為任意單一字元；time: HH[:MM[:SS[.ffffff]]]；時區: Z / ±HH[:MM[:SS[.ffffff]]]
    [GeneratedRegex(@"^(?<y>\d{4})-?(?<mo>\d{2})-?(?<d>\d{2})(?:.(?<h>\d{2})(?::?(?<mi>\d{2})(?::?(?<s>\d{2})(?:[.,](?<f>\d+))?)?)?(?<tz>Z|[+-]\d{2}(?::?\d{2}(?::?\d{2}(?:\.\d+)?)?)?)?)?$")]
    private static partial Regex IsoRegex();

    /// <summary>
    /// 模擬 Python 3.11+ 的 datetime.fromisoformat（不支援 ISO 週日期）。
    /// 回傳牆上時間（不做時區換算，與 SQLAlchemy 寫入 SQLite 時丟棄 tzinfo 的行為一致）與時區偏移（若有）。
    /// </summary>
    public static bool TryFromIsoFormat(string? s, out DateTime wallClock, out TimeSpan? offset)
    {
        wallClock = default;
        offset = null;
        if (s is null) return false;

        var m = IsoRegex().Match(s);
        if (!m.Success) return false;

        try
        {
            int G(string name) => m.Groups[name].Success ? int.Parse(m.Groups[name].Value, CultureInfo.InvariantCulture) : 0;
            var micro = 0;
            if (m.Groups["f"].Success)
            {
                var f = m.Groups["f"].Value;
                f = f.Length >= 6 ? f[..6] : f.PadRight(6, '0');
                micro = int.Parse(f, CultureInfo.InvariantCulture);
            }
            wallClock = new DateTime(G("y"), G("mo"), G("d"), G("h"), G("mi"), G("s")).AddTicks(micro * 10L);

            if (m.Groups["tz"].Success)
            {
                var tz = m.Groups["tz"].Value;
                if (tz == "Z")
                {
                    offset = TimeSpan.Zero;
                }
                else
                {
                    var sign = tz[0] == '-' ? -1 : 1;
                    var digits = tz[1..].Replace(":", "").Split('.')[0];
                    var hh = int.Parse(digits[..2], CultureInfo.InvariantCulture);
                    var mm = digits.Length >= 4 ? int.Parse(digits[2..4], CultureInfo.InvariantCulture) : 0;
                    var ss = digits.Length >= 6 ? int.Parse(digits[4..6], CultureInfo.InvariantCulture) : 0;
                    if (hh > 23 || mm > 59 || ss > 59) return false;
                    offset = sign * new TimeSpan(hh, mm, ss);
                }
            }
            return true;
        }
        catch (ArgumentOutOfRangeException)
        {
            return false;
        }
    }

    /// <summary>SQLAlchemy SQLite DateTime 的儲存格式：yyyy-MM-dd HH:mm:ss.ffffff</summary>
    public static string ToSqlAlchemy(DateTime dt) => dt.ToString("yyyy-MM-dd HH:mm:ss.ffffff", CultureInfo.InvariantCulture);

    /// <summary>模擬 Python 的 datetime.isoformat()（微秒為 0 時省略小數部分）</summary>
    public static string IsoFormat(DateTime dt, TimeSpan? offset = null)
    {
        var s = dt.ToString(dt.Ticks % TimeSpan.TicksPerSecond / 10 == 0 ? "yyyy-MM-dd'T'HH:mm:ss" : "yyyy-MM-dd'T'HH:mm:ss.ffffff",
            CultureInfo.InvariantCulture);
        if (offset is { } o)
        {
            var sign = o < TimeSpan.Zero ? "-" : "+";
            var a = o.Duration();
            s += $"{sign}{a.Hours:D2}:{a.Minutes:D2}" + (a.Seconds != 0 ? $":{a.Seconds:D2}" : "");
        }
        return s;
    }
}

/// <summary>
/// SQLAlchemy 從 SQLite 讀出的 DateTime（Python 3.7 datetime.fromisoformat 規則，保留原始時區字尾），
/// 以及 Python 的 datetime.isoformat() 輸出。User / Account 模組使用。
/// 解析請求中的時間字串（Python 3.11 規則）請用 <see cref="PyDateTime"/>。
/// </summary>
public readonly record struct PyOrmDateTime(DateTime Value, string? TzSuffix)
{
    private static readonly Regex IsoRegex = new(
        @"\A([0-9]{4})-([0-9]{2})-([0-9]{2})(?:[\s\S]([0-9]{2})(?::([0-9]{2})(?::([0-9]{2})(?:\.([0-9]{6}|[0-9]{3}))?)?)?([+-][0-9]{2}:[0-9]{2}(?::[0-9]{2}(?:\.[0-9]{6})?)?)?)?\z");

    /// <summary>有時區資訊（aware），與 naive datetime 比較會 TypeError</summary>
    public bool IsAware => TzSuffix is not null;

    /// <summary>資料庫原始值 → PyOrmDateTime；NULL 回傳 null；格式錯誤丟出與 SQLAlchemy 相同訊息的例外</summary>
    public static PyOrmDateTime? FromDb(object? raw)
    {
        if (raw is null) return null;
        if (raw is not string s) throw new PyValueError("fromisoformat: argument must be str");

        var m = IsoRegex.Match(s);
        if (!m.Success) throw new PyValueError($"Invalid isoformat string: {PyOrm.Repr(s)}");
        try
        {
            int G(int i) => m.Groups[i].Success ? int.Parse(m.Groups[i].Value, CultureInfo.InvariantCulture) : 0;
            var frac = m.Groups[7].Success ? m.Groups[7].Value : "";
            var micro = frac.Length == 0 ? 0 : int.Parse(frac, CultureInfo.InvariantCulture) * (frac.Length == 3 ? 1000 : 1);
            var dt = new DateTime(G(1), G(2), G(3), G(4), G(5), G(6), DateTimeKind.Unspecified).AddTicks(micro * 10L);
            return new PyOrmDateTime(dt, m.Groups[8].Success ? m.Groups[8].Value : null);
        }
        catch (ArgumentOutOfRangeException)
        {
            throw new PyValueError($"Invalid isoformat string: {PyOrm.Repr(s)}");
        }
    }

    /// <summary>Python datetime.isoformat()：2023-11-12T11:11:11[.ffffff][+08:00]</summary>
    public string IsoFormat()
    {
        var s = Value.ToString("yyyy-MM-dd'T'HH:mm:ss", CultureInfo.InvariantCulture);
        var micro = Value.Ticks % TimeSpan.TicksPerSecond / 10;
        if (micro != 0) s += "." + micro.ToString("D6", CultureInfo.InvariantCulture);
        return s + TzSuffix;
    }
}
