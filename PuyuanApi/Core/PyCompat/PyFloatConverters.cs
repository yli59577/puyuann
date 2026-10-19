using System.Globalization;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace PuyuanApi.Core.PyCompat;

// 三個 float 轉換器輸出規則不同（各自對過 Python 版的輸出），不可互換。

/// <summary>
/// User / Account 用：以 <see cref="PyOrm.FloatRepr"/>（Python repr）輸出，例如 170.0、1e-05、1e+20、-0.0；
/// NaN/Inf 丟出 <see cref="PyValueError"/>。讀取只接受 JSON 數字。
/// </summary>
public class PyStrictFloatConverter : JsonConverter<double>
{
    public override double Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options) => reader.GetDouble();

    public override void Write(Utf8JsonWriter writer, double value, JsonSerializerOptions options) =>
        writer.WriteRawValue(PyOrm.FloatRepr(value));
}

/// <summary>
/// Measurement 用：只有「整數值」（有限且 |x| &lt; 1e16）補上 ".0"（0 → 0.0、-0.0 → 0.0），
/// 其他值使用 System.Text.Json 預設數字格式（不是 Python repr）。讀取只接受 JSON 數字。
/// </summary>
public sealed class PyIntegralFloatConverter : JsonConverter<double>
{
    public override double Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options) => reader.GetDouble();

    public override void Write(Utf8JsonWriter writer, double value, JsonSerializerOptions options)
    {
        if (double.IsFinite(value) && Math.Abs(value) < 1e16 && value == Math.Floor(value))
            writer.WriteRawValue(((long)value).ToString(CultureInfo.InvariantCulture) + ".0");
        else
            writer.WriteNumberValue(value);
    }
}

/// <summary>
/// Journal / Else 用：以 <see cref="Py.FloatRepr"/>（Python repr）輸出；NaN/Inf 輸出 NaN / Infinity / -Infinity
/// （與 Python json 相同）。讀取時也接受數字字串。
/// </summary>
public sealed class PyLenientFloatConverter : JsonConverter<double>
{
    public override double Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options) =>
        reader.TokenType == JsonTokenType.String
            ? double.Parse(reader.GetString()!, CultureInfo.InvariantCulture)
            : reader.GetDouble();

    public override void Write(Utf8JsonWriter writer, double value, JsonSerializerOptions options)
    {
        // Python json 對 NaN/Infinity 直接輸出 NaN / Infinity
        if (double.IsNaN(value)) writer.WriteRawValue("NaN", skipInputValidation: true);
        else if (double.IsPositiveInfinity(value)) writer.WriteRawValue("Infinity", skipInputValidation: true);
        else if (double.IsNegativeInfinity(value)) writer.WriteRawValue("-Infinity", skipInputValidation: true);
        else writer.WriteRawValue(Py.FloatRepr(value));
    }
}
