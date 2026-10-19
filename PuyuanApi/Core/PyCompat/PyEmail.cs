using System.Globalization;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.RegularExpressions;

namespace PuyuanApi.Core.PyCompat;

/// <summary>pydantic v1 的 EmailStr 驗證（pydantic 1.10 + email-validator 2.0，check_deliverability=False）</summary>
public static class PyEmail
{
    private static readonly Regex PrettyEmail = new(@"\A([\w ]*?) *<(.*)> *\z");
    private static readonly Regex QuotedLocal = new("\\A\"((?:[^\"\\\\]|\\\\.)*)\"@");
    private const string AText = @"a-zA-Z0-9_!#$%&'*+\-/=?^`{|}~";
    private static readonly Regex DotAtom = new($@"\A[{AText}]+(?:\.[{AText}]+)*\z");
    private static readonly Regex DotAtomIntl = new($@"\A[{AText}\u0080-\uFFFF]+(?:\.[{AText}\u0080-\uFFFF]+)*\z");
    private static readonly Regex HostChars = new(@"\A[a-zA-Z0-9\-.\u0080-\uFFFF]+\z");
    private const string Label = "(?:(?:[a-zA-Z0-9][a-zA-Z0-9-]*)?[a-zA-Z0-9])";
    private static readonly Regex Hostname = new($@"\A{Label}(?:\.{Label})*\z");
    private static readonly string[] SpecialUse = ["arpa", "invalid", "local", "localhost", "onion", "test"];
    private static readonly string[] CaseInsensitiveMailboxes =
        ["info", "marking", "sales", "support", "abuse", "noc", "security", "postmaster", "hostmaster", "usenet", "news", "webmaster", "www", "uucp", "ftp"];

    /// <summary>pydantic v1 的錯誤訊息</summary>
    public const string ErrorMessage = "value is not a valid email address (type=value_error.email)";

    /// <summary>驗證並正規化 email；不合法回傳 null</summary>
    public static string? Normalize(string value)
    {
        var pretty = PrettyEmail.Match(value);
        if (pretty.Success) value = pretty.Groups[2].Value;
        var email = value.Trim();

        if (QuotedLocal.IsMatch(email)) return null; // 不允許引號 local part
        var parts = email.Split('@');
        if (parts.Length != 2) return null;
        var (local, domain) = (parts[0], parts[1]);

        // ---- local part ----
        if (local.Length == 0 || local.EnumerateRunes().Count() > 64) return null;
        if (!DotAtom.IsMatch(local))
        {
            if (!DotAtomIntl.IsMatch(local)) return null;
            local = local.Normalize(NormalizationForm.FormC);
            if (!SafeChars(local)) return null;
        }
        else if (CaseInsensitiveMailboxes.Contains(local.ToLowerInvariant()))
        {
            local = local.ToLowerInvariant();
        }

        // ---- domain part ----
        if (domain.Length == 0 || (domain.StartsWith('[') && domain.EndsWith(']'))) return null;
        if (!HostChars.IsMatch(domain) || !SafeChars(domain)) return null;
        string asciiDomain, unicodeDomain;
        try
        {
            var idn = new IdnMapping { UseStd3AsciiRules = false, AllowUnassigned = false };
            var mapped = domain.All(c => c < 0x80) ? domain.ToLowerInvariant() : idn.GetUnicode(idn.GetAscii(domain));
            if (mapped.StartsWith('.') || mapped.EndsWith('.') || mapped.Contains("..")) return null;
            if (mapped.StartsWith('-') || mapped.EndsWith('-') || mapped.Contains(".-") || mapped.Contains("-.")) return null;
            if (mapped.Split('.').Any(l => Regex.IsMatch(l, "^(?!xn)..--", RegexOptions.IgnoreCase))) return null;
            asciiDomain = Hostname.IsMatch(mapped) ? mapped : idn.GetAscii(mapped);
            unicodeDomain = idn.GetUnicode(asciiDomain);
        }
        catch (ArgumentException)
        {
            return null;
        }
        if (!Hostname.IsMatch(asciiDomain) || asciiDomain.Length > 255) return null;
        if (asciiDomain.Split('.').Any(l => l.Length > 63)) return null;
        if (!asciiDomain.Contains('.') || !Regex.IsMatch(asciiDomain, "[A-Za-z]\\z")) return null;
        if (SpecialUse.Any(d => asciiDomain == d || asciiDomain.EndsWith("." + d))) return null;

        var normalized = local + "@" + unicodeDomain;
        if (Encoding.UTF8.GetByteCount(normalized) > 254) return null;
        return normalized;
    }

    private static bool SafeChars(string s)
    {
        var i = 0;
        foreach (var rune in s.EnumerateRunes())
        {
            var cat = Rune.GetUnicodeCategory(rune);
            switch (cat)
            {
                case UnicodeCategory.NonSpacingMark or UnicodeCategory.SpacingCombiningMark or UnicodeCategory.EnclosingMark:
                    if (i == 0) return false;
                    break;
                case UnicodeCategory.SpaceSeparator or UnicodeCategory.LineSeparator or UnicodeCategory.ParagraphSeparator
                    or UnicodeCategory.Control or UnicodeCategory.Format or UnicodeCategory.Surrogate
                    or UnicodeCategory.PrivateUse or UnicodeCategory.OtherNotAssigned:
                    return false;
            }
            i++;
        }
        return true;
    }
}

/// <summary>pydantic v1 的 EmailStr：驗證並正規化（網域轉小寫等），不合法視為驗證錯誤</summary>
public class EmailStrConverter : JsonConverter<string>
{
    public override string Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        // pydantic 先用 str_validator 轉字串（數字也會轉），再驗證 email
        var raw = reader.TokenType switch
        {
            JsonTokenType.String => reader.GetString()!,
            JsonTokenType.Number => "0", // 數字轉成字串後必定不含 @，一律不合法
            _ => throw new JsonException(PyEmail.ErrorMessage),
        };
        return PyEmail.Normalize(raw) ?? throw new JsonException(PyEmail.ErrorMessage);
    }

    public override void Write(Utf8JsonWriter writer, string value, JsonSerializerOptions options) =>
        writer.WriteStringValue(value);
}
