"""
METAR Reader - Aviation Weather Decoder

A Flask web application that fetches and decodes METAR weather reports
into plain English. Supports US and international METAR formats.

Usage:
    python app.py
    Open http://127.0.0.1:5000 in your browser
"""

from flask import Flask, render_template, request, jsonify
import requests
import re
import math

app = Flask(__name__)

# Weather phenomena codes and their plain English translations
WEATHER_CODES = {
    # Intensity
    '-': 'Light',
    '+': 'Heavy',
    'VC': 'In the vicinity',

    # Descriptor
    'MI': 'Shallow',
    'PR': 'Partial',
    'BC': 'Patches',
    'DR': 'Low drifting',
    'BL': 'Blowing',
    'SH': 'Showers',
    'TS': 'Thunderstorm',
    'FZ': 'Freezing',

    # Precipitation
    'DZ': 'Drizzle',
    'RA': 'Rain',
    'SN': 'Snow',
    'SG': 'Snow grains',
    'IC': 'Ice crystals',
    'PL': 'Ice pellets',
    'GR': 'Hail',
    'GS': 'Small hail',
    'UP': 'Unknown precipitation',

    # Obscuration
    'BR': 'Mist',
    'FG': 'Fog',
    'FU': 'Smoke',
    'VA': 'Volcanic ash',
    'DU': 'Widespread dust',
    'SA': 'Sand',
    'HZ': 'Haze',
    'PY': 'Spray',

    # Other
    'PO': 'Dust/sand whirls',
    'SQ': 'Squalls',
    'FC': 'Funnel cloud/tornado',
    'SS': 'Sandstorm',
    'DS': 'Duststorm',
}

CLOUD_CODES = {
    'SKC': 'Sky clear',
    'CLR': 'Clear below 12,000 ft',
    'NSC': 'No significant clouds',
    'FEW': 'Few clouds',
    'SCT': 'Scattered clouds',
    'BKN': 'Broken clouds',
    'OVC': 'Overcast',
    'VV': 'Vertical visibility (sky obscured)',
}


def fetch_metar(airport_code):
    """Fetch METAR data from Aviation Weather API."""
    url = f"https://aviationweather.gov/api/data/metar?ids={airport_code.upper()}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            metar_text = response.text.strip()
            if metar_text:
                return metar_text
            else:
                return None
        return None
    except requests.RequestException:
        return None


def fetch_taf(airport_code):
    """Fetch TAF (Terminal Aerodrome Forecast) data from Aviation Weather API."""
    url = f"https://aviationweather.gov/api/data/taf?ids={airport_code.upper()}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            taf_text = response.text.strip()
            if taf_text:
                return taf_text
            else:
                return None
        return None
    except requests.RequestException:
        return None


def decode_wind(wind_str):
    """Decode wind information."""
    if not wind_str:
        return None

    # Check for calm wind first
    if wind_str == '00000KT':
        return "Calm"

    # Pattern: dddssKT or dddssGggKT (with gusts) or VRB for variable
    match = re.match(r'(\d{3}|VRB)(\d{2,3})(G(\d{2,3}))?(KT|MPS)', wind_str)
    if match:
        direction = match.group(1)
        speed = int(match.group(2))
        gust = match.group(4)
        unit = match.group(5)

        speed_unit = "knots" if unit == "KT" else "meters per second"

        if direction == 'VRB':
            result = f"Variable direction at {speed} {speed_unit}"
        else:
            direction_deg = int(direction)
            cardinal = get_cardinal_direction(direction_deg)
            result = f"From {cardinal} ({direction_deg}°) at {speed} {speed_unit}"

        if gust:
            result += f", gusting to {gust} {speed_unit}"

        return result

    return None


def get_cardinal_direction(degrees):
    """Convert degrees to cardinal direction."""
    directions = ['North', 'North-Northeast', 'Northeast', 'East-Northeast',
                  'East', 'East-Southeast', 'Southeast', 'South-Southeast',
                  'South', 'South-Southwest', 'Southwest', 'West-Southwest',
                  'West', 'West-Northwest', 'Northwest', 'North-Northwest']
    index = round(degrees / 22.5) % 16
    return directions[index]


def decode_visibility(vis_str):
    """Decode visibility information."""
    if not vis_str:
        return None

    # Statute miles (US)
    if 'SM' in vis_str:
        vis_str = vis_str.replace('SM', '')
        # Handle fractions like 1/2, 1 1/2
        if '/' in vis_str:
            parts = vis_str.split()
            if len(parts) == 2:  # e.g., "1 1/2"
                whole = int(parts[0])
                frac = parts[1].split('/')
                result = whole + int(frac[0]) / int(frac[1])
            else:  # e.g., "1/2"
                frac = vis_str.split('/')
                result = int(frac[0]) / int(frac[1])
        else:
            result = float(vis_str)

        if result >= 10:
            return "10 miles or more (excellent visibility)"
        elif result >= 6:
            return f"{result} miles (good visibility)"
        elif result >= 3:
            return f"{result} miles (moderate visibility)"
        elif result >= 1:
            return f"{result} miles (poor visibility)"
        else:
            return f"{result} miles (very poor visibility)"

    # Meters (international)
    if vis_str.isdigit():
        meters = int(vis_str)
        if meters >= 9999:
            return "10 km or more (excellent visibility)"
        else:
            km = meters / 1000
            return f"{km:.1f} km ({meters} meters)"

    return vis_str


def decode_weather(weather_str):
    """Decode weather phenomena."""
    if not weather_str:
        return None

    # Handle intensity prefix
    intensity = ""
    if weather_str.startswith('-'):
        intensity = "Light "
        weather_str = weather_str[1:]
    elif weather_str.startswith('+'):
        intensity = "Heavy "
        weather_str = weather_str[1:]
    elif weather_str.startswith('VC'):
        intensity = "In the vicinity: "
        weather_str = weather_str[2:]

    # Decode remaining codes in pairs
    decoded = []
    i = 0
    while i < len(weather_str):
        code = weather_str[i:i+2]
        if code in WEATHER_CODES:
            decoded.append(WEATHER_CODES[code])
        i += 2

    if decoded:
        return intensity + ' '.join(decoded)
    return None


def decode_clouds(cloud_str):
    """Decode cloud coverage."""
    if not cloud_str:
        return None

    # Pattern: CCChhhh or CCChhh (coverage + height in hundreds of feet)
    match = re.match(r'(SKC|CLR|NSC|FEW|SCT|BKN|OVC|VV)(\d{3})?(\w+)?', cloud_str)
    if match:
        coverage = match.group(1)
        height = match.group(2)
        modifier = match.group(3)

        coverage_text = CLOUD_CODES.get(coverage, coverage)

        if height:
            height_ft = int(height) * 100
            result = f"{coverage_text} at {height_ft:,} feet"
        else:
            result = coverage_text

        if modifier == 'CB':
            result += " (Cumulonimbus - thunderstorm clouds)"
        elif modifier == 'TCU':
            result += " (Towering cumulus)"

        return result

    return None


def decode_temp_dewpoint(temp_str):
    """Decode temperature and dewpoint.

    Returns:
        Tuple of (temp_text, dewpoint_text, temp_celsius, dewpoint_celsius)
    """
    if not temp_str or '/' not in temp_str:
        return None, None, None, None

    parts = temp_str.split('/')
    if len(parts) != 2:
        return None, None, None, None

    def parse_temp(t):
        if not t:
            return None
        if t.startswith('M'):
            return -int(t[1:])
        return int(t)

    temp = parse_temp(parts[0])
    dewpoint = parse_temp(parts[1])

    temp_text = None
    dewpoint_text = None

    if temp is not None:
        temp_f = (temp * 9/5) + 32
        temp_text = f"{temp}°C ({temp_f:.0f}°F)"

    if dewpoint is not None:
        dewpoint_f = (dewpoint * 9/5) + 32
        dewpoint_text = f"{dewpoint}°C ({dewpoint_f:.0f}°F)"

    return temp_text, dewpoint_text, temp, dewpoint


def decode_altimeter(alt_str):
    """Decode altimeter setting."""
    if not alt_str:
        return None

    # US format: Axxxx (inches of mercury * 100)
    if alt_str.startswith('A') and len(alt_str) == 5:
        value = int(alt_str[1:]) / 100
        hpa = value * 33.8639
        return f"{value:.2f} inHg ({hpa:.0f} hPa)"

    # International format: Qxxxx (hectopascals)
    if alt_str.startswith('Q') and len(alt_str) == 5:
        value = int(alt_str[1:])
        inhg = value / 33.8639
        return f"{value} hPa ({inhg:.2f} inHg)"

    return None


def calculate_relative_humidity(temp_celsius, dewpoint_celsius):
    """Calculate relative humidity from temperature and dewpoint.

    Uses the Magnus formula for accurate humidity calculation.

    Args:
        temp_celsius: Temperature in degrees Celsius
        dewpoint_celsius: Dewpoint in degrees Celsius

    Returns:
        Relative humidity as a percentage (0-100), or None if inputs invalid
    """
    if temp_celsius is None or dewpoint_celsius is None:
        return None

    # Magnus formula constants
    a = 17.625
    b = 243.04

    # Calculate relative humidity
    try:
        exp_dewpoint = math.exp((a * dewpoint_celsius) / (b + dewpoint_celsius))
        exp_temp = math.exp((a * temp_celsius) / (b + temp_celsius))
        rh = 100 * (exp_dewpoint / exp_temp)

        # Clamp to valid range (can exceed 100% slightly due to measurement precision)
        rh = max(0, min(100, rh))
        return round(rh, 1)
    except (ValueError, ZeroDivisionError):
        return None


def decode_remarks(remarks_str):
    """Decode METAR remarks section into plain English."""
    if not remarks_str:
        return None

    decoded_remarks = []
    parts = remarks_str.split()

    i = 0
    while i < len(parts):
        part = parts[i]

        # AO1/AO2 - Automated station type
        if part == 'AO1':
            decoded_remarks.append("Automated station without precipitation sensor")
            i += 1
            continue
        if part == 'AO2':
            decoded_remarks.append("Automated station with precipitation sensor")
            i += 1
            continue

        # SLP - Sea Level Pressure (e.g., SLP273 = 1027.3 hPa)
        if part.startswith('SLP') and len(part) >= 6:
            try:
                slp_value = int(part[3:])
                # SLP is reported as last 3 digits, prepend 9 or 10
                if slp_value > 500:
                    pressure = 900 + slp_value / 10
                else:
                    pressure = 1000 + slp_value / 10
                decoded_remarks.append(f"Sea level pressure: {pressure:.1f} hPa")
            except ValueError:
                pass
            i += 1
            continue

        # Precise temperature T####
        if part.startswith('T') and len(part) == 9 and part[1:].replace('/', '').isdigit():
            try:
                temp_sign = 1 if part[1] == '0' else -1
                temp = temp_sign * int(part[2:5]) / 10
                dew_sign = 1 if part[5] == '0' else -1
                dew = dew_sign * int(part[6:9]) / 10
                decoded_remarks.append(f"Precise temperature: {temp:.1f}°C, dewpoint: {dew:.1f}°C")
            except (ValueError, IndexError):
                pass
            i += 1
            continue

        # Precipitation P#### (hundredths of inch)
        if part.startswith('P') and len(part) == 5 and part[1:].isdigit():
            precip = int(part[1:]) / 100
            if precip == 0:
                decoded_remarks.append("Precipitation last hour: Trace or none")
            else:
                decoded_remarks.append(f"Precipitation last hour: {precip:.2f} inches")
            i += 1
            continue

        # Rain/Snow began/ended (e.g., RAB08E25, SNB15)
        weather_match = re.match(r'^(RA|SN|DZ|FG|BR|TS|SH)([BE])(\d{2})(?:([BE])(\d{2}))?$', part)
        if weather_match:
            weather_types = {
                'RA': 'Rain', 'SN': 'Snow', 'DZ': 'Drizzle',
                'FG': 'Fog', 'BR': 'Mist', 'TS': 'Thunderstorm', 'SH': 'Showers'
            }
            wx_type = weather_types.get(weather_match.group(1), weather_match.group(1))
            action1 = 'began' if weather_match.group(2) == 'B' else 'ended'
            time1 = weather_match.group(3)
            result = f"{wx_type} {action1} at :{time1}"

            if weather_match.group(4) and weather_match.group(5):
                action2 = 'began' if weather_match.group(4) == 'B' else 'ended'
                time2 = weather_match.group(5)
                result += f", {action2} at :{time2}"

            decoded_remarks.append(result)
            i += 1
            continue

        # Maintenance indicator
        if part == '$':
            decoded_remarks.append("Station needs maintenance")
            i += 1
            continue

        # Peak wind PK WND dddff/hhmm or PK WND dddff/mm
        if part == 'PK' and i + 2 < len(parts) and parts[i + 1] == 'WND':
            pk_match = re.match(r'^(\d{3})(\d{2,3})/(\d{2,4})$', parts[i + 2])
            if pk_match:
                direction = pk_match.group(1)
                speed = pk_match.group(2)
                time_part = pk_match.group(3)
                if len(time_part) == 4:
                    time_str = f"{time_part[:2]}:{time_part[2:]}"
                else:
                    time_str = f":{time_part}"
                decoded_remarks.append(f"Peak wind: {direction}° at {speed} knots at {time_str}")
            i += 3
            continue

        # Wind shift WSHFT hhmm
        if part == 'WSHFT' and i + 1 < len(parts):
            time_match = re.match(r'^(\d{2,4})$', parts[i + 1])
            if time_match:
                time_part = time_match.group(1)
                if len(time_part) == 4:
                    time_str = f"{time_part[:2]}:{time_part[2:]}"
                else:
                    time_str = f":{time_part}"
                decoded_remarks.append(f"Wind shift at {time_str}")
                i += 2
                continue

        # Visibility at specific location (e.g., VIS 1/2V2)
        if part == 'VIS' and i + 1 < len(parts):
            decoded_remarks.append(f"Variable visibility: {parts[i + 1]}")
            i += 2
            continue

        # Ceiling height variable (CIG minVmax)
        if part == 'CIG' and i + 1 < len(parts):
            cig_match = re.match(r'^(\d{3})V(\d{3})$', parts[i + 1])
            if cig_match:
                min_cig = int(cig_match.group(1)) * 100
                max_cig = int(cig_match.group(2)) * 100
                decoded_remarks.append(f"Ceiling variable: {min_cig:,} to {max_cig:,} feet")
                i += 2
                continue

        # Lightning (LTG types)
        if part.startswith('LTG'):
            ltg_types = {
                'IC': 'in-cloud', 'CC': 'cloud-to-cloud',
                'CG': 'cloud-to-ground', 'CA': 'cloud-to-air'
            }
            ltg_desc = []
            for code, desc in ltg_types.items():
                if code in part:
                    ltg_desc.append(desc)
            if ltg_desc:
                decoded_remarks.append(f"Lightning: {', '.join(ltg_desc)}")
            else:
                decoded_remarks.append("Lightning observed")
            i += 1
            continue

        # Thunderstorm location (TS directions)
        if part == 'TS' and i + 1 < len(parts):
            decoded_remarks.append(f"Thunderstorm {parts[i + 1]}")
            i += 2
            continue

        # Virga
        if part == 'VIRGA':
            decoded_remarks.append("Virga (precipitation not reaching ground)")
            i += 1
            continue

        # Pressure rising/falling rapidly
        if part == 'PRESRR':
            decoded_remarks.append("Pressure rising rapidly")
            i += 1
            continue
        if part == 'PRESFR':
            decoded_remarks.append("Pressure falling rapidly")
            i += 1
            continue

        # NOSIG - No significant change expected
        if part == 'NOSIG':
            decoded_remarks.append("No significant weather change expected")
            i += 1
            continue

        # FROPA - Frontal passage
        if part == 'FROPA':
            decoded_remarks.append("Frontal passage")
            i += 1
            continue

        i += 1

    return decoded_remarks if decoded_remarks else None


def decode_metar(metar_text):
    """Decode a complete METAR report."""
    if not metar_text:
        return None

    parts = metar_text.split()
    decoded = {
        'raw': metar_text,
        'station': None,
        'time': None,
        'wind': None,
        'visibility': None,
        'weather': [],
        'clouds': [],
        'temperature': None,
        'dewpoint': None,
        'relative_humidity': None,
        'altimeter': None,
        'remarks': None,
        'remarks_decoded': None,
        'flight_category': None,
    }

    i = 0

    # Skip METAR/SPECI prefix if present
    if parts[i] in ['METAR', 'SPECI']:
        i += 1

    # Station identifier (4 letters)
    if i < len(parts) and re.match(r'^[A-Z]{4}$', parts[i]):
        decoded['station'] = parts[i]
        i += 1

    # Time (ddhhmmZ)
    if i < len(parts) and re.match(r'^\d{6}Z$', parts[i]):
        time_str = parts[i]
        day = time_str[:2]
        hour = time_str[2:4]
        minute = time_str[4:6]
        decoded['time'] = f"Day {day} at {hour}:{minute} UTC"
        i += 1

    # AUTO indicator
    if i < len(parts) and parts[i] == 'AUTO':
        i += 1

    # Wind
    if i < len(parts) and ('KT' in parts[i] or 'MPS' in parts[i]):
        decoded['wind'] = decode_wind(parts[i])
        i += 1

        # Variable wind direction (e.g., 180V240)
        if i < len(parts) and re.match(r'^\d{3}V\d{3}$', parts[i]):
            var_match = re.match(r'^(\d{3})V(\d{3})$', parts[i])
            if var_match and decoded['wind']:
                decoded['wind'] += f", varying between {var_match.group(1)}° and {var_match.group(2)}°"
            i += 1

    # Visibility
    if i < len(parts):
        # Check for visibility (SM suffix or 4-digit meters)
        vis_parts = []
        while i < len(parts) and ('SM' in parts[i] or parts[i].isdigit() or '/' in parts[i]):
            if 'SM' in parts[i]:
                vis_parts.append(parts[i])
                i += 1
                break
            elif parts[i].isdigit() and len(parts[i]) == 4:
                vis_parts.append(parts[i])
                i += 1
                break
            elif '/' in parts[i] and i + 1 < len(parts) and 'SM' in parts[i + 1]:
                vis_parts.append(parts[i] + parts[i + 1])
                i += 2
                break
            else:
                break

        if vis_parts:
            decoded['visibility'] = decode_visibility(''.join(vis_parts))

    # Weather phenomena and clouds
    while i < len(parts):
        part = parts[i]

        # Check for remarks section
        if part == 'RMK':
            decoded['remarks'] = ' '.join(parts[i+1:])
            decoded['remarks_decoded'] = decode_remarks(decoded['remarks'])
            break

        # Check for altimeter
        if part.startswith('A') and len(part) == 5 and part[1:].isdigit():
            decoded['altimeter'] = decode_altimeter(part)
            i += 1
            continue

        if part.startswith('Q') and len(part) == 5 and part[1:].isdigit():
            decoded['altimeter'] = decode_altimeter(part)
            i += 1
            continue

        # Check for temperature/dewpoint
        if '/' in part and re.match(r'^M?\d{2}/M?\d{2}$', part):
            temp, dew, temp_c, dew_c = decode_temp_dewpoint(part)
            decoded['temperature'] = temp
            decoded['dewpoint'] = dew
            # Calculate relative humidity
            rh = calculate_relative_humidity(temp_c, dew_c)
            if rh is not None:
                decoded['relative_humidity'] = f"{rh}%"
            i += 1
            continue

        # Check for cloud coverage
        if any(part.startswith(code) for code in CLOUD_CODES.keys()):
            cloud = decode_clouds(part)
            if cloud:
                decoded['clouds'].append(cloud)
            i += 1
            continue

        # Check for weather phenomena
        weather = decode_weather(part)
        if weather:
            decoded['weather'].append(weather)

        i += 1

    # Determine flight category
    decoded['flight_category'] = determine_flight_category(decoded)

    return decoded


def determine_flight_category(decoded):
    """Determine VFR/MVFR/IFR/LIFR flight category."""
    # This is a simplified determination
    visibility_text = decoded.get('visibility', '')
    clouds = decoded.get('clouds', [])

    # Default to VFR
    category = 'VFR'
    description = 'Visual Flight Rules - Good flying conditions'

    # Check for poor conditions in weather
    weather = decoded.get('weather', [])
    for w in weather:
        if any(bad in w.lower() for bad in ['fog', 'thunderstorm', 'heavy']):
            category = 'IFR'
            description = 'Instrument Flight Rules - Reduced visibility'

    # Check clouds for low ceilings
    for cloud in clouds:
        if 'Overcast' in cloud or 'Broken' in cloud:
            # Try to extract height
            match = re.search(r'(\d+,?\d*) feet', cloud)
            if match:
                height = int(match.group(1).replace(',', ''))
                if height < 500:
                    category = 'LIFR'
                    description = 'Low IFR - Very poor conditions'
                elif height < 1000:
                    category = 'IFR'
                    description = 'Instrument Flight Rules - Low ceiling'
                elif height < 3000:
                    category = 'MVFR'
                    description = 'Marginal VFR - Ceiling below 3000 feet'

    return {'category': category, 'description': description}


def generate_summary(decoded):
    """Generate a friendly weather summary."""
    if not decoded:
        return "Unable to decode METAR data."

    summary_parts = []

    # Station and time
    if decoded['station']:
        summary_parts.append(f"Weather report for {decoded['station']}")
    if decoded['time']:
        summary_parts.append(f"Observed: {decoded['time']}")

    summary_parts.append("")  # Blank line

    # Conditions summary
    conditions = []

    if decoded['temperature']:
        conditions.append(f"Temperature: {decoded['temperature']}")

    if decoded['wind']:
        conditions.append(f"Wind: {decoded['wind']}")

    if decoded['visibility']:
        conditions.append(f"Visibility: {decoded['visibility']}")

    if decoded['clouds']:
        conditions.append(f"Sky: {', '.join(decoded['clouds'])}")

    if decoded['weather']:
        conditions.append(f"Weather: {', '.join(decoded['weather'])}")

    if decoded['dewpoint']:
        conditions.append(f"Dewpoint: {decoded['dewpoint']}")

    if decoded['relative_humidity']:
        conditions.append(f"Relative Humidity: {decoded['relative_humidity']}")

    if decoded['altimeter']:
        conditions.append(f"Pressure: {decoded['altimeter']}")

    summary_parts.extend(conditions)

    # Flight category
    if decoded['flight_category']:
        summary_parts.append("")
        fc = decoded['flight_category']
        summary_parts.append(f"Flight Category: {fc['category']} - {fc['description']}")

    return '\n'.join(summary_parts)


def decode_taf_period(period_str, is_main=False):
    """Decode a single TAF forecast period.

    Args:
        period_str: The TAF period string to decode
        is_main: True if this is the main forecast, False for FM/TEMPO/BECMG

    Returns:
        Dictionary with decoded period information
    """
    if not period_str:
        return None

    parts = period_str.split()
    decoded = {
        'raw': period_str,
        'type': 'MAIN' if is_main else None,
        'time': None,
        'wind': None,
        'visibility': None,
        'weather': [],
        'clouds': [],
        'probability': None,
    }

    i = 0

    # Check for period type (FM, TEMPO, BECMG, PROB)
    if not is_main and i < len(parts):
        part = parts[i]
        if part.startswith('FM'):
            decoded['type'] = 'FROM'
            # FM followed by time (e.g., FM271200)
            time_str = part[2:]
            if len(time_str) >= 4:
                day = time_str[:2]
                hour = time_str[2:4]
                minute = time_str[4:6] if len(time_str) >= 6 else '00'
                decoded['time'] = f"From day {day} at {hour}:{minute} UTC"
            i += 1
        elif part == 'TEMPO':
            decoded['type'] = 'TEMPORARY'
            i += 1
        elif part == 'BECMG':
            decoded['type'] = 'BECOMING'
            i += 1
        elif part.startswith('PROB'):
            prob_match = re.match(r'PROB(\d{2})', part)
            if prob_match:
                decoded['probability'] = f"{prob_match.group(1)}% probability"
                decoded['type'] = 'PROBABILITY'
            i += 1

    # Parse time period for TEMPO/BECMG (e.g., 2718/2724)
    if i < len(parts) and re.match(r'^\d{4}/\d{4}$', parts[i]):
        time_match = re.match(r'^(\d{2})(\d{2})/(\d{2})(\d{2})$', parts[i])
        if time_match:
            start_day, start_hour = time_match.group(1), time_match.group(2)
            end_day, end_hour = time_match.group(3), time_match.group(4)
            decoded['time'] = f"Day {start_day} {start_hour}:00 to day {end_day} {end_hour}:00 UTC"
        i += 1

    # Parse remaining elements (wind, visibility, weather, clouds)
    while i < len(parts):
        part = parts[i]

        # Wind
        if ('KT' in part or 'MPS' in part) and re.match(r'^(\d{3}|VRB)\d{2,3}', part):
            decoded['wind'] = decode_wind(part)
            i += 1
            continue

        # Visibility (US format P6SM, 6SM, etc.)
        if 'SM' in part:
            vis_str = part
            if part.startswith('P'):
                vis_str = part[1:]  # Remove P prefix for "plus"
                decoded['visibility'] = "Greater than " + decode_visibility(vis_str)
            else:
                decoded['visibility'] = decode_visibility(part)
            i += 1
            continue

        # Visibility (meters - 4 digit number)
        if part.isdigit() and len(part) == 4:
            decoded['visibility'] = decode_visibility(part)
            i += 1
            continue

        # Cloud coverage
        if any(part.startswith(code) for code in CLOUD_CODES.keys()):
            cloud = decode_clouds(part)
            if cloud:
                decoded['clouds'].append(cloud)
            i += 1
            continue

        # Weather phenomena
        if any(code in part for code in ['RA', 'SN', 'FG', 'BR', 'TS', 'SH', 'DZ', 'HZ']):
            weather = decode_weather(part)
            if weather:
                decoded['weather'].append(weather)
            i += 1
            continue

        # Special conditions
        if part == 'NSW':
            decoded['weather'].append('No significant weather')
            i += 1
            continue

        if part == 'SKC' or part == 'CLR':
            decoded['clouds'].append(CLOUD_CODES.get(part, part))
            i += 1
            continue

        if part == 'CAVOK':
            decoded['visibility'] = "Greater than 10 km (CAVOK)"
            decoded['clouds'].append("No clouds below 5,000 ft")
            i += 1
            continue

        i += 1

    return decoded


def decode_taf(taf_text):
    """Decode a complete TAF report.

    Args:
        taf_text: Raw TAF text string

    Returns:
        Dictionary with decoded TAF information
    """
    if not taf_text:
        return None

    # Split into lines and rejoin (TAFs often have line breaks)
    taf_text = ' '.join(taf_text.split())

    decoded = {
        'raw': taf_text,
        'station': None,
        'issued': None,
        'valid_from': None,
        'valid_to': None,
        'periods': [],
    }

    # Split by FM, TEMPO, BECMG, PROB to get periods
    # First, extract the header and main forecast
    pattern = r'\s+(FM\d{6}|TEMPO|BECMG|PROB\d{2})'
    parts = re.split(pattern, taf_text)

    if not parts:
        return decoded

    # Parse header (first part)
    header = parts[0].split()
    i = 0

    # Skip TAF prefix
    if i < len(header) and header[i] in ['TAF', 'TAF AMD']:
        i += 1
    if i < len(header) and header[i] == 'AMD':
        i += 1

    # Station identifier
    if i < len(header) and re.match(r'^[A-Z]{4}$', header[i]):
        decoded['station'] = header[i]
        i += 1

    # Issue time
    if i < len(header) and re.match(r'^\d{6}Z$', header[i]):
        time_str = header[i]
        day = time_str[:2]
        hour = time_str[2:4]
        minute = time_str[4:6]
        decoded['issued'] = f"Day {day} at {hour}:{minute} UTC"
        i += 1

    # Valid period
    if i < len(header) and re.match(r'^\d{4}/\d{4}$', header[i]):
        valid_match = re.match(r'^(\d{2})(\d{2})/(\d{2})(\d{2})$', header[i])
        if valid_match:
            start_day, start_hour = valid_match.group(1), valid_match.group(2)
            end_day, end_hour = valid_match.group(3), valid_match.group(4)
            decoded['valid_from'] = f"Day {start_day} at {start_hour}:00 UTC"
            decoded['valid_to'] = f"Day {end_day} at {end_hour}:00 UTC"
        i += 1

    # Main forecast (rest of header after valid period)
    main_forecast = ' '.join(header[i:])
    if main_forecast:
        main_period = decode_taf_period(main_forecast, is_main=True)
        if main_period:
            main_period['type'] = 'INITIAL'
            decoded['periods'].append(main_period)

    # Parse subsequent periods (FM, TEMPO, BECMG, PROB)
    j = 1
    while j < len(parts):
        period_type = parts[j] if j < len(parts) else ''
        period_content = parts[j + 1] if j + 1 < len(parts) else ''

        if period_type and period_content:
            full_period = period_type + ' ' + period_content.strip()
            period = decode_taf_period(full_period, is_main=False)
            if period:
                decoded['periods'].append(period)
        j += 2

    return decoded


def generate_taf_summary(decoded):
    """Generate a human-readable TAF summary.

    Args:
        decoded: Decoded TAF dictionary

    Returns:
        Formatted string summary
    """
    if not decoded:
        return "Unable to decode TAF data."

    lines = []

    if decoded['station']:
        lines.append(f"Forecast for {decoded['station']}")

    if decoded['issued']:
        lines.append(f"Issued: {decoded['issued']}")

    if decoded['valid_from'] and decoded['valid_to']:
        lines.append(f"Valid: {decoded['valid_from']} to {decoded['valid_to']}")

    lines.append("")

    for i, period in enumerate(decoded['periods']):
        period_header = period.get('type', 'FORECAST')
        if period.get('probability'):
            period_header = period['probability']
        if period.get('time') and period['type'] != 'INITIAL':
            period_header += f" - {period['time']}"

        lines.append(f"[{period_header}]")

        if period.get('wind'):
            lines.append(f"  Wind: {period['wind']}")
        if period.get('visibility'):
            lines.append(f"  Visibility: {period['visibility']}")
        if period.get('clouds'):
            lines.append(f"  Clouds: {', '.join(period['clouds'])}")
        if period.get('weather'):
            lines.append(f"  Weather: {', '.join(period['weather'])}")

        lines.append("")

    return '\n'.join(lines)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/metar', methods=['POST'])
def get_metar():
    airport_code = request.form.get('airport_code', '').strip().upper()

    if not airport_code:
        return jsonify({'error': 'Please enter an airport code'})

    if not re.match(r'^[A-Z]{3,4}$', airport_code):
        return jsonify({'error': 'Invalid airport code. Please enter a 3 or 4 letter ICAO code (e.g., KJFK, EGLL)'})

    # Fetch METAR data
    metar_text = fetch_metar(airport_code)

    if not metar_text:
        return jsonify({'error': f'No METAR data found for {airport_code}. Please check the airport code.'})

    # Decode METAR
    decoded = decode_metar(metar_text)

    # Generate summary
    summary = generate_summary(decoded)

    # Fetch and decode TAF data
    taf_text = fetch_taf(airport_code)
    taf_decoded = None
    taf_summary = None

    if taf_text:
        taf_decoded = decode_taf(taf_text)
        taf_summary = generate_taf_summary(taf_decoded)

    return jsonify({
        'success': True,
        'raw_metar': metar_text,
        'decoded': decoded,
        'summary': summary,
        'raw_taf': taf_text,
        'taf_decoded': taf_decoded,
        'taf_summary': taf_summary
    })


if __name__ == '__main__':
    app.run(debug=True)
