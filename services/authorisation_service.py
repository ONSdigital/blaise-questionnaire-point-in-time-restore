from typing import Any

from dotenv import load_dotenv
from Tools.scripts import google

load_dotenv()


class AuthorisationService:

    def __init__(self):
        self._credentials, self._project_id = google.auth.default()

    def get_credentials_token(self) -> Any:
        self._credentials.refresh(google.auth.transport.requests.Request())

        return self._credentials.token
