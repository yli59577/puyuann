using Microsoft.AspNetCore.Mvc;
using PuyuanApi.Core;

namespace PuyuanApi.Modules.Friend;

/// <summary>
/// 控糖團好友 API（對應 app/friend/api.py，掛載於 /api/friend）。
/// Python 使用 HTTPBearer(auto_error=False)，沒帶 token 也會進到 handler，回傳「未授權」。
/// </summary>
[ApiController]
public class FriendController(Database db, Security security, ILogger<FriendController> logger) : ControllerBase
{
    private readonly FriendModule _module = new(db, security, logger);

    /// <summary>驗證 token 並取得 user_id；Python 的 `if not user_id` 會把 0 也當成未授權</summary>
    private int? CurrentUserId()
    {
        var id = _module.ParseUserIdFromToken(Request);
        return id is null or 0 ? null : id;
    }

    /// <summary>獲取控糖團好友列表</summary>
    [HttpGet("/api/friend/list")]
    public FriendListResponse GetFriendList()
    {
        try
        {
            if (CurrentUserId() is not { } userId)
                return new FriendListResponse("1", "未授權", []);

            var friends = _module.GetFriendList(userId);
            return new FriendListResponse("0", "ok", friends);
        }
        catch (Exception e)
        {
            logger.LogError(e, "get_friend_list 錯誤: {Message}", e.Message);
            return new FriendListResponse("1", "失敗", []);
        }
    }

    /// <summary>獲取自己的邀請碼</summary>
    [HttpGet("/api/friend/code")]
    public InviteCodeResponse GetInviteCode()
    {
        try
        {
            if (CurrentUserId() is not { } userId)
                return new InviteCodeResponse("1", "未授權");

            var inviteCode = _module.GetInviteCode(userId);
            return new InviteCodeResponse("0", "ok", inviteCode);
        }
        catch (Exception e)
        {
            logger.LogError(e, "get_invite_code 錯誤: {Message}", e.Message);
            return new InviteCodeResponse("1", "失敗");
        }
    }

    /// <summary>獲取好友邀請列表（別人寄給我的邀請）</summary>
    [HttpGet("/api/friend/requests")]
    public FriendRequestsResponse GetFriendRequests()
    {
        try
        {
            if (CurrentUserId() is not { } userId)
                return new FriendRequestsResponse("1", "未授權", []);

            var requests = _module.GetFriendRequests(userId);
            return new FriendRequestsResponse("0", "ok", requests);
        }
        catch (Exception e)
        {
            logger.LogError(e, "get_friend_requests 錯誤: {Message}", e.Message);
            return new FriendRequestsResponse("1", "失敗", []);
        }
    }

    /// <summary>送出好友邀請</summary>
    [HttpPost("/api/friend/send")]
    public BaseResponse SendFriendInvite([FromBody] SendInviteRequest data)
    {
        try
        {
            if (CurrentUserId() is not { } userId)
                return BaseResponse.Fail("未授權");

            return _module.SendFriendInvite(userId, data)
                ? BaseResponse.Ok("成功")
                : BaseResponse.Fail("邀請碼無效或已送出過邀請");
        }
        catch (Exception e)
        {
            logger.LogError(e, "send_friend_invite 錯誤: {Message}", e.Message);
            return BaseResponse.Fail("失敗");
        }
    }

    /// <summary>接受好友邀請</summary>
    [HttpGet("/api/friend/{friend_invite_id}/accept")]
    public BaseResponse AcceptFriendInvite([FromRoute(Name = "friend_invite_id")] int friendInviteId)
    {
        try
        {
            if (CurrentUserId() is not { } userId)
                return BaseResponse.Fail("未授權");

            return _module.AcceptFriendInvite(userId, friendInviteId)
                ? BaseResponse.Ok("ok")
                : BaseResponse.Fail("邀請不存在或已處理");
        }
        catch (Exception e)
        {
            logger.LogError(e, "accept_friend_invite 錯誤: {Message}", e.Message);
            return BaseResponse.Fail("失敗");
        }
    }

    /// <summary>拒絕好友邀請</summary>
    [HttpGet("/api/friend/{friend_invite_id}/refuse")]
    public BaseResponse RefuseFriendInvite([FromRoute(Name = "friend_invite_id")] int friendInviteId)
    {
        try
        {
            if (CurrentUserId() is not { } userId)
                return BaseResponse.Fail("未授權");

            return _module.RefuseFriendInvite(userId, friendInviteId)
                ? BaseResponse.Ok("ok")
                : BaseResponse.Fail("邀請不存在或已處理");
        }
        catch (Exception e)
        {
            logger.LogError(e, "refuse_friend_invite 錯誤: {Message}", e.Message);
            return BaseResponse.Fail("失敗");
        }
    }

    /// <summary>刪除好友（DELETE + JSON body {"ids[]": [...]}）</summary>
    [HttpDelete("/api/friend/remove")]
    public BaseResponse RemoveFriends([FromBody] RemoveFriendsRequest data)
    {
        try
        {
            if (CurrentUserId() is not { } userId)
                return BaseResponse.Fail("未授權");

            return _module.RemoveFriends(userId, data.Ids)
                ? BaseResponse.Ok("ok")
                : BaseResponse.Fail("刪除失敗");
        }
        catch (Exception e)
        {
            logger.LogError(e, "remove_friends 錯誤: {Message}", e.Message);
            return BaseResponse.Fail("失敗");
        }
    }

    /// <summary>獲取控糖團結果列表（我送出的邀請的狀態）</summary>
    [HttpGet("/api/friend/results")]
    public FriendResultsResponse GetFriendResults()
    {
        try
        {
            if (CurrentUserId() is not { } userId)
                return new FriendResultsResponse("1", "未授權", []);

            var results = _module.GetFriendResults(userId);
            return new FriendResultsResponse("0", "ok", results);
        }
        catch (Exception e)
        {
            logger.LogError(e, "get_friend_results 錯誤: {Message}", e.Message);
            return new FriendResultsResponse("1", "失敗", []);
        }
    }
}
