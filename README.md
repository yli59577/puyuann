# 普元後端 API（C# / ASP.NET Core）

由原 Python FastAPI 版本移植而來，API 路徑與 JSON 格式與原版相容，iOS App 不需修改。

## 專案架構

```
puyuan - Cs/
├─ Puyuan.sln
├─ .env                     # SECRET_KEY、SMTP、API_HOST / API_PORT
└─ PuyuanApi/
   ├─ Program.cs            # 啟動、JSON 設定、全域錯誤處理、Swagger
   ├─ appsettings.json
   ├─ Core/                 # 共用：Database、Security(JWT)、EmailService、CleanupService、TimeUtil
   │  └─ PyCompat/          # 模擬 FastAPI / pydantic 行為的相容工具
   ├─ Modules/              # 各功能模組（Controller / Models / Module）
   │  ├─ Account/           # /api/register、/api/auth、/api/password/*、/api/verification/*
   │  ├─ User/              # /api/user、/api/user/setting、/api/user/badge
   │  ├─ Measurement/       # /api/user/blood/pressure、weight、blood/sugar、records、last-upload
   │  ├─ Journal/           # /api/user/diary、diet、records (DELETE)
   │  ├─ A1c/               # /api/user/a1c
   │  ├─ Medicine/          # /api/user/medical、drug-used
   │  ├─ Care/              # /api/user/care
   │  ├─ Friend/            # /api/friend/*
   │  └─ Else/              # /api/news、/api/share
   └─ Data/
      ├─ Puyuan.db          # SQLite 資料庫
      └─ Puyuan.db.backup
```

## 快速開始

需要 [.NET 10 SDK](https://dotnet.microsoft.com/download)。

```bash
dotnet run --project PuyuanApi
```

- 本機：http://localhost:8000
- API 文件（Swagger）：http://localhost:8000/docs
- 手機：http://你的電腦IP:8000（`ipconfig` 查 IPv4 位址）

埠號與監聽位址由 `.env` 的 `API_HOST` / `API_PORT` 設定。

## 資料庫

- SQLite，預設位置 `PuyuanApi/Data/Puyuan.db`
- 可在 `appsettings.json` 加入 `"Database": { "Path": "..." }` 或設定環境變數 `Database__Path` 覆寫（相對路徑以 `PuyuanApi/` 為基準）
- 找不到檔案時程式會直接報錯，不會自動建立空資料庫

## 設定（.env）

| 變數 | 說明 |
|---|---|
| `SECRET_KEY` | JWT 簽章金鑰（HS256） |
| `ACCESS_TOKEN_EXPIRE_HOURS` | Token 有效時數，預設 24 |
| `API_HOST` / `API_PORT` | 監聽位址與埠號 |
| `SMTP_SERVER` / `SMTP_PORT` / `SMTP_EMAIL` / `SMTP_PASSWORD` | 寄送驗證碼的 Gmail 設定 |
| `SEND_EMAIL` | `false` 時不寄信 |

## 故障排除

- **埠被佔用**：修改 `.env` 的 `API_PORT`。注意 Windows 可能保留部分埠號範圍（可用 `netsh int ipv4 show excludedportrange protocol=tcp` 查詢）。
- **防火牆**：允許 `PuyuanApi.exe` / `dotnet` 通過 Windows 防火牆，手機才能連線。
