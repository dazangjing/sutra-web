#!/usr/bin/env python3
"""
生成桌面端图标。

以站点之「圆相 + 阅字」为形制，输出 Tauri 所需的全套图标：
  icons/32x32.png        icons/128x128.png     icons/128x128@2x.png
  icons/icon.icns        icons/icon.ico

依赖 Pillow（DSH 内置 Python 已含）。
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("需要 Pillow：pip install pillow", file=sys.stderr)
    sys.exit(1)

OUT = Path(__file__).resolve().parents[1] / "src-tauri" / "icons"

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
    d.ellipse(bbox2, outline=JADE_DIM, width=max(1, int(s * 0.007)))

    # 「阅」字：优先用系统宋体，取不到则以方框代替
    glyph = "阅"
    font = None
    for path in (
        "/System/Library/Fonts/Supplemental/Songti.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
    ):
        p = Path(path)
        if p.exists():
            try:
                from PIL import ImageFont

                font = ImageFont.truetype(str(p), int(s * 0.42))
                break
            except Exception:
                continue

    if font is not None:
        try:
            d.text((cx, cy), glyph, font=font, fill=JADE, anchor="mm")
        except Exception:
            font = None
    if font is None:
        # 无字体可用时画一个印章方框
        m = s * 0.13
        d.rounded_rectangle(
            (cx - m, cy - m, cx + m, cy + m),
            radius=int(s * 0.02),
            outline=JADE,
            width=int(s * 0.022),
        )

    return img.resize((size, size), Image.LANCZOS)


def write_ico(images: list[Image.Image], path: Path) -> None:
    """
    写多尺寸 ICO。

    尺寸 ≤ 64 用 BMP（无 alpha 时更通用），> 64 用 PNG 块 ——
    BMP 块的宽高字段各只 1 字节，装不下 256×256 的尺寸值，
    故大尺寸必须走 PNG 形式。
    """
    import io

    sizes = [16, 24, 32, 48, 64, 128, 256]
    entries: list[tuple[int, int, bytes, int]] = []

    for size in sizes:
        img = draw_seal(size)
        if size <= 64:
            # BMP：DIB 头 + BGRA 像素 + AND 掩码
            w = h = size
            pixels = img.convert("RGBA").tobytes()
            # 转为自下而上的 BGRA
            rows = []
            for y in range(h - 1, -1, -1):
                row = b""
                for x in range(w):
                    r, g, b, a = pixels[(y * w + x) * 4 : (y * w + x) * 4 + 4]
                    row += bytes((b, g, r, a))
                rows.append(row)
            xor = b"".join(rows)
            and_mask = b"\x00" * (4 * h)  # 32 位图用 4 字节/行，透明皆 0
            header = struct.pack(
                "<IiiHHIIiiII",
                40,
                w,
                h * 2,
                1,
                32,
                0,
                len(xor) + len(and_mask),
                0,
                0,
                0,
                0,
            )
            entries.append((w, h, header + xor + and_mask, 0))
        else:
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            entries.append((w, h, buf.getvalue(), 1))  # 1 = PNG 形式

    with path.open("wb") as f:
        f.write(struct.pack("<HHH", 0, 1, len(entries)))
        offset = 6 + 16 * len(entries)
        for w, h, data, _is_png in entries:
            f.write(struct.pack("<BBBBHHII", w % 256, h % 256, 0, 0, 1, 32, len(data), offset))
            offset += len(data)
        for _w, _h, data, _is_png in entries:
            f.write(data)


def write_icns(images: list[Image.Image], path: Path) -> None:
    """
    写 ICNS。

    ICNS 由若干「类型 + 长度 + 数据」块组成；
    这里用 PNG 格式的块（ic07/ic08/ic09/ic10 等），macOS 皆支持。
    """
    import io

    blocks: list[tuple[bytes, bytes]] = []

    def png_bytes(img: Image.Image) -> bytes:
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    # 类型代码 → 尺寸
    types = [
        (b"icp4", 16),
        (b"icp5", 32),
        (b"icp6", 64),
        (b"ic07", 128),
        (b"ic08", 256),
        (b"ic09", 512),
        (b"ic10", 1024),
        (b"ic11", 32),
        (b"ic12", 64),
        (b"ic13", 256),
        (b"ic14", 512),
    ]
    for code, size in types:
        img = draw_seal(size)
        blocks.append((code, png_bytes(img)))

    body = b"".join(code + struct.pack(">I", len(data) + 8) + data for code, data in blocks)
    with path.open("wb") as f:
        f.write(b"icns")
        f.write(struct.pack(">I", len(body) + 8))
        f.write(body)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    draw_seal(32).save(OUT / "32x32.png")
    draw_seal(128).save(OUT / "128x128.png")
    draw_seal(256).save(OUT / "128x128@2x.png")
    write_ico([], OUT / "icon.ico")
    write_icns([], OUT / "icon.icns")

    for f in sorted(OUT.iterdir()):
        print(f"  {f.name:20s} {f.stat().st_size / 1024:.1f} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
