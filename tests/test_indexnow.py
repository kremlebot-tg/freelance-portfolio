import contextlib
import io
import json
import os
import unittest
from unittest import mock

from tools import submit_indexnow


class _Response:
    status = 202

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class IndexNowTests(unittest.TestCase):
    def test_sitemap_contains_only_unique_public_urls(self):
        urls = submit_indexnow.sitemap_urls()
        self.assertEqual(len(urls), 28)
        self.assertEqual(len(urls), len(set(urls)))
        self.assertTrue(all(url.startswith("https://rednd.ru/") for url in urls))

    def test_invalid_key_is_rejected_before_network(self):
        with mock.patch.dict(os.environ, {"INDEXNOW_KEY": "bad key"}, clear=False):
            with mock.patch.object(submit_indexnow, "urlopen") as mocked_urlopen:
                self.assertEqual(submit_indexnow.main(), 2)
        mocked_urlopen.assert_not_called()

    def test_submission_contains_sitemap_urls_without_printing_key(self):
        key = "TestIndexNowKey12345678"
        output = io.StringIO()
        with mock.patch.dict(os.environ, {"INDEXNOW_KEY": key}, clear=False):
            with mock.patch.object(submit_indexnow, "urlopen", return_value=_Response()) as mocked:
                with contextlib.redirect_stdout(output):
                    self.assertEqual(submit_indexnow.main(), 0)
        request = mocked.call_args.args[0]
        payload = json.loads(request.data)
        self.assertEqual(payload["host"], "rednd.ru")
        self.assertEqual(payload["key"], key)
        self.assertEqual(payload["keyLocation"], f"https://rednd.ru/{key}.txt")
        self.assertEqual(payload["urlList"], submit_indexnow.sitemap_urls())
        self.assertNotIn(key, output.getvalue())


if __name__ == "__main__":
    unittest.main()
