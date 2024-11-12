# Parse CLI args
import argparse

parser = argparse.ArgumentParser( description="Generate a weather forecast for a named location or a set of coordinates, using OpenMeteo data and a local LLM.")
parser.add_argument('-c', '--city', help='city or other location search string to be used for geocoding' )
parser.add_argument('-y', '--lon', type=float, help='longitude' )
parser.add_argument('-x', '--lat', type=float, help='latitude' )
parser.add_argument('-v', '--verbose', action='count', default=0, help='wordiness of the forecast output')
# parser.add_argument('-d', '--debug', action='store_true')
args = parser.parse_args()

# Geocoding and reverse geocoding

if args.city != None:
    # City name passed - geocode required
    from geocode import nominatim_geocode
    geocoded_location = nominatim_geocode( args.city )
elif args.lon != None and args.lat != None :
    # Coordinates passed directly
    from geocode import nominatim_reverse
    geocoded_location = nominatim_reverse( lat=args.lat, lon=args.lon)
else : 
    print("Either location name (--city) or geographic coordinates (--lon and --lat) are required")
    exit()

latitude = geocoded_location['lat'], 
longitude = geocoded_location['lon'] 
location_name = geocoded_location['name']
location_area = geocoded_location['region']

# Weather forecast 
from weather import get_weather_forecast

forecast_data = get_weather_forecast( latitude, longitude)

# Build the LLM prompt
sentence_count = 3 + args.verbose * 2

llm_prompt = f"Using the following data table, generate a {sentence_count} sentence long weather forecast for {geocoded_location['name']}, noting any clear trends regarding temperature or precipitation, if applicable. Assume that the first date in the series is today. You can add practical advice regarding driving and travel, clothing choice, indoor/outdoor activities etc.\n"
llm_prompt += forecast_data['daily']

# Prompt the LLM and show the result
import ollama

llm_output = ollama.generate(model="llama3.2", prompt = llm_prompt )


# Output
import textwrap
lines = textwrap.wrap(llm_output['response'], replace_whitespace=False)

print ( f"LLM WEATHER FORECAST | {geocoded_location['name']}, {geocoded_location['region']}", "\n" )

for line in lines : print ( line )

print()
print ( llm_output['model'], llm_output['created_at'], llm_output['total_duration'])