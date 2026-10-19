using System.ComponentModel.DataAnnotations;

namespace PuyuanApi.Modules.Care;

// ==================== 請求模型 ====================

/// <summary>上傳關懷訊息請求</summary>
public class CareMessageUpload
{
    /// <summary>關懷訊息</summary>
    [Required(AllowEmptyStrings = true)]
    public required string Message { get; init; }
}

// ==================== 回應模型 ====================

/// <summary>關懷諮詢紀錄（欄位順序與 Python CareRecord 相同；member_id / reply_id 為 null 時仍輸出 null）</summary>
public record CareRecord(
    long Id,
    long UserId,
    long? MemberId,
    long? ReplyId,
    string Message,
    string UpdatedAt,
    string CreatedAt);

/// <summary>關懷諮詢列表回應</summary>
public record CareListResponse(string Status, string Message, List<CareRecord> Cares);
