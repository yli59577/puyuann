using Dapper;
using PuyuanApi.Core;
using PuyuanApi.Core.PyCompat;

namespace PuyuanApi.Modules.Medicine;

/// <summary>就醫、藥物資訊模組（對應 app/medicine/module.py，資料表 MedicalInfo、DrugInfo）</summary>
public class MedicineModule(Database db, Security security, ILogger logger)
{
    /// <summary>
    /// 對應 UserModule.parse_user_id_from_token：
    /// authorization.split(" ") 必須剛好兩段且第一段為 "Bearer"，否則回傳 null。
    /// </summary>
    public int? ParseUserIdFromToken(string? authorization)
    {
        if (string.IsNullOrEmpty(authorization))
        {
            logger.LogWarning("缺少 Authorization header");
            return null;
        }

        var parts = authorization.Split(' ');
        if (parts.Length != 2)
        {
            logger.LogError("Token 處理錯誤: too many values to unpack (expected 2)");
            return null;
        }
        if (parts[0] != "Bearer")
        {
            logger.LogWarning("Token 類型錯誤: {Type}", parts[0]);
            return null;
        }

        var userId = security.VerifyToken(parts[1]);
        if (userId is null) logger.LogWarning("Token 解析失敗: 簽名驗證失敗或格式錯誤");
        return userId;
    }

    /// <summary>Python 的 datetime.now().isoformat()（本地時間，含微秒）</summary>
    private static string NowIso() => PyDateTime.IsoFormat(DateTime.Now);

    /// <summary>獲取使用者的就醫資訊（查無資料或任何錯誤 / 型別驗證失敗 → null）</summary>
    public MedicalInfo? GetMedicalInfo(int userId)
    {
        try
        {
            using var conn = db.Open();
            var row = (IDictionary<string, object?>?)conn.QueryFirstOrDefault(
                "SELECT * FROM MedicalInfo WHERE user_id = @userId", new { userId });
            if (row is null) return null;

            return new MedicalInfo(
                PyCoerce.Int(row["id"], "id"),
                PyCoerce.Int(row["user_id"], "user_id"),
                PyCoerce.Int(row["oad"], "oad"),
                PyCoerce.Int(row["insulin"], "insulin"),
                PyCoerce.Int(row["anti_hypertensives"], "anti_hypertensives"),
                PyCoerce.Int(row["diabetes_type"], "diabetes_type"),
                PyCoerce.Str(row["created_at"], "created_at"),
                PyCoerce.Str(row["updated_at"], "updated_at"));
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "get_medical_info error: {Message}", ex.Message);
            return null;
        }
    }

    /// <summary>更新或創建使用者的就醫資訊</summary>
    public bool UpdateMedicalInfo(int userId, int oad, int insulin, int antiHypertensives, int diabetesType)
    {
        try
        {
            var now = NowIso();
            using var conn = db.Open();
            var existing = conn.ExecuteScalar<long?>("SELECT id FROM MedicalInfo WHERE user_id = @userId", new { userId });

            if (existing is not null)
            {
                conn.Execute(
                    """
                    UPDATE MedicalInfo
                    SET oad = COALESCE(@oad, oad), insulin = COALESCE(@insulin, insulin),
                        anti_hypertensives = COALESCE(@antiHypertensives, anti_hypertensives),
                        diabetes_type = COALESCE(@diabetesType, diabetes_type), updated_at = @now
                    WHERE user_id = @userId
                    """, new { oad, insulin, antiHypertensives, diabetesType, now, userId });
            }
            else
            {
                conn.Execute(
                    """
                    INSERT INTO MedicalInfo (user_id, oad, insulin, anti_hypertensives, diabetes_type, created_at, updated_at)
                    VALUES (@userId, @oad, @insulin, @antiHypertensives, @diabetesType, @now, @now)
                    """, new { userId, oad, insulin, antiHypertensives, diabetesType, now });
            }
            return true;
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "update_medical_info error: {Message}", ex.Message);
            return false;
        }
    }

    /// <summary>獲取使用者的藥物使用紀錄列表（任何一筆驗證失敗或資料庫錯誤 → 空列表）</summary>
    public List<DrugUsedRecord> GetDrugUsedList(int userId)
    {
        try
        {
            using var conn = db.Open();
            return conn.Query("SELECT id, drugname AS name, drug_type AS type, recorded_at, created_at, updated_at, user_id FROM DrugInfo WHERE user_id = @userId ORDER BY recorded_at DESC", new { userId })
                .Select(r => (IDictionary<string, object?>)r)
                .Select(row => new DrugUsedRecord(
                    PyCoerce.Int(row["id"], "id"),
                    PyCoerce.Str(row["name"], "name"),
                    PyCoerce.Int(row["type"], "type"),
                    PyCoerce.Str(row["recorded_at"], "recorded_at"),
                    PyCoerce.Str(row["updated_at"], "updated_at"),
                    PyCoerce.Str(row["created_at"], "created_at"),
                    PyCoerce.Int(row["user_id"], "user_id")))
                .ToList();
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "get_drug_used_list error: {Message}", ex.Message);
            return [];
        }
    }

    /// <summary>上傳藥物使用紀錄</summary>
    public bool UploadDrugUsed(int userId, int drugType, string name, string recordedAt)
    {
        try
        {
            var now = NowIso();
            using var conn = db.Open();
            conn.Execute(
                """
                INSERT INTO DrugInfo (user_id, drugname, drug_type, recorded_at, created_at, updated_at)
                VALUES (@userId, @name, @drugType, @recordedAt, @now, @now)
                """, new { userId, name, drugType, recordedAt, now });
            return true;
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "upload_drug_used error: {Message}", ex.Message);
            return false;
        }
    }

    /// <summary>刪除藥物使用紀錄（只能刪除自己的記錄）</summary>
    public bool DeleteDrugUsedRecords(int userId, List<int> ids)
    {
        if (ids.Count == 0) return true;

        try
        {
            using var conn = db.Open();
            conn.Execute("DELETE FROM DrugInfo WHERE user_id = @userId AND id IN @ids", new { userId, ids });
            return true;
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "delete_drug_used_records error: {Message}", ex.Message);
            return false;
        }
    }
}
