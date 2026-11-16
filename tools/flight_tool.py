import os
import re
import certifi
import airportsdata
import pycountry
from dotenv import load_dotenv
import requests

load_dotenv()

api_key = os.getenv("AVIATION_API_KEY")

BASE_URL = "https://api.aviationstack.com/v1/flights"

AIRPORTS = airportsdata.load('IATA')

def parse_route(query: str) -> tuple[str | None, str | None]:
    """
    Parse the input query to extract origin and destination airports.

    Args:
        query (str): The input query containing the route information.
    Returns:
        tuple: Origin and destination names or IATA codes, or (None, None) if not found.
    """
    if not isinstance(query, str) or not query.strip():
        return None, None

    parts = re.split(r"\s+to\s+", query.strip(), maxsplit=1, flags=re.IGNORECASE)
    if len(parts) == 2:
        origin = re.sub(
            r"^\s*(?:flights?\s+)?from\s+",
            "",
            parts[0],
            flags=re.IGNORECASE,
        ).strip()
        destination = parts[1].strip()
        if origin and destination:
            return origin, destination
    return None, None

def resolve_airport_code(location: str) -> str | None:
    """Resolve an IATA code or an unambiguous airport city to an IATA code."""
    location = location.strip()
    airport_code = location.upper()
    if airport_code in AIRPORTS:
        return airport_code

    matches = [
        code for code, airport in AIRPORTS.items()
        if (airport.get("city") or "").casefold() == location.casefold()
    ]
    return matches[0] if len(matches) == 1 else None

def is_country_name(location: str) -> bool:
    """Return whether pycountry recognizes the input as a country name or code."""
    try:
        pycountry.countries.lookup(location.strip())
        return True
    except LookupError:
        return False

def format_flight_info(flight_data: dict) -> dict:
    """Map an Aviationstack flight record to a predictable, compact structure."""
    airline = flight_data.get("airline") or {}
    flight = flight_data.get("flight") or {}
    departure = flight_data.get("departure") or {}
    arrival = flight_data.get("arrival") or {}

    def format_airport(details: dict) -> dict:
        return {
            "airport": details.get("airport"),
            "iata": details.get("iata"),
            "terminal": details.get("terminal"),
            "gate": details.get("gate"),
            "scheduled": details.get("scheduled"),
            "estimated": details.get("estimated"),
            "actual": details.get("actual"),
            "delay_minutes": details.get("delay"),
        }

    return {
        "date": flight_data.get("flight_date"),
        "status": flight_data.get("flight_status"),
        "airline": {
            "name": airline.get("name"),
            "iata": airline.get("iata"),
            "icao": airline.get("icao"),
        },
        "flight_number": flight.get("number"),
        "origin": format_airport(departure),
        "destination": format_airport(arrival),
    }

def search_flights(query: str, limit: int = 5) -> list[dict]:
    """
    Search for flights between the specified origin and destination.

    Args:
        query (str): The input query containing the route information.
        limit (int): The maximum number of flights to return.
    Returns:
        list: A list of flight data dictionaries.
    """
    if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
        raise ValueError("limit must be a positive integer")

    origin, destination = parse_route(query)
    if not origin or not destination:
        print("Could not parse route. Use a route such as 'Flights from JFK to LHR'.")
        return []

    origin_code = resolve_airport_code(origin)
    destination_code = resolve_airport_code(destination)
    if not origin_code or not destination_code:
        unresolved = [
            location
            for location, code in ((origin, origin_code), (destination, destination_code))
            if not code
        ]
        if any(is_country_name(location) for location in unresolved):
            print("A country is not specific enough for a flight search. Specify a city or IATA airport code.")
        else:
            print("Use valid IATA airport codes (for example, JFK to LHR); city names may be ambiguous.")
        return []
    if not api_key:
        print("AVIATION_API_KEY is not set.")
        return []

    try:
        params = {
            "dep_iata": origin_code,
            "arr_iata": destination_code,
            "access_key": api_key,
            "limit": limit,
        }
        response = requests.get(BASE_URL, params=params, timeout=20, verify=certifi.where())
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            print("Flight search returned an unexpected response structure.")
            return []
        if payload.get("error"):
            print("Aviationstack reported an API error. Check the API key, plan, and request parameters.")
            return []
        flights = payload.get("data")
        if not isinstance(flights, list):
            print("Flight search returned an unexpected response structure.")
            return []
        if not all(isinstance(flight, dict) for flight in flights):
            print("Flight search returned malformed flight records.")
            return []
        return [format_flight_info(flight) for flight in flights[:limit]]
    except requests.exceptions.JSONDecodeError:
        print("Flight search returned invalid JSON.")
        return []
    except requests.RequestException as e:
        print(f"Flight search request failed ({type(e).__name__}). Check DNS/network connectivity and API settings.")
        return []

if __name__ == "__main__":
    # Example usage
    query = "Flights from JFK to LHR"
    origin, destination = parse_route(query)
    print(f"query: {query}")
    print(f"Origin: {origin}, Destination: {destination}")