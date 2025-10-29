from pathlib import Path

# Resolve project root (folder containing Back_end, Data, etc.)
BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent

# Data directories
DATA_DIR = PROJECT_ROOT / "Data"
DATA_CLEANED_DIR = DATA_DIR / "Data cleaned"
DATA_RAW_DIR = DATA_DIR / "Data raw"
DATA_STORE_DIR = DATA_DIR / "Data_store"
REPORT_EXPORT_DIR = DATA_DIR / "Report_export"

# Fonts directory (bundled in Back_end/assets/fonts)
ASSETS_DIR = BACKEND_DIR / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"

# Font file paths (using Path for cross-platform compatibility)
FONT_SANS_REG = FONTS_DIR / "DejaVuSans.ttf"
FONT_SANS_BOLD = FONTS_DIR / "DejaVuSans-Bold.ttf"
FONT_SANS_ITAL = FONTS_DIR / "DejaVuSans-Oblique.ttf"  # italic/oblique
FONT_SANS_BI = FONTS_DIR / "DejaVuSans-BoldOblique.ttf"
FONT_SANS_XL = FONTS_DIR / "DejaVuSans-ExtraLight.ttf"  # extra light

# Condensed fonts
FONT_COND_REG = FONTS_DIR / "DejaVuSansCondensed.ttf"
FONT_COND_BOLD = FONTS_DIR / "DejaVuSansCondensed-Bold.ttf"
FONT_COND_ITAL = FONTS_DIR / "DejaVuSansCondensed-Oblique.ttf"
FONT_COND_BI = FONTS_DIR / "DejaVuSansCondensed-BoldOblique.ttf"

# Common files
SUGGESTION_XLSX = DATA_CLEANED_DIR / "Phan_loai_nganh(cleaned).xlsx"
CSV_FT_FILE = DATA_RAW_DIR / "FT2325.csv"
MARKET_INDEX_FILE = DATA_RAW_DIR / "market_index.xlsx"

# Ensure output dirs exist at runtime (create when imported by writers)
def ensure_output_dirs() -> None:
    DATA_STORE_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
