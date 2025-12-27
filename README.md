# METAR Reader

A Flask web application that fetches and decodes METAR aviation weather reports into plain English.

## Features

- **Real-time METAR data** from Aviation Weather Center API
- **Full decoding** of METAR components:
  - Wind direction, speed, and gusts
  - Visibility (miles and kilometers)
  - Cloud coverage and heights
  - Weather phenomena (rain, snow, fog, etc.)
  - Temperature and dewpoint (Celsius and Fahrenheit)
  - Altimeter/pressure settings
  - Remarks section (AO2, SLP, precipitation timing, etc.)
- **Flight category** determination (VFR/MVFR/IFR/LIFR)
- **Modern responsive UI** with dark theme

## Installation

```bash
# Clone or download the project
cd metar-reader

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

Open http://127.0.0.1:5000 in your browser.

## Usage

1. Enter a 3 or 4 letter ICAO airport code (e.g., KJFK, EGLL, KHIO)
2. Click "Get Weather" or press Enter
3. View the decoded weather report

### Example Airport Codes

| Code | Airport |
|------|---------|
| KJFK | New York JFK |
| KLAX | Los Angeles |
| KORD | Chicago O'Hare |
| EGLL | London Heathrow |
| LFPG | Paris CDG |
| VIDP | Delhi |

## API Endpoint

### POST /metar

Fetch and decode METAR for an airport.

**Request:**
```bash
curl -X POST -d "airport_code=KJFK" http://127.0.0.1:5000/metar
```

**Response:**
```json
{
  "success": true,
  "raw_metar": "METAR KJFK 271951Z 36009KT 10SM FEW017 M01/M05 A3014 RMK AO2",
  "decoded": {
    "station": "KJFK",
    "time": "Day 27 at 19:51 UTC",
    "wind": "From North (360°) at 9 knots",
    "visibility": "10 miles or more (excellent visibility)",
    "clouds": ["Few clouds at 1,700 feet"],
    "temperature": "-1°C (30°F)",
    "dewpoint": "-5°C (23°F)",
    "altimeter": "30.14 inHg (1021 hPa)",
    "remarks": "AO2",
    "remarks_decoded": ["Automated station with precipitation sensor"],
    "flight_category": {
      "category": "VFR",
      "description": "Visual Flight Rules - Good flying conditions"
    }
  },
  "summary": "Weather report for KJFK..."
}
```

## METAR Codes Reference

### Wind
| Code | Meaning |
|------|---------|
| 36009KT | From 360° at 9 knots |
| 18015G25KT | From 180° at 15 knots, gusting 25 |
| VRB05KT | Variable direction at 5 knots |
| 00000KT | Calm |

### Visibility
| Code | Meaning |
|------|---------|
| 10SM | 10 statute miles |
| 1/2SM | Half mile |
| 9999 | 10 km or more (international) |

### Clouds
| Code | Meaning |
|------|---------|
| SKC | Sky clear |
| FEW020 | Few clouds at 2,000 ft |
| SCT040 | Scattered at 4,000 ft |
| BKN080 | Broken at 8,000 ft |
| OVC100 | Overcast at 10,000 ft |

### Weather
| Code | Meaning |
|------|---------|
| RA | Rain |
| SN | Snow |
| FG | Fog |
| BR | Mist |
| TS | Thunderstorm |
| -RA | Light rain |
| +SN | Heavy snow |

### Flight Categories
| Category | Ceiling | Visibility |
|----------|---------|------------|
| VFR | > 3,000 ft | > 5 miles |
| MVFR | 1,000-3,000 ft | 3-5 miles |
| IFR | 500-1,000 ft | 1-3 miles |
| LIFR | < 500 ft | < 1 mile |

## Testing

```bash
# Run all tests
pytest test_app.py -v

# Run with coverage report
pytest test_app.py --cov=app --cov-report=term-missing
```

**Test Coverage:** 99% (155 tests)

## Project Structure

```
metar-reader/
├── app.py              # Flask application and METAR decoder
├── test_app.py         # Unit tests (155 tests)
├── requirements.txt    # Python dependencies
├── README.md           # This file
└── templates/
    └── index.html      # Web interface
```

## Dependencies

- Flask >= 2.0.0
- Requests >= 2.25.0
- pytest >= 7.0.0 (dev)
- pytest-cov >= 4.0.0 (dev)

## Data Source

METAR data is fetched from the [Aviation Weather Center](https://aviationweather.gov) API.

## License

MIT License
