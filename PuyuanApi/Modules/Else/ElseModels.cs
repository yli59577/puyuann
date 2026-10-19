using System.ComponentModel.DataAnnotations;
using System.Text.Json.Serialization;
using PuyuanApi.Core.PyCompat;

namespace PuyuanApi.Modules.Else;

// ==================== 請求模型 ====================

/// <summary>分享請求（對應 ShareRequest）</summary>
public class ShareRequest
{
    /// <summary>種類, 0：血壓；1：體重；2：血糖；3：飲食；4：其他</summary>
    [Range(0, 4)]
    public required int Type { get; set; }

    /// <summary>紀錄ID</summary>
    [Range(0, int.MaxValue)]
    public required int Id { get; set; }

    /// <summary>1：親友；2：糖友</summary>
    [Range(1, 2)]
    public required int RelationType { get; set; }
}

// ==================== 回應模型 ====================

/// <summary>最新消息項目</summary>
public record NewsItem(
    long Id,
    long MemberId,
    long Group,
    string Title,
    string Message,
    string PushedAt,
    string CreatedAt,
    string UpdatedAt);

/// <summary>最新消息回應</summary>
public record NewsResponse(string Status, string Message, List<NewsItem> News);

/// <summary>位置資料</summary>
public record LocationData(string Lat, string Lng);

/// <summary>用戶資訊</summary>
public record UserInfo(long Id, string Name, string Account);

/// <summary>分享記錄（未設定的 Optional 欄位輸出 null，與 pydantic 相同）</summary>
public class ShareRecord
{
    public long Id { get; set; }
    public long UserId { get; set; }
    [JsonConverter(typeof(PyLenientFloatConverter))] public double? Sugar { get; set; }
    public long? Timeperiod { get; set; }
    [JsonConverter(typeof(PyLenientFloatConverter))] public double? Weight { get; set; }
    [JsonConverter(typeof(PyLenientFloatConverter))] public double? BodyFat { get; set; }
    [JsonConverter(typeof(PyLenientFloatConverter))] public double? Bmi { get; set; }
    public long? Systolic { get; set; }
    public long? Diastolic { get; set; }
    public long? Pulse { get; set; }
    public long? Meal { get; set; }
    public List<string> Tag { get; set; } = [];
    public List<string> Image { get; set; } = [];
    public LocationData? Location { get; set; }
    public long RelationType { get; set; }
    public long RelationId { get; set; }
    public string Message { get; set; } = "";
    public long Type { get; set; }
    public string Url { get; set; } = "";
    public string RecordedAt { get; set; } = "";
    public string CreatedAt { get; set; } = "";
    public required UserInfo User { get; set; }
}

/// <summary>查看分享回應</summary>
public record ShareRecordsResponse(string Status, string Message, List<ShareRecord> Records);
