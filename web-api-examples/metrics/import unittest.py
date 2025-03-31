import unittest
from unittest.mock import patch, Mock

# filepath: /Users/roberto.luzardo/tools-and-scripts/web-api-examples/metrics/test_insecure-weather-app.py
from web-api-examples.metrics.insecure_weather_app import get_weather

class TestGetWeather(unittest.TestCase):

    @patch('web-api-examples.metrics.insecure_weather_app.requests.get')
    def test_get_weather_success(self, mock_get):
        # Mock a successful API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "cod": 200,
            "main": {"temp": 72},
            "weather": [{"description": "clear sky"}]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        with patch('builtins.print') as mock_print:
            get_weather("Los Angeles", "fake_api_key")
            mock_print.assert_any_call("Weather in Los Angeles:")
            mock_print.assert_any_call("Temperature: 72°F")
            mock_print.assert_any_call("Description: Clear sky")

    @patch('web-api-examples.metrics.insecure_weather_app.requests.get')
    def test_get_weather_error_response(self, mock_get):
        # Mock an API response with an error code
        mock_response = Mock()
        mock_response.json.return_value = {
            "cod": 404,
            "message": "city not found"
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        with patch('builtins.print') as mock_print:
            get_weather("InvalidCity", "fake_api_key")
            mock_print.assert_any_call("Error: city not found")

    @patch('web-api-examples.metrics.insecure_weather_app.requests.get')
    def test_get_weather_request_exception(self, mock_get):
        # Mock a RequestException
        mock_get.side_effect = requests.exceptions.RequestException("Network error")

        with patch('builtins.print') as mock_print:
            get_weather("Los Angeles", "fake_api_key")
            mock_print.assert_any_call("An error occurred: Network error")

if __name__ == "__main__":
    unittest.main()