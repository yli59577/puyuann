namespace PuyuanApi.Core;

/// <summary>台灣時間工具（對應 app/common/utils.py 的 get_taiwan_time）</summary>
public static class TimeUtil
{
    public static readonly TimeSpan TaiwanOffset = TimeSpan.FromHours(8);

    /// <summary>台灣時間 (UTC+8)，精確到秒，不含時區資訊</summary>
    public static DateTime TaiwanNow()
    {
        var t = DateTime.UtcNow + TaiwanOffset;
        return new DateTime(t.Year, t.Month, t.Day, t.Hour, t.Minute, t.Second, DateTimeKind.Unspecified);
    }

    /// <summary>資料庫儲存用格式：yyyy-MM-dd HH:mm:ss</summary>
    public static string Format(DateTime dt) => dt.ToString("yyyy-MM-dd HH:mm:ss");

    public static string TaiwanNowString() => Format(TaiwanNow());
}
