using System.ComponentModel.DataAnnotations;
using System.Text.Json.Serialization;
using PuyuanApi.Core.PyCompat;

namespace PuyuanApi.Modules.Journal;

// ==================== 請求模型 ====================

/// <summary>上傳飲食日記請求（對應 DietUpload）</summary>
public class DietUpload
{
    /// <summary>描述</summary>
    public required string Description { get; set; }

    /// <summary>時段 (0:早餐, 1:午餐, 2:晚餐)</summary>
    [Range(0, 2)]
    public required int Meal { get; set; }

    /// <summary>標籤列表（pydantic v1 只認 alias "tag[]"）</summary>
    [JsonPropertyName("tag[]")]
    public List<string> Tag { get; set; } = [];

    /// <summary>照片數量</summary>
    [Range(0, int.MaxValue)]
    public int Image { get; set; } = 0;

    /// <summary>緯度</summary>
    public double? Lat { get; set; }

    /// <summary>經度</summary>
    public double? Lng { get; set; }

    /// <summary>記錄時間</summary>
    public required string RecordedAt { get; set; }
}

/// <summary>刪除日記記錄請求（對應 DeleteRecordsRequest）</summary>
public class DeleteRecordsRequest
{
    /// <summary>要刪除的記錄 ID：blood_pressures / blood_sugars / weights / diets</summary>
    [JsonPropertyName("deleteObject")]
    public required Dictionary<string, List<long>> DeleteObject { get; set; }
}

// ==================== 回應模型 ====================

/// <summary>上傳飲食日記回應（image_url 為 null 時照樣輸出 null）</summary>
public record DietUploadResponse(string Status, string Message, string? ImageUrl);

/// <summary>日記記錄（所有欄位都有預設值，Swift 端不能接受 null）</summary>
public class DiaryRecord
{
    public long Id { get; set; }
    public long UserId { get; set; }
    public long Systolic { get; set; }
    public long Diastolic { get; set; }
    public long Pulse { get; set; }
    [JsonConverter(typeof(PyLenientFloatConverter))] public double Weight { get; set; }
    [JsonConverter(typeof(PyLenientFloatConverter))] public double BodyFat { get; set; }
    [JsonConverter(typeof(PyLenientFloatConverter))] public double Bmi { get; set; }
    [JsonConverter(typeof(PyLenientFloatConverter))] public double Sugar { get; set; }
    public long Exercise { get; set; }
    public long Drug { get; set; }
    public long Timeperiod { get; set; }
    public string Description { get; set; } = "";
    public long Meal { get; set; }
    public List<Dictionary<string, object?>> Tag { get; set; } = [];
    public List<string> Image { get; set; } = [];
    public Dictionary<string, string> Location { get; set; } = new() { ["lat"] = "0", ["lng"] = "0" };
    public string Reply { get; set; } = "";
    public string RecordedAt { get; set; } = "";
    public string Type { get; set; } = "";
}

/// <summary>獲取日記列表回應</summary>
public record DiaryListResponse(string Status, string Message, List<DiaryRecord> Diary);
