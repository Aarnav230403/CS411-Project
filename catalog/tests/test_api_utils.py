import pytest
import requests
from catalog.utils.api_utils import get_random

RANDOM_NUMBER = 4


def test_get_random(mocker):
    """Test retrieving a random number from random.org."""
    mock_response = mocker.Mock()
    mock_response.text = f"{RANDOM_NUMBER}"
    mock_get = mocker.patch("requests.get", return_value=mock_response)

    result = get_random(10)

    assert result == RANDOM_NUMBER, f"Expected random number {RANDOM_NUMBER}, but got {result}"
    mock_get.assert_called_once_with(
        "https://www.random.org/integers/?num=1&min=1&col=1&base=10&format=plain&rnd=new&max=10",
        timeout=5
    )


def test_get_random_request_failure(mocker):
    """Test handling of a request failure when calling random.org."""
    mocker.patch("requests.get", side_effect=requests.exceptions.RequestException("Connection error"))

    with pytest.raises(RuntimeError, match="Request to random.org failed: Connection error"):
        get_random(10)


def test_get_random_timeout(mocker):
    """Test handling of a timeout when calling random.org."""
    mocker.patch("requests.get", side_effect=requests.exceptions.Timeout)

    with pytest.raises(RuntimeError, match="Request to random.org timed out."):
        get_random(10)


def test_get_random_invalid_response(mocker):
    """Test handling of an invalid response from random.org."""
    mock_response = mocker.Mock()
    mock_response.text = "invalid_response"
    mocker.patch("requests.get", return_value=mock_response)

    with pytest.raises(ValueError, match="Invalid response from random.org: invalid_response"):
        get_random(10)
