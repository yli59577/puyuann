using System.Text.Json;
using System.Text.Json.Serialization;

namespace PuyuanApi.Core.PyCompat;

/// <summary>輸出 Python dict（值可能是 int / float / str / None / 巢狀 dict），float 用 <see cref="PyOrm.FloatRepr"/> 格式</summary>
public class PyDictConverter : JsonConverter<Dictionary<string, object?>>
{
    public override Dictionary<string, object?> Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options) =>
        throw new NotSupportedException();

    public override void Write(Utf8JsonWriter writer, Dictionary<string, object?> value, JsonSerializerOptions options) =>
        WriteValue(writer, value, options);

    private static void WriteValue(Utf8JsonWriter writer, object? value, JsonSerializerOptions options)
    {
        switch (value)
        {
            case null: writer.WriteNullValue(); break;
            case string s: writer.WriteStringValue(s); break;
            case bool b: writer.WriteBooleanValue(b); break;
            case long l: writer.WriteNumberValue(l); break;
            case int i: writer.WriteNumberValue(i); break;
            case double d: writer.WriteRawValue(PyOrm.FloatRepr(d)); break;
            case Dictionary<string, object?> dict:
                writer.WriteStartObject();
                foreach (var (k, v) in dict)
                {
                    writer.WritePropertyName(k);
                    WriteValue(writer, v, options);
                }
                writer.WriteEndObject();
                break;
            default: JsonSerializer.Serialize(writer, value, value.GetType(), options); break;
        }
    }
}

/// <summary>pydantic v1 的 Optional[int]：接受 "1"、1.9（截斷）、true</summary>
public class PyIntConverter : JsonConverter<long?>
{
    public override bool HandleNull => true;

    public override long? Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        switch (reader.TokenType)
        {
            case JsonTokenType.Null: return null;
            case JsonTokenType.True: return 1;
            case JsonTokenType.False: return 0;
            case JsonTokenType.Number:
                if (reader.TryGetInt64(out var l)) return l;
                var d = reader.GetDouble();
                if (double.IsFinite(d) && Math.Abs(d) < 9.2e18) return (long)Math.Truncate(d);
                break;
            case JsonTokenType.String:
                if (PyOrm.TryParseInt(reader.GetString()!, out var parsed)) return parsed;
                break;
        }
        throw new JsonException("value is not a valid integer");
    }

    public override void Write(Utf8JsonWriter writer, long? value, JsonSerializerOptions options)
    {
        if (value is null) writer.WriteNullValue(); else writer.WriteNumberValue(value.Value);
    }
}

/// <summary>pydantic v1 的 Optional[bool]：接受 0/1、"yes"/"no"、"on"/"off"、"t"/"f" 等</summary>
public class PyBoolConverter : JsonConverter<bool?>
{
    public override bool HandleNull => true;

    public override bool? Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        switch (reader.TokenType)
        {
            case JsonTokenType.Null: return null;
            case JsonTokenType.True: return true;
            case JsonTokenType.False: return false;
            case JsonTokenType.Number:
                var d = reader.GetDouble();
                if (d == 1) return true;
                if (d == 0) return false;
                break;
            case JsonTokenType.String:
                switch (reader.GetString()!.ToLowerInvariant())
                {
                    case "1" or "on" or "t" or "true" or "y" or "yes": return true;
                    case "0" or "off" or "f" or "false" or "n" or "no": return false;
                }
                break;
        }
        throw new JsonException("value could not be parsed to a boolean");
    }

    public override void Write(Utf8JsonWriter writer, bool? value, JsonSerializerOptions options)
    {
        if (value is null) writer.WriteNullValue(); else writer.WriteBooleanValue(value.Value);
    }
}
