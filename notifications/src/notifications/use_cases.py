import logging

from notifications.service import EmailService

logger = logging.getLogger("commands")


class NotificationCommands:
    def __init__(self, email_service: EmailService) -> None:
        self._email_service = email_service

    async def send_email_notification(
        self,
        email: str,
        subject: str,
        body: str,
    ) -> None:
        logger.info(f"Sending email to user {email}")
        await self._email_service.send_email(email, subject, body, html=True)
