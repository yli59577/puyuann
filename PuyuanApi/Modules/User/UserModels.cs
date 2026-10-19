using System.Text.Json;
using System.Text.Json.Serialization;
using PuyuanApi.Core.PyCompat;

namespace PuyuanApi.Modules.User;

// ==================== 資料庫列（對應 SQLAlchemy 模型 UserAuth）====================

/// <summary>
/// UserAuth 資料列（對應 app/account/models.py 的 User）。
/// 欄位型別保留 SQLite 原始值（object?），以便照 Python 的 truthiness / 轉型規則處理。
/// </summary>
public sealed class UserAuthRow
{
    public const string SelectSql = """
        SELECT id AS Id, account AS Account, email AS Email, password AS Password, code AS Code,
               verified AS Verified, privacy_policy AS PrivacyPolicy, must_change_password AS MustChangePassword,
               google_id AS GoogleId, apple_id AS AppleId, login_times AS LoginTimes,
               token_expire_at AS TokenExpireAt, created_at AS CreatedAt, updated_at AS UpdatedAt,
               verification_expires_at AS VerificationExpiresAt
        FROM UserAuth
        """;

    public long Id { get; set; }
    public object? Account { get; set; }
    public object? Email { get; set; }
    public string? Password { get; set; }
    public object? Code { get; set; }
    public object? Verified { get; set; }
    public object? PrivacyPolicy { get; set; }
    public object? MustChangePassword { get; set; }
    public object? GoogleId { get; set; }
    public object? AppleId { get; set; }
    public object? LoginTimes { get; set; }
    public object? TokenExpireAt { get; set; }
    public object? CreatedAt { get; set; }
    public object? UpdatedAt { get; set; }
    public object? VerificationExpiresAt { get; set; }

    /// <summary>
    /// SQLAlchemy 載入時會解析所有 DateTime 欄位，格式錯誤會丟 ValueError；這裡照做。
    /// 回傳 (created_at, updated_at)。
    /// </summary>
    public (PyOrmDateTime? CreatedAt, PyOrmDateTime? UpdatedAt) ParseDates()
    {
        PyOrmDateTime.FromDb(TokenExpireAt);
        var created = PyOrmDateTime.FromDb(CreatedAt);
        var updated = PyOrmDateTime.FromDb(UpdatedAt);
        PyOrmDateTime.FromDb(VerificationExpiresAt);
        return (created, updated);
    }
}

// ==================== 請求模型 ====================

/// <summary>更新個人資料的請求（PATCH /api/user）</summary>
public class UserProfileUpdate
{
    public string? Name { get; set; }

    [JsonConverter(typeof(PyIntConverter))]
    public long? Gender { get; set; }

    /// <summary>接受任何類型（字串、數字、空值）</summary>
    public JsonElement? Birthday { get; set; }

    /// <summary>接受任何類型（字串、數字、空值）</summary>
    public JsonElement? Height { get; set; }

    /// <summary>接受任何類型（字串、數字、空值）</summary>
    public JsonElement? Weight { get; set; }

    public string? Phone { get; set; }
    public string? Address { get; set; }
    public string? Avatar { get; set; }
    public string? FcmId { get; set; }
}

/// <summary>
/// 更新個人設定的請求（PATCH /api/user/setting）。
/// 對應 Python 的 request.dict(exclude_unset=True)：需記錄哪些欄位有出現在 JSON 中。
/// </summary>
public class UserSettingsUpdate
{
    private bool? _afterRecording;
    private bool? _noRecordingForADay;

    [JsonPropertyName("after_recording")]
    [JsonConverter(typeof(PyBoolConverter))]
    public bool? AfterRecording
    {
        get => _afterRecording;
        set { _afterRecording = value; AfterRecordingSet = true; }
    }

    [JsonPropertyName("no_recording_for_a_day")]
    [JsonConverter(typeof(PyBoolConverter))]
    public bool? NoRecordingForADay
    {
        get => _noRecordingForADay;
        set { _noRecordingForADay = value; NoRecordingForADaySet = true; }
    }

    /// <summary>
    /// Python 版：notification_enabled（alias = over_max_or_under_min）。
    /// 因 dict() 以欄位名稱 notification_enabled 輸出，而 UserSettings 沒有這個欄位，所以實際上不會被更新。
    /// </summary>
    [JsonPropertyName("over_max_or_under_min")]
    [JsonConverter(typeof(PyBoolConverter))]
    public bool? NotificationEnabled { get; set; }

    /// <summary>UserSettings 沒有此欄位，只做驗證不會寫入</summary>
    public string? Language { get; set; }

    /// <summary>UserSettings 沒有此欄位，只做驗證不會寫入</summary>
    public string? Theme { get; set; }

    [JsonIgnore] public bool AfterRecordingSet { get; private set; }
    [JsonIgnore] public bool NoRecordingForADaySet { get; private set; }
}

// ==================== 回應模型 ====================

/// <summary>GET /api/user 的回應（Python 回傳原始 dict：status, message, user）</summary>
public record UserProfileResponse(string Status, string Message, UserProfileData? User);

/// <summary>
/// API 回應的用戶完整資料結構（對應 pydantic 的 UserProfileData，欄位順序相同）。
/// 由 <see cref="FromDict"/> 依 pydantic v1 規則驗證 / 轉型；未知鍵（例如 inviteCode）會被忽略。
/// </summary>
public class UserProfileData
{
    public long Id { get; init; }
    public string Account { get; init; } = "";
    public string Email { get; init; } = "";
    public string Phone { get; init; } = "";
    public string Name { get; init; } = "";
    public long Gender { get; init; }
    public string Birthday { get; init; } = "";
    [JsonConverter(typeof(PyStrictFloatConverter))] public double Height { get; init; }
    [JsonConverter(typeof(PyStrictFloatConverter))] public double Weight { get; init; }
    public long Verified { get; init; }
    public long PrivacyPolicy { get; init; }
    public long MustChangePassword { get; init; }
    public string FcmId { get; init; } = "";
    public string FbId { get; init; } = "";
    public string GoogleId { get; init; } = "";
    public string AppleId { get; init; } = "";
    public long LoginTimes { get; init; }
    public string Address { get; init; } = "";
    public string InviteCode { get; init; } = "";
    public long Badge { get; init; }
    public string Avatar { get; init; } = "";
    public string Group { get; init; } = "";
    public List<long> UnreadRecords { get; init; } = [];
    public string Status { get; init; } = "0";
    [JsonConverter(typeof(PyDictConverter))] public Dictionary<string, object?>? Vip { get; init; }
    public string CreatedAt { get; init; } = "";
    public string UpdatedAt { get; init; } = "";
    [JsonPropertyName("default")]
    [JsonConverter(typeof(PyDictConverter))] public Dictionary<string, object?>? Default { get; init; }
    [JsonConverter(typeof(PyDictConverter))] public Dictionary<string, object?>? Setting { get; init; }

    /// <summary>模擬 UserProfileData(**user_data)：驗證失敗丟出 <see cref="PyValidationError"/></summary>
    public static UserProfileData FromDict(Dictionary<string, object?> d)
    {
        var errors = new List<(string, string)>();

        T Field<T>(string key, Func<object?, T> coerce, T fallback)
        {
            if (!d.TryGetValue(key, out var raw)) return fallback; // 未提供 → 使用預設值
            try { return coerce(raw); }
            catch (FormatException e) { errors.Add((key, e.Message)); return fallback; }
        }

        var data = new UserProfileData
        {
            Id = Field("id", ToInt, 0L),
            Account = Field("account", ToStr, ""),
            Email = Field("email", ToEmail, ""),
            Phone = Field("phone", ToStr, ""),
            Name = Field("name", ToStr, ""),
            Gender = Field("gender", ToInt, 0L),
            Birthday = Field("birthday", ToStr, ""),
            Height = Field("height", ToFloat, 0.0),
            Weight = Field("weight", ToFloat, 0.0),
            Verified = Field("verified", ToInt, 0L),
            PrivacyPolicy = Field("privacy_policy", ToInt, 0L),
            MustChangePassword = Field("must_change_password", ToInt, 0L),
            FcmId = Field("fcm_id", ToStr, ""),
            FbId = Field("fb_id", ToStr, ""),
            GoogleId = Field("google_id", ToStr, ""),
            AppleId = Field("apple_id", ToStr, ""),
            LoginTimes = Field("login_times", ToInt, 0L),
            Address = Field("address", ToStr, ""),
            InviteCode = Field("invite_code", ToStr, ""),
            Badge = Field("badge", ToInt, 0L),
            Avatar = Field("avatar", ToStr, ""),
            Group = Field("group", ToStr, ""),
            UnreadRecords = Field("unread_records", v => (List<long>)v!, []),
            Status = Field("status", ToStr, "0"),
            Vip = Field("vip", v => (Dictionary<string, object?>?)v, null),
            CreatedAt = Field("created_at", ToStr, ""),
            UpdatedAt = Field("updated_at", ToStr, ""),
            Default = Field("default", v => (Dictionary<string, object?>?)v, null),
            Setting = Field("setting", v => (Dictionary<string, object?>?)v, null),
        };

        if (errors.Count > 0) throw new PyValidationError(nameof(UserProfileData), errors);
        return data;
    }

    // ---- pydantic v1 的轉型規則（失敗以 FormatException 帶出 pydantic 錯誤訊息）----

    private static string ToStr(object? v) => v switch
    {
        string or long or int or double or byte[] => PyOrm.Str(v),
        _ => throw new FormatException("str type expected (type=type_error.str)"),
    };

    private static long ToInt(object? v) => v switch
    {
        long l => l,
        int i => i,
        double d when double.IsFinite(d) => (long)Math.Truncate(d),
        string s when PyOrm.TryParseInt(s, out var l) => l,
        _ => throw new FormatException("value is not a valid integer (type=type_error.integer)"),
    };

    private static double ToFloat(object? v) => v switch
    {
        double d => d,
        long l => l,
        int i => i,
        string s when PyOrm.TryParseFloat(s, out var d) => d,
        _ => throw new FormatException("value is not a valid float (type=type_error.float)"),
    };

    private static string ToEmail(object? v) =>
        (v is string or long or int or double ? PyEmail.Normalize(PyOrm.Str(v)) : null)
        ?? throw new FormatException(PyEmail.ErrorMessage);
}
