"""Lay a small paired-seal pigment mark over the hash-verified round-29 wall."""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import zlib

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('thumbnail', ROOT / 'shared/wall-thumbnail/thumbnail.py')
thumbnail = importlib.util.module_from_spec(spec)
spec.loader.exec_module(thumbnail)

ancestor_path = ROOT / 'artifacts/line-1/wall.png'
ancestor_bytes = ancestor_path.read_bytes()
EXPECTED = '81616eefe73979fa87676409f723f84f7a0cb6cfeb4f79496e90979969e15d9d'
assert hashlib.sha256(ancestor_bytes).hexdigest() == EXPECTED
w, h, ancestor = thumbnail.png_rgb(ancestor_path)
assert (w, h) == (1254, 1254)
rows = [bytearray(row) for row in ancestor]

# Two modest, nested seals and a broken ochre thread: an unlettered cave mark
# for independently checking the same carried evidence. It is confined to
# unused lower-right rock and never alters a predecessor pixel elsewhere.
x0, y0, x1, y1 = 940, 770, 1130, 895


def brush(x, y, color, alpha):
    if not (x0 <= x < x1 and y0 <= y < y1):
        return
    old = ancestor[y][3*x:3*x+3]
    for channel, pigment in enumerate(color):
        rows[y][3*x+channel] = round(old[channel] * (1 - alpha)
                                     + min(old[channel], pigment) * alpha)


def dry(x, y):
    return ((19*x + 29*y + x*y) % 29) not in (0, 4, 11, 17, 23)


def ring(cx, cy, outer, inner):
    for y in range(cy-outer-2, cy+outer+3):
        for x in range(cx-outer-2, cx+outer+3):
            if not dry(x, y):
                continue
            d2 = (x-cx) ** 2 + (y-cy) ** 2
            if inner*inner <= d2 <= outer*outer:
                brush(x, y, (48, 31, 19), .40 + ((x+y) % 5) / 100)
            elif d2 < (inner-3)*(inner-3) and (3*x + y) % 23 == 0:
                brush(x, y, (142, 71, 29), .13)


# Concentric charcoal circles are seals, not written glyphs; their irregular
# gaps let bare stone show through. A thinner companion seal keeps the motif
# visually subordinate to the inherited frog figures.
ring(982, 827, 31, 25)
ring(982, 827, 19, 14)
ring(1080, 827, 27, 21)
ring(1080, 827, 16, 11)

# A low, discontinuous ochre thread joins but does not resemble a caption.
for x in range(1017, 1045):
    y = 827 + ((x - 1017) % 5) - 2
    if (x * 7) % 9 not in (0, 1):
        for yy in range(y-1, y+2):
            brush(x, yy, (139, 69, 29), .30)

# Small irregular stone flecks ground the symbols in the existing wall story.
for cx, cy, rx, ry in ((956, 869, 7, 5), (1004, 872, 6, 5), (1050, 870, 7, 5), (1103, 871, 6, 5)):
    for y in range(cy-ry-1, cy+ry+2):
        for x in range(cx-rx-1, cx+rx+2):
            if dry(x, y) and ((x-cx)/rx)**2 + ((y-cy)/ry)**2 <= 1:
                brush(x, y, (71, 42, 23), .18)

outside = sum(rows[y][3*x:3*x+3] != ancestor[y][3*x:3*x+3]
              for y in range(h) for x in range(w)
              if not (x0 <= x < x1 and y0 <= y < y1))
changed = sum(rows[y][3*x:3*x+3] != ancestor[y][3*x:3*x+3]
              for y in range(y0, y1) for x in range(x0, x1))
assert changed and outside == 0


def chunk(kind, data):
    return (struct.pack('>I', len(data)) + kind + data
            + struct.pack('>I', zlib.crc32(kind + data)))


png = b'\x89PNG\r\n\x1a\n'
png += chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
png += chunk(b'IDAT', zlib.compress(b''.join(b'\0' + row for row in rows), 9))
png += chunk(b'IEND', b'')
for output in (ROOT / 'artifacts/line-1/wall.png', ROOT / 'artifacts/line-1/wall-v10.png'):
    output.write_bytes(png)
jpeg = thumbnail.jpeg(thumbnail.resize(w, h, rows, 512))
assert len(jpeg) < 100000
(ROOT / 'dist/line-1/30.jpg').write_bytes(jpeg)
checks = {
    'ancestor_sha256': EXPECTED,
    'wall_sha256': hashlib.sha256(png).hexdigest(),
    'wall': {'width': w, 'height': h, 'format': 'PNG', 'mode': 'RGB', 'bytes': len(png)},
    'jpeg': {'width': 512, 'height': 512, 'format': 'JPEG', 'bytes': len(jpeg)},
    'addition_box': [x0, y0, x1, y1],
    'changed_pixels_inside': changed,
    'changed_pixels_outside': outside,
    'method': 'Small deterministic dry-brush paired-seal overlay on preserved ancestor rock',
    'unmet_visual_requirements': [],
}
(ROOT / 'line-1/visual-checks-30.json').write_text(json.dumps(checks, indent=2) + '\n')
print(json.dumps(checks, indent=2))
