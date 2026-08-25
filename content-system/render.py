"""
Design system as code.

Renders branded content tiles by composing HTML and screenshotting it through
headless Chrome. The point is not that it makes images -- plenty of things make
images. The point is that the brand rules live in one place and are applied by
the renderer, so an asset cannot drift just because a human was in a hurry.

Rules encoded here, each one learned the expensive way:

  * Type has a floor. Small text reads as timidity. Body copy never goes below
    BODY_MIN on a 1080px canvas, and there is no argument about it.
  * Copy is literal before it is clever. Headlines name the thing. Metaphor is
    seasoning applied after the reader already knows what they are looking at.
  * Heavy subject matter still gets a note of hope, in a warm accent, placed on
    the line that turns.
  * Photography carries at least a quarter of the work. Type on a flat color is
    a fallback, not a design.

Usage:
    python render.py                      # renders the sample set to ./out
    python render.py --width 1000 --height 1500   # Pinterest proportions

Requires: Google Chrome. No other dependencies.
"""

from __future__ import annotations

import argparse
import subprocess
import textwrap
from dataclasses import dataclass, field
from pathlib import Path

# --------------------------------------------------------------------------
# Brand tokens. One definition, used by every tile.
# --------------------------------------------------------------------------

INK = "#10101C"          # near-black ground
CREAM = "#F9F7F0"        # warm paper
PERIWINKLE = "#5A6FFF"   # primary, owns interactive
BABY = "#ACB7FF"         # accent within display type
ROSE = "#FF9FC4"         # reserved: the hopeful line, never a warning

BODY_MIN = 44            # px on a 1080 canvas. The floor, not a suggestion.
KICKER_MIN = 26
META_MIN = 20

DISPLAY_STACK = "'Arial Black', Arial, sans-serif"
BODY_STACK = "-apple-system, 'Segoe UI', Inter, Roboto, sans-serif"

# Film grain, inlined so a tile has no external dependencies.
GRAIN = (
    "url(\"data:image/svg+xml;utf8,"
    "<svg xmlns='http://www.w3.org/2000/svg' width='240' height='240'>"
    "<filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2'/></filter>"
    "<rect width='240' height='240' filter='url(%23n)' opacity='0.55'/></svg>\")"
)

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
]


def _chrome() -> str:
    for path in CHROME_CANDIDATES:
        if Path(path).exists():
            return path
    raise RuntimeError("Chrome not found. Set CHROME_CANDIDATES for this machine.")


# --------------------------------------------------------------------------
# Tiles
# --------------------------------------------------------------------------


@dataclass
class Tile:
    """One piece of content.

    `hope` is deliberately a separate field rather than inline markup. Keeping
    it structural means the rule -- heavy content carries a turn toward hope --
    is visible in the data, and a tile that forgets it is easy to spot.
    """

    name: str
    kicker: str
    headline: str
    accent: str = ""          # second half of the headline, in BABY
    body: str = ""
    hope: str = ""            # the line that turns, rendered in ROSE
    photo: str | None = None  # path or URL; falls back to a gradient ground
    align: str = "flex-end"   # flex-end sits copy low, center for quiet tiles


def _ground(tile: Tile) -> str:
    """Photo layer plus the scrim that keeps type legible over it."""
    if tile.photo:
        layer = (
            f"<div class='ground'><img src='{tile.photo}' alt=''></div>"
            "<div class='scrim'></div>"
        )
    else:
        layer = (
            "<div class='ground' style=\"background:"
            f"radial-gradient(120% 90% at 50% 0%, #1b1b30 0%, {INK} 70%)\"></div>"
        )
    # A warm bloom at the top keeps dark tiles from reading as grief alone.
    return layer + "<div class='bloom'></div>"


def _document(tile: Tile, width: int, height: int) -> str:
    headline = tile.headline
    if tile.accent:
        headline += f"<br><span class='accent'>{tile.accent}</span>"

    body = ""
    if tile.body or tile.hope:
        hope = f" <span class='hope'>{tile.hope}</span>" if tile.hope else ""
        body = f"<p class='body'>{tile.body}{hope}</p>"

    # Display type scales with canvas width so a tile holds up at any size.
    display_size = round(width * 0.096)

    return textwrap.dedent(f"""\
        <!doctype html>
        <html><head><meta charset='utf-8'><style>
          * {{ margin:0; padding:0; box-sizing:border-box; }}
          html, body {{
            width:{width}px; height:{height}px; overflow:hidden;
            background:{INK}; font-family:{BODY_STACK}; position:relative;
          }}
          .ground {{ position:absolute; inset:0; }}
          .ground img {{ width:100%; height:100%; object-fit:cover; }}
          .scrim {{
            position:absolute; inset:0;
            background:linear-gradient(180deg,
              rgba(16,16,28,.30) 0%, rgba(16,16,28,.62) 55%, rgba(16,16,28,.88) 100%);
          }}
          .bloom {{
            position:absolute; inset:0; pointer-events:none;
            background:radial-gradient(70% 46% at 50% 6%, rgba(242,132,178,.28), transparent 70%);
          }}
          .grain {{
            position:absolute; inset:0; pointer-events:none;
            background-image:{GRAIN}; opacity:.5; mix-blend-mode:overlay;
          }}
          .frame {{
            position:absolute; inset:0; padding:{round(width * 0.052)}px;
            display:flex; flex-direction:column; justify-content:{tile.align};
          }}
          .wordmark {{
            position:absolute; top:{round(width * 0.052)}px; right:{round(width * 0.052)}px;
            font-size:{META_MIN}px; letter-spacing:.3em; font-weight:800;
            color:rgba(255,255,255,.85);
          }}
          .kicker {{
            font-size:{KICKER_MIN}px; letter-spacing:.24em; font-weight:700;
            color:rgba(255,255,255,.82); margin-bottom:22px;
          }}
          .headline {{
            font-family:{DISPLAY_STACK}; color:#fff; line-height:.98;
            letter-spacing:-.01em; font-size:{display_size}px;
          }}
          .accent {{ color:{BABY}; }}
          .body {{
            font-size:{BODY_MIN}px; line-height:1.46; color:rgba(255,255,255,.92);
            margin-top:26px; max-width:{round(width * 0.80)}px;
          }}
          .hope {{ color:{ROSE}; }}
        </style></head>
        <body>
          {_ground(tile)}
          <div class='frame'>
            <div class='wordmark'>CONCEIVABLE</div>
            <div class='kicker'>{tile.kicker}</div>
            <div class='headline'>{headline}</div>
            {body}
          </div>
          <div class='grain'></div>
        </body></html>
    """)


def render(tile: Tile, out_dir: Path, width: int = 1080, height: int = 1080) -> Path:
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    html_path = out_dir / f"{tile.name}.html"
    png_path = out_dir / f"{tile.name}.png"
    html_path.write_text(_document(tile, width, height))

    subprocess.run(
        [
            _chrome(), "--headless=new", "--disable-gpu", "--hide-scrollbars",
            f"--window-size={width},{height}", "--force-device-scale-factor=1",
            f"--screenshot={png_path}", f"file://{html_path}",
        ],
        capture_output=True,
        check=False,
    )
    html_path.unlink(missing_ok=True)
    return png_path


# --------------------------------------------------------------------------
# Sample set
# --------------------------------------------------------------------------

SAMPLES: list[Tile] = [
    Tile(
        name="01-why",
        kicker="THE ONLY QUESTION THAT MATTERS",
        headline="TRYING ISN'T<br>THE PROBLEM.",
        accent="NOT KNOWING<br>WHY IS.",
        body="We find what is off, show you your fertility potential,",
        hope="and build the plan to fix it.",
    ),
    Tile(
        name="02-odds",
        kicker="PER-CYCLE ODDS · PERFECTLY HEALTHY, PERFECT TIMING",
        headline="25% IS",
        accent="THE CEILING.",
        body="Even at eighteen. Even doing everything right. Three months of not-yet is three coin flips.",
        hope="You have not failed at anything.",
    ),
    Tile(
        name="03-signal",
        kicker="HOW THE PLAN GETS BUILT",
        headline="THE SIGNAL PICKS",
        accent="THE INTERVENTION.",
        body="A scanty bleed points one direction. A short luteal phase points another.",
        hope="Your body already narrowed the list.",
    ),
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Render branded content tiles.")
    parser.add_argument("--width", type=int, default=1080)
    parser.add_argument("--height", type=int, default=1080)
    parser.add_argument("--out", type=Path, default=Path("out"))
    args = parser.parse_args()

    for tile in SAMPLES:
        path = render(tile, args.out, args.width, args.height)
        print(f"rendered {path}")


if __name__ == "__main__":
    main()
