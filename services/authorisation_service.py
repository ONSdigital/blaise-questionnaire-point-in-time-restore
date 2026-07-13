import subprocess
from typing import cast

import google.auth
from google.auth.credentials import Credentials
from google.auth.transport.requests import Request

_CLOUD_PLATFORM_SCOPE = "https://www.googleapis.com/auth/cloud-platform"


class AuthorisationService:
    def __init__(self):
        credentials, _ = google.auth.default()
        self._credentials = self.__ensure_scoped_credentials(credentials)

    def get_credentials_token(self) -> str:
        try:
            self._credentials.refresh(Request())
            return cast(str, self._credentials.token)
        except Exception:
            return self.__token_via_gcloud()

    @staticmethod
    def __ensure_scoped_credentials(credentials: Credentials) -> Credentials:
        if getattr(credentials, "requires_scopes", False):
            with_scopes = getattr(credentials, "with_scopes", None)
            if callable(with_scopes):
                return cast(Credentials, with_scopes([_CLOUD_PLATFORM_SCOPE]))

        return credentials

    @staticmethod
    def __token_via_gcloud() -> str:
        result = subprocess.run(
            ["gcloud", "auth", "print-access-token"],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
