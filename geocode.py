import requests
import urllib.parse
import json

def _str_sanitise( query : str ) :
    query = query.strip()
    encoded = urllib.parse.quote( query )
    return encoded

# OpenMeteo
def openmeteo_geocode ( query : str, count=5 ) :
    query = _str_sanitise( query )
    api_url = f"https://geocoding-api.open-meteo.com/v1/search?name={query}&count={count}&language=en&format=json"
    geocode_response = requests.get( api_url )
    if geocode_response :
        response_json = json.loads( geocode_response.content )
        return response_json

# Nominatim    
nominatim_headers = {
    'User-Agent' : 'py-AI-Weather'
}
nominatim_params = {
    'format' : 'json',
    'addressdetails' : 1,
    "accept-language":"en"
}

def _map_nominatim_response( single_location : dict ) :
    if 'province' in single_location['address'] :
            region = single_location['address']['province']
    elif 'state' in single_location['address'] :
        region = single_location['address']['state']
    result = {
        'name' : single_location['name'],
        'region' : region,
        'lat' :  single_location['lat'],
        'lon' : single_location['lon'],
    }
    return result

def nominatim_geocode( query : str ) :
    query = _str_sanitise( query )

    url = f"https://nominatim.openstreetmap.org/search?"
    nominatim_params.update( {'q' : query } )

    nominatim_response = requests.get( url, params=nominatim_params, headers=nominatim_headers)

    if nominatim_response :
        response_json = json.loads( nominatim_response.content )
        top_location : dict = response_json[0]
        
        return _map_nominatim_response( top_location )

def nominatim_reverse( lat : float, lon : float ) :
    url = f"https://nominatim.openstreetmap.org/reverse?"
    nominatim_params.update( {'lat' : lat , 'lon' : lon} )

    nominatim_response = requests.get( url, params=nominatim_params, headers=nominatim_headers)

    if nominatim_response :
        response_json : dict = json.loads( nominatim_response.content )

        return _map_nominatim_response ( response_json )