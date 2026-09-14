"""
Configuration for NextGen Lead Generator — FINAL MERGED EDITION
Triple System (Web + Marketing + Power BI + AI) + VIP 195 Countries
"""

import os

def _env_bool(name, default):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}

def _env_int(name, default):
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default

# ═══════════════════════════════════════════════
# FLASK APP SETTINGS
# ═══════════════════════════════════════════════
FLASK_HOST = os.environ.get("FLASK_HOST", "0.0.0.0")
FLASK_PORT = _env_int("FLASK_PORT", 5000)
FLASK_DEBUG = _env_bool("FLASK_DEBUG", False)

# ═══════════════════════════════════════════════
# BROWSER SETTINGS
# ═══════════════════════════════════════════════
HEADLESS = _env_bool("HEADLESS", False)
BROWSER_TIMEOUT = 30
DEBUG_SCREENSHOTS = _env_bool("DEBUG_SCREENSHOTS", True)

# ═══════════════════════════════════════════════
# SCRAPING SETTINGS
# ═══════════════════════════════════════════════
MAX_RESULTS_DEFAULT = 20
MAX_RESULTS_PER_SEARCH = 1000
MAX_RESULTS_LIMIT = 1000
SCROLL_PAUSE_TIME = 3
SCROLL_MAX_STALL_RETRIES = 20

# ═══════════════════════════════════════════════
# WEBSITE ANALYSIS SETTINGS
# ═══════════════════════════════════════════════
WEBSITE_CHECK_TIMEOUT = 10
MAX_CONCURRENT_CHECKS = 5

# ═══════════════════════════════════════════════
# LEAD SCORING — FINAL (High Priority Values)
# ═══════════════════════════════════════════════
SCORE_NO_WEBSITE = 95        # No website — HIGHEST PRIORITY
SCORE_BAD_WEBSITE = 80       # Very poor/broken
SCORE_OUTDATED_WEBSITE = 65  # Old design
SCORE_DECENT_WEBSITE = 30    # Okay
SCORE_GOOD_WEBSITE = 10      # Modern — LOW PRIORITY

# ═══════════════════════════════════════════════
# LEAD TYPE DROPDOWN — TRIPLE + AI SYSTEM
# ═══════════════════════════════════════════════
LEAD_TYPE_OPTIONS = [
    {"value": "all", "label": "🌟 All — Web + Marketing + Power BI + AI", "desc": "Finds all opportunities — Best for agency"},
    {"value": "web", "label": "💻 Web Development Clients", "desc": "No/bad websites, needs redesign"},
    {"value": "marketing", "label": "📢 Marketing Clients", "desc": "Low rating, few reviews, needs growth"},
    {"value": "powerbi", "label": "📊 Power BI / Fabric Clients", "desc": "High reviews, data-heavy, needs dashboard — HIGH TICKET"},
    {"value": "ai", "label": "🤖 AI & Automation Clients", "desc": "High volume, booking businesses, needs AI bot"},
]

# ═══════════════════════════════════════════════
# POWER BI — HOT CATEGORIES (High Ticket Clients)
# ═══════════════════════════════════════════════
POWER_BI_CATEGORIES = [
    "real estate", "real estate agency", "property", "car dealer", "auto dealer",
    "car dealership", "used car", "restaurant", "clinic", "hospital", "dental",
    "gym", "fitness", "hotel", "wholesale", "distributor", "supermarket",
    "pharmacy", "lab", "school", "travel agency", "logistics", "construction",
    "accountant", "lawyer", "insurance", "salon", "spa", "auto repair"
]

# Alias for backward compatibility
POWER_BI_HOT_CATEGORIES = POWER_BI_CATEGORIES

# ═══════════════════════════════════════════════
# MARKETING — HOT SIGNALS
# ═══════════════════════════════════════════════
MARKETING_LOW_RATING_THRESHOLD = 4.0
MARKETING_LOW_REVIEWS_THRESHOLD = 30

# ═══════════════════════════════════════════════
# SEARCH TEMPLATES
# ═══════════════════════════════════════════════
DEFAULT_SEARCH_QUERIES = [
    "{business_type} in {location}, {country}",
]

# ═══════════════════════════════════════════════
# COUNTRIES — ALL 195 UN RECOGNIZED + TERRITORIES
# ═══════════════════════════════════════════════
COUNTRIES = [
    "Afghanistan","Albania","Algeria","Andorra","Angola","Antigua and Barbuda","Argentina","Armenia","Australia","Austria",
    "Azerbaijan","Bahamas","Bahrain","Bangladesh","Barbados","Belarus","Belgium","Belize","Benin","Bhutan","Bolivia",
    "Bosnia and Herzegovina","Botswana","Brazil","Brunei","Bulgaria","Burkina Faso","Burundi","Cabo Verde","Cambodia",
    "Cameroon","Canada","Central African Republic","Chad","Chile","China","Colombia","Comoros","Costa Rica","Croatia",
    "Cuba","Cyprus","Czechia","Democratic Republic of the Congo","Denmark","Djibouti","Dominica","Dominican Republic",
    "Ecuador","Egypt","El Salvador","Equatorial Guinea","Eritrea","Estonia","Eswatini","Ethiopia","Fiji","Finland","France",
    "Gabon","Gambia","Georgia","Germany","Ghana","Greece","Grenada","Guatemala","Guinea","Guinea-Bissau","Guyana","Haiti",
    "Honduras","Hungary","Iceland","India","Indonesia","Iran","Iraq","Ireland","Israel","Italy","Ivory Coast","Jamaica",
    "Japan","Jordan","Kazakhstan","Kenya","Kiribati","Kuwait","Kyrgyzstan","Laos","Latvia","Lebanon","Lesotho","Liberia",
    "Libya","Liechtenstein","Lithuania","Luxembourg","Madagascar","Malawi","Malaysia","Maldives","Mali","Malta",
    "Marshall Islands","Mauritania","Mauritius","Mexico","Micronesia","Moldova","Monaco","Mongolia","Montenegro","Morocco",
    "Mozambique","Myanmar","Namibia","Nauru","Nepal","Netherlands","New Zealand","Nicaragua","Niger","Nigeria","North Korea",
    "North Macedonia","Norway","Oman","Pakistan","Palau","Palestine","Panama","Papua New Guinea","Paraguay","Peru",
    "Philippines","Poland","Portugal","Qatar","Republic of the Congo","Romania","Russia","Rwanda","Saint Kitts and Nevis",
    "Saint Lucia","Saint Vincent and the Grenadines","Samoa","San Marino","Sao Tome and Principe","Saudi Arabia","Senegal",
    "Serbia","Seychelles","Sierra Leone","Singapore","Slovakia","Slovenia","Solomon Islands","Somalia","South Africa",
    "South Korea","South Sudan","Spain","Sri Lanka","Sudan","Suriname","Sweden","Switzerland","Syria","Taiwan","Tajikistan",
    "Tanzania","Thailand","Timor-Leste","Togo","Tonga","Trinidad and Tobago","Tunisia","Turkey","Turkmenistan","Tuvalu",
    "Uganda","Ukraine","United Arab Emirates","United Kingdom","United States","Uruguay","Uzbekistan","Vanuatu",
    "Vatican City","Venezuela","Vietnam","Yemen","Zambia","Zimbabwe",
]

# Alias for backward compatibility with older app.py
COUNTRY_OPTIONS = COUNTRIES

# ═══════════════════════════════════════════════
# BUSINESS TYPES — Most likely to need services
# ═══════════════════════════════════════════════
BUSINESS_TYPES = [
    "restaurants","cafes","plumbers","electricians","dentists","doctors","lawyers","real estate agents",
    "auto repair shops","car dealerships","beauty salons","barber shops","gyms","fitness centers","yoga studios",
    "contractors","construction companies","accountants","tax consultants","veterinarians","pet grooming",
    "photographers","wedding planners","event venues","florists","bakeries","catering services",
    "landscaping companies","pest control","cleaning services","hotels","guest houses","travel agencies",
    "tour operators","schools","tutoring centers","driving schools","clinics","pharmacies","opticians",
    "jewelry stores","clothing stores","furniture stores",
]

# ═══════════════════════════════════════════════
# LOGGING & DEBUGGING
# ═══════════════════════════════════════════════
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

if DEBUG_SCREENSHOTS:
    SCREENSHOT_DIR = os.path.join(LOG_DIR, "screenshots")
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
