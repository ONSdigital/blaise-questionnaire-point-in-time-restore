import subprocess
from typing import cast

import google.auth
from google.auth.transport.requests import Request


class AuthorisationService:
    def __init__(self):
        self._credentials, _ = google.auth.default()

    def get_credentials_token(self) -> str:
        try:
            self._credentials.refresh(Request())
            return cast(str, self._credentials.token)
        except Exception:
            return self.__token_via_gcloud()

    @staticmethod
    def __token_via_gcloud() -> str:
        result = subprocess.run(
            ["gcloud", "auth", "print-access-token"],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
