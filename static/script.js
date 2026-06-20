// Global state
let arrivalsData = [];
let departuresData = [];
let currentView = "arrivals"; // "arrivals" or "departures"
let currentPage = 1;
const FLIGHTS_PER_PAGE = 8;
let lastUpdatedTime = null;

// DOM Elements
const flightTable = document.getElementById("flightTable");
const clockTime = document.getElementById("clockTime");
const clockDate = document.getElementById("clockDate");
const boardTitle = document.getElementById("boardTitle");
const scheduledHeader = document.getElementById("scheduledHeader");
const estimatedHeader = document.getElementById("estimatedHeader");
const pageIndicator = document.getElementById("pageIndicator");
const updatedTime = document.getElementById("updatedTime");

// Live Clock Logic (Format: HH:MM:SS, including seconds for airport feel)
function updateClock() {
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const seconds = String(now.getSeconds()).padStart(2, '0');
    clockTime.innerText = `${hours}:${minutes}:${seconds}`;
    
    const options = { weekday: 'short', day: '2-digit', month: 'short', year: 'numeric' };
    clockDate.innerText = now.toLocaleDateString('en-US', options).toUpperCase();
}

// Map status strings to original CSS classes
function getStatusClass(status) {
    if (!status) return "scheduled";
    status = status.toUpperCase();
    if (status.includes("LAND") || status.includes("ARRIVED") || status.includes("DEPARTED")) {
        return "landed";
    }
    if (status.includes("DELAY")) {
        return "delayed";
    }
    if (status.includes("ROUTE") || status.includes("APPROACH") || status.includes("ACTIVE") || status.includes("AIR")) {
        return "enroute";
    }
    if (status.includes("CANCEL")) {
        return "cancelled";
    }
    if (status.includes("SCHED")) {
        return "scheduled";
    }
    return "ontime"; // Default fallback (green)
}

// Fetch live flight schedule data from Flightradar24
async function fetchData() {
    try {
        const [arrivalsRes, departuresRes] = await Promise.all([
            fetch("/api/arrivals"),
            fetch("/api/departures")
        ]);
        
        if (!arrivalsRes.ok || !departuresRes.ok) {
            throw new Error(`Failed to fetch: arrivals(${arrivalsRes.status}), departures(${departuresRes.status})`);
        }
        
        arrivalsData = await arrivalsRes.json();
        departuresData = await departuresRes.json();
        
        lastUpdatedTime = new Date();
        const hrs = String(lastUpdatedTime.getHours()).padStart(2, '0');
        const mins = String(lastUpdatedTime.getMinutes()).padStart(2, '0');
        const secs = String(lastUpdatedTime.getSeconds()).padStart(2, '0');
        updatedTime.innerText = `Last Updated: ${hrs}:${mins}:${secs}`;
    } catch (error) {
        console.error("Failed to load flights:", error);
        if (arrivalsData.length === 0 && departuresData.length === 0) {
            flightTable.innerHTML = `
                <tr>
                    <td colspan="7" class="empty-cell">
                        Failed to connect to Flightradar24 Feed. Reconnecting...
                    </td>
                </tr>
            `;
        }
    }
}

// Render flights to table body for the current view and page
function renderFlights() {
    const data = (currentView === "arrivals") ? arrivalsData : departuresData;
    const totalPages = Math.max(1, Math.ceil(data.length / FLIGHTS_PER_PAGE));
    
    // Clamp current page to safety bounds
    if (currentPage > totalPages) {
        currentPage = totalPages;
    }
    
    // Update headers and indicators
    boardTitle.innerText = currentView.toUpperCase();
    boardTitle.className = "header-title";
    
    if (currentView === "arrivals") {
        scheduledHeader.innerText = "STA";
        estimatedHeader.innerText = "ETA";
    } else {
        scheduledHeader.innerText = "STD";
        estimatedHeader.innerText = "ETD";
    }
    
    pageIndicator.innerText = `PAGE ${currentPage} OF ${totalPages}`;
    
    // Slice data for current page
    const startIndex = (currentPage - 1) * FLIGHTS_PER_PAGE;
    const pageData = data.slice(startIndex, startIndex + FLIGHTS_PER_PAGE);
    
    flightTable.innerHTML = "";
    
    // Loop through 8 slots to build the rows
    for (let i = 0; i < FLIGHTS_PER_PAGE; i++) {
        if (i < pageData.length) {
            const flight = pageData[i];
            const statusClass = getStatusClass(flight.status);
            
            flightTable.innerHTML += `
                <tr class="flight-row">
                    <td class="flight-col">${flight.flight}</td>
                    <td>
                        <div class="airline-cell">
                            ${flight.logo ? `<img class="airline-logo" src="${flight.logo}" onerror="this.style.display='none';" alt="" />` : ''}
                            <span class="airline-name">${flight.airline}</span>
                        </div>
                    </td>
                    <td class="city-col">${flight.city}</td>
                    <td class="time-col scheduled-time">${flight.scheduled}</td>
                    <td class="time-col estimated-time">${flight.estimated}</td>
                    <td>
                        <span class="status-pill ${statusClass}">
                            ${flight.status}
                        </span>
                    </td>
                    <td class="aircraft-col">${flight.aircraft}</td>
                </tr>
            `;
        } else {
            // Render an empty/blank placeholder row to maintain exact 8-row height
            flightTable.innerHTML += `
                <tr class="flight-row empty-row">
                    <td>&nbsp;</td>
                    <td>&nbsp;</td>
                    <td>&nbsp;</td>
                    <td>&nbsp;</td>
                    <td>&nbsp;</td>
                    <td>&nbsp;</td>
                    <td>&nbsp;</td>
                </tr>
            `;
        }
    }
}

// Tick rotation timer (every 10s)
function rotatePage() {
    const data = (currentView === "arrivals") ? arrivalsData : departuresData;
    const totalPages = Math.max(1, Math.ceil(data.length / FLIGHTS_PER_PAGE));
    
    if (currentPage < totalPages) {
        // Go to next page of current view
        currentPage++;
    } else {
        // Switch view (Arrivals -> Departures -> Arrivals)
        if (currentView === "arrivals") {
            currentView = "departures";
        } else {
            currentView = "arrivals";
        }
        currentPage = 1;
    }
    renderFlights();
}

// Initialize on page load
async function init() {
    updateClock();
    setInterval(updateClock, 1000);
    
    // Load initial data
    await fetchData();
    renderFlights();
    
    // Rotate pages every 10 seconds
    setInterval(rotatePage, 10000);
    
    // Automatically refresh schedules from Flightradar24 every 60 seconds
    setInterval(async () => {
        await fetchData();
        renderFlights();
    }, 60000);
}

window.addEventListener("DOMContentLoaded", init);