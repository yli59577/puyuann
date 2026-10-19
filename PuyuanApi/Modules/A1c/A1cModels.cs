using System.ComponentModel.DataAnnotations;
using System.Text.Json.Serialization;

namespace PuyuanApi.Modules.A1c;

// ==================== 請求模型 ====================

/// <summary>上傳糖化血色素請求</summary>
public class A1cUpload
{
    /// <summary>糖化血色素（字串；數字會被 LenientStringConverter 轉成字串）</summary>
    [JsonPropertyName("a1c")]
    [Required(AllowEmptyStrings = true)]
    public required string A1c { get; init; }

    /// <summary>記錄時間 (格式: YYYY-MM-DD HH:MM:SS)，原樣存入</summary>
    [Required(AllowEmptyStrings = true)]
    public required string RecordedAt { get; init; }
}

/// <summary>刪除糖化血色素請求：接受 "ids[]"（alias）或 "ids"（populate_by_name）</summary>
public class A1cDeleteRequest : IValidatableObject
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

/// <summary>糖化血色素記錄（欄位順序與 Python A1cRecord 相同）</summary>
public record A1cRecord(
    long Id,
    [property: JsonPropertyName("a1c")] string A1c,
    string RecordedAt,
    string UpdatedAt,
    string CreatedAt,
    long UserId);

/// <summary>獲取糖化血色素列表回應</summary>
public record A1cListResponse(
    string Status,
    string Message,
    [property: JsonPropertyName("a1cs")] List<A1cRecord> A1cs);
