import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEFAULT_CHARSET="utf-8",
    )
    django.setup()

import unittest
from email.message import MIMEPart
from email.mime.application import MIMEApplication
from unittest.mock import patch, MagicMock
from django.core.mail import EmailMessage
from django_o365.backend import O365EmailBackend, O365Exception


class TestO365EmailBackend(unittest.TestCase):
    @patch("django_o365.backend.Account")
    def test_send_simple_email(self, mock_account_cls):
        # Setup mocks
        mock_account = MagicMock()
        mock_mailbox = MagicMock()
        mock_message = MagicMock()
        mock_account_cls.return_value = mock_account
        mock_account.authenticate.return_value = True
        mock_account.mailbox.return_value = mock_mailbox
        mock_mailbox.new_message.return_value = mock_message

        backend = O365EmailBackend(
            tenant_id="tenant",
            client_id="client",
            client_secret="secret",
            sender="sender@example.com",
        )
        email = EmailMessage(
            subject="Test Subject",
            body="Test Body",
            from_email="sender@example.com",
            to=["recipient@example.com"],
        )
        sent_count = backend.send_messages([email])
        self.assertEqual(sent_count, 1)
        mock_account_cls.assert_called_once()
        mock_account.authenticate.assert_called_once()
        mock_account.mailbox.assert_called_once_with(resource="sender@example.com")
        mock_mailbox.new_message.assert_called_once()
        mock_message.to.add.assert_called_once_with("recipient@example.com")
        self.assertEqual(mock_message.subject, "Test Subject")
        self.assertEqual(mock_message.body, "Test Body")
        mock_message.send.assert_called_once()

    @patch("django_o365.backend.Account")
    def test_missing_credentials_raises_valueerror(self, mock_account_cls):
        backend = O365EmailBackend(
            tenant_id=None, client_id=None, client_secret=None, sender=None
        )
        with self.assertRaises(ValueError):
            backend.open()

    @patch("django_o365.backend.Account")
    def test_authentication_failure_raises_o365exception(self, mock_account_cls):
        mock_account = MagicMock()
        mock_account_cls.return_value = mock_account
        mock_account.authenticate.return_value = False
        backend = O365EmailBackend(
            tenant_id="tenant",
            client_id="client",
            client_secret="secret",
            sender="sender@example.com",
        )
        with self.assertRaises(O365Exception):
            backend.open()

    @patch("django_o365.backend.Account")
    def test_send_message_with_no_recipients(self, mock_account_cls):
        mock_account = MagicMock()
        mock_mailbox = MagicMock()
        mock_account_cls.return_value = mock_account
        mock_account.authenticate.return_value = True
        mock_account.mailbox.return_value = mock_mailbox
        backend = O365EmailBackend(
            tenant_id="tenant",
            client_id="client",
            client_secret="secret",
            sender="sender@example.com",
        )
        backend.mailbox = mock_mailbox
        email = EmailMessage(
            subject="No Recipients", body="Body", from_email="sender@example.com", to=[]
        )
        result = backend._send(email)
        self.assertFalse(result)

    @patch("django_o365.backend.Account")
    def test_send_message_with_string_attachment(self, mock_account_cls):
        mock_account = MagicMock()
        mock_mailbox = MagicMock()
        mock_message = MagicMock()
        mock_account_cls.return_value = mock_account
        mock_account.authenticate.return_value = True
        mock_account.mailbox.return_value = mock_mailbox
        mock_mailbox.new_message.return_value = mock_message
        backend = O365EmailBackend(
            tenant_id="tenant",
            client_id="client",
            client_secret="secret",
            sender="sender@example.com",
        )
        backend.mailbox = mock_mailbox
        email = EmailMessage(
            subject="With Attachment",
            body="Body",
            from_email="sender@example.com",
            to=["to@example.com"],
        )
        email.attachments = ["file.pdf"]
        result = backend._send(email)
        self.assertTrue(result)
        mock_message.attachments.add.assert_called_with("file.pdf")

    @patch("django_o365.backend.Account")
    def test_send_message_with_tuple_attachment(self, mock_account_cls):
        mock_account = MagicMock()
        mock_mailbox = MagicMock()
        mock_message = MagicMock()
        mock_account_cls.return_value = mock_account
        mock_account.authenticate.return_value = True
        mock_account.mailbox.return_value = mock_mailbox
        mock_mailbox.new_message.return_value = mock_message
        backend = O365EmailBackend(
            tenant_id="tenant",
            client_id="client",
            client_secret="secret",
            sender="sender@example.com",
        )
        backend.mailbox = mock_mailbox
        email = EmailMessage(
            subject="With Tuple Attachment",
            body="Body",
            from_email="sender@example.com",
            to=["to@example.com"],
        )
        email.attachments = [("file.txt", b"content", "text/plain")]
        result = backend._send(email)
        self.assertTrue(result)
        # Check that attachments.add was called with a list containing a BytesIO and filename
        args, kwargs = mock_message.attachments.add.call_args
        self.assertEqual(len(args), 1)
        attachment_arg = args[0]
        self.assertIsInstance(attachment_arg, list)
        self.assertEqual(len(attachment_arg), 1)
        content_obj, filename = attachment_arg[0]
        self.assertEqual(filename, "file.txt")
        self.assertEqual(content_obj.read(), b"content")
        content_obj.seek(0)  # Reset for any further use

    @patch("django_o365.backend.Account")
    def test_send_exception_fail_silently_false(self, mock_account_cls):
        mock_account = MagicMock()
        mock_mailbox = MagicMock()
        mock_account_cls.return_value = mock_account
        mock_account.authenticate.return_value = True
        mock_account.mailbox.return_value = mock_mailbox
        mock_mailbox.new_message.side_effect = Exception("fail")
        backend = O365EmailBackend(
            tenant_id="tenant",
            client_id="client",
            client_secret="secret",
            sender="sender@example.com",
            fail_silently=False,
        )
        backend.mailbox = mock_mailbox
        email = EmailMessage(
            subject="Test",
            body="Body",
            from_email="sender@example.com",
            to=["to@example.com"],
        )
        with self.assertRaises(Exception):
            backend._send(email)

    @patch("django_o365.backend.Account")
    def test_send_exception_fail_silently_true(self, mock_account_cls):
        mock_account = MagicMock()
        mock_mailbox = MagicMock()
        mock_account_cls.return_value = mock_account
        mock_account.authenticate.return_value = True
        mock_account.mailbox.return_value = mock_mailbox
        mock_mailbox.new_message.side_effect = Exception("fail")
        backend = O365EmailBackend(
            tenant_id="tenant",
            client_id="client",
            client_secret="secret",
            sender="sender@example.com",
            fail_silently=True,
        )
        backend.mailbox = mock_mailbox
        email = EmailMessage(
            subject="Test",
            body="Body",
            from_email="sender@example.com",
            to=["to@example.com"],
        )
        result = backend._send(email)
        self.assertFalse(result)

    @patch("django_o365.backend.Account")
    def test_send_html_email(self, mock_account_cls):
        mock_account = MagicMock()
        mock_mailbox = MagicMock()
        mock_message = MagicMock()
        mock_account_cls.return_value = mock_account
        mock_account.authenticate.return_value = True
        mock_account.mailbox.return_value = mock_mailbox
        mock_mailbox.new_message.return_value = mock_message
        backend = O365EmailBackend(
            tenant_id="tenant",
            client_id="client",
            client_secret="secret",
            sender="sender@example.com",
        )
        backend.mailbox = mock_mailbox
        email = EmailMessage(
            subject="HTML Test",
            body="This is the plain text body.",
            from_email="sender@example.com",
            to=["to@example.com"],
        )
        html_content = "<p>This is the <b>HTML</b> body.</p>"
        email.alternatives = [(html_content, "text/html")]
        result = backend._send(email)
        self.assertTrue(result)
        self.assertEqual(mock_message.body, html_content)
        self.assertEqual(mock_message.body_type, "HTML")
        mock_message.send.assert_called_once()

    @patch("django_o365.backend.Account")
    def test_send_message_with_text_attachment(self, mock_account_cls):
        mock_mailbox = MagicMock()
        mock_message = MagicMock()
        mock_mailbox.new_message.return_value = mock_message
        backend = O365EmailBackend(
            tenant_id="tenant",
            client_id="client",
            client_secret="secret",
            sender="sender@example.com",
        )
        backend.mailbox = mock_mailbox
        email = EmailMessage(
            subject="With Text Attachment",
            body="Body",
            from_email="sender@example.com",
            to=["to@example.com"],
        )
        # Django decodes text/* attachments to str
        email.attach("file.txt", "Grüße".encode("utf-8"), "text/plain")
        result = backend._send(email)
        self.assertTrue(result)
        args, kwargs = mock_message.attachments.add.call_args
        content_obj, filename = args[0][0]
        self.assertEqual(filename, "file.txt")
        self.assertEqual(content_obj.read(), "Grüße".encode("utf-8"))

    @patch("django_o365.backend.Account")
    def test_send_message_with_display_name_recipient(self, mock_account_cls):
        mock_mailbox = MagicMock()
        mock_message = MagicMock()
        mock_mailbox.new_message.return_value = mock_message
        backend = O365EmailBackend(
            tenant_id="tenant",
            client_id="client",
            client_secret="secret",
            sender="sender@example.com",
        )
        backend.mailbox = mock_mailbox
        email = EmailMessage(
            subject="Display Name",
            body="Body",
            from_email="Sender <sender@example.com>",
            to=["Jörg Müller <joerg@example.com>"],
        )
        result = backend._send(email)
        self.assertTrue(result)
        mock_message.to.add.assert_called_once_with(
            ("Jörg Müller", "joerg@example.com")
        )

    @patch("django_o365.backend.Account")
    def test_send_message_with_invalid_recipient_raises(self, mock_account_cls):
        mock_mailbox = MagicMock()
        backend = O365EmailBackend(
            tenant_id="tenant",
            client_id="client",
            client_secret="secret",
            sender="sender@example.com",
        )
        backend.mailbox = mock_mailbox
        email = EmailMessage(
            subject="Invalid",
            body="Body",
            from_email="sender@example.com",
            to=["not-an-address"],
        )
        with self.assertRaises(ValueError):
            backend._send(email)
        mock_mailbox.new_message.assert_not_called()

    @patch("django_o365.backend.Account")
    def test_send_message_keeps_cc_bcc_and_reply_to_separate(self, mock_account_cls):
        mock_mailbox = MagicMock()
        mock_message = MagicMock()
        mock_mailbox.new_message.return_value = mock_message
        backend = O365EmailBackend(
            tenant_id="tenant",
            client_id="client",
            client_secret="secret",
            sender="sender@example.com",
        )
        backend.mailbox = mock_mailbox
        email = EmailMessage(
            subject="Recipients",
            body="Body",
            from_email="sender@example.com",
            to=["to@example.com"],
            cc=["Cc Person <cc@example.com>"],
            bcc=["bcc@example.com"],
            reply_to=["reply@example.com"],
        )
        result = backend._send(email)
        self.assertTrue(result)
        mock_message.to.add.assert_called_once_with("to@example.com")
        mock_message.cc.add.assert_called_once_with(("Cc Person", "cc@example.com"))
        mock_message.bcc.add.assert_called_once_with("bcc@example.com")
        mock_message.reply_to.add.assert_called_once_with("reply@example.com")

    @patch("django_o365.backend.Account")
    def test_send_message_with_bcc_only(self, mock_account_cls):
        mock_mailbox = MagicMock()
        mock_message = MagicMock()
        mock_mailbox.new_message.return_value = mock_message
        backend = O365EmailBackend(
            tenant_id="tenant",
            client_id="client",
            client_secret="secret",
            sender="sender@example.com",
        )
        backend.mailbox = mock_mailbox
        email = EmailMessage(
            subject="Bcc only",
            body="Body",
            from_email="sender@example.com",
            bcc=["a@example.com", "b@example.com"],
        )
        result = backend._send(email)
        self.assertTrue(result)
        mock_message.to.add.assert_not_called()
        self.assertEqual(mock_message.bcc.add.call_count, 2)

    @patch("django_o365.backend.Account")
    def test_send_message_with_mime_attachment(self, mock_account_cls):
        mock_mailbox = MagicMock()
        mock_message = MagicMock()
        mock_mailbox.new_message.return_value = mock_message
        backend = O365EmailBackend(
            tenant_id="tenant",
            client_id="client",
            client_secret="secret",
            sender="sender@example.com",
        )
        backend.mailbox = mock_mailbox
        mime_attachments = [MIMEApplication(b"%PDF", Name="file.pdf")]
        mime_part = MIMEPart()
        mime_part.set_content(b"%PDF", "application", "pdf", filename="part.pdf")
        mime_attachments.append(mime_part)
        mime_attachments[0]["Content-Disposition"] = 'attachment; filename="file.pdf"'
        for mime_attachment in mime_attachments:
            mock_message.reset_mock()
            email = EmailMessage(
                subject="MIME Attachment",
                body="Body",
                from_email="sender@example.com",
                to=["to@example.com"],
            )
            email.attachments = [mime_attachment]
            result = backend._send(email)
            self.assertTrue(result)
            args, kwargs = mock_message.attachments.add.call_args
            content_obj, filename = args[0][0]
            self.assertEqual(filename, mime_attachment.get_filename())
            self.assertEqual(content_obj.read(), b"%PDF")

    def test_fail_silently_is_set_on_backend(self):
        backend = O365EmailBackend(fail_silently=True)
        self.assertTrue(backend.fail_silently)
        backend = O365EmailBackend()
        self.assertFalse(backend.fail_silently)
