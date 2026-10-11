"""Lines of business the app handles: claim-number prefix and display label."""
LINES = {
    "health": ("CLM-H", "Health"),
    "motor": ("CLM-M", "Motor"),
    "travel": ("CLM-T", "Travel"),
    "home": ("CLM-P", "Home"),
    "personal_accident": ("CLM-A", "Personal accident"),
    "life": ("CLM-L", "Life"),
}
LINE_PATTERN = "^(" + "|".join(LINES) + ")$"
