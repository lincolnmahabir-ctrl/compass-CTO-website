# Compass CTO logo files

Vector rebuild of the Compass CTO logo. Every shape is a plain filled path: the
white gaps between the compass parts are true cut-outs (transparent), and the
lettering is converted to outlines, so no fonts are needed to open or print
these files.

## Which file to use

| Folder | Use it for |
| --- | --- |
| `svg/` | Website, and anything a designer or printer will edit. Opens in Illustrator, Inkscape, Affinity, Figma and Canva. |
| `pdf/` | Sending to a printer (business cards, letterhead, signage, merchandise). Pure vector, scales to any size. |
| `png/` | Documents, slides, email signatures and social media. Transparent background, 3000 px on the long side. |

## Versions

| File name | Description | Use on |
| --- | --- | --- |
| `compass-cto-logo` | Stacked: compass over name and tagline | Light backgrounds |
| `compass-cto-logo-horizontal` | Compass beside name and tagline | Letterhead, website, wide spaces |
| `compass-cto-mark` | Compass only | Social avatars, app icons, small spaces |
| *(no suffix)* | Full colour, metallic gold gradient | Screens, full-colour print |
| `-flat` | Full colour, solid gold (no gradient) | Embroidery, screen printing, vinyl, promotional items |
| `-navy` | One colour, navy | One-colour print, stamps, engraving |
| `-reversed` | White and gold | Navy or dark backgrounds |
| `-white` | One colour, white | Dark backgrounds, one-colour print on dark items |

## Colours

| Colour | HEX | RGB |
| --- | --- | --- |
| Navy | `#0f3254` | 15, 50, 84 |
| Gold (solid) | `#c09a4c` | 192, 154, 76 |
| Gold gradient | `#a37a30` → `#e3c674` → `#c9a253` → `#e8cf86` → `#a8802f` | |

For print, ask your printer to match these colours to Pantone or CMYK and to
show you a proof first.

## Typefaces

- Name: Source Serif 4 SemiBold
- Tagline and compass letters: Montserrat SemiBold / Bold

Both are free Google Fonts, and the same typefaces the website uses.

## Regenerating

`source/gen_logo.py` builds every SVG from geometry, and `source/export.js`
renders the PNG and PDF versions with Playwright. The generator needs Python
with `shapely`, `fonttools`, `brotli` and `uharfbuzz`, and the
`@fontsource/source-serif-4` and `@fontsource/montserrat` npm packages unpacked
to `source/fonts/package/`.

```sh
python3 source/gen_logo.py out
mkdir -p out/png out/pdf && node source/export.js out
```
