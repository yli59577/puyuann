namespace PuyuanApi.Core;

/// <summary>讀取 .env 檔案到環境變數（對應 Python 的 python-dotenv）</summary>
public static class DotEnv
{
    public static void Load(params string[] candidatePaths)
    {
        foreach (var path in candidatePaths)
        {
            if (!File.Exists(path)) continue;

            foreach (var raw in File.ReadAllLines(path))
            {
                var line = raw.Trim();
                if (line.Length == 0 || line.StartsWith('#')) continue;

                var idx = line.IndexOf('=');
                if (idx <= 0) continue;

                var key = line[..idx].Trim();
                var value = line[(idx + 1)..].Trim().Trim('"', '\'');

                // 已存在的環境變數優先，與 python-dotenv 預設行為一致
                if (Environment.GetEnvironmentVariable(key) is null)
                    Environment.SetEnvironmentVariable(key, value);
            }
            return;
        }
    }

    public static string Get(string key, string defaultValue = "") =>
        Environment.GetEnvironmentVariable(key) ?? defaultValue;

    public static int GetInt(string key, int defaultValue) =>
        int.TryParse(Environment.GetEnvironmentVariable(key), out var v) ? v : defaultValue;
}
