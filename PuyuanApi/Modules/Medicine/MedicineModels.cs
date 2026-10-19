using System.ComponentModel.DataAnnotations;
using System.Text.Json.Serialization;

namespace PuyuanApi.Modules.Medicine;

// ==================== 請求模型 ====================

/// <summary>更新就醫資訊請求（四個欄位皆為必填）</summary>
public class MedicalInfoUpdate
{
    /// <summary>糖尿病口服藥 (0:否, 1:是)</summary>
    public required int Oad { get; init; }

    /// <summary>胰島素 (0:否, 1:是)</summary>
    public required int Insulin { get; init; }

    /// <summary>高血壓藥 (0:否, 1:是)</summary>
    public required int AntiHypertensives { get; init; }

    /// <summary>糖尿病類型 (0:無, 1:糖尿病前期, 2:第一型, 3:第二型, 4:妊娠)</summary>
    [Range(0, 4)]
    public required int DiabetesType { get; init; }
}

/// <summary>上傳藥物資訊請求</summary>
public class DrugUsedUpload
{
    /// <summary>使用藥物類型 (0:糖尿病藥物, 1:高血壓藥物)</summary>
    public required int Type { get; init; }

    /// <summary>藥物名稱</summary>
    [Required(AllowEmptyStrings = true)]
    public required string Name { get; init; }

    /// <summary>記錄時間 (格式: YYYY-MM-DD HH:MM:SS)，原樣存入</summary>
    [Required(AllowEmptyStrings = true)]
    public required string RecordedAt { get; init; }
}

/// <summary>刪除藥物資訊請求：接受 "ids[]"（alias）或 "ids"（populate_by_name）</summary>
public class DrugUsedDeleteRequest : IValidatableObject
{
    [JsonPropertyName("ids[]")]
    public List<int>? IdsAlias { get; init; }

    [JsonPropertyName("ids")]
    public List<int>? IdsByName { get; init; }

    [JsonIgnore]
    public List<int> Ids => IdsAlias ?? IdsByName ?? [];

    public IEnumerable<ValidationResult> Validate(ValidationContext validationContext)
    {
        if (IdsAlias is null && IdsByName is null)
            yield return new ValidationResult("Field required", ["ids[]"]);
    }
}

// ==================== 回應模型 ====================

/// <summary>就醫資訊（GET /medical 回傳的 dict，欄位順序與 Python 相同）</summary>
public record MedicalInfo(
    long Id,
    long UserId,
    long Oad,
    long Insulin,
    long AntiHypertensives,
    long DiabetesType,
    string CreatedAt,
    string UpdatedAt)
{
    /// <summary>查無資料或驗證失敗時的預設物件（避免 Swift 解析失敗）</summary>
    public static MedicalInfo Default(long userId) => new(0, userId, 0, 0, 0, 0, "", "");
}

/// <summary>GET /medical 回應（Python 回傳 raw dict）</summary>
public record MedicalInfoResponse(string Status, string Message, MedicalInfo MedicalInfo);

/// <summary>藥物資訊記錄（欄位順序與 Python DrugUsedRecord 相同）</summary>
public record DrugUsedRecord(
    long Id,
    string Name,
    long Type,
    string RecordedAt,
    string UpdatedAt,
    string CreatedAt,
    long UserId);

/// <summary>獲取藥物資訊列表回應</summary>
public record DrugUsedListResponse(string Status, string Message, List<DrugUsedRecord> DrugUseds);
