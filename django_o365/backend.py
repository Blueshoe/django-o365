import threading
from email.utils import parseaddr
from io import BytesIO

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from O365 import Account
from django.core.mail.message import sanitize_address


class O365Exception(Exception):
    pass


class O365EmailBackend(BaseEmailBackend):
    def __init__(
        self,
        tenant_id=None,
        client_id=None,
        client_secret=None,
        sender=None,
        fail_silently=False,
        **kwargs
    ):
        super(O365EmailBackend, self).__init__(fail_silently=fail_silently)
        # Get O365 credentials and sender from kwargs or Django settings
        self.tenant_id = tenant_id or getattr(settings, "EMAIL_O365_TENANT_ID", None)
        self.client_id = client_id or getattr(settings, "EMAIL_O365_CLIENT_ID", None)
        self.client_secret = client_secret or getattr(
            settings, "EMAIL_O365_CLIENT_SECRET", None
        )
        self.sender = sender or getattr(settings, "EMAIL_O365_SENDER", None)
        self.mailbox = None
        self._lock = threading.RLock()

    def open(self):
        if not all([self.tenant_id, self.client_id, self.client_secret, self.sender]):
            raise ValueError("O365 credentials or sender not configured.")

        credentials = (self.client_id, self.client_secret)
        account = Account(
            credentials, auth_flow_type="credentials", tenant_id=self.tenant_id
        )

        if not account.authenticate():
            raise O365Exception("O365 authentication failed.")

        self.mailbox = account.mailbox(resource=self.sender)
        return True

    def send_messages(self, email_messages):
        if not email_messages:
            return 0
        with self._lock:
            try:
                self.open()
            except Exception as e:
                if self.fail_silently:
                    return 0
                raise e

            num_sent = 0
            for message in email_messages:
                sent = self._send(message)
                if sent:
                    num_sent += 1
        return num_sent

    def _send(self, email_message):
        """A helper method that does the actual sending."""
        if not email_message.recipients():
            return False
        encoding = email_message.encoding or settings.DEFAULT_CHARSET
        from_email = sanitize_address(email_message.from_email, encoding)
        # from_email could be a formatted email string, e.g. "FOO <foo@bar.com>"
        _, from_email_address = parseaddr(from_email)
        recipients = [
            sanitize_address(addr, encoding) for addr in email_message.recipients()
        ]

        with self._lock:
            try:
                m = self.mailbox.new_message()
                for recipient in recipients:
                    m.to.add(recipient)
                m.subject = email_message.subject

                # Handle HTML emails if alternatives are present
                if (
                    hasattr(email_message, "alternatives")
                    and email_message.alternatives
                ):
                    html_set = False
                    for content, mimetype in email_message.alternatives:
                        if mimetype == "text/html":
                            m.body = content
                            m.body_type = "HTML"
                            html_set = True
                            break
                    if not html_set:
                        m.body = email_message.body
                        m.body_type = "Text"
                else:
                    m.body = email_message.body
                    m.body_type = "Text"

                # Attachments: Django EmailMessage.attachments is a list of
                # (filename, content, mimetype) or file paths
                for attachment in getattr(email_message, "attachments", []):
                    if isinstance(attachment, str):
                        m.attachments.add(attachment)
                    elif isinstance(attachment, tuple) and len(attachment) == 3:
                        filename, content, mimetype = attachment
                        # If content is not a BytesIO, wrap it
                        if not isinstance(content, BytesIO):
                            content = BytesIO(content)
                        m.attachments.add([(content, filename)])
                m.send()
            except Exception:
                if not self.fail_silently:
                    raise
                return False
        return True
