#!/usr/bin/env python3
"""
Cabal Weather Check  //  NWS Full API Suite
osintcabal.org  |  api.weather.gov

Full-featured National Weather Service API interface.
Covers alerts, forecasts, observations, radar, aviation, and more.
"""

import sys
import json
import time
import requests
from datetime import datetime, timezone
from typing import Optional, Any

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.prompt import Prompt, Confirm
    from rich.columns import Columns
    from rich.rule import Rule
    from rich.live import Live
    from rich.spinner import Spinner
    from rich import box
    from rich.padding import Padding
    from rich.style import Style
    from rich.align import Align
    from rich.layout import Layout
    from rich.markup import escape
except ImportError:
    print("Missing dependency: pip install rich requests")
    sys.exit(1)

# ── Constants ──────────────────────────────────────────────────────────────────
BASE_URL = "https://api.weather.gov"
HEADERS  = {
    "User-Agent": "(CabalWeatherCheck/1.0, osintcabal.org)",
    "Accept": "application/geo+json"
}

console = Console()

# ── Color palette ──────────────────────────────────────────────────────────────
C = {
    "primary":   "bold cyan",
    "accent":    "bold yellow",
    "danger":    "bold red",
    "warn":      "bold orange1",
    "success":   "bold green",
    "muted":     "dim white",
    "header":    "bold bright_cyan",
    "sub":       "bold bright_white",
    "label":     "bright_magenta",
    "value":     "bright_white",
    "extreme":   "bold red on dark_red",
    "severe":    "bold red",
    "moderate":  "bold orange1",
    "minor":     "bold yellow",
    "unknown":   "dim white",
}

# ── Severity coloring ──────────────────────────────────────────────────────────
SEVERITY_STYLE = {
    "Extreme":  C["extreme"],
    "Severe":   C["severe"],
    "Moderate": C["moderate"],
    "Minor":    C["minor"],
    "Unknown":  C["unknown"],
}

# ── US States & marine areas for menus ────────────────────────────────────────
US_STATES = [
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA",
    "HI","ID","IL","IN","IA","KS","KY","LA","ME","MD",
    "MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
    "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC",
    "SD","TN","TX","UT","VT","VA","WA","WV","WI","WY",
    "DC","PR","GU","AS","VI","MP",
]

WFO_OFFICES = [
    "AKQ","ALY","BGM","BOX","BTV","BUF","CAE","CAR","CHS","CLE",
    "CTP","GSP","GYX","ILM","ILN","LWX","MHX","OKX","PBZ","PHI",
    "RAH","RLX","RNK","ABQ","AMA","BMX","BRO","CRP","EPZ","EWX",
    "FFC","FWD","HGX","HUN","JAN","JAX","KEY","LCH","LIX","LUB",
    "LZK","MAF","MEG","MFL","MLB","MOB","MRX","OHX","OUN","SHV",
    "SJT","SJU","TAE","TBW","TSA","ABR","APX","ARX","BIS","BOU",
    "CYS","DDC","DLH","DMX","DTX","DVN","EAX","FGF","FSD","GID",
    "GJT","GLD","GRB","GRR","ICT","ILX","IND","IWX","JKL","LBF",
    "LMK","LOT","LSX","MKX","MPX","MQT","OAX","PAH","PUB","RIW",
    "SGF","TOP","UNR","BOI","BYZ","EKA","FGZ","GGW","HNX","LKN",
    "LOX","MFR","MSO","MTR","OTX","PDT","PIH","PQR","PSR","REV",
    "SEW","SGX","SLC","STO","TFX","TWC","VEF","HFO","AFC","AFG",
]

# ── ASCII art banner ───────────────────────────────────────────────────────────
BANNER_ART = r"""
        __I__
   .-'"  .  "'-.
 .'  / . ' . \  '.
/_.-..-..-..-..-._\ .---------------------------------.
         #  _,,_   ( I hear it might rain people today )
         #/`    `\ /'---------------------------------'
         / / 6 6\ \
         \/\  Y /\/       /\-/\
         #/ `'U` \       /a a  \               _
       , (  \   | \     =\ Y  =/-~~~~~~-,_____/ )
       |\|\_/#  \_/       '^--'          ______/
       \/'.  \  /'\         \           /
        \    /=\  /         ||  |---'\  \
        /____)/____)       (_(__|   ((__|

--_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-

_________       ___.          .__     __      __               __  .__
\_   ___ \_____ \_ |__ _____  |  |   /  \    /  \ ____ _____ _/  |_|  |__   ___________
/    \  \/\__  \ | __ \\__  \ |  |   \   \/\/   // __ \\__  \\   __\  |  \_/ __ \_  __ \
\     \____/ __ \| \_\ \/ __ \|  |__  \        /\  ___/ / __ \|  | |   Y  \  ___/|  | \/
 \______  (____  /___  (____  /____/   \__/\  /  \___  >____  /__| |___|  /\___  >__|
        \/     \/    \/     \/              \/       \/     \/          \/     \/
  _________
 /   _____/ ________________  ______   ___________
 \_____  \_/ ___\_  __ \__  \ \____ \_/ __ \_  __ \
 /        \  \___|  | \// __ \|  |_> >  ___/|  | \/
/_______  /\___  >__|  (____  /   __/ \___  >__|
        \/     \/           \/|__|        \/
"""

# ── API Helper ─────────────────────────────────────────────────────────────────
def api_get(endpoint: str, params: dict = None) -> Optional[dict]:
    url = f"{BASE_URL}{endpoint}"
    try:
        with console.status(f"[cyan]Contacting NWS API...[/]", spinner="dots"):
            r = requests.get(url, headers=HEADERS, params=params, timeout=15)
        if r.status_code == 200:
            return r.json()
        elif r.status_code == 301:
            r2 = requests.get(r.headers.get("Location", url), headers=HEADERS, timeout=15)
            if r2.status_code == 200:
                return r2.json()
        console.print(f"[red]API Error {r.status_code}:[/] {r.text[:300]}")
        return None
    except requests.exceptions.ConnectionError:
        console.print("[bold red]Connection error -- check your internet connection.[/]")
        return None
    except requests.exceptions.Timeout:
        console.print("[bold red]Request timed out.[/]")
        return None
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/] {escape(str(e))}")
        return None

def api_get_text(endpoint: str) -> Optional[str]:
    url = f"{BASE_URL}{endpoint}"
    try:
        with console.status(f"[cyan]Fetching...[/]", spinner="dots"):
            r = requests.get(url, headers={**HEADERS, "Accept": "application/json"}, timeout=15)
        if r.status_code == 200:
            return r.text
        return None
    except Exception as e:
        console.print(f"[bold red]Error:[/] {escape(str(e))}")
        return None

# ── UI Helpers ─────────────────────────────────────────────────────────────────
def banner():
    console.clear()

    # ASCII art block
    console.print(f"[bold cyan]{escape(BANNER_ART)}[/]")

    # Header box
    box_art = Text()
    box_art.append("  \u2554", style="bold cyan")
    box_art.append("\u2550" * 58, style="bold cyan")
    box_art.append("\u2557\n", style="bold cyan")
    box_art.append("  \u2551  ", style="bold cyan")
    box_art.append("CABAL WEATHER CHECK", style="bold bright_cyan")
    box_art.append("  //  NWS FULL API SUITE  ", style="bold yellow")
    box_art.append("  \u2551\n", style="bold cyan")
    box_art.append("  \u2551        ", style="bold cyan")
    box_art.append("[ osintcabal.org ]", style="dim cyan")
    box_art.append("  \u2022  ", style="dim white")
    box_art.append("api.weather.gov", style="dim cyan")
    box_art.append("             \u2551\n", style="bold cyan")
    box_art.append("  \u255a", style="bold cyan")
    box_art.append("\u2550" * 58, style="bold cyan")
    box_art.append("\u255d", style="bold cyan")
    console.print(box_art)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    console.print(f"\n  [dim]Session started: {now}[/]\n")

def section(title: str):
    console.print()
    console.rule(f"[bold cyan]  {title}  [/]", style="cyan")
    console.print()

def label_value(label: str, value: Any, label_style="bright_magenta", value_style="bright_white"):
    console.print(f"  [bold {label_style}]{label}:[/] [{value_style}]{escape(str(value))}[/]")

def no_data(msg="No data returned from API."):
    console.print(f"\n  [bold yellow]  {msg}[/]\n")

def press_enter():
    console.print()
    Prompt.ask("  [dim]Press ENTER to return[/]", default="")

def fmt_time(ts: str) -> str:
    if not ts:
        return "N/A"
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        return ts[:19] if len(ts) >= 19 else ts

def c_to_f(c) -> str:
    if c is None:
        return "N/A"
    try:
        return f"{round(c * 9/5 + 32, 1)}F"
    except Exception:
        return "N/A"

def ms_to_mph(ms) -> str:
    if ms is None:
        return "N/A"
    try:
        return f"{round(ms * 2.237, 1)} mph"
    except Exception:
        return "N/A"

def pa_to_inhg(pa) -> str:
    if pa is None:
        return "N/A"
    try:
        return f"{round(pa / 3386.39, 2)} inHg"
    except Exception:
        return "N/A"

def m_to_mi(m) -> str:
    if m is None:
        return "N/A"
    try:
        return f"{round(m / 1609.34, 2)} mi"
    except Exception:
        return "N/A"

def severity_badge(sev: str) -> str:
    style = SEVERITY_STYLE.get(sev, C["unknown"])
    return f"[{style}]{sev}[/]"

def pick_from_list(items: list, prompt: str, title="Select") -> Optional[str]:
    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
    table.add_column("N", style="bold cyan", width=4)
    table.add_column("Value", style="bright_white")
    for i, item in enumerate(items, 1):
        table.add_row(str(i), str(item))
    console.print(table)
    raw = Prompt.ask(f"  [bold yellow]{prompt}[/] (number or value)")
    try:
        idx = int(raw) - 1
        if 0 <= idx < len(items):
            return items[idx]
    except ValueError:
        pass
    if raw.upper() in [x.upper() for x in items]:
        return raw.upper()
    console.print(f"  [red]Invalid selection:[/] {escape(raw)}")
    return None

# ══════════════════════════════════════════════════════════════════════════════
#  FEATURE MODULES
# ══════════════════════════════════════════════════════════════════════════════

# ── 1. Active Alert Count Dashboard ───────────────────────────────────────────
def feature_alert_count():
    section("ACTIVE ALERT COUNT DASHBOARD")
    data = api_get("/alerts/active/count")
    if not data:
        no_data(); press_enter(); return

    total  = data.get("total", 0)
    land   = data.get("land", 0)
    marine = data.get("marine", 0)

    summary = Text()
    summary.append(f"  Total Active Alerts: ", style="bold white")
    summary.append(f"{total}\n", style="bold bright_cyan")
    summary.append(f"  Land Alerts:         ", style="bold white")
    summary.append(f"{land}\n", style="bold green")
    summary.append(f"  Marine Alerts:       ", style="bold white")
    summary.append(f"{marine}", style="bold blue")
    console.print(Panel(summary, title="[bold cyan]ALERT TOTALS[/]", border_style="cyan"))

    regions = data.get("regions", {})
    if regions:
        t = Table(title="By Marine Region", box=box.ROUNDED, border_style="blue",
                  header_style="bold cyan", show_lines=False)
        t.add_column("Region", style="bright_cyan", width=10)
        t.add_column("Count",  style="bold yellow", justify="right")
        for r, cnt in sorted(regions.items(), key=lambda x: -x[1]):
            t.add_row(r, str(cnt))
        console.print(t)

    areas = data.get("areas", {})
    if areas:
        t = Table(title="By State/Area", box=box.ROUNDED, border_style="green",
                  header_style="bold cyan", show_lines=False)
        t.add_column("State", style="bright_cyan", width=8)
        t.add_column("Count", style="bold yellow", justify="right")
        top = sorted(areas.items(), key=lambda x: -x[1])[:20]
        for state, cnt in top:
            style = "bold red" if cnt >= 5 else ("yellow" if cnt >= 2 else "white")
            t.add_row(f"[{style}]{state}[/]", f"[{style}]{cnt}[/]")
        console.print(t)

    press_enter()

# ── 2. Active Alerts by State ─────────────────────────────────────────────────
def feature_alerts_by_state():
    section("ACTIVE ALERTS BY STATE / AREA")
    state = Prompt.ask("  [bold yellow]Enter state code[/] (e.g. TX, CA, FL)").upper().strip()
    if not state:
        return

    data = api_get(f"/alerts/active/area/{state}")
    if not data:
        no_data(); press_enter(); return

    features = data.get("features", [])
    if not features:
        no_data(f"No active alerts for {state}."); press_enter(); return

    console.print(f"\n  [bold green]Found {len(features)} alert(s) for {state}[/]\n")

    for i, feat in enumerate(features, 1):
        props = feat.get("properties", {})
        evt   = props.get("event", "Unknown Event")
        sev   = props.get("severity", "Unknown")
        urg   = props.get("urgency", "Unknown")
        area  = props.get("areaDesc", "N/A")
        onset = fmt_time(props.get("onset", ""))
        ends  = fmt_time(props.get("ends", "") or props.get("expires", ""))
        head  = props.get("headline", "")
        desc  = props.get("description", "")[:500]
        instr = props.get("instruction", "")[:300]

        sev_style = SEVERITY_STYLE.get(sev, "white")
        panel_content = Text()
        panel_content.append(f"  Severity: ", style="bold white"); panel_content.append(f"{sev}\n", style=sev_style)
        panel_content.append(f"  Urgency:  ", style="bold white"); panel_content.append(f"{urg}\n", style="bold cyan")
        panel_content.append(f"  Area:     ", style="bold white"); panel_content.append(f"{area}\n", style="bright_white")
        panel_content.append(f"  Onset:    ", style="bold white"); panel_content.append(f"{onset}\n", style="yellow")
        panel_content.append(f"  Ends:     ", style="bold white"); panel_content.append(f"{ends}\n", style="yellow")
        if head:
            panel_content.append(f"\n  {head}\n", style="italic bright_white")
        if desc:
            panel_content.append(f"\n  {desc[:400]}\n", style="dim white")
        if instr:
            panel_content.append(f"\n  {instr[:250]}", style="bold orange1")

        border = "red" if sev in ("Extreme","Severe") else ("yellow" if sev == "Moderate" else "cyan")
        console.print(Panel(
            panel_content,
            title=f"[bold {border}]  #{i} -- {evt}  [/]",
            border_style=border,
            padding=(0, 1)
        ))
        console.print()

    press_enter()

# ── 3. Active Alerts by Zone ───────────────────────────────────────────────────
def feature_alerts_by_zone():
    section("ACTIVE ALERTS BY ZONE ID")
    console.print("  [dim]Zone IDs look like: TXZ001, FLZ068, etc.[/]")
    zone_id = Prompt.ask("  [bold yellow]Enter Zone ID[/]").upper().strip()
    if not zone_id:
        return

    data = api_get(f"/alerts/active/zone/{zone_id}")
    if not data:
        no_data(); press_enter(); return

    features = data.get("features", [])
    if not features:
        no_data(f"No active alerts for zone {zone_id}."); press_enter(); return

    console.print(f"\n  [bold green]Found {len(features)} alert(s) for zone {zone_id}[/]\n")
    _render_alert_list(features)
    press_enter()

# ── 4. Point Forecast ──────────────────────────────────────────────────────────
def feature_point_forecast():
    section("POINT FORECAST  (lat/lon -> 7-day)")
    console.print("  [dim]Enter coordinates to look up forecast grid and get a 7-day forecast.[/]")
    lat = Prompt.ask("  [bold yellow]Latitude[/]  (e.g. 33.7490)")
    lon = Prompt.ask("  [bold yellow]Longitude[/] (e.g. -84.3880)")
    try:
        lat_f = float(lat)
        lon_f = float(lon)
    except ValueError:
        console.print("  [red]Invalid coordinates.[/]"); press_enter(); return

    point_data = api_get(f"/points/{lat_f},{lon_f}")
    if not point_data:
        no_data("Could not resolve this point."); press_enter(); return

    props     = point_data.get("properties", {})
    wfo       = props.get("cwa", "")
    gx        = props.get("gridX", "")
    gy        = props.get("gridY", "")
    city      = props.get("relativeLocation", {}).get("properties", {}).get("city", "N/A")
    state_loc = props.get("relativeLocation", {}).get("properties", {}).get("state", "N/A")
    tz        = props.get("timeZone", "N/A")

    info = Table(box=box.SIMPLE, show_header=False, padding=(0,1))
    info.add_column("Label", style="bold bright_magenta")
    info.add_column("Value", style="bright_white")
    info.add_row("Location",    f"{city}, {state_loc}")
    info.add_row("Grid",        f"{wfo} ({gx}, {gy})")
    info.add_row("Time Zone",   tz)
    info.add_row("Coordinates", f"{lat_f}, {lon_f}")
    console.print(Panel(info, title="[bold cyan]Grid Resolution[/]", border_style="cyan"))

    if not wfo:
        no_data("Could not determine WFO for this point."); press_enter(); return

    forecast_data = api_get(f"/gridpoints/{wfo}/{gx},{gy}/forecast")
    if not forecast_data:
        no_data(); press_enter(); return

    periods = forecast_data.get("properties", {}).get("periods", [])
    if not periods:
        no_data("No forecast periods returned."); press_enter(); return

    t = Table(
        title=f"7-Day Forecast -- {city}, {state_loc}",
        box=box.ROUNDED, border_style="cyan",
        header_style="bold cyan", show_lines=True, expand=True
    )
    t.add_column("Period",   style="bold white",     width=18)
    t.add_column("Temp",     style="bold yellow",    width=8,  justify="center")
    t.add_column("Wind",     style="bright_cyan",    width=16)
    t.add_column("Precip %", style="bright_magenta", width=8,  justify="center")
    t.add_column("Forecast", style="bright_white",   min_width=30)

    for p in periods:
        name   = p.get("name", "")
        temp_v = p.get("temperature", {})
        if isinstance(temp_v, dict):
            temp_c   = temp_v.get("value")
            temp_str = c_to_f(temp_c) if temp_c is not None else "N/A"
        else:
            temp_str = f"{temp_v}F" if temp_v else "N/A"

        wind_speed = p.get("windSpeed", {})
        if isinstance(wind_speed, dict):
            ws       = wind_speed.get("value")
            wind_str = ms_to_mph(ws)
        else:
            wind_str = str(wind_speed) if wind_speed else "N/A"

        wind_dir = p.get("windDirection", "")
        precip   = p.get("probabilityOfPrecipitation", {})
        if isinstance(precip, dict):
            precip_v = precip.get("value", 0) or 0
        else:
            precip_v = precip or 0

        short  = p.get("shortForecast", "")
        is_day = p.get("isDaytime", True)
        icon   = "DAY" if is_day else "NIGHT"
        t.add_row(
            f"{name}",
            temp_str,
            f"{wind_str} {wind_dir}",
            f"{int(precip_v)}%",
            short
        )

    console.print(t)
    press_enter()

# ── 5. Hourly Forecast ─────────────────────────────────────────────────────────
def feature_hourly_forecast():
    section("HOURLY FORECAST")
    console.print("  [dim]Enter coordinates for an hourly breakdown.[/]")
    lat = Prompt.ask("  [bold yellow]Latitude[/]")
    lon = Prompt.ask("  [bold yellow]Longitude[/]")
    try:
        lat_f, lon_f = float(lat), float(lon)
    except ValueError:
        console.print("  [red]Invalid coordinates.[/]"); press_enter(); return

    point_data = api_get(f"/points/{lat_f},{lon_f}")
    if not point_data:
        no_data(); press_enter(); return

    props = point_data.get("properties", {})
    wfo, gx, gy = props.get("cwa",""), props.get("gridX",""), props.get("gridY","")

    hours_to_show = Prompt.ask("  [bold yellow]Hours to display[/]", default="12")
    try:
        hours_to_show = min(int(hours_to_show), 156)
    except ValueError:
        hours_to_show = 12

    data = api_get(f"/gridpoints/{wfo}/{gx},{gy}/forecast/hourly")
    if not data:
        no_data(); press_enter(); return

    periods = data.get("properties", {}).get("periods", [])[:hours_to_show]
    if not periods:
        no_data(); press_enter(); return

    t = Table(
        title=f"Hourly Forecast -- Next {hours_to_show} Hours",
        box=box.ROUNDED, border_style="blue",
        header_style="bold cyan", show_lines=False, expand=True
    )
    t.add_column("Time",       style="bold cyan",      width=20)
    t.add_column("Temp",       style="bold yellow",    width=8,  justify="center")
    t.add_column("Dew Pt",     style="bright_cyan",    width=8,  justify="center")
    t.add_column("Humidity",   style="bright_magenta", width=9,  justify="center")
    t.add_column("Wind",       style="bright_white",   width=16)
    t.add_column("Precip%",    style="bright_blue",    width=7,  justify="center")
    t.add_column("Conditions", style="white",          min_width=20)

    for p in periods:
        start  = fmt_time(p.get("startTime",""))
        temp_v = p.get("temperature",{})
        if isinstance(temp_v, dict):
            temp_str = c_to_f(temp_v.get("value"))
        else:
            temp_str = f"{temp_v}F"

        dew_v   = p.get("dewpoint",{})
        dew_str = c_to_f(dew_v.get("value") if isinstance(dew_v, dict) else dew_v)

        hum_v   = p.get("relativeHumidity",{})
        hum_str = f"{int(hum_v.get('value',0) or 0)}%" if isinstance(hum_v, dict) else f"{hum_v}%"

        ws_v = p.get("windSpeed",{})
        if isinstance(ws_v, dict):
            ws_str = ms_to_mph(ws_v.get("value"))
        else:
            ws_str = str(ws_v)
        wd = p.get("windDirection","")

        precip_v = p.get("probabilityOfPrecipitation",{})
        if isinstance(precip_v, dict):
            pp = int(precip_v.get("value",0) or 0)
        else:
            pp = int(precip_v or 0)

        short    = p.get("shortForecast","")
        pp_style = "bold cyan" if pp >= 50 else ("yellow" if pp >= 30 else "white")

        t.add_row(
            start, temp_str, dew_str, hum_str,
            f"{ws_str} {wd}",
            f"[{pp_style}]{pp}%[/]",
            short
        )

    console.print(t)
    press_enter()

# ── 6. Station Observations ────────────────────────────────────────────────────
def feature_station_obs():
    section("STATION OBSERVATIONS")
    console.print("  [dim]ASOS/AWOS station IDs are 4-letter codes, e.g. KDFW, KAUS, KATL[/]")
    station_id = Prompt.ask("  [bold yellow]Enter Station ID[/]").upper().strip()
    if not station_id:
        return

    console.print("\n  [bold cyan]1.[/] Latest observation")
    console.print("  [bold cyan]2.[/] Recent observations (last N records)")
    choice = Prompt.ask("  [bold yellow]Choice[/]", default="1")

    if choice == "1":
        data = api_get(f"/stations/{station_id}/observations/latest")
        if not data:
            no_data(); press_enter(); return
        _render_observation(data.get("properties", {}), station_id)

    elif choice == "2":
        limit = Prompt.ask("  [bold yellow]Number of records[/]", default="10")
        try:
            limit = min(int(limit), 100)
        except ValueError:
            limit = 10
        data = api_get(f"/stations/{station_id}/observations", params={"limit": limit})
        if not data:
            no_data(); press_enter(); return
        features = data.get("features", [])
        if not features:
            no_data(); press_enter(); return

        t = Table(
            title=f"Recent Observations -- {station_id}",
            box=box.ROUNDED, border_style="cyan",
            header_style="bold cyan", show_lines=True, expand=True
        )
        t.add_column("Timestamp",   style="bold cyan",      width=20)
        t.add_column("Temp",        style="bold yellow",    width=9,  justify="center")
        t.add_column("Dew Pt",      style="bright_cyan",    width=9,  justify="center")
        t.add_column("Wind",        style="bright_white",   width=16)
        t.add_column("Pressure",    style="bright_magenta", width=11, justify="center")
        t.add_column("Visibility",  style="bright_green",   width=10, justify="center")
        t.add_column("Description", style="white",          min_width=20)

        for feat in features:
            p    = feat.get("properties", {})
            ts   = fmt_time(p.get("timestamp",""))
            temp = c_to_f(p.get("temperature",{}).get("value") if isinstance(p.get("temperature",{}), dict) else p.get("temperature"))
            dew  = c_to_f(p.get("dewpoint",{}).get("value") if isinstance(p.get("dewpoint",{}), dict) else p.get("dewpoint"))
            ws_v = p.get("windSpeed",{})
            ws   = ms_to_mph(ws_v.get("value") if isinstance(ws_v, dict) else ws_v)
            wd_v = p.get("windDirection",{})
            wd   = str(int(wd_v.get("value",0) or 0))+"deg" if isinstance(wd_v, dict) else str(wd_v or "N/A")
            pres_v = p.get("seaLevelPressure",{})
            pres = pa_to_inhg(pres_v.get("value") if isinstance(pres_v, dict) else pres_v)
            vis_v  = p.get("visibility",{})
            vis  = m_to_mi(vis_v.get("value") if isinstance(vis_v, dict) else vis_v)
            desc = p.get("textDescription","--")
            t.add_row(ts, temp, dew, f"{ws} {wd}", pres, vis, desc)

        console.print(t)

    press_enter()

# ── 7. Observation Renderer ────────────────────────────────────────────────────
def _render_observation(p: dict, station_id: str):
    ts   = fmt_time(p.get("timestamp",""))
    desc = p.get("textDescription","N/A")
    raw  = p.get("rawMessage","")

    def gv(field):
        v = p.get(field, {})
        if isinstance(v, dict):
            return v.get("value")
        return v

    temp    = c_to_f(gv("temperature"))
    dew     = c_to_f(gv("dewpoint"))
    windspd = ms_to_mph(gv("windSpeed"))
    windgst = ms_to_mph(gv("windGust"))
    wd_raw  = gv("windDirection")
    wind_dir= f"{int(wd_raw)}deg" if wd_raw is not None else "N/A"
    pres    = pa_to_inhg(gv("barometricPressure"))
    slp     = pa_to_inhg(gv("seaLevelPressure"))
    vis     = m_to_mi(gv("visibility"))
    hum_raw = gv("relativeHumidity")
    hum     = f"{round(hum_raw,1)}%" if hum_raw is not None else "N/A"
    wc      = c_to_f(gv("windChill"))
    hi      = c_to_f(gv("heatIndex"))

    t = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    t.add_column("Field", style="bold bright_magenta", width=24)
    t.add_column("Value", style="bright_white")

    rows = [
        ("Station",             station_id),
        ("Timestamp",           ts),
        ("Conditions",          desc),
        ("Temperature",         temp),
        ("Dew Point",           dew),
        ("Relative Humidity",   hum),
        ("Wind Speed",          windspd),
        ("Wind Gusts",          windgst),
        ("Wind Direction",      wind_dir),
        ("Barometric Pressure", pres),
        ("Sea Level Pressure",  slp),
        ("Visibility",          vis),
        ("Wind Chill",          wc),
        ("Heat Index",          hi),
    ]

    for label, val in rows:
        t.add_row(label, str(val))

    console.print(Panel(t, title=f"[bold cyan]LATEST OBS -- {station_id}[/]", border_style="cyan"))

    if raw:
        console.print(Panel(
            f"[dim]{escape(raw)}[/]",
            title="[dim]Raw METAR[/]",
            border_style="dim",
            expand=False
        ))

# ── 8. NWS Office Info ─────────────────────────────────────────────────────────
def feature_office_info():
    section("NWS FORECAST OFFICE LOOKUP")
    console.print("  [dim]WFO codes: FWD (Dallas/Ft Worth), HGX (Houston), OUN (Norman OK), etc.[/]")
    office_id = Prompt.ask("  [bold yellow]Enter WFO office ID[/]").upper().strip()
    if not office_id:
        return

    data = api_get(f"/offices/{office_id}")
    if not data:
        no_data(); press_enter(); return

    addr     = data.get("address", {})
    street   = addr.get("streetAddress","")
    locality = addr.get("addressLocality","")
    region   = addr.get("addressRegion","")
    postal   = addr.get("postalCode","")

    t = Table(box=box.SIMPLE, show_header=False, padding=(0,2))
    t.add_column("Field", style="bold bright_magenta", width=22)
    t.add_column("Value", style="bright_white")

    t.add_row("Office ID", office_id)
    t.add_row("Name",      data.get("name","N/A"))
    t.add_row("Address",   f"{street}, {locality}, {region} {postal}".strip(" ,"))
    t.add_row("Phone",     data.get("telephone","N/A"))
    t.add_row("Email",     data.get("email","N/A"))
    t.add_row("NWS Region",data.get("nwsRegion","N/A"))

    console.print(Panel(t, title=f"[bold cyan]NWS Office -- {office_id}[/]", border_style="cyan"))

    hl_data = api_get(f"/offices/{office_id}/headlines")
    if hl_data:
        items = hl_data.get("@graph", [])
        if items:
            console.print(f"\n  [bold cyan]Latest Headlines from {office_id}:[/]\n")
            for hl in items[:5]:
                title   = hl.get("title","")
                summary = hl.get("summary","")[:200]
                issued  = fmt_time(hl.get("issuanceTime",""))
                console.print(Panel(
                    f"  [bold white]{escape(title)}[/]\n  [dim]{issued}[/]\n\n  {escape(summary)}",
                    border_style="dim cyan", expand=False
                ))

    press_enter()

# ── 9. Text Products ───────────────────────────────────────────────────────────
def feature_text_products():
    section("NWS TEXT PRODUCTS")
    console.print("  [bold cyan]Options:[/]")
    console.print("  [cyan]1.[/] Browse products by type")
    console.print("  [cyan]2.[/] Browse products by office")
    console.print("  [cyan]3.[/] Get latest product (type + office)")
    console.print("  [cyan]4.[/] List all product types")
    choice = Prompt.ask("  [bold yellow]Choice[/]", default="4")

    if choice == "4":
        data = api_get("/products/types")
        if not data:
            no_data(); press_enter(); return
        items = data.get("@graph", [])
        t = Table(
            title="All NWS Product Types",
            box=box.ROUNDED, border_style="cyan",
            header_style="bold cyan", show_lines=False
        )
        t.add_column("Code", style="bold bright_cyan", width=8)
        t.add_column("Name", style="bright_white")
        for item in sorted(items, key=lambda x: x.get("productCode","")):
            t.add_row(item.get("productCode",""), item.get("productName",""))
        console.print(t)

    elif choice == "1":
        type_id = Prompt.ask("  [bold yellow]Product type code[/] (e.g. AFD, REC, SPS)").upper().strip()
        if not type_id:
            press_enter(); return
        data = api_get(f"/products/types/{type_id}")
        if not data:
            no_data(); press_enter(); return
        _render_product_list(data.get("@graph",[]), f"Products: {type_id}")

    elif choice == "2":
        office = Prompt.ask("  [bold yellow]Office ID[/] (e.g. FWD)").upper().strip()
        if not office:
            press_enter(); return
        data = api_get("/products", params={"office": [office], "limit": 20})
        if not data:
            no_data(); press_enter(); return
        _render_product_list(data.get("@graph",[]), f"Products from {office}")

    elif choice == "3":
        type_id = Prompt.ask("  [bold yellow]Product type code[/]").upper().strip()
        office  = Prompt.ask("  [bold yellow]Office ID[/]").upper().strip()
        if not type_id or not office:
            press_enter(); return
        data = api_get(f"/products/types/{type_id}/locations/{office}/latest")
        if not data:
            no_data(); press_enter(); return
        text   = data.get("productText","No text available.")
        issued = fmt_time(data.get("issuanceTime",""))
        console.print(Panel(
            f"[dim]{issued}[/]\n\n{escape(text[:3000])}",
            title=f"[bold cyan]{data.get('productName',type_id)} -- {office}[/]",
            border_style="cyan"
        ))

    press_enter()

def _render_product_list(items: list, title: str):
    if not items:
        no_data(); return
    t = Table(
        title=title, box=box.ROUNDED, border_style="cyan",
        header_style="bold cyan", show_lines=True, expand=True
    )
    t.add_column("ID",     style="bold bright_cyan", width=40)
    t.add_column("Office", style="bright_magenta",   width=8)
    t.add_column("Issued", style="yellow",           width=20)
    t.add_column("Name",   style="bright_white",     min_width=20)
    for item in items[:30]:
        pid    = item.get("id","")[:36]
        office = item.get("issuingOffice","")
        issued = fmt_time(item.get("issuanceTime",""))
        name   = item.get("productName","")
        t.add_row(pid, office, issued, name)
    console.print(t)

# ── 10. Radar Stations ────────────────────────────────────────────────────────
def feature_radar_stations():
    section("RADAR STATIONS")
    data = api_get("/radar/stations")
    if not data:
        no_data(); press_enter(); return

    features = data.get("features", [])
    if not features:
        no_data(); press_enter(); return

    t = Table(
        title=f"NWS Radar Stations ({len(features)} total)",
        box=box.ROUNDED, border_style="cyan",
        header_style="bold cyan", show_lines=False, expand=True
    )
    t.add_column("Station ID", style="bold bright_cyan", width=12)
    t.add_column("Name",       style="bright_white",     min_width=30)
    t.add_column("Type",       style="bright_magenta",   width=12)
    t.add_column("Lat",        style="yellow",           width=10, justify="right")
    t.add_column("Lon",        style="yellow",           width=12, justify="right")
    t.add_column("Elev (ft)",  style="bright_green",     width=10, justify="right")

    for feat in features:
        props  = feat.get("properties", {})
        sid    = props.get("stationIdentifier","")
        name   = props.get("name","")
        rtype  = props.get("stationType","")
        geom   = feat.get("geometry",{})
        coords = geom.get("coordinates",[None,None])
        lo     = round(coords[0],4) if coords[0] else ""
        la     = round(coords[1],4) if coords[1] else ""
        elev   = props.get("elevation",{})
        if isinstance(elev, dict):
            elev_m  = elev.get("value")
            elev_ft = str(round(elev_m * 3.28084)) if elev_m is not None else "N/A"
        else:
            elev_ft = "N/A"
        t.add_row(sid, name, rtype, str(la), str(lo), elev_ft)

    console.print(t)

    if Confirm.ask("\n  [bold yellow]Look up a specific radar station?[/]", default=False):
        sid   = Prompt.ask("  [bold yellow]Station ID[/]").upper().strip()
        data2 = api_get(f"/radar/stations/{sid}")
        if data2:
            p    = data2.get("properties",{})
            info = Table(box=box.SIMPLE, show_header=False, padding=(0,2))
            info.add_column("Field", style="bold bright_magenta", width=22)
            info.add_column("Value", style="bright_white")
            for k, v in p.items():
                if isinstance(v, str):
                    info.add_row(k, v)
            console.print(Panel(info, title=f"[bold cyan]Radar Station -- {sid}[/]", border_style="cyan"))

    press_enter()

# ── 11. Zone Lookup ───────────────────────────────────────────────────────────
def feature_zone_lookup():
    section("NWS ZONE LOOKUP")
    console.print("  [dim]Query forecast/county/fire zones by state or ID[/]")
    console.print("  [cyan]1.[/] Zones by state")
    console.print("  [cyan]2.[/] Zone detail by ID")
    console.print("  [cyan]3.[/] Zone forecast by ID")
    choice = Prompt.ask("  [bold yellow]Choice[/]", default="1")

    if choice == "1":
        state = Prompt.ask("  [bold yellow]State code[/] (e.g. TX)").upper().strip()
        ztype = Prompt.ask("  [bold yellow]Zone type[/] (forecast/public/county/fire)", default="forecast")
        data  = api_get(f"/zones/{ztype}", params={"area": state, "limit": 50})
        if not data:
            no_data(); press_enter(); return
        features = data.get("features",[])
        t = Table(
            title=f"{ztype.title()} Zones -- {state}",
            box=box.ROUNDED, border_style="cyan",
            header_style="bold cyan", show_lines=False
        )
        t.add_column("Zone ID", style="bold bright_cyan", width=12)
        t.add_column("Name",    style="bright_white")
        t.add_column("Type",    style="bright_magenta", width=12)
        t.add_column("TZ",      style="yellow",         width=20)
        for feat in features:
            p  = feat.get("properties",{})
            tz = ", ".join(p.get("timeZone",[]))
            t.add_row(p.get("id",""), p.get("name",""), p.get("type",""), tz)
        console.print(t)

    elif choice == "2":
        ztype   = Prompt.ask("  [bold yellow]Zone type[/]", default="forecast")
        zone_id = Prompt.ask("  [bold yellow]Zone ID[/] (e.g. TXZ105)").upper().strip()
        data    = api_get(f"/zones/{ztype}/{zone_id}")
        if not data:
            no_data(); press_enter(); return
        p    = data.get("properties",{})
        info = Table(box=box.SIMPLE, show_header=False, padding=(0,2))
        info.add_column("Field", style="bold bright_magenta", width=22)
        info.add_column("Value", style="bright_white")
        info.add_row("Zone ID",       p.get("id",""))
        info.add_row("Name",          p.get("name",""))
        info.add_row("Type",          p.get("type",""))
        info.add_row("State",         p.get("state",""))
        info.add_row("Time Zone",     ", ".join(p.get("timeZone",[])))
        info.add_row("Radar Station", p.get("radarStation",""))
        console.print(Panel(info, title=f"[bold cyan]Zone Info -- {zone_id}[/]", border_style="cyan"))

    elif choice == "3":
        ztype   = Prompt.ask("  [bold yellow]Zone type[/]", default="forecast")
        zone_id = Prompt.ask("  [bold yellow]Zone ID[/] (e.g. TXZ105)").upper().strip()
        data    = api_get(f"/zones/{ztype}/{zone_id}/forecast")
        if not data:
            no_data(); press_enter(); return
        periods = data.get("properties",{}).get("periods",[])
        for p in periods:
            console.print(Panel(
                f"{escape(p.get('detailedForecast',''))}",
                title=f"[bold cyan]{p.get('name','')}[/]",
                border_style="dim cyan"
            ))

    press_enter()

# ── 12. Marine Region Alerts ──────────────────────────────────────────────────
def feature_marine_alerts():
    section("MARINE REGION ALERTS")
    console.print("  [dim]AL=Alaska  AT=Atlantic  GL=Great Lakes  GM=Gulf of Mexico  PA=Pacific  PI=Pacific Islands[/]\n")
    region = Prompt.ask("  [bold yellow]Region code[/]").upper().strip()
    valid  = ["AL","AT","GL","GM","PA","PI"]
    if region not in valid:
        console.print(f"  [red]Invalid region. Choose from: {', '.join(valid)}[/]")
        press_enter(); return

    data = api_get(f"/alerts/active/region/{region}")
    if not data:
        no_data(); press_enter(); return

    features = data.get("features",[])
    if not features:
        no_data(f"No active marine alerts for {region}."); press_enter(); return

    console.print(f"  [bold green]Found {len(features)} marine alert(s) for {region}[/]\n")
    _render_alert_list(features)
    press_enter()

# ── 13. Alert Types Reference ─────────────────────────────────────────────────
def feature_alert_types():
    section("NWS ALERT TYPES REFERENCE")
    data = api_get("/alerts/types")
    if not data:
        no_data(); press_enter(); return

    types = data.get("eventTypes",[])
    if not types:
        no_data(); press_enter(); return

    t = Table(
        title=f"All NWS Event Types ({len(types)} types)",
        box=box.ROUNDED, border_style="cyan",
        header_style="bold cyan", show_lines=False
    )
    t.add_column("#",          style="dim white",   width=4)
    t.add_column("Event Type", style="bright_white")

    for i, et in enumerate(sorted(types), 1):
        t.add_row(str(i), et)

    console.print(t)
    press_enter()

# ── 14. Glossary ──────────────────────────────────────────────────────────────
def feature_glossary():
    section("NWS METEOROLOGICAL GLOSSARY")
    data = api_get("/glossary")
    if not data:
        no_data(); press_enter(); return

    terms = data.get("glossary",[])
    if not terms:
        no_data(); press_enter(); return

    console.print(f"  [dim]Total terms available: {len(terms)}[/]")
    search   = Prompt.ask("  [bold yellow]Search term[/] (or ENTER to browse first 30)").strip()
    filtered = [t for t in terms if search.lower() in t.get("term","").lower()] if search else terms[:30]

    if not filtered:
        no_data(f"No terms matching '{search}'."); press_enter(); return

    for item in filtered[:30]:
        term = item.get("term","")
        defn = item.get("definition","")
        console.print(Panel(
            f"[bright_white]{escape(defn)}[/]",
            title=f"[bold cyan]{escape(term)}[/]",
            border_style="dim cyan",
            expand=False
        ))
    press_enter()

# ── 15. Aviation SIGMETs ──────────────────────────────────────────────────────
def feature_sigmets():
    section("AVIATION SIGMET / AIRMET")
    console.print("  [dim]SIGMETs are significant meteorological advisories for aviation.[/]")
    console.print("  [cyan]1.[/] All current SIGMETs")
    console.print("  [cyan]2.[/] SIGMETs by ATSU")
    choice = Prompt.ask("  [bold yellow]Choice[/]", default="1")

    if choice == "1":
        data = api_get("/aviation/sigmets")
    else:
        atsu = Prompt.ask("  [bold yellow]ATSU identifier[/] (e.g. KKCI)").upper().strip()
        data = api_get(f"/aviation/sigmets/{atsu}")

    if not data:
        no_data(); press_enter(); return

    features = data.get("features",[])
    if not features:
        no_data("No active SIGMETs/AIRMETs."); press_enter(); return

    t = Table(
        title=f"Active SIGMETs/AIRMETs ({len(features)})",
        box=box.ROUNDED, border_style="yellow",
        header_style="bold cyan", show_lines=True, expand=True
    )
    t.add_column("ID",         style="bold bright_cyan",  width=12)
    t.add_column("ATSU",       style="bright_magenta",    width=8)
    t.add_column("Sequence",   style="yellow",            width=10)
    t.add_column("Issued",     style="bright_white",      width=20)
    t.add_column("Start",      style="cyan",              width=20)
    t.add_column("End",        style="cyan",              width=20)
    t.add_column("Phenomenon", style="white",             min_width=20)

    for feat in features:
        p    = feat.get("properties",{})
        pid  = str(feat.get("id",""))[-12:]
        atsu = p.get("atsu","")
        seq  = str(p.get("sequence",""))
        iss  = fmt_time(p.get("issueTime",""))
        st   = fmt_time(p.get("start",""))
        en   = fmt_time(p.get("end",""))
        phen = str(p.get("phenomenon",""))[-30:]
        t.add_row(pid, atsu, seq, iss, st, en, phen)

    console.print(t)
    press_enter()

# ── 16. Station Search by State ───────────────────────────────────────────────
def feature_station_search():
    section("OBSERVATION STATION SEARCH")
    console.print("  [dim]Find weather observation stations by state.[/]")
    state = Prompt.ask("  [bold yellow]State code[/] (e.g. TX, CA)").upper().strip()
    if not state:
        press_enter(); return

    data = api_get("/stations", params={"state": state, "limit": 50})
    if not data:
        no_data(); press_enter(); return

    features = data.get("features",[])
    if not features:
        no_data(f"No stations found for {state}."); press_enter(); return

    t = Table(
        title=f"Observation Stations -- {state} ({len(features)} shown)",
        box=box.ROUNDED, border_style="cyan",
        header_style="bold cyan", show_lines=False, expand=True
    )
    t.add_column("Station ID", style="bold bright_cyan", width=12)
    t.add_column("Name",       style="bright_white",     min_width=30)
    t.add_column("Time Zone",  style="yellow",           width=22)
    t.add_column("Lat",        style="bright_green",     width=10, justify="right")
    t.add_column("Lon",        style="bright_green",     width=12, justify="right")

    for feat in features:
        p      = feat.get("properties",{})
        sid    = p.get("stationIdentifier","")
        name   = p.get("name","")
        tz     = p.get("timeZone","")
        geom   = feat.get("geometry",{})
        coords = geom.get("coordinates",[None,None])
        la     = round(coords[1],4) if coords and len(coords)>1 and coords[1] else ""
        lo     = round(coords[0],4) if coords and len(coords)>0 and coords[0] else ""
        t.add_row(sid, name, tz, str(la), str(lo))

    console.print(t)
    press_enter()

# ── 17. Alert Lookup by ID ────────────────────────────────────────────────────
def feature_alert_by_id():
    section("ALERT LOOKUP BY ID")
    console.print("  [dim]NWS alert IDs look like: urn:oid:2.49.0.1.840.0.xxx...[/]")
    alert_id = Prompt.ask("  [bold yellow]Enter Alert ID[/]").strip()
    if not alert_id:
        press_enter(); return

    data = api_get(f"/alerts/{alert_id}")
    if not data:
        no_data(); press_enter(); return

    p = data.get("properties",{})
    _render_single_alert(p)
    press_enter()

# ── 18. Point Radio Stations ───────────────────────────────────────────────────
def feature_point_radio():
    section("NOAA WEATHER RADIO STATIONS")
    console.print("  [dim]Find NOAA Weather Radio transmitters near a lat/lon point.[/]")
    lat = Prompt.ask("  [bold yellow]Latitude[/]")
    lon = Prompt.ask("  [bold yellow]Longitude[/]")
    try:
        lat_f, lon_f = float(lat), float(lon)
    except ValueError:
        console.print("  [red]Invalid coordinates.[/]"); press_enter(); return

    data = api_get(f"/points/{lat_f},{lon_f}/radio")
    if not data:
        no_data("No radio station data for this point."); press_enter(); return

    console.print(Panel(
        escape(json.dumps(data, indent=2)[:2000]),
        title="[bold cyan]NOAA Weather Radio Data[/]",
        border_style="cyan"
    ))
    press_enter()

# ── Shared alert renderers ─────────────────────────────────────────────────────
def _render_alert_list(features: list):
    for i, feat in enumerate(features, 1):
        p = feat.get("properties",{})
        _render_single_alert(p, index=i)
        console.print()

def _render_single_alert(p: dict, index: int = 0):
    evt  = p.get("event","Unknown")
    sev  = p.get("severity","Unknown")
    urg  = p.get("urgency","Unknown")
    cert = p.get("certainty","Unknown")
    area = p.get("areaDesc","N/A")
    onset= fmt_time(p.get("onset",""))
    ends = fmt_time(p.get("ends","") or p.get("expires",""))
    head = p.get("headline","")
    desc = p.get("description","")[:600]
    inst = p.get("instruction","")[:300]
    resp = p.get("response","")

    sev_style = SEVERITY_STYLE.get(sev, "white")
    body = Text()
    body.append(f"  Severity:   ", style="bold white");  body.append(f"{sev}\n",  style=sev_style)
    body.append(f"  Urgency:    ", style="bold white");  body.append(f"{urg}\n",  style="bold cyan")
    body.append(f"  Certainty:  ", style="bold white");  body.append(f"{cert}\n", style="bright_cyan")
    body.append(f"  Response:   ", style="bold white");  body.append(f"{resp}\n", style="bright_white")
    body.append(f"  Area:       ", style="bold white");  body.append(f"{area}\n", style="bright_white")
    body.append(f"  Onset:      ", style="bold white");  body.append(f"{onset}\n", style="yellow")
    body.append(f"  Expires:    ", style="bold white");  body.append(f"{ends}\n", style="yellow")
    if head:
        body.append(f"\n  {head}\n", style="italic bright_white")
    if desc:
        body.append(f"\n  {desc[:500]}\n", style="dim white")
    if inst:
        body.append(f"\n  INSTRUCTIONS: {inst[:250]}", style="bold orange1")

    bdr    = "red" if sev in ("Extreme","Severe") else ("yellow" if sev=="Moderate" else "cyan")
    prefix = f"#{index} -- " if index else ""
    console.print(Panel(
        body,
        title=f"[bold {bdr}]  {prefix}{evt}  [/]",
        border_style=bdr,
        padding=(0, 1)
    ))

# ══════════════════════════════════════════════════════════════════════════════
#  MAIN MENU
# ══════════════════════════════════════════════════════════════════════════════

MENU_ITEMS = [
    ("1",  "Active Alert Count Dashboard",          feature_alert_count,      "ALERTS"),
    ("2",  "Active Alerts by State/Area",            feature_alerts_by_state,  "ALERTS"),
    ("3",  "Active Alerts by Zone ID",               feature_alerts_by_zone,   "ALERTS"),
    ("4",  "Marine Region Alerts",                   feature_marine_alerts,    "ALERTS"),
    ("5",  "Alert Lookup by ID",                     feature_alert_by_id,      "ALERTS"),
    ("6",  "Alert Types Reference",                  feature_alert_types,      "ALERTS"),
    ("7",  "7-Day Point Forecast",                   feature_point_forecast,   "FORECAST"),
    ("8",  "Hourly Point Forecast",                  feature_hourly_forecast,  "FORECAST"),
    ("9",  "Zone Forecast Lookup",                   feature_zone_lookup,      "FORECAST"),
    ("10", "Station Latest Observation",             feature_station_obs,      "OBSERVATIONS"),
    ("11", "Observation Station Search (by state)",  feature_station_search,   "OBSERVATIONS"),
    ("12", "NWS Forecast Office Info",               feature_office_info,      "OFFICES"),
    ("13", "NWS Text Products",                      feature_text_products,    "PRODUCTS"),
    ("14", "Radar Stations",                         feature_radar_stations,   "RADAR"),
    ("15", "Aviation SIGMETs / AIRMETs",             feature_sigmets,          "AVIATION"),
    ("16", "NOAA Weather Radio Stations",            feature_point_radio,      "RADIO"),
    ("17", "Meteorological Glossary",                feature_glossary,         "REFERENCE"),
    ("Q",  "Quit",                                   None,                     ""),
]

def draw_menu():
    banner()
    current_cat = ""
    for key, label, _, cat in MENU_ITEMS:
        if cat and cat != current_cat:
            console.print(f"  [bold bright_magenta]-- {cat} --[/]")
            current_cat = cat
        if key == "Q":
            console.print(f"\n  [bold red][Q][/] [dim white]{label}[/]")
        else:
            console.print(f"  [bold cyan][{key:>2}][/] [bright_white]{label}[/]")
    console.print()

def main():
    while True:
        draw_menu()
        choice = Prompt.ask("  [bold yellow]Select option[/]").strip().upper()

        for key, label, func, _ in MENU_ITEMS:
            if choice == key.upper():
                if key == "Q":
                    console.print("\n  [bold cyan]CabalWeatherCheck terminated. Stay frosty.[/]\n")
                    sys.exit(0)
                func()
                break
        else:
            console.print(f"\n  [red]Invalid option:[/] {escape(choice)}")
            time.sleep(1)

if __name__ == "__main__":
    main()
