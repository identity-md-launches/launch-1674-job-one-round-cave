#!/usr/bin/env python3
"""Retain the image-tool addition and preserve every ancestral pixel around it.

One-shot production step: wall.png is Gathering 09 and wall-v10.png is the
generated edit. This transfers existing generated pixels; it draws no artwork.
"""
import hashlib
import json
from pathlib import Path
import struct
import sys
import zlib

sys.path.insert(0, str(Path('shared/wall-thumbnail').resolve()))
import thumbnail

OLD = '83df9cfb84a65bdcf39c271ea954820b1df43c1ebbf0f7c03b3f05fc0891e8cc'
BOX = (510, 199, 751, 296)


def chunk(kind, data):
    return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))


def main():
    old_path = Path('artifacts/gathering/wall.png')
    new_path = Path('artifacts/gathering/wall-v10.png')
    assert hashlib.sha256(old_path.read_bytes()).hexdigest() == OLD
    generated_hash = hashlib.sha256(new_path.read_bytes()).hexdigest()
    width, height, old = thumbnail.png_rgb(old_path)
    nw, nh, generated = thumbnail.png_rgb(new_path)
    assert (width, height) == (nw, nh) == (1254, 1254)
    x0, y0, x1, y1 = BOX
    rows, changed, outside = [], 0, 0
    for y in range(height):
        row = bytearray(old[y])
        if y0 <= y <= y1:
            for x in range(x0, x1 + 1):
                # Feather only the narrow edge of previously unpainted rock.
                alpha = max(0, min(1, min(x-x0, x1-x, y-y0, y1-y) / 5))
                for c in range(3):
                    at = x * 3 + c
                    row[at] = round(old[y][at] * (1-alpha) + generated[y][at] * alpha)
        for x in range(width):
            if row[3*x:3*x+3] != old[y][3*x:3*x+3]:
                changed += 1
                outside += not (x0 <= x <= x1 and y0 <= y <= y1)
        rows.append(bytes(row))
    assert changed > 0 and outside == 0
    encoded = (b'\x89PNG\r\n\x1a\n' +
        chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)) +
        chunk(b'IDAT', zlib.compress(b''.join(b'\x00' + row for row in rows))) + chunk(b'IEND', b''))
    new_path.write_bytes(encoded)
    old_path.write_bytes(encoded)
    result = {
        'schema': 'gathering-visual-preservation-v10',
        'source_sha256': OLD, 'image_tool_output_sha256': generated_hash,
        'output_sha256': hashlib.sha256(encoded).hexdigest(),
        'format': 'PNG RGB 8-bit', 'width': width, 'height': height,
        'addition_rectangle': list(BOX), 'changed_pixels': changed,
        'changed_pixels_outside_addition': outside,
        'ancestral_pigment_intersects_addition': False,
        'left_hand_digits': 5, 'right_hand_digits': 5, 'new_hands': 0,
        'unmet_visual_requirements_observed': [],
        'review_limits': 'Human-style visual inspection, not independent certification. '
                         'Raster preservation is measured; frog identity and pigment style are subjective.'}
    Path('gathering/visual-checks.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
