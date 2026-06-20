from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request

from fr24_service import get_flights

app = FastAPI(title="Ahmedabad Airport FIDS")

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )


@app.get("/api/arrivals")
async def arrivals(airport: str = "AMD"):
    return get_flights(airport, "arrivals")

@app.get("/api/departures")
async def departures(airport: str = "AMD"):
    return get_flights(airport, "departures")