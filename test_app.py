"""
Comprehensive unit tests for METAR Reader application.

Tests cover:
    - Wind decoding (calm, gusts, variable, MPS/KT)
    - Visibility decoding (miles, meters, fractions)
    - Weather phenomena (rain, snow, fog, etc.)
    - Cloud coverage (FEW, SCT, BKN, OVC)
    - Temperature/dewpoint (positive, negative)
    - Altimeter settings (US and international)
    - Remarks decoding (AO2, SLP, precipitation, etc.)
    - Flight category determination (VFR/MVFR/IFR/LIFR)
    - Flask routes (index and METAR endpoint)

Run with: pytest test_app.py -v
Coverage: pytest test_app.py --cov=app --cov-report=term-missing
"""

import pytest
from unittest.mock import patch, Mock
from app import (
    app,
    decode_wind,
    decode_visibility,
    decode_weather,
    decode_clouds,
    decode_temp_dewpoint,
    decode_altimeter,
    decode_remarks,
    decode_metar,
    get_cardinal_direction,
    determine_flight_category,
    fetch_metar,
    generate_summary,
)


# =============================================================================
# Flask Test Client Fixture
# =============================================================================

@pytest.fixture
def client():
    """Create a test client for the Flask application."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


# =============================================================================
# Wind Decoder Tests
# =============================================================================

class TestDecodeWind:
    """Tests for decode_wind function."""

    def test_calm_wind(self):
        """Test calm wind (00000KT)."""
        result = decode_wind("00000KT")
        assert result == "Calm"

    def test_standard_wind(self):
        """Test standard wind format."""
        result = decode_wind("27015KT")
        assert "West" in result
        assert "270°" in result
        assert "15 knots" in result

    def test_wind_with_gusts(self):
        """Test wind with gusts."""
        result = decode_wind("18020G35KT")
        assert "South" in result
        assert "180°" in result
        assert "20 knots" in result
        assert "gusting to 35" in result

    def test_variable_wind_direction(self):
        """Test variable wind direction (VRB)."""
        result = decode_wind("VRB05KT")
        assert "Variable direction" in result
        assert "5 knots" in result

    def test_wind_mps(self):
        """Test wind in meters per second."""
        result = decode_wind("36010MPS")
        assert "North" in result
        assert "10 meters per second" in result

    def test_strong_wind(self):
        """Test strong wind (3-digit speed)."""
        result = decode_wind("270100KT")
        assert "100 knots" in result

    def test_north_wind(self):
        """Test north wind (360 degrees)."""
        result = decode_wind("36009KT")
        assert "North" in result
        assert "360°" in result
        assert "9 knots" in result

    def test_east_wind(self):
        """Test east wind (090 degrees)."""
        result = decode_wind("09012KT")
        assert "East" in result
        assert "90°" in result

    def test_none_input(self):
        """Test None input returns None."""
        assert decode_wind(None) is None

    def test_empty_string(self):
        """Test empty string returns None."""
        assert decode_wind("") is None

    def test_invalid_format(self):
        """Test invalid format returns None."""
        assert decode_wind("INVALID") is None


# =============================================================================
# Cardinal Direction Tests
# =============================================================================

class TestGetCardinalDirection:
    """Tests for get_cardinal_direction function."""

    def test_north(self):
        assert get_cardinal_direction(0) == "North"
        assert get_cardinal_direction(360) == "North"

    def test_east(self):
        assert get_cardinal_direction(90) == "East"

    def test_south(self):
        assert get_cardinal_direction(180) == "South"

    def test_west(self):
        assert get_cardinal_direction(270) == "West"

    def test_northeast(self):
        assert get_cardinal_direction(45) == "Northeast"

    def test_southeast(self):
        assert get_cardinal_direction(135) == "Southeast"

    def test_southwest(self):
        assert get_cardinal_direction(225) == "Southwest"

    def test_northwest(self):
        assert get_cardinal_direction(315) == "Northwest"


# =============================================================================
# Visibility Decoder Tests
# =============================================================================

class TestDecodeVisibility:
    """Tests for decode_visibility function."""

    def test_ten_miles(self):
        """Test 10 statute miles visibility."""
        result = decode_visibility("10SM")
        assert "10 miles" in result
        assert "excellent" in result.lower()

    def test_good_visibility(self):
        """Test good visibility (6+ miles)."""
        result = decode_visibility("7SM")
        assert "7" in result
        assert "good" in result.lower()

    def test_moderate_visibility(self):
        """Test moderate visibility (3-6 miles)."""
        result = decode_visibility("5SM")
        assert "5" in result
        assert "moderate" in result.lower()

    def test_poor_visibility(self):
        """Test poor visibility (1-3 miles)."""
        result = decode_visibility("2SM")
        assert "2" in result
        assert "poor" in result.lower()

    def test_very_poor_visibility(self):
        """Test very poor visibility (<1 mile)."""
        result = decode_visibility("1/2SM")
        assert "0.5" in result
        assert "very poor" in result.lower()

    def test_fraction_visibility(self):
        """Test fractional visibility."""
        result = decode_visibility("3/4SM")
        assert "0.75" in result

    def test_mixed_fraction_visibility(self):
        """Test mixed number visibility (e.g., 1 1/2)."""
        result = decode_visibility("1 1/2SM")
        assert "1.5" in result

    def test_meters_visibility(self):
        """Test visibility in meters."""
        result = decode_visibility("9999")
        assert "10 km" in result
        assert "excellent" in result.lower()

    def test_low_meters_visibility(self):
        """Test low visibility in meters."""
        result = decode_visibility("0800")
        assert "800 meters" in result

    def test_none_input(self):
        """Test None input returns None."""
        assert decode_visibility(None) is None


# =============================================================================
# Weather Phenomena Decoder Tests
# =============================================================================

class TestDecodeWeather:
    """Tests for decode_weather function."""

    def test_rain(self):
        """Test rain."""
        result = decode_weather("RA")
        assert "Rain" in result

    def test_light_rain(self):
        """Test light rain."""
        result = decode_weather("-RA")
        assert "Light" in result
        assert "Rain" in result

    def test_heavy_rain(self):
        """Test heavy rain."""
        result = decode_weather("+RA")
        assert "Heavy" in result
        assert "Rain" in result

    def test_thunderstorm_rain(self):
        """Test thunderstorm with rain."""
        result = decode_weather("TSRA")
        assert "Thunderstorm" in result
        assert "Rain" in result

    def test_snow(self):
        """Test snow."""
        result = decode_weather("SN")
        assert "Snow" in result

    def test_freezing_rain(self):
        """Test freezing rain."""
        result = decode_weather("FZRA")
        assert "Freezing" in result
        assert "Rain" in result

    def test_fog(self):
        """Test fog."""
        result = decode_weather("FG")
        assert "Fog" in result

    def test_mist(self):
        """Test mist."""
        result = decode_weather("BR")
        assert "Mist" in result

    def test_haze(self):
        """Test haze."""
        result = decode_weather("HZ")
        assert "Haze" in result

    def test_drizzle(self):
        """Test drizzle."""
        result = decode_weather("DZ")
        assert "Drizzle" in result

    def test_showers(self):
        """Test rain showers."""
        result = decode_weather("SHRA")
        assert "Showers" in result
        assert "Rain" in result

    def test_vicinity(self):
        """Test weather in vicinity."""
        result = decode_weather("VCTS")
        assert "vicinity" in result.lower()
        assert "Thunderstorm" in result

    def test_hail(self):
        """Test hail."""
        result = decode_weather("GR")
        assert "Hail" in result

    def test_none_input(self):
        """Test None input returns None."""
        assert decode_weather(None) is None


# =============================================================================
# Cloud Decoder Tests
# =============================================================================

class TestDecodeClouds:
    """Tests for decode_clouds function."""

    def test_sky_clear(self):
        """Test sky clear."""
        result = decode_clouds("SKC")
        assert "clear" in result.lower()

    def test_clear(self):
        """Test CLR."""
        result = decode_clouds("CLR")
        assert "Clear" in result

    def test_few_clouds(self):
        """Test few clouds."""
        result = decode_clouds("FEW020")
        assert "Few" in result
        assert "2,000 feet" in result

    def test_scattered_clouds(self):
        """Test scattered clouds."""
        result = decode_clouds("SCT040")
        assert "Scattered" in result
        assert "4,000 feet" in result

    def test_broken_clouds(self):
        """Test broken clouds."""
        result = decode_clouds("BKN080")
        assert "Broken" in result
        assert "8,000 feet" in result

    def test_overcast(self):
        """Test overcast."""
        result = decode_clouds("OVC100")
        assert "Overcast" in result
        assert "10,000 feet" in result

    def test_vertical_visibility(self):
        """Test vertical visibility (obscured sky)."""
        result = decode_clouds("VV005")
        assert "Vertical visibility" in result or "obscured" in result.lower()

    def test_cumulonimbus(self):
        """Test cumulonimbus clouds."""
        result = decode_clouds("BKN040CB")
        assert "Broken" in result
        assert "4,000 feet" in result
        assert "Cumulonimbus" in result or "thunderstorm" in result.lower()

    def test_towering_cumulus(self):
        """Test towering cumulus clouds."""
        result = decode_clouds("SCT050TCU")
        assert "Scattered" in result
        assert "Towering cumulus" in result

    def test_no_significant_clouds(self):
        """Test no significant clouds."""
        result = decode_clouds("NSC")
        assert "No significant" in result or "NSC" in result

    def test_none_input(self):
        """Test None input returns None."""
        assert decode_clouds(None) is None


# =============================================================================
# Temperature/Dewpoint Decoder Tests
# =============================================================================

class TestDecodeTempDewpoint:
    """Tests for decode_temp_dewpoint function."""

    def test_positive_temps(self):
        """Test positive temperature and dewpoint."""
        temp, dew = decode_temp_dewpoint("25/20")
        assert "25°C" in temp
        assert "77°F" in temp
        assert "20°C" in dew
        assert "68°F" in dew

    def test_negative_temp(self):
        """Test negative temperature (M prefix)."""
        temp, dew = decode_temp_dewpoint("M05/M10")
        assert "-5°C" in temp
        assert "23°F" in temp
        assert "-10°C" in dew
        assert "14°F" in dew

    def test_mixed_temps(self):
        """Test mixed positive/negative temps."""
        temp, dew = decode_temp_dewpoint("02/M01")
        assert "2°C" in temp
        assert "-1°C" in dew

    def test_zero_temp(self):
        """Test zero temperature."""
        temp, dew = decode_temp_dewpoint("00/M02")
        assert "0°C" in temp
        assert "32°F" in temp

    def test_none_input(self):
        """Test None input returns None."""
        temp, dew = decode_temp_dewpoint(None)
        assert temp is None
        assert dew is None

    def test_invalid_format(self):
        """Test invalid format returns None."""
        temp, dew = decode_temp_dewpoint("INVALID")
        assert temp is None
        assert dew is None


# =============================================================================
# Altimeter Decoder Tests
# =============================================================================

class TestDecodeAltimeter:
    """Tests for decode_altimeter function."""

    def test_us_format(self):
        """Test US format (inches of mercury)."""
        result = decode_altimeter("A3014")
        assert "30.14" in result
        assert "inHg" in result
        assert "hPa" in result

    def test_international_format(self):
        """Test international format (hectopascals)."""
        result = decode_altimeter("Q1013")
        assert "1013" in result
        assert "hPa" in result
        assert "inHg" in result

    def test_high_pressure(self):
        """Test high pressure."""
        result = decode_altimeter("A3050")
        assert "30.50" in result

    def test_low_pressure(self):
        """Test low pressure."""
        result = decode_altimeter("A2950")
        assert "29.50" in result

    def test_none_input(self):
        """Test None input returns None."""
        assert decode_altimeter(None) is None

    def test_invalid_format(self):
        """Test invalid format returns None."""
        assert decode_altimeter("INVALID") is None


# =============================================================================
# Full METAR Decoder Tests
# =============================================================================

class TestDecodeMetar:
    """Tests for decode_metar function - full METAR parsing."""

    def test_standard_metar(self):
        """Test standard METAR format."""
        metar = "METAR KJFK 271951Z 36009KT 10SM FEW017 BKN036 OVC050 M01/M05 A3014 RMK AO2"
        result = decode_metar(metar)

        assert result["station"] == "KJFK"
        assert "27" in result["time"]
        assert "19:51" in result["time"]
        assert "North" in result["wind"]
        assert "9 knots" in result["wind"]
        assert "10 miles" in result["visibility"]
        assert len(result["clouds"]) == 3
        assert "-1°C" in result["temperature"]
        assert "-5°C" in result["dewpoint"]
        assert "30.14" in result["altimeter"]
        assert "AO2" in result["remarks"]

    def test_metar_with_weather(self):
        """Test METAR with weather phenomena."""
        metar = "METAR KORD 271951Z 18015G25KT 3SM -RA BR BKN010 OVC020 05/04 A2990"
        result = decode_metar(metar)

        assert result["station"] == "KORD"
        assert "South" in result["wind"]
        assert "gusting" in result["wind"]
        assert len(result["weather"]) >= 1

    def test_metar_calm_wind(self):
        """Test METAR with calm wind."""
        metar = "METAR KHIO 271953Z 00000KT 10SM FEW040 05/03 A3032"
        result = decode_metar(metar)

        assert result["station"] == "KHIO"
        assert result["wind"] == "Calm"

    def test_metar_international(self):
        """Test international METAR format."""
        metar = "METAR EGLL 272020Z 06011KT 9999 BKN010 OVC020 07/05 Q1035"
        result = decode_metar(metar)

        assert result["station"] == "EGLL"
        assert "East" in result["wind"]
        assert "10 km" in result["visibility"]
        assert "1035" in result["altimeter"]

    def test_metar_with_speci(self):
        """Test SPECI (special) report."""
        metar = "SPECI KLAX 271800Z 25010KT 10SM SKC 18/08 A3002"
        result = decode_metar(metar)

        assert result["station"] == "KLAX"
        assert "18°C" in result["temperature"]

    def test_metar_variable_wind(self):
        """Test METAR with variable wind direction."""
        metar = "METAR KSFO 271956Z 29008KT 260V320 10SM FEW020 15/10 A3010"
        result = decode_metar(metar)

        assert "varying" in result["wind"].lower()
        assert "260" in result["wind"]
        assert "320" in result["wind"]

    def test_none_input(self):
        """Test None input returns None."""
        assert decode_metar(None) is None

    def test_empty_string(self):
        """Test empty string returns None."""
        assert decode_metar("") is None


# =============================================================================
# Flight Category Tests
# =============================================================================

class TestDetermineFlightCategory:
    """Tests for determine_flight_category function."""

    def test_vfr_conditions(self):
        """Test VFR conditions."""
        decoded = {
            "visibility": "10 miles (excellent visibility)",
            "clouds": ["Few clouds at 5,000 feet"],
            "weather": []
        }
        result = determine_flight_category(decoded)
        assert result["category"] == "VFR"

    def test_mvfr_ceiling(self):
        """Test MVFR due to ceiling."""
        decoded = {
            "visibility": "5 miles",
            "clouds": ["Broken clouds at 2,500 feet"],
            "weather": []
        }
        result = determine_flight_category(decoded)
        assert result["category"] == "MVFR"

    def test_ifr_low_ceiling(self):
        """Test IFR due to low ceiling."""
        decoded = {
            "visibility": "3 miles",
            "clouds": ["Overcast at 800 feet"],
            "weather": []
        }
        result = determine_flight_category(decoded)
        assert result["category"] == "IFR"

    def test_lifr_very_low_ceiling(self):
        """Test LIFR due to very low ceiling."""
        decoded = {
            "visibility": "1 mile",
            "clouds": ["Overcast at 400 feet"],
            "weather": []
        }
        result = determine_flight_category(decoded)
        assert result["category"] == "LIFR"

    def test_ifr_with_fog(self):
        """Test IFR due to fog."""
        decoded = {
            "visibility": "1/2 mile",
            "clouds": ["Few clouds at 1,000 feet"],
            "weather": ["Fog"]
        }
        result = determine_flight_category(decoded)
        assert result["category"] == "IFR"

    def test_ifr_with_thunderstorm(self):
        """Test IFR due to thunderstorm."""
        decoded = {
            "visibility": "5 miles",
            "clouds": ["Broken clouds at 3,000 feet"],
            "weather": ["Thunderstorm Rain"]
        }
        result = determine_flight_category(decoded)
        assert result["category"] == "IFR"


# =============================================================================
# Fetch METAR Tests (Mocked)
# =============================================================================

class TestFetchMetar:
    """Tests for fetch_metar function with mocked responses."""

    @patch('app.requests.get')
    def test_successful_fetch(self, mock_get):
        """Test successful METAR fetch."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "METAR KJFK 271951Z 36009KT 10SM FEW017 A3014"
        mock_get.return_value = mock_response

        result = fetch_metar("KJFK")
        assert result is not None
        assert "KJFK" in result

    @patch('app.requests.get')
    def test_empty_response(self, mock_get):
        """Test empty response returns None."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = ""
        mock_get.return_value = mock_response

        result = fetch_metar("XXXX")
        assert result is None

    @patch('app.requests.get')
    def test_api_error(self, mock_get):
        """Test API error returns None."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        result = fetch_metar("KJFK")
        assert result is None

    @patch('app.requests.get')
    def test_request_exception(self, mock_get):
        """Test request exception returns None."""
        import requests
        mock_get.side_effect = requests.RequestException("Connection error")

        result = fetch_metar("KJFK")
        assert result is None


# =============================================================================
# Generate Summary Tests
# =============================================================================

class TestGenerateSummary:
    """Tests for generate_summary function."""

    def test_full_summary(self):
        """Test summary generation with full data."""
        decoded = {
            "station": "KJFK",
            "time": "Day 27 at 19:51 UTC",
            "temperature": "5°C (41°F)",
            "wind": "From North at 10 knots",
            "visibility": "10 miles (excellent)",
            "clouds": ["Few clouds at 3,000 feet"],
            "weather": ["Light Rain"],
            "dewpoint": "3°C (37°F)",
            "altimeter": "30.14 inHg",
            "flight_category": {"category": "VFR", "description": "Good conditions"},
            "remarks": "AO2"
        }

        result = generate_summary(decoded)

        assert "KJFK" in result
        assert "5°C" in result
        assert "North" in result
        assert "10 miles" in result
        assert "VFR" in result

    def test_none_input(self):
        """Test None input."""
        result = generate_summary(None)
        assert "Unable to decode" in result


# =============================================================================
# Real-World METAR Examples
# =============================================================================

class TestRealWorldMetars:
    """Tests using real-world METAR examples."""

    def test_khio_metar(self):
        """Test KHIO (Hillsboro, OR) METAR."""
        metar = "METAR KHIO 271953Z 00000KT 10SM FEW040 FEW050 OVC060 05/03 A3032 RMK AO2 RAE38 SLP268 P0000 T00500033"
        result = decode_metar(metar)

        assert result["station"] == "KHIO"
        assert result["wind"] == "Calm"
        assert "10 miles" in result["visibility"]
        assert "5°C" in result["temperature"]
        assert "3°C" in result["dewpoint"]

    def test_kjfk_metar(self):
        """Test KJFK (JFK Airport) METAR."""
        metar = "METAR KJFK 271951Z 36009KT 10SM FEW017 BKN036 OVC050 M01/M05 A3014 RMK AO2 SLP204 T10111050"
        result = decode_metar(metar)

        assert result["station"] == "KJFK"
        assert "North" in result["wind"]
        assert "-1°C" in result["temperature"]

    def test_egll_metar(self):
        """Test EGLL (London Heathrow) METAR."""
        metar = "METAR EGLL 272020Z 06011KT 9999 BKN010 OVC020 07/05 Q1035"
        result = decode_metar(metar)

        assert result["station"] == "EGLL"
        assert "East" in result["wind"]
        assert "1035" in result["altimeter"]

    def test_severe_weather_metar(self):
        """Test METAR with severe weather."""
        metar = "METAR KORD 271856Z 23025G40KT 1/2SM +TSRA FG BKN005 OVC010CB 18/17 A2965"
        result = decode_metar(metar)

        assert result["station"] == "KORD"
        assert "gusting" in result["wind"].lower()
        assert "40" in result["wind"]
        assert len(result["weather"]) >= 1
        assert any("CB" in cloud or "Cumulonimbus" in cloud for cloud in result["clouds"])


# =============================================================================
# Edge Cases
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_three_digit_wind_speed(self):
        """Test three-digit wind speed."""
        result = decode_wind("270105KT")
        assert "105 knots" in result

    def test_minimum_visibility(self):
        """Test minimum visibility."""
        result = decode_visibility("0SM")
        assert "0" in result

    def test_maximum_cloud_height(self):
        """Test high cloud ceiling."""
        result = decode_clouds("FEW250")
        assert "25,000 feet" in result

    def test_freezing_temperature(self):
        """Test exactly freezing temperature."""
        temp, _ = decode_temp_dewpoint("00/M02")
        assert "0°C" in temp
        assert "32°F" in temp

    def test_very_negative_temperature(self):
        """Test very cold temperature."""
        temp, dew = decode_temp_dewpoint("M40/M45")
        assert "-40°C" in temp
        assert "-45°C" in dew

    def test_unknown_visibility_format(self):
        """Test unknown visibility format returns as-is."""
        result = decode_visibility("UNKNOWN")
        assert result == "UNKNOWN"

    def test_invalid_cloud_format(self):
        """Test invalid cloud format returns None."""
        result = decode_clouds("INVALID")
        assert result is None

    def test_temp_dewpoint_too_many_parts(self):
        """Test temp/dewpoint with too many parts."""
        temp, dew = decode_temp_dewpoint("05/03/01")
        assert temp is None
        assert dew is None

    def test_temp_dewpoint_empty_parts(self):
        """Test temp/dewpoint with empty parts."""
        temp, dew = decode_temp_dewpoint("/03")
        # First part is empty, should handle gracefully
        assert temp is None or dew is not None

    def test_metar_with_auto(self):
        """Test METAR with AUTO indicator."""
        metar = "METAR KJFK 271951Z AUTO 36009KT 10SM FEW017 05/03 A3014"
        result = decode_metar(metar)
        assert result["station"] == "KJFK"
        assert result["wind"] is not None

    def test_metar_with_split_visibility(self):
        """Test METAR with visibility split across parts (e.g., 1/2 SM)."""
        metar = "METAR KJFK 271951Z 36009KT 1/2SM FEW017 05/03 A3014"
        result = decode_metar(metar)
        assert result["visibility"] is not None
        assert "0.5" in result["visibility"]

    def test_metar_with_space_split_visibility(self):
        """Test METAR with visibility fraction and SM separated by space."""
        metar = "METAR KJFK 271951Z 36009KT 1/4 SM FEW017 05/03 A3014"
        result = decode_metar(metar)
        assert result["visibility"] is not None

    def test_metar_visibility_break_on_non_vis(self):
        """Test METAR visibility parsing breaks correctly."""
        metar = "METAR KJFK 271951Z 36009KT FEW017 05/03 A3014"
        result = decode_metar(metar)
        # No visibility in this METAR, but should still parse correctly
        assert result["station"] == "KJFK"

    def test_metar_visibility_fraction_no_sm(self):
        """Test visibility parsing breaks when fraction not followed by SM."""
        # This should trigger the else: break path when '/' is found but next part isn't SM
        metar = "METAR KJFK 271951Z 36009KT 1/2 BKN020 05/03 A3014"
        result = decode_metar(metar)
        # Should still parse the rest correctly
        assert result["station"] == "KJFK"
        assert len(result["clouds"]) > 0


# =============================================================================
# Remarks Decoder Tests
# =============================================================================

class TestDecodeRemarks:
    """Tests for decode_remarks function."""

    def test_ao1_station(self):
        """Test AO1 automated station type."""
        result = decode_remarks("AO1")
        assert any("without precipitation sensor" in r for r in result)

    def test_ao2_station(self):
        """Test AO2 automated station type."""
        result = decode_remarks("AO2")
        assert any("with precipitation sensor" in r for r in result)

    def test_sea_level_pressure_high(self):
        """Test sea level pressure (high)."""
        result = decode_remarks("SLP273")
        assert any("1027.3" in r for r in result)

    def test_sea_level_pressure_low(self):
        """Test sea level pressure (low)."""
        result = decode_remarks("SLP987")
        assert any("998.7" in r for r in result)

    def test_precise_temperature_positive(self):
        """Test precise temperature (positive values)."""
        result = decode_remarks("T00610039")
        assert any("6.1°C" in r and "3.9°C" in r for r in result)

    def test_precise_temperature_negative(self):
        """Test precise temperature (negative values)."""
        result = decode_remarks("T10171050")
        assert any("-1.7°C" in r and "-5.0°C" in r for r in result)

    def test_precipitation_trace(self):
        """Test trace precipitation."""
        result = decode_remarks("P0000")
        assert any("Trace" in r or "none" in r.lower() for r in result)

    def test_precipitation_amount(self):
        """Test precipitation amount."""
        result = decode_remarks("P0025")
        assert any("0.25" in r for r in result)

    def test_rain_began_ended(self):
        """Test rain began and ended."""
        result = decode_remarks("RAB08E25")
        assert any("Rain" in r and "began" in r and ":08" in r for r in result)
        assert any("ended" in r and ":25" in r for r in result)

    def test_snow_began(self):
        """Test snow began."""
        result = decode_remarks("SNB15")
        assert any("Snow" in r and "began" in r and ":15" in r for r in result)

    def test_maintenance_indicator(self):
        """Test station needs maintenance."""
        result = decode_remarks("$")
        assert any("maintenance" in r.lower() for r in result)

    def test_peak_wind(self):
        """Test peak wind."""
        result = decode_remarks("PK WND 27035/1520")
        assert any("Peak wind" in r and "270" in r and "35" in r for r in result)

    def test_wind_shift(self):
        """Test wind shift."""
        result = decode_remarks("WSHFT 1530")
        assert any("Wind shift" in r for r in result)

    def test_lightning_cg(self):
        """Test cloud-to-ground lightning."""
        result = decode_remarks("LTGCG")
        assert any("Lightning" in r and "cloud-to-ground" in r for r in result)

    def test_lightning_ic(self):
        """Test in-cloud lightning."""
        result = decode_remarks("LTGIC")
        assert any("Lightning" in r and "in-cloud" in r for r in result)

    def test_virga(self):
        """Test virga."""
        result = decode_remarks("VIRGA")
        assert any("Virga" in r for r in result)

    def test_pressure_rising_rapidly(self):
        """Test pressure rising rapidly."""
        result = decode_remarks("PRESRR")
        assert any("rising rapidly" in r.lower() for r in result)

    def test_pressure_falling_rapidly(self):
        """Test pressure falling rapidly."""
        result = decode_remarks("PRESFR")
        assert any("falling rapidly" in r.lower() for r in result)

    def test_no_significant_change(self):
        """Test no significant change."""
        result = decode_remarks("NOSIG")
        assert any("No significant" in r for r in result)

    def test_frontal_passage(self):
        """Test frontal passage."""
        result = decode_remarks("FROPA")
        assert any("Frontal passage" in r for r in result)

    def test_ceiling_variable(self):
        """Test ceiling variable."""
        result = decode_remarks("CIG 005V010")
        assert any("Ceiling variable" in r and "500" in r and "1,000" in r for r in result)

    def test_multiple_remarks(self):
        """Test multiple remarks combined."""
        result = decode_remarks("AO2 SLP273 T00610039 P0000")
        assert len(result) >= 3
        assert any("precipitation sensor" in r for r in result)
        assert any("1027.3" in r for r in result)
        assert any("6.1°C" in r for r in result)

    def test_real_world_remarks(self):
        """Test real-world remarks from KHIO."""
        result = decode_remarks("AO2 RAB08E25 SLP268 P0000 T00500033")
        assert len(result) >= 4
        assert any("precipitation sensor" in r for r in result)
        assert any("Rain" in r and "began" in r for r in result)
        assert any("Sea level pressure" in r for r in result)
        assert any("Precipitation" in r for r in result)

    def test_none_input(self):
        """Test None input returns None."""
        assert decode_remarks(None) is None

    def test_empty_string(self):
        """Test empty string returns None."""
        assert decode_remarks("") is None

    def test_unrecognized_remarks(self):
        """Test unrecognized remarks don't crash."""
        result = decode_remarks("UNKNOWN123 RANDOM")
        # Should return None or empty list for unrecognized codes
        assert result is None or len(result) == 0

    def test_lightning_no_type(self):
        """Test lightning without specific type."""
        result = decode_remarks("LTG")
        assert any("Lightning" in r for r in result)

    def test_thunderstorm_location(self):
        """Test thunderstorm with location."""
        result = decode_remarks("TS NW")
        assert any("Thunderstorm" in r and "NW" in r for r in result)

    def test_peak_wind_short_time(self):
        """Test peak wind with 2-digit time (minutes only)."""
        result = decode_remarks("PK WND 27035/35")
        assert any("Peak wind" in r and "270" in r and "35" in r for r in result)

    def test_wind_shift_short_time(self):
        """Test wind shift with 2-digit time (minutes only)."""
        result = decode_remarks("WSHFT 30")
        assert any("Wind shift" in r for r in result)

    def test_variable_visibility(self):
        """Test variable visibility remark."""
        result = decode_remarks("VIS 1/2V2")
        assert any("Variable visibility" in r for r in result)

    def test_slp_invalid_value(self):
        """Test SLP with invalid (non-numeric) value."""
        result = decode_remarks("SLPXXX")
        # Should not crash, may return None or skip the invalid code
        assert result is None or isinstance(result, list)

    def test_temperature_invalid_format(self):
        """Test precise temperature with invalid format."""
        result = decode_remarks("TXXXXXXXX")
        # Should not crash, may return None or skip the invalid code
        assert result is None or isinstance(result, list)

    def test_drizzle_ended(self):
        """Test drizzle ended."""
        result = decode_remarks("DZE45")
        assert any("Drizzle" in r and "ended" in r for r in result)

    def test_fog_began(self):
        """Test fog began."""
        result = decode_remarks("FGB30")
        assert any("Fog" in r and "began" in r for r in result)

    def test_thunderstorm_began_ended(self):
        """Test thunderstorm began and ended."""
        result = decode_remarks("TSB15E45")
        assert any("Thunderstorm" in r and "began" in r for r in result)


# =============================================================================
# Flask Route Tests - Index
# =============================================================================

class TestIndexRoute:
    """Tests for the index route (/)."""

    def test_index_returns_200(self, client):
        """Test that index page returns 200 status."""
        response = client.get('/')
        assert response.status_code == 200

    def test_index_contains_title(self, client):
        """Test that index page contains the app title."""
        response = client.get('/')
        assert b'METAR Reader' in response.data

    def test_index_contains_form(self, client):
        """Test that index page contains the search form."""
        response = client.get('/')
        assert b'airport_code' in response.data
        assert b'form' in response.data

    def test_index_contains_example_airports(self, client):
        """Test that index page contains example airport codes."""
        response = client.get('/')
        assert b'KJFK' in response.data
        assert b'EGLL' in response.data


# =============================================================================
# Flask Route Tests - METAR Endpoint
# =============================================================================

class TestMetarEndpoint:
    """Tests for the /metar POST endpoint."""

    def test_metar_missing_airport_code(self, client):
        """Test error when airport code is missing."""
        response = client.post('/metar', data={})
        json_data = response.get_json()

        assert 'error' in json_data
        assert 'enter an airport code' in json_data['error'].lower()

    def test_metar_empty_airport_code(self, client):
        """Test error when airport code is empty."""
        response = client.post('/metar', data={'airport_code': ''})
        json_data = response.get_json()

        assert 'error' in json_data

    def test_metar_invalid_airport_code_format(self, client):
        """Test error when airport code format is invalid."""
        response = client.post('/metar', data={'airport_code': 'TOOLONG123'})
        json_data = response.get_json()

        assert 'error' in json_data
        assert 'invalid' in json_data['error'].lower()

    def test_metar_invalid_airport_code_numbers(self, client):
        """Test error when airport code contains only numbers."""
        response = client.post('/metar', data={'airport_code': '1234'})
        json_data = response.get_json()

        assert 'error' in json_data

    @patch('app.fetch_metar')
    def test_metar_airport_not_found(self, mock_fetch, client):
        """Test error when airport is not found."""
        mock_fetch.return_value = None

        response = client.post('/metar', data={'airport_code': 'XXXX'})
        json_data = response.get_json()

        assert 'error' in json_data
        assert 'No METAR data found' in json_data['error']

    @patch('app.fetch_metar')
    def test_metar_successful_request(self, mock_fetch, client):
        """Test successful METAR request."""
        mock_fetch.return_value = "METAR KJFK 271951Z 36009KT 10SM FEW017 M01/M05 A3014"

        response = client.post('/metar', data={'airport_code': 'KJFK'})
        json_data = response.get_json()

        assert json_data['success'] is True
        assert 'raw_metar' in json_data
        assert 'decoded' in json_data
        assert 'summary' in json_data
        assert 'KJFK' in json_data['raw_metar']

    @patch('app.fetch_metar')
    def test_metar_lowercase_airport_code(self, mock_fetch, client):
        """Test that lowercase airport codes are converted to uppercase."""
        mock_fetch.return_value = "METAR KJFK 271951Z 36009KT 10SM FEW017 M01/M05 A3014"

        response = client.post('/metar', data={'airport_code': 'kjfk'})
        json_data = response.get_json()

        assert json_data['success'] is True
        # Verify fetch_metar was called with uppercase
        mock_fetch.assert_called_with('KJFK')

    @patch('app.fetch_metar')
    def test_metar_response_structure(self, mock_fetch, client):
        """Test the structure of a successful METAR response."""
        mock_fetch.return_value = "METAR KORD 271951Z 18015KT 5SM -RA BKN010 05/04 A2990"

        response = client.post('/metar', data={'airport_code': 'KORD'})
        json_data = response.get_json()

        # Check response structure
        assert 'success' in json_data
        assert 'raw_metar' in json_data
        assert 'decoded' in json_data
        assert 'summary' in json_data

        # Check decoded structure
        decoded = json_data['decoded']
        assert 'station' in decoded
        assert 'time' in decoded
        assert 'wind' in decoded
        assert 'visibility' in decoded
        assert 'clouds' in decoded
        assert 'temperature' in decoded
        assert 'dewpoint' in decoded
        assert 'altimeter' in decoded
        assert 'flight_category' in decoded

    @patch('app.fetch_metar')
    def test_metar_with_weather_phenomena(self, mock_fetch, client):
        """Test METAR with weather phenomena is decoded correctly."""
        mock_fetch.return_value = "METAR KORD 271951Z 18015G25KT 3SM +TSRA BKN010 OVC020 18/17 A2965"

        response = client.post('/metar', data={'airport_code': 'KORD'})
        json_data = response.get_json()

        assert json_data['success'] is True
        decoded = json_data['decoded']
        assert len(decoded['weather']) > 0
        assert 'gusting' in decoded['wind'].lower()

    @patch('app.fetch_metar')
    def test_metar_three_letter_code(self, mock_fetch, client):
        """Test that 3-letter airport codes work."""
        mock_fetch.return_value = "METAR JFK 271951Z 36009KT 10SM SKC 15/10 A3014"

        response = client.post('/metar', data={'airport_code': 'JFK'})
        json_data = response.get_json()

        # Should not return an error for 3-letter codes
        assert 'error' not in json_data or json_data.get('success') is True

    @patch('app.fetch_metar')
    def test_metar_whitespace_handling(self, mock_fetch, client):
        """Test that whitespace in airport code is trimmed."""
        mock_fetch.return_value = "METAR KJFK 271951Z 36009KT 10SM SKC 15/10 A3014"

        response = client.post('/metar', data={'airport_code': '  KJFK  '})
        json_data = response.get_json()

        assert json_data['success'] is True
        mock_fetch.assert_called_with('KJFK')
