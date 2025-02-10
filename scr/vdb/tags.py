from ollama import chat
from datetime import datetime
from typing import Optional
import json
import math
from geopy.geocoders import Nominatim
geolocator = Nominatim(user_agent="CompetenceMatching")

from scr.utils import YYYYMMDD_to_unix
from scr.vdb.prompts import *
from scr.vdb.response_models import *
from scr.config import *

def modify_query(query):
    """
    Recursively modifies a query to handle both location/distance and date conversion.
    """
    if not isinstance(query, dict):
        return query

    # If the query contains "$and" or "$or"
    if "$and" in query or "$or" in query:
        key = "$and" if "$and" in query else "$or"
        new_items = []
        location = None
        distance = 10  # default

        # Iterate through each condition in the list and filter out location/distance queries
        for item in query[key]:
            if isinstance(item, dict) and "location" in item:
                # Take only the first occurrence
                if location is None:
                    location = item["location"]
                # Exclude the item with "location" from the list
                continue
            elif isinstance(item, dict) and "distance" in item:
                d_val = item.get("distance")
                if isinstance(d_val, dict) and "$lte" in d_val:
                    distance = d_val["$lte"]
                continue
            else:
                new_items.append(modify_query(item))

        # If we found a location, add the coordinate query only once
        if location is not None:
            coords_query = location2query(location, distance)
            new_items.extend(coords_query)

        return {key: new_items}

    # If the query directly contains a "location" (not enclosed in $and/$or)
    if "location" in query:
        location = query["location"]
        distance = query.get("distance", 10)
        if isinstance(distance, dict) and "$lte" in distance:
            distance = distance["$lte"]

        # Remove "location" and "distance" so they are not processed again
        base_query = {k: v for k, v in query.items() if k not in ["location", "distance"]}
        coords_query = location2query(location, distance)

        if base_query:
            return {"$and": [base_query] + coords_query}
        else:
            return {"$and": coords_query}

    # Handle date conversion (if "start_date" is present in the key)
    new_query = {}
    for key, value in query.items():
        if "start_date" in key and isinstance(value, dict):
            new_query[key] = {
                op: YYYYMMDD_to_unix(date_str) if isinstance(date_str, str) else date_str
                for op, date_str in value.items()
            }
        else:
            new_query[key] = modify_query(value)

    return new_query

def extract_tags(job_description, max_retries=3):
    """
    Extract tags from the given job description with retry mechanism.
    Args:
        job_description (str): The job description to extract tags from
        max_retries (int): Maximum number of retry attempts (default: 3)
    Returns:
        dict: Extracted tags in JSON format, or None if all attempts fail
    """
    response = chat(
        model=model_config["extact_tags"],
        messages=[
            {
                "role": "system",
                "content": extract_tags_sys.format(
                    date=datetime.now().strftime("%Y-%m-%d")
                )
            },
            {
                "role": "user",
                "content": extract_tags_usr.format(
                    job_description=job_description
                )
            },
        ],
        format=JobDetails.model_json_schema()
    )
    
    json_response = json.loads(response.message.content)
    
    # Remove keys with None values
    json_response = {k: v for k, v in json_response.items() if v is not None}
    
    return json_response


def is_valid_query(query):
    """
    Validates if the given query follows the expected search filter format.
    """
    if not isinstance(query, dict):
        return False
    
    valid_keys = {"location", "distance", "start_date", "remote", "$and", "$or"}
    remote_values = {"fully_remote", "partly_remote", "on_site"}
    
    def validate_condition(condition):
        if not isinstance(condition, dict):
            return False
        
        for key, value in condition.items():
            if key not in valid_keys:
                return False
            
            if key == "location" and not isinstance(value, str):
                return False
            elif key == "distance" and not (isinstance(value, dict) and "$lte" in value and isinstance(value["$lte"], (int, float))):
                return False
            elif key == "start_date":
                if isinstance(value, dict):
                    if not all(k in {"$gte", "$lte"} and isinstance(v, str) for k, v in value.items()):
                        return False
                elif not isinstance(value, str):
                    return False
            elif key == "remote" and value not in remote_values:
                return False
            elif key in {"$and", "$or"}:
                if not (isinstance(value, list) and all(isinstance(v, dict) for v in value)):
                    return False
                if not all(validate_condition(v) for v in value):
                    return False
        
        return True
    
    return validate_condition(query)
    

def requirements2query(requirements):
    """Converts the requirements to a query than can be used to filter job listings."""
    if not requirements:
        return None
    response = chat(
        model=model_config["requirements2query"],
        messages=[
            {"role": "system", "content": requirements2query_sys.format(date=datetime.now().strftime("%Y-%m-%d"))},
            {"role": "user", "content": requirements2query_usr.format(text=requirements)},
        ],
        format="json"
    )
    json_response = json.loads(response.message.content)
    if json_response == {}:
        return None
    
    if not is_valid_query(json_response):
        return requirements2query(requirements)

    # Covert date (YYYY-MM-DD) to unix and location to coordinates
    query = modify_query(json_response)
    
    return query


def get_bounding_box(lat, lon, km_range):
    """
    Given a latitude, longitude, and a range in km, 
    returns a bounding box (min_lat, max_lat, min_lon, max_lon).
    """
    # Earth's rough radius in km
    earth_radius = 6371.0  
    
    # Latitude bounds (111.32 km per degree)
    delta_lat = km_range / 111.32  
    
    # Longitude bounds (adjusted by latitude)
    delta_lon = km_range / (111.32 * math.cos(math.radians(lat)))

    # Bounding box
    min_lat = lat - delta_lat
    max_lat = lat + delta_lat
    min_lon = lon - delta_lon
    max_lon = lon + delta_lon

    return min_lat, max_lat, min_lon, max_lon


def location2coords(location, gl=geolocator):
    loc = gl.geocode(location)
    if loc:
        return loc.latitude, loc.longitude
    else:
        return None, None


def location2query(location, distance=10):
    """
    Given a location and distance, returns a query that filters on the location and distance.
    """
    coords = location2coords(location)
    if coords is None:
        return None
    lat, lon = coords
    min_lat, max_lat, min_lon, max_lon = get_bounding_box(lat, lon, distance)
    return [
        {"latitude": {"$gte": min_lat}},
        {"latitude": {"$lte": max_lat}},
        {"longitude": {"$gte": min_lon}},
        {"longitude": {"$lte": max_lon}}
    ]
    return new_query

def convert_tags(tags_dict):
    # Convert the start_date to unix timestamp - if start_date is in the tags_dict
    try: 
        # Save the YYYY-MM-DD date before converting to unix
        tags_dict["start_date_str"] = tags_dict["start_date"]
        tags_dict["start_date"] = YYYYMMDD_to_unix(tags_dict["start_date"])
    except:
        pass
    

    # Convert the location to coordinates - if location is in the tags_dict
    try:
        latitude, longitude = location2coords(tags_dict["location"])
        if any([latitude is None, longitude is None]):
            latitude, longitude = "NULL", "NULL"
        # add coords
        tags_dict["latitude"] = latitude
        tags_dict["longitude"] = longitude
    except:
        pass

    return tags_dict