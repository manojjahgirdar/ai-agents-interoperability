from mcp_server import mcp
from serpapi import GoogleSearch
import os
from tabulate import tabulate

def minutes_to_hours_minutes(minutes):
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins}m"

@mcp.tool()
def get_flight_search_results(
        departure_id: str,
        arrival_id: str,
        outbound_date: str,
        adults:int = 1,
        currency: str= "USD"
    ) -> str:
    """
    Fetch flight search results from Google Flights using SerpAPI.
    
    Args:
        departure_id (str): Departure airport code.
        arrival_id (str): Arrival airport code.
        outbound_date (str): Date of departure in YYYY-MM-DD format.
        adults (int): Number of adults traveling.
        currency (str): Currency for the flight prices.
        
    Returns:
        str: Flight search results in a table format.
    """
    params = {
        "engine": "google_flights",
        "hl": "en",
        "gl": "us",
        "departure_id": departure_id,
        "arrival_id": arrival_id,
        "outbound_date": outbound_date,
        "currency": currency,
        "type": "2",
        "adults": adults,
        "sort_by": "1",
        "travel_class": "1",
        "api_key": str(os.getenv("SERP_API_KEY"))
    }

    try:
        search = GoogleSearch(params)
        data = search.get_dict()
        # Combine best and other flights
        flights_data = data["best_flights"] + data["other_flights"]

        # Prepare rows for markdown table
        table_rows = []
        for itinerary in flights_data:
            flights = itinerary["flights"]
            route_parts = []
            time_parts = []
            airlines = set()
            delayed = False
            
            for flight in flights:
                dep = flight["departure_airport"]["id"]
                arr = flight["arrival_airport"]["id"]
                dt = flight["departure_airport"]["time"]
                at = flight["arrival_airport"]["time"]
                airline = flight["airline"]
                airlines.add(airline)
                # delayed |= flight.get("often_delayed_by_over_30_min", False)
                route_parts.append(f"{dep}→{arr}")
                time_parts.append(f"{dt}→{at}")
            
            layovers = [lay["id"] for lay in itinerary.get("layovers", [])]
            duration_min = itinerary.get("total_duration", 0)
            duration_str = minutes_to_hours_minutes(duration_min)
            emissions = itinerary.get("carbon_emissions", {}).get("this_flight", 0) / 1000  # g to kg
            row = [
                ", ".join(airlines),
                " → ".join(route_parts),
                " → ".join(time_parts),
                duration_str,
                ", ".join(layovers) if layovers else "Non-stop",
                f"{currency} {itinerary.get('price', '-')}",
                f"{emissions:.0f} kg"
                # "Yes" if delayed else "No"
            ]
            table_rows.append(row)

        # Define headers
        headers = [
            "Airline(s)",
            "Route",
            "Time",
            "Total Duration",
            "Layovers",
            "Price",
            "CO₂ Emissions"
            # "Flight gets delayed"
        ]

        # Output Markdown table
        return tabulate(table_rows, headers=headers, tablefmt="github")
    except Exception as e:
        return f"Error fetching flight search results: {e}"