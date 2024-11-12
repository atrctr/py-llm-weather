import openmeteo_requests
import json
import numpy
import requests_cache
import pandas as pd
from retry_requests import retry

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

# Make sure all required weather variables are listed here
openmeteo_api_url = "https://api.open-meteo.com/v1/forecast"

def get_weather_code_readable( weather_code : int ) :
    if type(weather_code) is not int or not 0 <= weather_code < 100  :
        raise ValueError( f"'{weather_code}' is not a valid WMO weather code" )
    readable_weather_codes = {
        # clear
        0 : "clear",
        1 : "mainly clear",
        # clouds and fog
        2 : "partly cloudy",
        3 : "overcast",
        45 : "fog",
        48 : "depositing rime fog",
        # drizzle
        51 : "light drizzle",
        53 : "moderate drizzle",
        55 : "heavy drizzle",
        56 : "light freezing drizzle",
        57 : "dense freezing drizzle",
        # rain
        61 : "light rain",
        63 : "moderate rain",
        65 : "heavy rain",
        66 : "light freezing rain",
        67 : "heavy freezing rain",
        # snow
        71 : "light snow",
        73 : "moderate snow",
        75 : "heavy snow",
        77 : "snow grains",
        # rain and snow showers
        80 : "light rain showers",
        81 : "moderate rain showers",
        82 : "heavy rain showers",
        85 : "light snow showers",
        86 : "heavy snow showers",
        # thunderstorms
        95 : "thunderstorm",
        96 : "thunderstorm with light hail",
        99 : "thunderstorm with heavy hail"
    }
    if weather_code in readable_weather_codes :
        return readable_weather_codes[weather_code]
    else :
        return "unknown"

def parse_weather_code_array ( code_array : numpy.ndarray ) :
    new_array = []
    for code in code_array:
        readable_code = get_weather_code_readable( int(code) )
        new_array.append( readable_code )
    return new_array

def get_relative_date ( datetime ) : 
    date = datetime['date']
    return date


def get_weather_forecast( lat, lon ) :

    # The order of variables in hourly or daily is important to assign them correctly below
    request_params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ["temperature_2m", "precipitation_probability", "weather_code", "wind_speed_10m", "wind_gusts_10m", "is_day"],
        "daily": ["weather_code", "temperature_2m_max", "temperature_2m_min", "precipitation_probability_max", "wind_speed_10m_max", "wind_gusts_10m_max"],
        "timezone": "auto"
    }

    responses = openmeteo.weather_api(openmeteo_api_url, params=request_params)

    # Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]

    # print(f"Coordinates {response.Latitude()}°N {response.Longitude()}°E")
    # print(f"Elevation {response.Elevation()} m asl")
    # print(f"Timezone {response.Timezone()} {response.TimezoneAbbreviation()}")
    # print(f"Timezone difference to GMT+0 {response.UtcOffsetSeconds()} s")
    metadata = {
        "latitude" : response.Latitude(),
        "longitude" : response.Longitude(),
        "elevation" : response.Elevation(),
        "timezone" : response.Timezone()
    }

    # Process hourly data. The order of variables needs to be the same as requested.
    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_precipitation_probability = hourly.Variables(1).ValuesAsNumpy()
    hourly_weather_code = hourly.Variables(2).ValuesAsNumpy()
    hourly_wind_speed_10m = hourly.Variables(3).ValuesAsNumpy()
    hourly_wind_gusts_10m = hourly.Variables(4).ValuesAsNumpy()
    hourly_is_day = hourly.Variables(5).ValuesAsNumpy()

    hourly_data = {"date": pd.date_range(
        start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
        end = pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
        freq = pd.Timedelta(seconds = hourly.Interval()),
        inclusive = "left"
    )}
    hourly_data["temperature_2m"] = hourly_temperature_2m
    hourly_data["precipitation_probability"] = hourly_precipitation_probability
    hourly_data["weather_code"] = hourly_weather_code
    hourly_data["weather_readable"] = parse_weather_code_array(hourly_weather_code)
    hourly_data["wind_speed_10m"] = hourly_wind_speed_10m
    hourly_data["wind_gusts_10m"] = hourly_wind_gusts_10m
    hourly_data["is_day"] = hourly_is_day

    hourly_dataframe = pd.DataFrame(data = hourly_data)

    # Process daily data. The order of variables needs to be the same as requested.
    daily = response.Daily()
    daily_weather_code = daily.Variables(0).ValuesAsNumpy()
    daily_temperature_2m_max = daily.Variables(1).ValuesAsNumpy()
    daily_temperature_2m_min = daily.Variables(2).ValuesAsNumpy()
    daily_precipitation_probability_max = daily.Variables(3).ValuesAsNumpy()
    daily_wind_speed_10m_max = daily.Variables(4).ValuesAsNumpy()
    daily_wind_gusts_10m_max = daily.Variables(5).ValuesAsNumpy()

    daily_data = {"date": pd.date_range(
        start = pd.to_datetime(daily.Time(), unit = "s", utc = True),
        end = pd.to_datetime(daily.TimeEnd(), unit = "s", utc = True),
        freq = pd.Timedelta(seconds = daily.Interval()),
        inclusive = "left"
    )}
    # daily_data["relative_date"] = get_relative_date( daily_data )
    daily_data["weather_code"] = daily_weather_code
    daily_data["weather_readable"] = parse_weather_code_array( daily_weather_code )
    daily_data["temperature_2m_max"] = daily_temperature_2m_max
    daily_data["temperature_2m_min"] = daily_temperature_2m_min
    daily_data["precipitation_probability_max"] = daily_precipitation_probability_max
    daily_data["wind_speed_10m_max"] = daily_wind_speed_10m_max
    daily_data["wind_gusts_10m_max"] = daily_wind_gusts_10m_max

    daily_dataframe = pd.DataFrame(data = daily_data)

    result = { 
        "metadata": metadata, 
        "daily_dataframe": daily_dataframe, 
        "daily" : daily_dataframe.to_string(),
        "hourly_dataframe": hourly_dataframe,
        "hourly": hourly_dataframe.to_string()
        }
    return result

