"""TrackFlow domain constants aligned with CONTEXT.md and scripts/stats.py."""

VALID_COUNTRIES = ("US", "ES")
VALID_CATEGORIES = (
    "LOST_PARCEL",
    "DELAYED_DELIVERY",
    "WRONG_ADDRESS",
    "RETURN_REQUEST",
    "DAMAGE",
)
CARRIERS_BY_COUNTRY = {
    "US": ("UPS", "FEDEX", "DHL_US"),
    "ES": ("MRW", "SEUR", "DHL_ES", "LOCAL_ES"),
}
CUSTOMER_TYPES = ("B2B", "B2C")
FEATURE_COLUMNS = ("country", "customer_type", "carrier", "category", "month", "day_of_week")
TARGET_COLUMN = "satisfaction_score"
N_SPLITS = 5
