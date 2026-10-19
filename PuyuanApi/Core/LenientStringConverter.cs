using System.Text.Json;
using System.Text.Json.Serialization;

namespace PuyuanApi.Core;

/// <summary>
/// 讓 string 欄位也能接受數字 / 布林值（模擬 pydantic v1 的自動轉型，
/// 例如 App 傳 "a1c": 5 而模型宣告為 str）。
/// </summary>
public class LenientStringConverter : JsonConverter<string>
{
    public override string? Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options) =>
        reader.TokenType switch
        {
            JsonTokenType.String => reader.GetString(),
            JsonTokenType.Number => System.Text.Encoding.UTF8.GetString(reader.ValueSpan), // 保留原始文字，1.0 → "1.0"
            JsonTokenType.True => "True",
            JsonTokenType.False => "False",
            JsonTokenType.Null => null,
            _ => throw new JsonException($"無法將 {reader.TokenType} 轉為字串"),
        };

    public override void Write(Utf8JsonWriter writer, string value, JsonSerializerOptions options) =>
        writer.WriteStringValue(value);
}
