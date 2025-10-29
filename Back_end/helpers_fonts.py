"""
Font helper utilities for cross-platform font management.
Provides font path validation and fallback mechanisms.
"""

import os
from pathlib import Path
from typing import Dict


def ensure_fonts_exist(font_map: Dict[str, Path]) -> Dict[str, str]:
    """
    Validate font file existence and return map {style: abs_path_str}.
    
    Args:
        font_map: Dictionary mapping font style to Path object
        
    Returns:
        Dictionary of successfully resolved fonts {style: absolute_path_string}
    """
    resolved = {}
    for style, p in font_map.items():
        abs_p = p.resolve()
        if abs_p.is_file():
            resolved[style] = str(abs_p)
        else:
            print(f"[WARN] Missing font file: {abs_p}")
    return resolved


def system_fallback_font() -> str:
    """
    Return fallback font name when DejaVu fonts are unavailable.
    FPDF includes Helvetica by default (no TTF file needed).
    
    Returns:
        String name of fallback font compatible with FPDF
    """
    return "helvetica"


def check_font_availability(font_paths: Dict[str, Path]) -> bool:
    """
    Check if all required fonts are available.
    
    Args:
        font_paths: Dictionary mapping font style to Path object
        
    Returns:
        True if all fonts exist, False otherwise
    """
    all_exist = True
    for style, path in font_paths.items():
        if not path.exists():
            print(f"[ERROR] Font file missing: {path}")
            all_exist = False
    return all_exist

