from Tools.scripts import google


class AuthorisationService:

    def __init__(self):
        self._credentials, self._project_id = google.auth.default()

    def get_credentials_token(self):
        self._credentials.refresh(google.auth.transport.requests.Request())

        return self._credentials.token
