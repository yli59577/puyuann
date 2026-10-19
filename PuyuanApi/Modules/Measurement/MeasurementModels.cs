using System.ComponentModel.DataAnnotations;
using System.Text.Json.Serialization;
using PuyuanApi.Core.PyCompat;

namespace PuyuanApi.Modules.Measurement;

// ==================== 請求模型 ====================

/// <summary>上傳血壓測量結果</summary>
public class BloodPressureUpload
{
    /// <summary>收縮壓 (mmHg)</summary>
    [Range(50, 250)]
    public required int Systolic { get; init; }

    /// <summary>舒張壓 (mmHg)</summary>
    [Range(30, 150)]
    public required int Diastolic { get; init; }

    /// <summary>脈搏 (次/分)，可選</summary>
    [Range(30, 200)]
    public int? Pulse { get; init; }

    /// <summary>測量時間 (ISO 8601 格式)</summary>
    [Required(AllowEmptyStrings = true)]
    public required string MeasuredAt { get; init; }
}

/// <summary>上傳體重測量結果</summary>
public class WeightUpload
{
    /// <summary>體重 (kg)，0 &lt; weight ≤ 500</summary>
    [Range(0d, 500d, MinimumIsExclusive = true)]
    public required double Weight { get; init; }

    /// <summary>BMI，可選</summary>
    [Range(0d, 50d)]
    public double? Bmi { get; init; }

    /// <summary>體脂率 (%)，可選</summary>
    [Range(0d, 100d)]
    public double? BodyFat { get; init; }

    /// <summary>測量時間 (ISO 8601 格式)</summary>
    [Required(AllowEmptyStrings = true)]
    public required string RecordedAt { get; init; }
}

/// <summary>上傳血糖測量結果</summary>
public class BloodSugarUpload
{
    /// <summary>血糖值 (mg/dL)</summary>
    [Range(20, 600)]
    public required int Glucose { get; init; }

    /// <summary>測量時段 (0:早上, 1:中午, 2:晚上)</summary>
    [Range(0, 2)]
    public required int MealTime { get; init; }

    /// <summary>測量時間 (ISO 8601 格式)</summary>
    [Required(AllowEmptyStrings = true)]
    public required string MeasuredAt { get; init; }
}

// ==================== 回應模型 ====================

/// <summary>上傳回應（data 為 null 時仍輸出 "data": null）</summary>
public record MeasurementUploadResponse(string Status, string Message, MeasurementUploadData? Data);

public record MeasurementUploadData(long RecordId);

/// <summary>最後上傳時間回應</summary>
public record LastUploadResponse(string Status, string Message, string? LastUploadTime);

// ==================== POST /records 的預設回應（Swift 期望每個欄位是單一值） ====================

public record RecordsDefaultResponse(
    string Status,
    string Message,
    RecordsBloodSugar BloodSugars,
    RecordsBloodPressure BloodPressures,
    RecordsWeight Weights,
    RecordsDiet Diets)
{
    public static RecordsDefaultResponse Create(long userId) => new(
        "0", "ok",
        new RecordsBloodSugar { UserId = userId },
        new RecordsBloodPressure { UserId = userId },
        new RecordsWeight { UserId = userId },
        new RecordsDiet { UserId = userId });
}

public class RecordsBloodSugar
{
    public long Id { get; init; }
    public long UserId { get; init; }
    [JsonConverter(typeof(PyIntegralFloatConverter))] public double Sugar { get; init; }
    public long Timeperiod { get; init; }
    public string RecordedAt { get; init; } = "";
    public string CreatedAt { get; init; } = "";
    public string UpdatedAt { get; init; } = "";
}

public class RecordsBloodPressure
{
    public long Id { get; init; }
    public long UserId { get; init; }
    [JsonConverter(typeof(PyIntegralFloatConverter))] public double Systolic { get; init; }
    [JsonConverter(typeof(PyIntegralFloatConverter))] public double Diastolic { get; init; }
    [JsonConverter(typeof(PyIntegralFloatConverter))] public double Pulse { get; init; }
    public string RecordedAt { get; init; } = "";
    public string CreatedAt { get; init; } = "";
    public string UpdatedAt { get; init; } = "";
}

public class RecordsWeight
{
    public long Id { get; init; }
    public long UserId { get; init; }
    [JsonConverter(typeof(PyIntegralFloatConverter))] public double Weight { get; init; }
    [JsonConverter(typeof(PyIntegralFloatConverter))] public double Bmi { get; init; }
    [JsonConverter(typeof(PyIntegralFloatConverter))] public double BodyFat { get; init; }
    public string RecordedAt { get; init; } = "";
    public string CreatedAt { get; init; } = "";
    public string UpdatedAt { get; init; } = "";
}

public class RecordsDiet
{
    public long Id { get; init; }
    public long UserId { get; init; }
    public string Description { get; init; } = "";
    public long Meal { get; init; }
    public string Tag { get; init; } = "";
    public long Image { get; init; }
    [JsonConverter(typeof(PyIntegralFloatConverter))] public double Lat { get; init; }
    [JsonConverter(typeof(PyIntegralFloatConverter))] public double Lng { get; init; }
    public string RecordedAt { get; init; } = "";
    public string CreatedAt { get; init; } = "";
    public string UpdatedAt { get; init; } = "";
}
