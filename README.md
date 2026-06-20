# Ahmedabad Airport FIDS - TV Display System

A full-screen, high-readability Flight Information Display System (FIDS) for **Ahmedabad Airport (Sardar Vallabhbhai Patel International Airport - AMD/VAAH)**. The application fetches live flight data from Flightradar24, filters it for the current date, and presents it as an automated, paginated TV slideshow display suitable for airport monitors.

---

## Features Implemented

1. **Auto-Rotation Cycle (TV Mode):**
   - No scrollbars or manual interaction required.
   - Restricts data display to exactly **8 flights per page**.
   - Automatically switches pages every **10 seconds**.
   - Cycles through all **Arrivals** pages first, switches to **Departures**, cycles through all pages, and then loops back to Arrivals Page 1.
   - Uses blank/placeholder rows if a page has fewer than 8 flights to prevent table size changes or page jitter.

2. **Server-Side Current Date Filtering:**
   - Filters flight feeds to display only schedules for the current date in Indian Standard Time (IST).

3. **Dynamic Airline Logo Rendering:**
   - Automatically resolves airline logos from the Flightradar24 API.
   - Falls back to Kiwi Airline Assets CDN using IATA codes to guarantee logo coverage.

4. **Classic FIDS Styling Retained:**
   - Restored and preserved the classic aviation blue theme (`#243F73` background, `#29467E` alternating rows, `#3A7BBB` table headers, and a `#002060` to `#2F75B5` top header gradient).
   - Constrained layout sizing to exactly `100vh` to prevent scrollbars.

---

## Detailed File Breakdown

### 1. `fr24_service.py` (Python Scraper & Feed API)
Implements server-side fetching, caching, and data processing.

* **Functions:**
  * `timestamp_to_ist(ts)`: Converts a UNIX epoch timestamp (UTC) to a formatted string `HH:MM` in Indian Standard Time (IST).
  * `get_airport_details_cached()`: Fetches Sarder Vallabhbhai Patel Int'l Airport (`VAAH`) details from Flightradar24 and caches the response for 60 seconds to avoid API throttling.
  * `get_flights(airport_code, direction)`: Processes raw Flightradar24 schedules, filters for today's date in IST, retrieves airline logos, and maps them to clean objects.

* **Parsed Attributes (Flightradar24 Payload):**
  * `identification` $\rightarrow$ `number` $\rightarrow$ `default` or `callsign`: Flight number (e.g., `6E931`).
  * `airline` $\rightarrow$ `name` or `owner` $\rightarrow$ `name`: Name of the operating airline.
  * `owner` $\rightarrow$ `logo` or `airline` $\rightarrow$ `logo`: URL to the airline logo logotype image.
  * `airport` $\rightarrow$ `origin` / `destination` $\rightarrow$ `position` $\rightarrow$ `region` $\rightarrow$ `city` and `code` $\rightarrow$ `iata`: City name and IATA code (e.g. `Delhi (DEL)`).
  * `time` $\rightarrow$ `scheduled` $\rightarrow$ `arrival` / `departure`: Scheduled times (STA/STD).
  * `time` $\rightarrow$ `estimated` / `real`: Estimated/Actual times (ETA/ETD).
  * `status` $\rightarrow$ `text` or `generic` $\rightarrow$ `status` $\rightarrow$ `text`: Current status label (e.g., `LANDED 20:38`, `DELAYED 21:05`).
  * `aircraft` $\rightarrow$ `model` $\rightarrow$ `code`: Aircraft type code (e.g., `A21N`, `B738`).

---

### 2. `static/script.js` (Frontend Automation & Data Sync)
Handles the automatic TV slide pagination, clocks, and API calls.

* **Functions:**
  * `updateClock()`: Updates the live digital clock in the header every second, formatted as `HH:MM:SS` along with the weekday and date (e.g., `SAT, JUN 20, 2026`).
  * `getStatusClass(status)`: Maps raw flight status text into the classic CSS style classes (`landed`, `delayed`, `enroute`, `ontime`, `scheduled`, `cancelled`).
  * `fetchData()`: Asynchronously fetches new arrivals and departures in the background, updating memory caches without interrupting the page loop.
  * `renderFlights()`: Slices the flight array for the active page, changes table headers dynamically (STA/ETA for Arrivals, STD/ETD for Departures), inserts airline logo image tags, and appends blank padding rows if the list size is under 8.
  * `rotatePage()`: Ticks every 10 seconds to increment the page counter or toggle views between Arrivals and Departures.
  * `init()`: Starts the clock loop, requests the initial payload, triggers the 10-second rotation loop, and sets a 60-second background feed refresh interval.

---

### 3. `static/style.css` (Style Sheet)
Maintains color compatibility and bounds layout elements for TV viewing.

* **Layout Sizing (Exactly 100vh):**
  * `html, body`: Restricts scrollbars (`overflow: hidden`) and sets padding to `1.5vh 1.5vw`.
  * `.fids-board`: Sets borders to `3px solid #1A2D52` and sets background to `#243F73`.
  * `.board-header`: Constrains header to `14vh` using a `linear-gradient(90deg, #002060, #2F75B5)`.
  * `.fids-table th`: Height set to `6vh`, colored in `#3A7BBB`.
  * `.flight-row`: Height set to `9vh` (9vh * 8 rows = 72vh).
  * `.board-footer`: Height set to `8vh`.
  * *Total: 14vh + 6vh + 72vh + 8vh = 100vh viewport alignment.*
* **Colors & Typography:**
  * Font Family: `'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif`.
  * Estimated Times: `#00FFFF` (Cyan).
  * Status Pills: Green (`#0A7D2C` / `#0B8F44`), Orange (`#C96A00`), Teal (`#008B9A`), Blue (`#1A2D52`), and Red (`#991b1b`).

---

### 4. `templates/index.html` (Markup Structure)
Specifies the structural layout of the TV monitor.

* **Key Elements & IDs:**
  * `#clockTime`, `#clockDate`: Targets for the live clock.
  * `#boardTitle`, `#pageIndicator`: Center FIDS headers for views and page numbers.
  * `#updatedTime`: Displays last sync time.
  * `#scheduledHeader`, `#estimatedHeader`: Dynamic column headers (`STA/STD` and `ETA/ETD`).
  * `#flightTable`: Body container for the rendered rows.

---

### 5. `main.py` (FastAPI Router)
Exposes endpoint paths to serve the app and request data.

* **Endpoints:**
  * `@app.get("/")`: Serves `index.html`.
  * `@app.get("/api/arrivals")`: Invokes `get_flights(airport, "arrivals")` and returns the JSON array.
  * `@app.get("/api/departures")`: Invokes `get_flights(airport, "departures")` and returns the JSON array.

---

## Installation & Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Launch the server:**
   ```bash
   python -m uvicorn main:app --reload
   ```

3. **Open FIDS Screen:**
   Navigate to `http://localhost:8000/` in a browser. Press `F11` to display in full-screen TV mode.
