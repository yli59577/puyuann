using System.Net;
using System.Net.Mail;

namespace PuyuanApi.Core;

/// <summary>郵件服務（對應 app/core/email_config.py）</summary>
public class EmailService(ILogger<EmailService> logger)
{
    private readonly string _server = DotEnv.Get("SMTP_SERVER", "smtp.gmail.com");
    private readonly int _port = DotEnv.GetInt("SMTP_PORT", 587);
    private readonly string _email = DotEnv.Get("SMTP_EMAIL");
    private readonly string _password = DotEnv.Get("SMTP_PASSWORD");
    private readonly bool _enabled = DotEnv.Get("SEND_EMAIL", "true").Equals("true", StringComparison.OrdinalIgnoreCase);

    /// <summary>發送驗證碼郵件</summary>
    public bool SendVerificationCode(string toEmail, string code)
    {
        logger.LogInformation("準備發送驗證碼到: {Email}", toEmail);
        var ok = Send(toEmail, "【普元健康】驗證碼通知", BuildHtml("驗證碼", "您的驗證碼是：", code, "#007bff",
            "此驗證碼將在 <strong>10 分鐘</strong> 後失效。<br>如果這不是您的操作，請忽略此郵件。"));
        if (ok) logger.LogInformation("驗證碼已發送到: {Email}", toEmail);
        return ok;
    }

    /// <summary>發送臨時密碼郵件</summary>
    public bool SendTempPassword(string toEmail, string tempPassword)
    {
        logger.LogInformation("準備發送臨時密碼到: {Email}", toEmail);
        var ok = Send(toEmail, "【普元健康】臨時密碼通知", BuildHtml("臨時密碼", "您的臨時密碼是：", tempPassword, "#dc3545",
            "請使用此臨時密碼登入，登入後請立即重設您的密碼。<br>如果這不是您的操作，請立即聯繫客服。"));
        if (ok) logger.LogInformation("臨時密碼已發送到: {Email}", toEmail);
        return ok;
    }

    private bool Send(string toEmail, string subject, string html)
    {
        if (!_enabled)
        {
            logger.LogInformation("郵件發送已停用 (SEND_EMAIL=false)");
            return false;
        }

        try
        {
            using var msg = new MailMessage(_email, toEmail, subject, html) { IsBodyHtml = true };
            using var client = new SmtpClient(_server, _port)
            {
                EnableSsl = true, // Gmail 587 使用 STARTTLS
                Credentials = new NetworkCredential(_email, _password),
            };
            client.Send(msg);
            return true;
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "發送失敗: {Message}", ex.Message);
            return false;
        }
    }

    private static string BuildHtml(string title, string intro, string value, string color, string note) => $"""
        <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: #f9f9f9; padding: 30px; border-radius: 10px;">
                    <h2 style="color: #333;">普元健康 - {title}</h2>
                    <p style="font-size: 16px; color: #555;">{intro}</p>
                    <div style="background-color: {color}; color: white; font-size: 32px; font-weight: bold; padding: 20px; text-align: center; border-radius: 5px; letter-spacing: 5px;">
                        {value}
                    </div>
                    <p style="margin-top: 20px; font-size: 14px; color: #777;">
                        {note}
                    </p>
                    <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
                    <p style="font-size: 12px; color: #999; text-align: center;">
                        © 2025 普元健康 IoT 系統
                    </p>
                </div>
            </body>
        </html>
        """;
}
