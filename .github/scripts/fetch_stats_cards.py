from __future__ import annotations

import argparse
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

SUMMARY_BASE_URL = "https://github-profile-summary-cards.vercel.app/api/cards"
SUMMARY_COLORS = {
    "theme": "github_dark",
    "title_color": "58A6FF",
    "text_color": "E6EDF3",
    "bg_color": "161B22",
    "border_color": "30363D",
    "icon_color": "58A6FF",
    "chart_color": "58A6FF",
}


def is_valid_card(content: bytes) -> bool:
    lowered = content.lower()
    return (
        b"<svg" in lowered[:500]
        and b"rate limit" not in lowered
        and b"error!!!" not in lowered
        and b"temporarily" not in lowered
        and b"something went wrong" not in lowered
    )


def download_svg(url: str, destination: Path) -> None:
    last_error = "unknown error"

    for attempt in range(1, 7):
        try:
            request = Request(url, headers={"User-Agent": "profile-assets-workflow"})
            with urlopen(request, timeout=30) as response:
                content = response.read()
            if is_valid_card(content):
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(content)
                print(f"Updated {destination.name} on attempt {attempt}")
                return
            last_error = "service returned an error card"
        except Exception as error:
            last_error = str(error)

        if attempt < 6:
            time.sleep(15)

    if destination.exists() and is_valid_card(destination.read_bytes()):
        print(f"Keeping last valid {destination.name}: {last_error}")
        return

    raise RuntimeError(f"Could not obtain a valid {destination.name}: {last_error}")


def summary_card_url(endpoint: str, username: str) -> str:
    params = {**SUMMARY_COLORS, "username": username}
    if endpoint == "profile-details":
        params["name"] = "Ahmad Masood Sahak"
    return f"{SUMMARY_BASE_URL}/{endpoint}?{urlencode(params)}"


def streak_card_url(username: str) -> str:
    params = {
        "user": username,
        "hide_border": "true",
        "background": "161B22",
        "stroke": "30363D",
        "ring": "58A6FF",
        "fire": "388BFD",
        "currStreakLabel": "58A6FF",
        "sideLabels": "E6EDF3",
        "currStreakNum": "F0F6FC",
        "sideNums": "F0F6FC",
        "dates": "8B949E",
    }
    return f"https://streak-stats.demolab.com?{urlencode(params)}"


def normalize_streak_card(path: Path) -> None:
    # Match the 340 x 200 stats card ratio while centering the native streak art.
    namespace = "http://www.w3.org/2000/svg"
    ET.register_namespace("", namespace)
    ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
    source = ET.parse(path)
    streak = source.getroot()
    if streak.get("data-profile-card") == "normalized-streak":
        return

    width = 495
    height = width * 200 / 340
    top = (height - 195) / 2
    canvas = ET.Element(
        f"{{{namespace}}}svg",
        {
            "width": str(width),
            "height": f"{height:.3f}",
            "viewBox": f"0 0 {width} {height:.3f}",
            "data-profile-card": "normalized-streak",
        },
    )
    ET.SubElement(
        canvas,
        f"{{{namespace}}}rect",
        {
            "x": "0.5",
            "y": "0.5",
            "width": str(width - 1),
            "height": f"{height - 1:.3f}",
            "rx": "7.3",
            "fill": "#161B22",
            "stroke": "#30363D",
            "stroke-width": "1",
        },
    )
    streak.set("x", "0")
    streak.set("y", f"{top:.3f}")
    canvas.append(streak)
    ET.ElementTree(canvas).write(path, encoding="utf-8", xml_declaration=True)


parser = argparse.ArgumentParser(
    description="Refresh hosted SVG cards while preserving the last valid copies."
)
parser.add_argument("--username", required=True)
parser.add_argument("--output-dir", type=Path, required=True)
args = parser.parse_args()

download_svg(
    summary_card_url("profile-details", args.username),
    args.output_dir / "0-profile-details.svg",
)
download_svg(
    summary_card_url("stats", args.username),
    args.output_dir / "3-stats.svg",
)
download_svg(
    streak_card_url(args.username),
    args.output_dir / "streak-card.svg",
)

normalize_streak_card(args.output_dir / "streak-card.svg")
