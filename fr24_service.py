import time
from datetime import datetime, timezone, timedelta
from FlightRadarAPI import FlightRadar24API

# Cache definition to avoid hitting Flightradar24 too frequently
_cache = {
    "timestamp": 0,
    "airport_details": None
}

def timestamp_to_ist(ts):
    """Converts a UTC timestamp to IST (HH:MM) string format."""
    if not ts:
        return ""
    try:
        utc_dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        ist_dt = utc_dt + timedelta(hours=5, minutes=30)
        return ist_dt.strftime("%H:%M")
    except Exception:
        return ""

def get_airport_details_cached():
    """Fetches and caches airport details for Ahmedabad (VAAH)."""
    now = time.time()
    # Cache for 60 seconds
    if _cache["airport_details"] is not None and (now - _cache["timestamp"] < 60):
        return _cache["airport_details"]
        
    try:
        fr_api = FlightRadar24API()
        # VAAH is the ICAO code for Ahmedabad Airport (Sardar Vallabhbhai Patel International Airport)
        details = fr_api.get_airport_details("VAAH")
        if details and "airport" in details:
            _cache["airport_details"] = details
            _cache["timestamp"] = now
            return details
    except Exception as e:
        print(f"Error fetching from FlightRadarAPI: {e}")
        # If the API call fails, return the stale cache if available
        if _cache["airport_details"] is not None:
            return _cache["airport_details"]
            
    return None

def get_flights(airport_code="VAAH", direction="arrivals"):
    """
    Returns the real-time list of arrivals or departures for Ahmedabad.
    Ignores airport_code to enforce Ahmedabad (VAAH) only.
    Filters flights to only include those scheduled for the current date in IST.
    """
    details = get_airport_details_cached()
    if not details:
        return []
        
    schedule = details.get("airport", {}).get("pluginData", {}).get("schedule", {})
    
    if direction.lower() == "arrivals":
        flights_raw = schedule.get("arrivals", {}).get("data", [])
    else:
        flights_raw = schedule.get("departures", {}).get("data", [])
        
    processed_flights = []
    
    # Get current date in IST (UTC+5:30)
    now_utc = datetime.now(timezone.utc)
    now_ist = now_utc + timedelta(hours=5, minutes=30)
    current_date_ist = now_ist.date()
    
    for item in flights_raw:
        if not isinstance(item, dict):
            continue
        f = item.get("flight")
        if not isinstance(f, dict):
            continue
            
        # Flight Number
        ident = f.get("identification")
        if not isinstance(ident, dict):
            ident = {}
        number_info = ident.get("number")
        flight_num = None
        if isinstance(number_info, dict):
            flight_num = number_info.get("default")
        if not flight_num:
            flight_num = ident.get("callsign") or "N/A"
            
        # Airline & Owner info
        airline = f.get("airline")
        if not isinstance(airline, dict):
            airline = {}
        owner = f.get("owner")
        if not isinstance(owner, dict):
            owner = {}
            
        airline_name = airline.get("name") or owner.get("name") or "Unknown"
        
        # Origin / Destination City & Code
        airport = f.get("airport")
        if not isinstance(airport, dict):
            airport = {}
            
        if direction.lower() == "arrivals":
            origin_airport = airport.get("origin")
            if not isinstance(origin_airport, dict):
                origin_airport = {}
            pos = origin_airport.get("position")
            if not isinstance(pos, dict):
                pos = {}
            region = pos.get("region")
            if not isinstance(region, dict):
                region = {}
            city_name = region.get("city") or origin_airport.get("name") or "Unknown"
            
            code = origin_airport.get("code")
            if not isinstance(code, dict):
                code = {}
            iata_code = code.get("iata") or ""
        else:
            dest_airport = airport.get("destination")
            if not isinstance(dest_airport, dict):
                dest_airport = {}
            pos = dest_airport.get("position")
            if not isinstance(pos, dict):
                pos = {}
            region = pos.get("region")
            if not isinstance(region, dict):
                region = {}
            city_name = region.get("city") or dest_airport.get("name") or "Unknown"
            
            code = dest_airport.get("code")
            if not isinstance(code, dict):
                code = {}
            iata_code = code.get("iata") or ""
            
        city_display = f"{city_name} ({iata_code})" if iata_code else city_name
        
        # Times (Scheduled & Estimated/Real)
        time_info = f.get("time")
        if not isinstance(time_info, dict):
            time_info = {}
            
        sched_time_ts = None
        est_time_ts = None
        real_time_ts = None
        
        sched_dict = time_info.get("scheduled")
        if isinstance(sched_dict, dict):
            sched_time_ts = sched_dict.get("arrival") if direction.lower() == "arrivals" else sched_dict.get("departure")
            
        est_dict = time_info.get("estimated")
        if isinstance(est_dict, dict):
            est_time_ts = est_dict.get("arrival") if direction.lower() == "arrivals" else est_dict.get("departure")
            
        real_dict = time_info.get("real")
        if isinstance(real_dict, dict):
            real_time_ts = real_dict.get("arrival") if direction.lower() == "arrivals" else real_dict.get("departure")
            
        # Filter for current date data only
        if sched_time_ts:
            flight_dt_utc = datetime.fromtimestamp(sched_time_ts, tz=timezone.utc)
            flight_dt_ist = flight_dt_utc + timedelta(hours=5, minutes=30)
            if flight_dt_ist.date() != current_date_ist:
                continue
        else:
            # If no scheduled timestamp is available, skip to ensure current date data only
            continue
            
        scheduled = timestamp_to_ist(sched_time_ts) or "--:--"
        
        # Estimate logic: if landed/departed, use real time, else estimated, else scheduled
        estimated_ts = real_time_ts or est_time_ts or sched_time_ts
        estimated = timestamp_to_ist(estimated_ts) or scheduled
        
        # Status Text (e.g. Landed 19:54, Scheduled, Estimated dep 20:30)
        status_info = f.get("status")
        if not isinstance(status_info, dict):
            status_info = {}
        status_text = status_info.get("text")
        if not status_text:
            generic_info = status_info.get("generic")
            if isinstance(generic_info, dict):
                gen_status = generic_info.get("status")
                if isinstance(gen_status, dict):
                    status_text = gen_status.get("text")
        if not status_text:
            status_text = "Scheduled"
        status_text = status_text.upper()
        
        # Aircraft Model Code
        aircraft_info = f.get("aircraft")
        if not isinstance(aircraft_info, dict):
            aircraft_info = {}
        model_info = aircraft_info.get("model")
        if not isinstance(model_info, dict):
            model_info = {}
        aircraft = model_info.get("code") or "Unknown"
        
        # Airline Logo URL
        logo_url = owner.get("logo") or airline.get("logo")
        
        airline_code = airline.get("code")
        if not isinstance(airline_code, dict):
            airline_code = {}
        owner_code = owner.get("code")
        if not isinstance(owner_code, dict):
            owner_code = {}
            
        airline_iata = airline_code.get("iata") or owner_code.get("iata") or ""
        if not logo_url and airline_iata:
            logo_url = f"https://images.kiwi.com/airlines/64/{airline_iata.upper()}.png"
            
        is_live = False
        if isinstance(status_info, dict):
            is_live = status_info.get("live", False)
            
        processed_flights.append({
            "flight": flight_num,
            "airline": airline_name,
            "logo": logo_url or "",
            "city": city_display,
            "scheduled": scheduled,
            "estimated": estimated,
            "status": status_text,
            "aircraft": aircraft,
            "is_live": is_live
        })
        
    return processed_flights