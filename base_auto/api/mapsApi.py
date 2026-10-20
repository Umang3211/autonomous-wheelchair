import googlemaps
from datetime import datetime
import os
import geocoder
import json
import folium
from voice.addressvoice import take_address
from polyline import decode as decode_polyline

# Get current location (once, not in loop)
def get_current_location():
    g = geocoder.ip("me")
    if g.latlng:
        lat, lng = g.latlng
        print(f"[Origin] Latitude: {lat}, Longitude: {lng}")
        return f"{lat},{lng}"
    else:
        print("Unable to get current location.")
        return None

# Get closest address match
def get_address_coords(address, gmaps):
    geocode_result = gmaps.geocode(address)
    if geocode_result:
        location = geocode_result[0]["geometry"]["location"]
        formatted_address = geocode_result[0]["formatted_address"]
        print(f"[Destination] Found match: {formatted_address}")
        return f"{location['lat']},{location['lng']}"
    else:
        print("No match found.")
        return None

# GOOGLE MAPS API KEY
gmaps = googlemaps.Client(key=os.getenv("GOOGLEMAPS_API"))  # or directly paste key

# Get user inputs
# address = input("Where do you want to go? ")
address = take_address()

# Get coordinates
origin = get_current_location()
destination = get_address_coords(address, gmaps)

if origin and destination:
    directions_result = gmaps.directions(
        origin,
        destination,
        mode="driving",
        departure_time="now"
    )

    path = []

    steps = directions_result[0]["legs"][0]["steps"]

    for step in steps:
        point = decode_polyline(step["polyline"]["points"])
        path.extend(point) # makes sure point is saved at end of arr

    # # Create folium map centered at origin
    # m = folium.Map(location=path[0], zoom_start=15)

    # # Add markers
    # folium.Marker(path[0], popup="Start", icon=folium.Icon(color="green")).add_to(m)
    # folium.Marker(path[-1], popup="Destination", icon=folium.Icon(color="red")).add_to(m)

    # # Add path line
    # folium.PolyLine(path, color="blue", weight=5).add_to(m)

    # Save and open map
    with open("waypoint_path.json", "w") as f:
        json.dump(path, f, indent=2)

else:
    print("Could not get directions.")
