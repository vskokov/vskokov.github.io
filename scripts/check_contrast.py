#!/usr/bin/env python3
"""Verify the custom palette meets WCAG AA contrast thresholds."""

from __future__ import annotations


def srgb_to_linear(channel: int) -> float:
    value = channel / 255
    if value <= 0.03928:
        return value / 12.92
    return ((value + 0.055) / 1.055) ** 2.4


def luminance(hex_color: str) -> float:
    value = hex_color.lstrip("#")
    red, green, blue = (int(value[index : index + 2], 16) for index in (0, 2, 4))
    return (
        0.2126 * srgb_to_linear(red)
        + 0.7152 * srgb_to_linear(green)
        + 0.0722 * srgb_to_linear(blue)
    )


def contrast(first: str, second: str) -> float:
    light, dark = sorted((luminance(first), luminance(second)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


PAIRS = {
    "body text on page background": ("#d7e1ef", "#0a1020", 4.5),
    "heading text on page background": ("#f8fbff", "#0a1020", 4.5),
    "cyan links on page background": ("#5eead4", "#0a1020", 4.5),
    "visited links on page background": ("#c084fc", "#0a1020", 4.5),
    "gold focus/hover on page background": ("#fde68a", "#0a1020", 4.5),
    "muted nav text on sidebar": ("#afbdd1", "#111a30", 4.5),
    "white active nav text on cyan tint": ("#f8fbff", "#182f3b", 4.5),
}


def main() -> int:
    failed = False
    for label, (foreground, background, threshold) in PAIRS.items():
        ratio = contrast(foreground, background)
        status = "OK" if ratio >= threshold else "FAIL"
        print(f"{status:4} {ratio:.2f}:1 {label}")
        failed = failed or ratio < threshold
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
