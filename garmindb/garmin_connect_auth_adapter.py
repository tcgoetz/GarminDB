"""Adapter around python-garminconnect authentication."""

__author__ = "Ilya Verchenko"
__copyright__ = "Copyright Ilya Verchenko"
__license__ = "GPL"

import logging
import os

from garminconnect import (
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)


logger = logging.getLogger(__file__)


_GARMINCONNECT_ERRORS = (
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)


class GarminConnectAuthError(Exception):
    """Garmin Connect authentication or request failed."""


class GarminConnectAuthAdapter:
    """Small GarminDB boundary around garminconnect.Garmin."""

    def __init__(self, gc_config, garmin_factory=None, mfa_prompt=None):
        """Create a new Garmin Connect auth adapter."""
        self.gc_config = gc_config
        self.garmin_factory = garmin_factory or self.__default_garmin_factory
        self.mfa_prompt = mfa_prompt or self.__prompt_mfa
        self.client = None
        self.profile = None
        self.display_name = None
        self.full_name = None

    @staticmethod
    def __default_garmin_factory(**kwargs):
        from garminconnect import Garmin

        return Garmin(**kwargs)

    @staticmethod
    def __prompt_mfa():
        return input("MFA code: ").strip()

    def __is_cn_domain(self):
        return self.gc_config.get_garmin_base_domain() == "garmin.cn"

    def __token_store_file(self):
        return self.gc_config.get_token_store_file()

    def login(self):
        """Authenticate using cached DI tokens first, then configured credentials."""
        token_store_file = self.__token_store_file()
        if os.path.isfile(token_store_file):
            try:
                self.client = self.garmin_factory(is_cn=self.__is_cn_domain())
                self.client.login(token_store_file)
                self.__load_profile()
                return True
            except _GARMINCONNECT_ERRORS as e:
                logger.warning(
                    "cached Garmin Connect token login failed for %s: %s; falling back to credential login",
                    token_store_file, e,
                )
                self.client = None

        username = self.gc_config.get_user()
        password = self.gc_config.get_password()
        if not username or not password:
            raise GarminConnectAuthError("Missing config: need username and password. Edit GarminConnectConfig.json.")

        try:
            self.client = self.garmin_factory(
                email=username,
                password=password,
                is_cn=self.__is_cn_domain(),
                prompt_mfa=self.mfa_prompt,
            )
            self.client.login(token_store_file)
            self.__load_profile()
            return True
        except _GARMINCONNECT_ERRORS as e:
            self.client = None
            raise GarminConnectAuthError(f"Garmin Connect login failed: {e}") from e

    def __load_profile(self):
        self.profile = self.client.connectapi("/userprofile-service/socialProfile")
        self.display_name = self.profile.get("displayName", getattr(self.client, "display_name", None))
        self.full_name = self.profile.get("fullName", getattr(self.client, "full_name", None))

    def connectapi(self, path, **kwargs):
        """Call a Garmin Connect JSON endpoint."""
        if self.client is None:
            raise GarminConnectAuthError("Garmin Connect client is not authenticated.")
        try:
            return self.client.connectapi(path, **kwargs)
        except _GARMINCONNECT_ERRORS as e:
            raise GarminConnectAuthError(f"Garmin Connect API request failed: {e}") from e

    def download(self, path, **kwargs):
        """Download binary content from Garmin Connect."""
        if self.client is None:
            raise GarminConnectAuthError("Garmin Connect client is not authenticated.")
        try:
            return self.client.download(path, **kwargs)
        except _GARMINCONNECT_ERRORS as e:
            raise GarminConnectAuthError(f"Garmin Connect download failed: {e}") from e
