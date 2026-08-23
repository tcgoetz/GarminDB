"""Test Garmin Connect auth adapter."""

__author__ = "Ilya Verchenko"
__copyright__ = "Copyright Ilya Verchenko"
__license__ = "GPL"

import os
import tempfile
import unittest

from garminconnect import GarminConnectAuthenticationError

from garmindb.garmin_connect_auth_adapter import GarminConnectAuthAdapter, GarminConnectAuthError


class FakeConfig:
    def __init__(self, config_dir, user="user@example.com", password="secret", domain="garmin.com"):
        self.config_dir = config_dir
        self.user = user
        self.password = password
        self.domain = domain

    def get_token_store_file(self):
        return self.config_dir + os.sep + "garmin_tokens.json"

    def get_garmin_base_domain(self):
        return self.domain

    def get_user(self):
        return self.user

    def get_password(self):
        return self.password


class FakeGarmin:
    instances = []

    def __init__(self, fail_login=False, **kwargs):
        self.fail_login = fail_login
        self.kwargs = kwargs
        self.login_calls = []
        self.connectapi_calls = []
        self.download_calls = []
        FakeGarmin.instances.append(self)

    def login(self, tokenstore):
        self.login_calls.append(tokenstore)
        if self.fail_login:
            raise GarminConnectAuthenticationError("login failed")

    def connectapi(self, path, **kwargs):
        self.connectapi_calls.append((path, kwargs))
        if path == "/userprofile-service/socialProfile":
            return {"displayName": "display", "fullName": "Full Name"}
        return {"path": path, "kwargs": kwargs}

    def download(self, path, **kwargs):
        self.download_calls.append((path, kwargs))
        return b"downloaded"


class TestGarminConnectAuthAdapter(unittest.TestCase):
    def setUp(self):
        FakeGarmin.instances = []
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config = FakeConfig(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_cached_token_login_uses_token_store_without_credentials(self):
        token_store_file = self.config.get_token_store_file()
        with open(token_store_file, "w", encoding="utf-8") as file:
            file.write("{}")

        adapter = GarminConnectAuthAdapter(self.config, garmin_factory=FakeGarmin)

        self.assertTrue(adapter.login())
        self.assertEqual(len(FakeGarmin.instances), 1)
        self.assertEqual(FakeGarmin.instances[0].kwargs, {"is_cn": False})
        self.assertEqual(FakeGarmin.instances[0].login_calls, [token_store_file])
        self.assertEqual(adapter.display_name, "display")
        self.assertEqual(adapter.full_name, "Full Name")

    def test_invalid_cached_token_falls_back_to_credentials(self):
        token_store_file = self.config.get_token_store_file()
        with open(token_store_file, "w", encoding="utf-8") as file:
            file.write("{}")

        def garmin_factory(**kwargs):
            return FakeGarmin(fail_login=len(FakeGarmin.instances) == 0, **kwargs)

        adapter = GarminConnectAuthAdapter(self.config, garmin_factory=garmin_factory)

        with self.assertLogs(level="WARNING") as captured:
            self.assertTrue(adapter.login())
        self.assertEqual(len(FakeGarmin.instances), 2)
        self.assertEqual(FakeGarmin.instances[1].kwargs["email"], "user@example.com")
        self.assertEqual(FakeGarmin.instances[1].kwargs["password"], "secret")
        self.assertEqual(FakeGarmin.instances[1].login_calls, [token_store_file])
        warnings = [r for r in captured.records if r.levelname == "WARNING"]
        self.assertTrue(
            any(token_store_file in r.getMessage() and "falling back to credential login" in r.getMessage() for r in warnings),
            f"expected WARNING mentioning {token_store_file} and fallback, got {[r.getMessage() for r in warnings]}",
        )

    def test_missing_credentials_raise_auth_error(self):
        config = FakeConfig(self.temp_dir.name, user="", password="")
        adapter = GarminConnectAuthAdapter(config, garmin_factory=FakeGarmin)

        with self.assertRaises(GarminConnectAuthError):
            adapter.login()

    def test_cn_domain_maps_to_is_cn(self):
        config = FakeConfig(self.temp_dir.name, domain="garmin.cn")
        adapter = GarminConnectAuthAdapter(config, garmin_factory=FakeGarmin)

        self.assertTrue(adapter.login())
        self.assertTrue(FakeGarmin.instances[0].kwargs["is_cn"])

    def test_connectapi_and_download_forward_to_authenticated_client(self):
        adapter = GarminConnectAuthAdapter(self.config, garmin_factory=FakeGarmin)
        adapter.login()

        self.assertEqual(
            adapter.connectapi("/example", params={"a": "b"}),
            {"path": "/example", "kwargs": {"params": {"a": "b"}}},
        )
        self.assertEqual(adapter.download("/file"), b"downloaded")


if __name__ == "__main__":
    unittest.main(verbosity=2)
