from types import SimpleNamespace
from unittest.mock import Mock, patch

from services.authorisation_service import AuthorisationService


@patch("services.authorisation_service.google.auth.default")
def test_get_credentials_token_uses_refreshed_google_credentials(
    mock_default: Mock,
) -> None:
    credentials = SimpleNamespace(token="token-from-adc")
    credentials.refresh = Mock()
    mock_default.return_value = (credentials, "project-id")

    service = AuthorisationService()

    token = service.get_credentials_token()

    assert token == "token-from-adc"
    credentials.refresh.assert_called_once()


@patch("services.authorisation_service.subprocess.run")
@patch("services.authorisation_service.google.auth.default")
def test_get_credentials_token_falls_back_to_gcloud_when_refresh_fails(
    mock_default: Mock,
    mock_run: Mock,
) -> None:
    credentials = SimpleNamespace(token=None)
    credentials.refresh = Mock(side_effect=RuntimeError("adc failed"))
    mock_default.return_value = (credentials, "project-id")
    mock_run.return_value = SimpleNamespace(stdout="gcloud-token\n")

    service = AuthorisationService()

    token = service.get_credentials_token()

    assert token == "gcloud-token"
    mock_run.assert_called_once()
