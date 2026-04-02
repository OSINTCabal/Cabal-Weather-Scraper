# Cabal Weather Check

Full-featured National Weather Service API terminal interface.
Built by osintcabal.org.

No API key required. All data sourced from api.weather.gov, the official
public REST API maintained by the National Weather Service.

---

## Features

**Alerts**
- Active alert count dashboard with regional and state-level breakdowns
- Active alerts by state or territory
- Active alerts by NWS zone ID
- Marine region alerts (Alaska, Atlantic, Great Lakes, Gulf of Mexico, Pacific, Pacific Islands)
- Direct alert lookup by URN
- Full alert type reference list

**Forecasts**
- 7-day point forecast from any lat/lon coordinate
- Hourly forecast with configurable display window (up to 156 hours)
- Zone-based forecast lookup by zone ID

**Observations**
- Latest ASOS/AWOS station observation with full METAR decode
- Historical observation records (up to 100 per query)
- Observation station search by state

**Offices and Products**
- NWS forecast office lookup with contact info and latest headlines
- Text product browser (by type, by office, or latest by type+office)
- Full product type reference

**Radar and Aviation**
- NWS radar station directory with coordinate and elevation data
- Individual radar station detail lookup
- Active SIGMETs and AIRMETs, browseable by ATSU

**Reference**
- NWS meteorological glossary with search
- NOAA Weather Radio transmitter lookup by coordinates

---

## Requirements

- Python 3.8 or later
- pip packages: `requests`, `rich`

---

## Installation

```bash
git clone https://github.com/yourusername/cabal-weather-check.git
cd cabal-weather-check
pip install -r requirements.txt
```

Or install dependencies manually:

```bash
pip install requests rich
```

---

## Usage

```bash
python Cabalweathercheck.py
```

Navigate the menu by entering the number next to each option and pressing ENTER.
Press Q to quit.

All coordinate inputs expect decimal degrees (e.g. `33.7490` / `-84.3880`).
Station IDs use ICAO 4-letter format (e.g. `KDFW`, `KAUS`, `KATL`).
State codes use standard 2-letter postal abbreviations (e.g. `TX`, `CA`, `FL`).

---

## Notes

- This tool uses only the public NWS REST API at `api.weather.gov`. No authentication or API key is required.
- All data is sourced directly from NOAA/NWS and reflects live operational data.
- Temperature output is in Fahrenheit. Wind speeds are in mph. Pressure in inHg. Visibility in miles.
- The NWS API occasionally returns incomplete data for some grid points or stations depending on availability.

---

## Data Source

National Weather Service REST API
https://www.weather.gov/documentation/services-web-api

The NWS API is a free public service. Please review their usage policy before
deploying this tool in any high-volume or automated context.

---

## License

MIT License. See LICENSE for details.

---

osintcabal.org
