import requests

def get_weather(city_name, api_key):
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        'q': city_name,
        'appid': api_key,
        'units': 'imperial'  # For Fahrenheit
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        if data.get("cod") != 200:
            print(f"Error: {data.get('message', 'Unable to fetch weather data')}")
        else:
            print(f"Weather in {city_name}:")
            print(f"Temperature: {data['main']['temp']}°F")
            print(f"Description: {data['weather'][0]['description'].capitalize()}")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

def main():
    api_key = input("Enter your OpenWeatherMap API key: ").strip()
    city_name = input("Enter the name of the city: ").strip()
    get_weather(city_name, api_key)

if __name__ == "__main__":
    main()