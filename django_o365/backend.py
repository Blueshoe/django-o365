import threading
from email.message import Message
from email.utils import parseaddr
from io import BytesIO

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from O365 import Account


class O365Exception(Exception):
    pass


def parse_address(address):
    """
    Split an address like "Name <foo@bar.com>" into a (name, address) tuple
    as expected by O365 Recipients.
    """
    if "\n" in address or "\r" in address:
        raise ValueError("Invalid address; address parts cannot contain newlines.")
    name, addr = parseaddr(address)
    if "@" not in addr:
        raise ValueError(f'Invalid address "{address}"')
    return name, addr


class O365EmailBackend(BaseEmailBackend):
    def __init__(
        self,
        tenant_id=None,
        client_id=None,
        client_secret=None,
        sender=None,
        fail_silently=False,
        **kwargs,
    ):
        # Django 6.1+ expects subclasses to handle fail_silently themselves and
        # to pass alias and unknown kwargs on to BaseEmailBackend.
        super().__init__(**kwargs)
        self.fail_silently = fail_silently
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
        # Keep to, cc, bcc and reply_to apart, otherwise e.g. bcc recipients
        # would be disclosed to all other recipients.
        recipient_fields = {
            field: [parse_address(addr) for addr in getattr(email_message, field)]
            for field in ("to", "cc", "bcc", "reply_to")
        }

        with self._lock:
            try:
                m = self.mailbox.new_message()
                for field, recipients in recipient_fields.items():
                    for name, address in recipients:
                        getattr(m, field).add((name, address) if name else address)
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
                # (filename, content, mimetype) tuples, MIME objects or file paths
                for attachment in getattr(email_message, "attachments", []):
                    if isinstance(attachment, str):
                        m.attachments.add(attachment)
                    elif isinstance(attachment, Message):
                        # MIMEBase (Django < 6.0) or MIMEPart (Django 6.0+)
                        content = BytesIO(attachment.get_payload(decode=True) or b"")
                        filename = attachment.get_filename() or "attachment"
                        m.attachments.add([(content, filename)])
                    elif isinstance(attachment, tuple) and len(attachment) == 3:
                        filename, content, mimetype = attachment
                        # Django decodes text/* attachments to str
                        if isinstance(content, str):
                            content = content.encode(encoding)
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
