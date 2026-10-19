using System.Text.Json.Serialization;

namespace PuyuanApi.Modules.Friend;

// 控糖團好友資料模型（對應 app/friend/models.py）

/// <summary>好友資訊</summary>
public record FriendInfo(long Id, string Name, long RelationType);

/// <summary>好友列表回應</summary>
public record FriendListResponse(string Status, string Message, List<FriendInfo> Friends);

/// <summary>邀請碼回應（invite_code 為 None 時 Python 會輸出 null，不省略）</summary>
public record InviteCodeResponse(
    string Status,
    string Message,
    [property: JsonIgnore(Condition = JsonIgnoreCondition.Never)] string? InviteCode = null);

/// <summary>用戶資訊</summary>
public record UserInfo(long Id, string Name, string Account);

/// <summary>好友邀請</summary>
public record FriendRequest(
    long Id,
    long UserId,
    long RelationId,
    long Type,
    long Read,
    long Status,
    string CreatedAt,
    string UpdatedAt,
    UserInfo User);

/// <summary>好友邀請列表回應</summary>
public record FriendRequestsResponse(string Status, string Message, List<FriendRequest> Requests);

/// <summary>送出邀請請求</summary>
public class SendInviteRequest
{
    /// <summary>好友類型（必填）</summary>
    public required int Type { get; set; }

    /// <summary>邀請碼（必填）</summary>
    public required string InviteCode { get; set; }
}

/// <summary>刪除好友請求（JSON key 為 "ids[]"）</summary>
public class RemoveFriendsRequest
{
    [JsonPropertyName("ids[]")]
    public required List<long> Ids { get; set; }
}

/// <summary>關係資訊</summary>
public record RelationInfo(long Id, string Name, string Account);

/// <summary>好友結果（注意欄位順序：status 在 read 之前）</summary>
public record FriendResult(
    long Id,
    long UserId,
    long RelationId,
    long Type,
    long Status,
    long Read,
    string CreatedAt,
    string UpdatedAt,
    RelationInfo Relation);

/// <summary>好友結果列表回應</summary>
public record FriendResultsResponse(string Status, string Message, List<FriendResult> Results);
