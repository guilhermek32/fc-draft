"""Configuration constants for the EA FC 26 draft app."""

CSV_FILE = "FC26_20250921.csv"
STATE_FILE = "draft_state.json"
IMAGE_CACHE_DIR = "image_cache"

NOTFOUND_IMG_URL = "https://cdn.sofifa.net/players/notfound_0_120.png"
TRANSPARENT_PIXEL_URI = (
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAA"
    "C0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
)

# Card tier thresholds (overall rating)
OVR_TIER_GOLD = 85
OVR_TIER_SILVER = 75

# Default minimum overall shown when no search query is given (keeps selectboxes snappy)
DEFAULT_MIN_OVR = 75

DEFAULT_BENCH_SLOTS = 5
BANS_PER_PARTICIPANT = 3
DOWNLOAD_TIMEOUT = 5

# Password hashing (PBKDF2-HMAC-SHA256)
PBKDF2_ITERATIONS = 600_000
SALT_BYTES = 16
GENERATED_PASSWORD_LENGTH = 8

FORMATIONS = {
    "4-3-3": ["GK", "LB", "CB", "CB", "RB", "CM", "CM", "CM", "LW", "ST", "RW"],
    "4-4-2": ["GK", "LB", "CB", "CB", "RB", "LM", "CM", "CM", "RM", "ST", "ST"],
    "3-5-2": ["GK", "CB", "CB", "CB", "CDM", "CDM", "CAM", "LM", "RM", "ST", "ST"],
    "4-2-3-1": ["GK", "LB", "CB", "CB", "RB", "CDM", "CDM", "CAM", "LM", "RM", "ST"],
    "5-3-2": ["GK", "LWB", "CB", "CB", "CB", "RWB", "CM", "CM", "CM", "ST", "ST"],
    "4-5-1": ["GK", "LB", "CB", "CB", "RB", "CM", "CAM", "CAM", "LM", "RM", "ST"],
    "3-4-3": ["GK", "CB", "CB", "CB", "LM", "CM", "CM", "RM", "LW", "ST", "RW"],
    "4-1-2-1-2": ["GK", "LB", "CB", "CB", "RB", "CDM", "LM", "RM", "CAM", "ST", "ST"],
    "4-3-2-1": ["GK", "LB", "CB", "CB", "RB", "CM", "CM", "CM", "LF", "ST", "RF"],
}

# Mapping of positions for flexible filters
FLEXIBLE_POSITIONS = {
    "GK": ["GK"],
    "LB": ["LB", "LWB", "CB"],
    "LWB": ["LWB", "LB", "LM"],
    "CB": ["CB", "LB", "RB", "CDM"],
    "RB": ["RB", "RWB", "CB"],
    "RWB": ["RWB", "RB", "RM"],
    "CDM": ["CDM", "CM", "CB"],
    "CM": ["CM", "CDM", "CAM"],
    "CAM": ["CAM", "CM", "CF", "LM", "RM"],
    "LM": ["LM", "LW", "LWB", "CM"],
    "RM": ["RM", "RW", "RWB", "CM"],
    "LW": ["LW", "LM", "LF", "RW"],
    "RW": ["RW", "RM", "RF", "LW"],
    "ST": ["ST", "CF"],
    "CF": ["CF", "ST", "CAM", "LF", "RF"],
    "LF": ["LF", "LW", "CF", "ST"],
    "RF": ["RF", "RW", "CF", "ST"],
    "SUB": [],
}

OUTFIELD_STATS = ["pace", "shooting", "passing", "dribbling", "defending", "physic"]
GK_STATS = [
    "goalkeeping_diving",
    "goalkeeping_handling",
    "goalkeeping_kicking",
    "goalkeeping_positioning",
    "goalkeeping_reflexes",
    "goalkeeping_speed",
]
