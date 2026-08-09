import importlib.util
import json
import os
from pathlib import Path
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parent.parent
os.environ.setdefault("LEADS_BUCKET", "test-leads")
os.environ.setdefault("S3_SECRET_ID", "test-s3")
os.environ.setdefault("TG_SECRET_ID", "test-telegram")
SPEC = importlib.util.spec_from_file_location(
    "rednd_form", ROOT / "yandex-function" / "index.py"
)
FORM = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(FORM)


def event(payload, ip="203.0.113.7"):
    return {
        "httpMethod": "POST",
        "headers": {"Origin": "https://rednd.ru"},
        "requestContext": {"identity": {"sourceIp": ip}},
        "body": json.dumps(payload),
    }


def payload():
    return {
        "lang": "ru",
        "task": "Нужен бот",
        "type": "Telegram-бот",
        "budget": "100 000 ₽",
        "contact": "@client",
        "website": "",
    }


class FormHandlerTests(unittest.TestCase):
    def setUp(self):
        FORM._RATE.clear()
        FORM._lockbox_cache.clear()

    @staticmethod
    def response_body(response):
        return json.loads(response["body"])

    def secrets(self, secret_id):
        if secret_id == FORM.S3_SECRET_ID:
            return {"S3_KEY_ID": "key", "S3_SECRET": "secret"}
        return {"TG_BOT_TOKEN": "token", "TG_CHAT_ID": "123"}

    def test_success_stores_before_notification_without_ip(self):
        stored = {}

        def put_object(_key, _secret, _bucket, _object_key, body):
            stored.update(json.loads(body))
            self.assertFalse(send.called)
            return True

        with mock.patch.object(FORM, "_lockbox", side_effect=self.secrets), mock.patch.object(
            FORM, "_put_object", side_effect=put_object
        ), mock.patch.object(FORM, "_send_telegram", return_value=(True, 200, "ok")) as send:
            response = FORM.handler(event(payload()), None)

        self.assertEqual(response["statusCode"], 200)
        self.assertTrue(self.response_body(response)["ok"])
        self.assertNotIn("ip", stored)
        self.assertEqual(stored["contact"], "@client")
        send.assert_called_once()

    def test_notification_failure_reports_that_request_is_stored(self):
        with mock.patch.object(FORM, "_lockbox", side_effect=self.secrets), mock.patch.object(
            FORM, "_put_object", return_value=True
        ), mock.patch.object(FORM, "_send_telegram", return_value=(False, 500, "failed")):
            response = FORM.handler(event(payload()), None)

        self.assertEqual(response["statusCode"], 502)
        self.assertEqual(
            self.response_body(response),
            {"error": "notification delivery failed", "stored": True},
        )

    def test_notification_exception_reports_that_request_is_stored(self):
        with mock.patch.object(FORM, "_lockbox", side_effect=self.secrets), mock.patch.object(
            FORM, "_put_object", return_value=True
        ), mock.patch.object(FORM, "_send_telegram", side_effect=TimeoutError("timeout")):
            response = FORM.handler(event(payload()), None)

        self.assertEqual(response["statusCode"], 502)
        self.assertTrue(self.response_body(response)["stored"])

    def test_storage_failure_does_not_notify(self):
        with mock.patch.object(FORM, "_lockbox", side_effect=self.secrets), mock.patch.object(
            FORM, "_put_object", return_value=False
        ), mock.patch.object(FORM, "_send_telegram") as send:
            response = FORM.handler(event(payload()), None)

        self.assertEqual(response["statusCode"], 502)
        self.assertEqual(self.response_body(response), {"error": "storage write failed"})
        send.assert_not_called()

    def test_honeypot_writes_nothing(self):
        trapped = payload()
        trapped["website"] = "https://spam.example"
        with mock.patch.object(FORM, "_put_object") as put, mock.patch.object(
            FORM, "_send_telegram"
        ) as send:
            response = FORM.handler(event(trapped), None)
        self.assertEqual(response["statusCode"], 200)
        put.assert_not_called()
        send.assert_not_called()

    def test_missing_required_fields_returns_400(self):
        response = FORM.handler(event({"task": "", "contact": ""}), None)
        self.assertEqual(response["statusCode"], 400)


if __name__ == "__main__":
    unittest.main()
