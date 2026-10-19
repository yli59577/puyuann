using System.Data;
using Microsoft.Data.Sqlite;

namespace PuyuanApi.Core;

/// <summary>SQLite 連線工廠（對應 app/core/database.py，共用同一個 Puyuan.db）</summary>
public class Database
{
    private readonly string _connectionString;

    public Database(string dbPath)
    {
        DbPath = Path.GetFullPath(dbPath);

        // 找不到檔案就直接報錯，避免 SQLite 默默建立一個空的資料庫
        if (!File.Exists(DbPath))
            throw new FileNotFoundException($"找不到資料庫檔案: {DbPath}，請確認 Database:Path 設定。", DbPath);

        _connectionString = new SqliteConnectionStringBuilder
        {
            DataSource = DbPath,
            Mode = SqliteOpenMode.ReadWrite,
        }.ToString();
    }

    public string DbPath { get; }

    /// <summary>開啟一個新連線，使用後請 dispose（using var conn = db.Open();）</summary>
    public IDbConnection Open()
    {
        var conn = new SqliteConnection(_connectionString);
        conn.Open();
        return conn;
    }
}
