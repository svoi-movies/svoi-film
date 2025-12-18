from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from aiosmtplib import SMTP


class EmailService:

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        use_tls: bool = True,
    ) -> None:
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.use_tls = use_tls

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html: bool = False,
    ) -> None:
        """
        Отправка email сообщения.

        Args:
            to_email: Email получателя
            subject: Тема письма
            body: Текст письма
            html: Если True, отправляет HTML письмо, иначе plain text
        """
        # Создаем сообщение
        msg = MIMEMultipart()
        msg["From"] = self.smtp_user
        msg["To"] = to_email
        msg["Subject"] = subject

        # Добавляем тело письма
        mime_type = "html" if html else "plain"
        msg.attach(MIMEText(body, mime_type))

        # Отправляем письмо асинхронно
        async with SMTP(
            hostname=self.smtp_host,
            port=self.smtp_port,
            start_tls=True,
        ) as smtp:
            await smtp.login(self.smtp_user, self.smtp_password)
            await smtp.send_message(msg)
