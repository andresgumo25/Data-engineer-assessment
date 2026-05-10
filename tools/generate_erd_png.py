import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

DBML_PATH = Path('erd.dbml')
OUT_PATH = Path('erd.png')

if not DBML_PATH.exists():
    raise SystemExit('erd.dbml not found')

text = DBML_PATH.read_text(encoding='utf-8')

# parse tables
pattern = re.compile(r"Table\s+(\w+)\s*\{([^}]*)\}", re.S)
matches = pattern.findall(text)

tables = []
for name, body in matches:
    cols = []
    refs = []
    for line in body.splitlines():
        line = line.strip()
        if not line or line.startswith('//'):
            continue
        # remove trailing comma
        if line.endswith(','):
            line = line[:-1].strip()
        # column line may have [pk] or [ref: > table.col]
        m_ref = re.search(r"(\w+)\s+[^\[]*\[ref:\s*>\s*(\w+)\.(\w+)\]", line)
        m_pk = re.search(r"(\w+)\s+[^\[]*\[pk\]", line)
        m_col = re.match(r"(\w+)\s+([\w()]+).*", line)
        col_name = None
        if m_ref:
            col_name = m_ref.group(1)
            refs.append((col_name, m_ref.group(2), m_ref.group(3)))
            cols.append((col_name, f"ref -> {m_ref.group(2)}.{m_ref.group(3)}"))
        elif m_pk:
            col_name = m_pk.group(1)
            cols.append((col_name, 'pk'))
        elif m_col:
            col_name = m_col.group(1)
            cols.append((col_name, ''))
    tables.append({'name': name, 'cols': cols, 'refs': refs})

# layout
num = len(tables)
cols_layout = min(3, num)
rows_layout = (num + cols_layout - 1) // cols_layout
box_w = 320
box_h_base = 24
box_h_line = 18
padding = 40
width = cols_layout * (box_w + padding) + padding
height = rows_layout * (200) + padding

img = Image.new('RGB', (width, height), 'white')
draw = ImageDraw.Draw(img)
try:
    font = ImageFont.truetype('arial.ttf', 14)
except Exception:
    font = ImageFont.load_default()

positions = {}
for idx, t in enumerate(tables):
    col = idx % cols_layout
    row = idx // cols_layout
    x = padding + col * (box_w + padding)
    y = padding + row * 200
    # compute box height
    h = box_h_base + max(4, len(t['cols'])) * box_h_line + 10
    # draw rectangle
    draw.rectangle([x, y, x + box_w, y + h], outline='black', width=2, fill='#f8f9fa')
    # title
    draw.text((x + 8, y + 6), t['name'], fill='black', font=font)
    # draw separator
    draw.line([x, y + 28, x + box_w, y + 28], fill='black')
    # columns
    cy = y + 34
    for col_name, note in t['cols']:
        txt = col_name + (f' ({note})' if note else '')
        draw.text((x + 8, cy), txt, fill='black', font=font)
        cy += box_h_line
    positions[t['name']] = (x + box_w/2, y + h/2)

# draw arrows for refs
for t in tables:
    for col_name, ref_table, ref_col in t['refs']:
        if ref_table in positions and t['name'] in positions:
            x1, y1 = positions[t['name']]
            x2, y2 = positions[ref_table]
            # simple line
            draw.line([x1, y1, x2, y2], fill='black', width=2)
            # arrowhead
            # compute direction
            import math
            dx = x2 - x1
            dy = y2 - y1
            dist = max(1, math.hypot(dx, dy))
            ux = dx / dist
            uy = dy / dist
            # arrow base
            ax = x2 - ux * 10
            ay = y2 - uy * 10
            leftx = ax + uy * 6
            lefty = ay - ux * 6
            rightx = ax - uy * 6
            righty = ay + ux * 6
            draw.polygon([(x2, y2), (leftx, lefty), (rightx, righty)], fill='black')

img.save(OUT_PATH)
print(f'ERD exported to {OUT_PATH}')
