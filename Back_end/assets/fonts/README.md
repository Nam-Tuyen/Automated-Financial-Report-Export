# Font Files Directory

This directory should contain DejaVu Sans fonts for PDF report generation.

## Required Font Files

Please download and place the following DejaVu Sans font files in this directory:

1. `DejaVuSans.ttf` (Regular)
2. `DejaVuSans-Bold.ttf` (Bold)
3. `DejaVuSans-Oblique.ttf` (Italic/Oblique)
4. `DejaVuSans-BoldOblique.ttf` (Bold Italic)

### Optional Fonts (for extended support):

- `DejaVuSans-ExtraLight.ttf`
- `DejaVuSansCondensed.ttf`
- `DejaVuSansCondensed-Bold.ttf`
- `DejaVuSansCondensed-Oblique.ttf`
- `DejaVuSansCondensed-BoldOblique.ttf`

## Where to Download

### Option 1: Official DejaVu Fonts Website
Visit: https://dejavu-fonts.github.io/Download.html

Download the latest version (e.g., `dejavu-fonts-ttf-2.37.zip`)

Extract and copy the `.ttf` files from the `ttf` folder to this directory.

### Option 2: GitHub Repository
Visit: https://github.com/dejavu-fonts/dejavu-fonts/releases

Download the latest release and extract the font files.

### Option 3: System Fonts (Windows)
If you have DejaVu fonts installed on your system, you can copy them from:
- Windows: `C:\Windows\Fonts\`
- Linux: `/usr/share/fonts/truetype/dejavu/`
- macOS: `/Library/Fonts/` or `~/Library/Fonts/`

## License

DejaVu fonts are licensed under a free license.
See: `DejaVu Fonts License.txt` in the Back_end directory for details.

## Fallback Behavior

If fonts are not found, the application will automatically fall back to the built-in **Helvetica** font. However, note that Helvetica does not support Vietnamese characters properly.

**For Vietnamese text support, DejaVu fonts are strongly recommended.**

## Verification

After placing the font files, you can verify they're detected by running a report generation.
You should see:
```
[INFO] Registered 4/4 DejaVu fonts.
```

If you see warnings about missing fonts, check that:
1. Files are in the correct directory (`Back_end/assets/fonts/`)
2. File names match exactly (case-sensitive on Linux/macOS)
3. Files are valid `.ttf` font files

