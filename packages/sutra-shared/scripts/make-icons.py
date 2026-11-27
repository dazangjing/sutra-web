#!/usr/bin/env python3
"""
生成应用图标（Web / 桌面端 / 移动端共用同一形制）。

以站点之「圆相 + 阅字」为形制 —— 一笔周而复始，唯留交叠处为接。
三端同一图标，故一改三端同变。

产出：
  sutra-desktop/src-tauri/icons/   Tauri 全套（32/128/128@2x/icns/ico）
  sutra-app/public/icon.png        移动端（含 Android/iOS/OHOS 之源）
  sutra-app/android/…/ic_launcher  Android 密度档
  sutra-app/ios/App/App/Assets.xcassets/AppIcon  iOS 图标集
  sutra-app/ohos/…/media          鸿蒙图标

依赖 Pillow（DSH 内置 Python 已含）。
"""

from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("需要 Pillow：pip install pillow", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parents[3]

DESKTOP_ICONS = ROOT / "sutra-desktop" / "src-tauri" / "icons"
APP_PUBLIC = ROOT / "sutra-app" / "public"
APP_ANDROID = ROOT / "sutra-app" / "android" / "app" / "src" / "main" / "res"
APP_IOS = ROOT / "sutra-app" / "ios" / "App" / "App" / "Assets.xcassets" / "AppIcon.appiconset"
APP_OHOS = ROOT / "sutra-app" / "ohos" / "entry" / "src" / "main" / "resources" / "base" / "media"
OHOS_APP_ICON = ROOT / "sutra-app" / "ohos" / "AppScope" / "resources" / "base" / "media"

# 墨夜底 + 翠绿描边，与站点墨夜主题同源
BG = (43, 47, 53, 255)
JADE = (95, 227, 192, 255)
JADE_DIM = (47, 179, 146, 255)


def draw_seal(size: int, supersample: int = 4) -> Image.Image:
    """画圆相 + 「阅」字。"""
    s = size * supersample
    img = Image.new("RGBA", (s, s), BG)

    d = ImageDraw.Draw(img)

    # 圆相：闭环 —— 一笔周而复始，唯留一线交叠处为接
    r = s * 0.38
    cx = cy = s / 2
    bbox = (cx - r, cy - r, cx + r, cy + r)
    # 全环描线，两端稍重，以示首尾相衔（闭环之意）
    width = max(1, int(s * 0.022))
    d.ellipse(bbox, outline=JADE, width=width)
    # 首尾交叠处：加一小段浓墨，使环之接痕可见
    d.arc(bbox, start=-78, end=-58, fill=JADE, width=width + max(1, int(s * 0.006)))

    # 内圈淡环（亦闭环）
    r2 = s * 0.30
    bbox2 = (cx - r2, cy - r2, cx + r2, cy + r2)
    d.ellipse(bbox2, outline=JADE_DIM, width=max(1, int(s * 0.010)))

    # 「阅」字：字形近似，以笔画示意
    font_size = int(s * 0.26)
    try:
        from PIL import ImageFont

        font = ImageFont.truetype("/System/Library/Fonts/STHeiti Medium.ttc", font_size)
        d.text((cx, cy), "阅", font=font, fill=JADE, anchor="mm")
    except OSError:
        # 无字体则画简化之「门」形
        gw = s * 0.16
        gh = s * 0.20
        gx = cx - gw / 2
        gy = cy - gh / 2
        lw = max(1, int(s * 0.018))
        d.line([(gx, gy), (gx, gy + gh)], fill=JADE, width=lw)
        d.line([(gx, gy), (gx + gw, gy)], fill=JADE, width=lw)
        d.line([(gx + gw, gy), (gx + gw, gy + gh)], fill=JADE, width=lw)
        d.line([(gx + gw * 0.55, gy + gh * 0.42), (gx + gw * 0.55, gy + gh * 0.78)], fill=JADE, width=lw)

    return img.resize((size, size), Image.LANCZOS)


def write_ico(img: Image.Image, path: Path) -> None:
    """写 Windows 之 .ico（自 PNG 尺寸派生多档）。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    sizes = [16, 24, 32, 48, 64, 128, 256]
    img.save(path, format="ICO", sizes=[(s, s) for s in sizes])


def write_icns(img: Image.Image, path: Path) -> None:
    """写 macOS 之 .icns（内嵌 PNG 若干档）。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    entries = [
        (16, b"icp4"),
        (32, b"icp5"),
        (64, b"icp6"),
        (128, b"ic07"),
        (256, b"ic08"),
        (512, b"ic09"),
        (1024, b"ic10"),
    ]
    blobs: list[bytes] = []
    for size, ostype in entries:
        buf = io_bytes(img.resize((size, size), Image.LANCZOS))
        blobs.append(ostype + struct.pack(">I", len(buf) + 8) + buf)

    total = 8 + len(b"".join(blobs))
    out = b"icns" + struct.pack(">I", total) + b"".join(blobs)
    path.write_bytes(out)


def io_bytes(img: Image.Image) -> bytes:
    """图片转 PNG 字节。"""
    from io import BytesIO

    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def main() -> int:
    seal = draw_seal(1024)

    # ── 桌面端：Tauri 全套 ────────────────────────────────────
    DESKTOP_ICONS.mkdir(parents=True, exist_ok=True)
    seal.resize((32, 32), Image.LANCZOS).save(DESKTOP_ICONS / "32x32.png")
    seal.resize((128, 128), Image.LANCZOS).save(DESKTOP_ICONS / "128x128.png")
    seal.resize((256, 256), Image.LANCZOS).save(DESKTOP_ICONS / "128x128@2x.png")
    write_ico(seal, DESKTOP_ICONS / "icon.ico")
    write_icns(seal, DESKTOP_ICONS / "icon.icns")
    print(f"桌面端图标 → {DESKTOP_ICONS}")

    # ── 移动端：通用源图 ───────────────────────────────────────
    APP_PUBLIC.mkdir(parents=True, exist_ok=True)
    seal.resize((512, 512), Image.LANCZOS).save(APP_PUBLIC / "icon.png")
    print(f"移动端源图 → {APP_PUBLIC / 'icon.png'}")

    # ── Android：密度档 ───────────────────────────────────────
    android_densities = {
        "mipmap-mdpi": 48,
        "mipmap-hdpi": 72,
        "mipmap-xhdpi": 96,
        "mipmap-xxhdpi": 144,
        "mipmap-xxxhdpi": 192,
    }
    for folder, size in android_densities.items():
        target = APP_ANDROID / folder
        if not target.parent.exists():
            continue  # Android 工程未生成时略过
        target.mkdir(parents=True, exist_ok=True)
        seal.resize((size, size), Image.LANCZOS).save(target / "ic_launcher.png")
        seal.resize((round(size * 1.5), round(size * 1.5)), Image.LANCZOS).save(
            target / "ic_launcher_round.png"
        )
        seal.resize((round(size * 1.5), round(size * 1.5)), Image.LANCZOS).save(
            target / "ic_launcher_foreground.png"
        )
    if (APP_ANDROID / "mipmap-mdpi").exists():
        print(f"Android 图标 → {APP_ANDROID}")

    # ── iOS：图标集 ───────────────────────────────────────────
    if APP_IOS.parent.exists():
        APP_IOS.mkdir(parents=True, exist_ok=True)
        ios_entries = [
            ("Icon-20@2x.png", 40),
            ("Icon-20@3x.png", 60),
            ("Icon-29@2x.png", 58),
            ("Icon-29@3x.png", 87),
            ("Icon-40@2x.png", 80),
            ("Icon-40@3x.png", 120),
            ("Icon-60@2x.png", 120),
            ("Icon-60@3x.png", 180),
            ("Icon-76@1x.png", 76),
            ("Icon-76@2x.png", 152),
            ("Icon-83.5@2x.png", 167),
            ("Icon-1024.png", 1024),
        ]
        images = []
        for name, size in ios_entries:
            seal.resize((size, size), Image.LANCZOS).save(APP_IOS / name)
            images.append({"filename": name, "idiom": "universal", "platform": "ios", "size": f"{size:g}x{size:g}"})
        (APP_IOS / "Contents.json").write_text(
            json.dumps({"images": images, "info": {"version": 1, "author": "xcode"}}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"iOS 图标 → {APP_IOS}")

    # ── 鸿蒙：图标 ────────────────────────────────────────────
    for folder in (APP_OHOS, OHOS_APP_ICON):
        if not folder.parent.exists():
            continue
        folder.mkdir(parents=True, exist_ok=True)
        seal.resize((216, 216), Image.LANCZOS).save(folder / "app_icon.png")
    if APP_OHOS.exists():
        print(f"鸿蒙图标 → {APP_OHOS}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
