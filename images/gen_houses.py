"""Generate isometric house SVG illustrations for ReBuild3D catalog."""
import math, os

OUT = os.path.dirname(os.path.abspath(__file__))

# Isometric projection helpers
# In isometric: x→right-down, y→left-down, z→up
def iso(x, y, z, cx=400, cy=280, scale=52):
    """Convert 3D isometric coords to 2D SVG coords."""
    sx = (x - y) * scale * math.cos(math.radians(30))
    sy = (x + y) * scale * math.sin(math.radians(30)) - z * scale
    return cx + sx, cy + sy

def pt(coords):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in coords)

def face(points, fill, stroke="#2d4a6b", sw=1.5, opacity=1.0):
    op = f' opacity="{opacity}"' if opacity < 1 else ""
    return f'<polygon points="{pt(points)}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{op}/>'

def rect_face(x0,y0,z0, x1,y1,z1, fill, stroke="#2d4a6b"):
    """Draw a rectangular face given 4 corners in iso space."""
    corners = [iso(x0,y0,z0), iso(x1,y0,z0), iso(x1,y1,z1), iso(x0,y1,z1)]
    return face(corners, fill, stroke)

def box(x, y, w, d, h, top, left, right, stroke="#2d4a6b"):
    """Draw an isometric box (x,y = base corner, w=width, d=depth, h=height)."""
    parts = []
    # top face
    tl = iso(x,y,h); tr = iso(x+w,y,h); br = iso(x+w,y+d,h); bl = iso(x,y+d,h)
    parts.append(face([tl,tr,br,bl], top, stroke))
    # left face (visible y face)
    tl2 = iso(x,y,h); bl2 = iso(x,y,0); br2 = iso(x+w,y,0); tr2 = iso(x+w,y,h)
    parts.append(face([tl2,bl2,br2,tr2], left, stroke))
    # right face (visible x face)
    tl3 = iso(x+w,y,h); bl3 = iso(x+w,y,0); br3 = iso(x+w,y+d,0); tr3 = iso(x+w,y+d,h)
    parts.append(face([tl3,bl3,br3,tr3], right, stroke))
    return "\n".join(parts)

def window(x, y, z, axis='x', w=0.5, h=0.4, fill="#b8d4f0", stroke="#2d4a6b"):
    """Draw a small window on a wall face."""
    if axis == 'x':
        corners = [iso(x,y,z), iso(x,y+w,z), iso(x,y+w,z+h), iso(x,y,z+h)]
    else:
        corners = [iso(x,y,z), iso(x+w,y,z), iso(x+w,y,z+h), iso(x,y,z+h)]
    return face(corners, fill, stroke, sw=1.0)

def door(x, y, z=0, axis='x', fill="#8b6a3e", stroke="#2d4a6b"):
    if axis == 'x':
        corners = [iso(x,y,z), iso(x,y+0.5,z), iso(x,y+0.5,z+0.9), iso(x,y,z+0.9)]
    else:
        corners = [iso(x,y,z), iso(x+0.5,y,z), iso(x+0.5,y,z+0.9), iso(x,y,z+0.9)]
    return face(corners, fill, stroke, sw=1.0)

def roof_gable(x, y, w, d, base_h, peak_h, fill_top, fill_side, stroke="#2d4a6b"):
    """Gable roof on isometric box."""
    parts = []
    # Left slope (front face)
    ridge_x = x + w/2
    ridge_y = y
    p1 = iso(x, y, base_h); p2 = iso(x+w, y, base_h)
    ridge = iso(ridge_x, y, peak_h)
    parts.append(face([p1, p2, ridge], fill_top, stroke))
    # Right slope (right face)
    p3 = iso(x+w, y+d, base_h); p4 = iso(x, y+d, base_h)
    ridge2 = iso(ridge_x, y+d, peak_h)
    parts.append(face([p2, p3, ridge2, ridge], fill_side, stroke))
    # Ridge line
    parts.append(f'<line x1="{iso(ridge_x,y,peak_h)[0]:.1f}" y1="{iso(ridge_x,y,peak_h)[1]:.1f}" x2="{iso(ridge_x,y+d,peak_h)[0]:.1f}" y2="{iso(ridge_x,y+d,peak_h)[1]:.1f}" stroke="{stroke}" stroke-width="2"/>')
    return "\n".join(parts)

def flat_roof(x, y, w, d, h, color, stroke="#2d4a6b", parapet=0.2):
    """Flat roof with parapet."""
    parts = [box(x, y, w, d, parapet, color, color, color, stroke)]
    # move up by h offset — handled by caller shifting z
    return "\n".join(parts)

def tree(cx, cy, trunk_h=0.6, crown_r=0.7, fill="#5a9e5a", stroke="#2d4a6b"):
    tx, ty = iso(cx, cy, 0)
    tx2, ty2 = iso(cx, cy, trunk_h)
    return (f'<line x1="{tx:.1f}" y1="{ty:.1f}" x2="{tx2:.1f}" y2="{ty2:.1f}" stroke="#7a5c2e" stroke-width="3"/>'
            f'<ellipse cx="{tx2:.1f}" cy="{ty2-8:.1f}" rx="14" ry="10" fill="{fill}" stroke="{stroke}" stroke-width="1.2"/>')

def label(text, x, y, size=13, color="#1b3a5c", weight="700"):
    return f'<text x="{x}" y="{y}" font-size="{size}" font-family="Segoe UI,Arial,sans-serif" fill="{color}" font-weight="{weight}" text-anchor="middle">{text}</text>'

def badge(text, x, y, bg="#dde8f5", fg="#1b3a5c"):
    w = len(text) * 7 + 16
    return (f'<rect x="{x-w//2}" y="{y-14}" width="{w}" height="20" rx="10" fill="{bg}" stroke="#b0c4de" stroke-width="1"/>'
            f'<text x="{x}" y="{y}" font-size="11" font-family="Segoe UI,Arial,sans-serif" fill="{fg}" text-anchor="middle">{text}</text>')

def svg_wrap(content, title, tags, sqft, storeys, w=800, h=560):
    tag_els = ""
    x_start = w//2 - (len(tags)*90)//2 + 45
    for i, t in enumerate(tags):
        tag_els += badge(t, x_start + i*90, h-28)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#e8f2fb"/>
      <stop offset="100%" stop-color="#f5f8fb"/>
    </linearGradient>
    <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
      <line x1="0" y1="0" x2="0" y2="40" stroke="#d4e0ec" stroke-width="0.5"/>
    </pattern>
  </defs>
  <rect width="{w}" height="{h}" fill="url(#sky)"/>
  <rect width="{w}" height="{h}" fill="url(#grid)" opacity="0.4"/>
  <!-- ground shadow -->
  <ellipse cx="{w//2}" cy="{h-90}" rx="220" ry="30" fill="#c8d8e8" opacity="0.4"/>
  {content}
  <!-- labels -->
  <rect x="0" y="{h-62}" width="{w}" height="62" fill="rgba(255,255,255,0.88)"/>
  <line x1="0" y1="{h-62}" x2="{w}" y2="{h-62}" stroke="#b0c4de" stroke-width="1"/>
  {label(title, w//2, h-42, 15, "#1b3a5c")}
  {label(f"{storeys} storey · {sqft:,} sq ft", w//2, h-24, 11, "#466585", "400")}
  {tag_els}
</svg>'''

# Interior floor plan helper
def floor_plan(rooms, w=800, h=560, scale=55, cx=400, cy=300):
    """Generate a simple floor plan SVG for interior views."""
    COLORS = {
        'living': '#e8f0fa', 'bedroom': '#faf0e8', 'kitchen': '#e8faf0',
        'bathroom': '#f0e8fa', 'prayer': '#faf0e0', 'corridor': '#f5f5f5',
        'courtyard': '#e0f0e0', 'garage': '#f0f0f0', 'utility': '#f5f0e0',
    }
    parts = []
    # isometric floor plan projection (top view slightly angled)
    for room in rooms:
        rx, ry, rw, rd, rtype, rname = room
        col = COLORS.get(rtype, '#f0f0f0')
        # draw as isometric top face
        corners = [iso(rx,ry,0,cx,cy,scale), iso(rx+rw,ry,0,cx,cy,scale),
                   iso(rx+rw,ry+rd,0,cx,cy,scale), iso(rx,ry+rd,0,cx,cy,scale)]
        parts.append(face(corners, col, "#2d4a6b", 1.5))
        # room label at center
        mc = iso(rx+rw/2, ry+rd/2, 0, cx, cy, scale)
        parts.append(f'<text x="{mc[0]:.1f}" y="{mc[1]+4:.1f}" font-size="10" font-family="Segoe UI,Arial,sans-serif" fill="#2d4a6b" text-anchor="middle">{rname}</text>')
    return "\n".join(parts)

# ─── HOUSE DESIGNS ─────────────────────────────────────────────────────────────

def h001_exterior():
    """1-storey coastal house, cross-ventilation, prayer room."""
    parts = []
    # Ground
    g = [iso(0,0,0,400,320), iso(6,0,0,400,320), iso(6,5,0,400,320), iso(0,5,0,400,320)]
    parts.append(face(g, "#d8e8d0", "#b0c8b0"))
    # Main body
    parts.append(box(0.2, 0.2, 5.6, 4.6, 2.2,
                     "#f0f4f8", "#dce8f0", "#c8d8e8", "#2d4a6b"))
    # Prayer room alcove (protruding left)
    parts.append(box(0.2, 0.2, 1.2, 1.4, 2.2,
                     "#f5f0e8", "#ede0d0", "#ddd0c0", "#2d4a6b"))
    # Gable roof
    parts.append(roof_gable(0.2, 0.2, 5.6, 4.6, 2.2, 3.4,
                            "#b8cde0", "#8aabcc", "#2d4a6b"))
    # Wind vents on roof
    for yi in [0.8, 2.4]:
        v = [iso(2.6,yi,3.0,400,320), iso(3.0,yi,3.0,400,320),
             iso(3.0,yi,3.3,400,320), iso(2.6,yi,3.3,400,320)]
        parts.append(face(v, "#c0d8ec", "#2d4a6b", 1.2))
    # Windows
    parts.append(window(5.8, 1.0, 0.7, 'x', 0.8, 0.5, "#b8d4f0"))
    parts.append(window(5.8, 2.5, 0.7, 'x', 0.8, 0.5, "#b8d4f0"))
    parts.append(window(2.5, 0.2, 0.7, 'y', 0.7, 0.5, "#b8d4f0"))
    parts.append(window(4.0, 0.2, 0.7, 'y', 0.7, 0.5, "#b8d4f0"))
    # Door
    parts.append(door(3.0, 0.2, 0, 'y', "#8b6a3e"))
    # Crescent on prayer room
    pc = iso(0.8, 0.2, 2.4, 400, 320)
    parts.append(f'<text x="{pc[0]:.1f}" y="{pc[1]:.1f}" font-size="14" fill="#c0a050" text-anchor="middle">☽</text>')
    # Trees
    parts.append(tree(5.5, 4.3, 0.5, 0.6, "#4a8e4a"))
    return svg_wrap("\n".join(parts), "Concept Aster 3BR — cross-vent musalla",
                    ["Coastal", "Muslim prayer", "1 storey"], 1280, 1, 800, 560)

def h001_interior():
    rooms = [
        (0,0,2,2,'living','Living'),
        (2,0,1.5,1.2,'kitchen','Kitchen'),
        (3.5,0,1.5,1.2,'bedroom','Bed 1'),
        (0,2,1.5,2,'prayer','Musalla'),
        (1.5,2,1.5,2,'bedroom','Bed 2'),
        (3,2,0.8,2,'bathroom','Bath'),
        (3.8,2,1.2,2,'bedroom','Bed 3'),
        (2,1.2,1.5,0.8,'corridor','Corridor'),
    ]
    content = floor_plan(rooms, scale=55, cx=400, cy=300)
    # compass
    content += '<text x="720" y="80" font-size="11" font-family="Segoe UI,Arial,sans-serif" fill="#2d4a6b" text-anchor="middle">N ↑</text>'
    return svg_wrap(content, "Concept Aster 3BR — Interior floor plan",
                    ["Open plan", "Prayer room", "1,280 sq ft"], 1280, 1, 800, 560)

def h002_exterior():
    """2-storey courtyard house, hot-humid."""
    parts = []
    # Ground
    g = [iso(0,0,0,400,300), iso(7,0,0,400,300), iso(7,6,0,400,300), iso(0,6,0,400,300)]
    parts.append(face(g, "#c8d8c0", "#a8b8a0"))
    # Left wing
    parts.append(box(0, 0, 2.5, 6, 2.0, "#f2f6f0", "#dce8d8", "#c8d8c4"))
    parts.append(box(0, 0, 2.5, 6, 4.0, "#eff3ed", "#d8e4d4", "#c4d4c0"))
    # Right wing
    parts.append(box(4.5, 0, 2.5, 6, 2.0, "#f2f6f0", "#dce8d8", "#c8d8c4"))
    parts.append(box(4.5, 0, 2.5, 6, 4.0, "#eff3ed", "#d8e4d4", "#c4d4c0"))
    # Back
    parts.append(box(0, 4.5, 7, 1.5, 2.0, "#f2f6f0", "#dce8d8", "#c8d8c4"))
    parts.append(box(0, 4.5, 7, 1.5, 4.0, "#eff3ed", "#d8e4d4", "#c4d4c0"))
    # Courtyard floor (central)
    cy_g = [iso(2.5,0,0,400,300), iso(4.5,0,0,400,300),
            iso(4.5,4.5,0,400,300), iso(2.5,4.5,0,400,300)]
    parts.append(face(cy_g, "#e0ead8", "#b0c0a8"))
    # Courtyard plant
    parts.append(tree(3.5, 2.2, 0.5, 0.7, "#4a8e4a"))
    # Shading overhangs
    for storey_h in [2.0, 4.0]:
        oh = [iso(0,0,storey_h+0.3,400,300), iso(7,0,storey_h+0.3,400,300),
              iso(7,-0.4,storey_h+0.3,400,300), iso(0,-0.4,storey_h+0.3,400,300)]
        parts.append(face(oh, "#d8e8d0", "#b0c0a8", 1.2, 0.85))
    # Windows
    for yi in [0.8,2.5,4.0]:
        parts.append(window(0,yi,2.5,'x',0.6,0.4,"#b8d4f0"))
        parts.append(window(7,yi,2.5,'x',0.6,0.4,"#b8d4f0"))
    # Flat roofs with parapets
    parts.append(box(0,0,2.5,6,4.3,"#e0e8dc","#d0dcd0","#c8d4c4"))
    parts.append(box(4.5,0,2.5,6,4.3,"#e0e8dc","#d0dcd0","#c8d4c4"))
    parts.append(box(0,4.5,7,1.5,4.3,"#e0e8dc","#d0dcd0","#c8d4c4"))
    return svg_wrap("\n".join(parts), "Concept Delta 4BR Courtyard",
                    ["Hot & humid", "Courtyard", "2 storeys"], 1680, 2, 800, 560)

def h002_interior():
    rooms = [
        (0,0,2,2.5,'living','Living'),
        (2,0,3,1.5,'corridor','Entry / Corridor'),
        (5,0,2,2.5,'bedroom','Bed 1'),
        (0,2.5,2,2,'kitchen','Kitchen'),
        (2,1.5,3,3,'courtyard','Courtyard'),
        (5,2.5,2,2,'bedroom','Bed 2'),
        (0,4.5,2,1.5,'bedroom','Bed 3'),
        (2,4.5,3,1.5,'bathroom','Bath + Utility'),
        (5,4.5,2,1.5,'bedroom','Bed 4'),
    ]
    content = floor_plan(rooms, scale=48, cx=400, cy=280)
    return svg_wrap(content, "Concept Delta 4BR — Interior plan (GF)",
                    ["Courtyard", "4 bedroom", "1,680 sq ft"], 1680, 2, 800, 560)

def h003_exterior():
    """2-storey narrow urban infill."""
    parts = []
    # Ground narrow
    g = [iso(0,0,0,420,330), iso(3.5,0,0,420,330), iso(3.5,5,0,420,330), iso(0,5,0,420,330)]
    parts.append(face(g, "#c8c8c8", "#a8a8a8"))
    # Neighbouring buildings hint
    parts.append(box(-2,0,1.5,5,3.5,"#d8d8d4","#c8c8c4","#b8b8b4","#666"))
    parts.append(box(3.5,0,1.5,5,4.5,"#d8d4d4","#c8c4c4","#b8b4b4","#666"))
    # Main house GF + FF
    parts.append(box(0,0,3.5,5,2.2,"#f4f2ee","#e8e0d8","#dcd4c8"))
    parts.append(box(0,0,3.5,5,4.5,"#f0eeea","#e4dcd4","#d8d0c8"))
    # Floor line
    fl = [iso(0,0,2.2,420,330), iso(3.5,0,2.2,420,330)]
    parts.append(f'<line x1="{fl[0][0]:.1f}" y1="{fl[0][1]:.1f}" x2="{fl[1][0]:.1f}" y2="{fl[1][1]:.1f}" stroke="#2d4a6b" stroke-width="2" stroke-dasharray="4,3"/>')
    # Flat roof parapet
    parts.append(box(0,0,3.5,5,4.8,"#e0dcd8","#d8d4d0","#d0ccc8"))
    # Windows grid
    for z in [0.7,1.4,2.9,3.6]:
        parts.append(window(3.5,0.6,z,'x',0.6,0.5,"#b8d4f0"))
        parts.append(window(3.5,2.0,z,'x',0.6,0.5,"#b8d4f0"))
        parts.append(window(1.0,0,z,'y',0.6,0.5,"#b8d4f0"))
        parts.append(window(2.4,0,z,'y',0.6,0.5,"#b8d4f0"))
    # Door
    parts.append(door(1.5,0,0,'y',"#5a3e2a"))
    return svg_wrap("\n".join(parts), "Concept Nova 2BR — Urban infill",
                    ["Urban", "Narrow lot", "2 storeys"], 860, 2, 800, 560)

def h003_interior():
    rooms = [
        (0,0,2,1.5,'living','Living / Dining'),
        (2,0,1.5,1.5,'kitchen','Kitchen'),
        (0,1.5,3.5,0.6,'corridor','Staircase'),
        (0,2.1,2,2,'bedroom','Bed 1'),
        (2,2.1,1.5,1,'bathroom','Bath'),
        (2,3.1,1.5,1,'bedroom','Bed 2'),
        (0,4.1,3.5,0.9,'utility','Utility'),
    ]
    content = floor_plan(rooms, scale=52, cx=420, cy=300)
    return svg_wrap(content, "Concept Nova 2BR — Interior plan",
                    ["Compact", "2 bedroom", "860 sq ft"], 860, 2, 800, 560)

def h004_exterior():
    """1-storey compact cold climate."""
    parts = []
    # Snowy ground
    g = [iso(0,0,0,400,330), iso(6,0,0,400,330), iso(6,5,0,400,330), iso(0,5,0,400,330)]
    parts.append(face(g, "#e8eef4", "#c8d4e0"))
    # Main body — thick walls (inset windows)
    parts.append(box(0.3,0.3,5.4,4.4,2.5,"#f0ece8","#e4dcd8","#d8d0cc"))
    # Deep-set windows (recessed)
    for yi in [0.8,2.5]:
        parts.append(window(5.7,yi,0.8,'x',0.7,0.5,"#b8d4f0"))
    for xi in [1.5,3.5]:
        parts.append(window(xi,0.3,0.8,'y',0.7,0.5,"#b8d4f0"))

    # Steep gable roof (cold climate)
    parts.append(roof_gable(0.3,0.3,5.4,4.4,2.5,4.2,"#8090a8","#606878"))
    # Chimney
    parts.append(box(4.0,0.8,0.5,0.5,4.8,"#808080","#686868","#585858"))
    # Smoke wisps
    cs = iso(4.25,1.05,5.0,400,330)
    parts.append(f'<text x="{cs[0]:.1f}" y="{cs[1]:.1f}" font-size="18" fill="#c0c0c0" opacity="0.7">~</text>')
    # Door with awning
    parts.append(door(2.8,0.3,0,'y',"#6b4c2e"))
    aw = [iso(2.5,0.3,1.2,400,330), iso(3.5,0.3,1.2,400,330),
          iso(3.5,-0.1,1.2,400,330), iso(2.5,-0.1,1.2,400,330)]
    parts.append(face(aw,"#9090a0","#606060",1.2))
    return svg_wrap("\n".join(parts), "Concept Atlas 3BR — Cold climate compact",
                    ["Cold winter", "3 bedroom", "1 storey"], 1180, 1, 800, 560)

def h004_interior():
    rooms = [
        (0,0,2.5,2,'living','Living room'),
        (2.5,0,2.5,1.2,'kitchen','Kitchen / Dining'),
        (5,0,1,2,'utility','Utility'),
        (0,2,2,2.5,'bedroom','Bed 1 (master)'),
        (2,2,1.5,2.5,'bedroom','Bed 2'),
        (3.5,2,1.5,1.5,'bedroom','Bed 3'),
        (3.5,3.5,1.5,1,'bathroom','Bath'),
        (5,2,1,2.5,'bathroom','WC + Hall'),
    ]
    content = floor_plan(rooms, scale=52, cx=400, cy=290)
    return svg_wrap(content, "Concept Atlas 3BR — Interior plan",
                    ["Compact", "3 bedroom", "1,180 sq ft"], 1180, 1, 800, 560)

def h005_exterior():
    """2-storey raised flood-resilient house on stilts."""
    parts = []
    # Water / ground hint
    g = [iso(0,0,0,400,350), iso(7,0,0,400,350), iso(7,6,0,400,350), iso(0,6,0,400,350)]
    parts.append(face(g, "#d0e8f8", "#a8c8e8"))
    # Water ripples
    for yi in [1,3,5]:
        r1 = iso(0.5,yi,0,400,350); r2 = iso(6,yi,0,400,350)
        parts.append(f'<line x1="{r1[0]:.1f}" y1="{r1[1]:.1f}" x2="{r2[0]:.1f}" y2="{r2[1]:.1f}" stroke="#a0c0e0" stroke-width="1" stroke-dasharray="8,4" opacity="0.6"/>')
    # Stilts
    for sx, sy in [(0.8,0.8),(0.8,5.0),(6.0,0.8),(6.0,5.0),(3.4,0.8),(3.4,5.0)]:
        s0 = iso(sx,sy,0,400,350); s1 = iso(sx,sy,1.5,400,350)
        parts.append(f'<line x1="{s0[0]:.1f}" y1="{s0[1]:.1f}" x2="{s1[0]:.1f}" y2="{s1[1]:.1f}" stroke="#7a5a3a" stroke-width="5"/>')
    # Platform / base
    parts.append(box(0.5,0.5,6,5,1.7,"#d0c8b8","#c0b8a8","#b8b0a0"))
    # GF house body
    parts.append(box(0.5,0.5,6,5,3.8,"#f4f0ec","#e8e0d8","#dcd4cc"))
    # FF
    parts.append(box(0.5,0.5,6,5,5.8,"#f0ede8","#e4dcd4","#d8d0c8"))
    # Gable roof
    parts.append(roof_gable(0.5,0.5,6,5,5.8,7.2,"#a0b8c8","#7898b0"))
    # External stairs
    stair_pts = [iso(3.0,-0.2,0,400,350), iso(3.8,-0.2,0,400,350),
                 iso(3.8,0.5,1.7,400,350), iso(3.0,0.5,1.7,400,350)]
    parts.append(face(stair_pts,"#c8b8a0","#a8a090",1.2))
    # Windows
    for z in [2.2,4.2]:
        parts.append(window(6.5,1.0,z,'x',0.8,0.5,"#b8d4f0"))
        parts.append(window(6.5,3.0,z,'x',0.8,0.5,"#b8d4f0"))
    # Prayer crescent
    pc = iso(1.0,0.5,6.5,400,350)
    parts.append(f'<text x="{pc[0]:.1f}" y="{pc[1]:.1f}" font-size="14" fill="#c0a050" text-anchor="middle">☽</text>')
    return svg_wrap("\n".join(parts), "Concept Tide 4BR — Flood-resilient raised",
                    ["Flood-resilient", "Raised", "2 storeys"], 1760, 2, 800, 560)

def h005_interior():
    rooms = [
        (0,0,3,2,'living','Living / Dining'),
        (3,0,2,1.5,'kitchen','Kitchen'),
        (5,0,1.5,2,'prayer','Musalla'),
        (0,2,2,2,'bedroom','Bed 1 (master)'),
        (2,2,2,2,'bedroom','Bed 2'),
        (4,2,1.5,1.2,'bathroom','Bath 1'),
        (4,3.2,1.5,0.8,'utility','Utility'),
        (5.5,2,1,2,'bedroom','Bed 3'),
        (0,4,3.5,2,'bedroom','Bed 4'),
        (3.5,4,3,2,'bathroom','Bath 2 + WC'),
    ]
    content = floor_plan(rooms, scale=46, cx=400, cy=290)
    return svg_wrap(content, "Concept Tide 4BR — Interior plan (GF)",
                    ["4 bedroom", "Prayer room", "1,760 sq ft"], 1760, 2, 800, 560)

def h006_exterior():
    """1-storey wheelchair-friendly, temperate."""
    parts = []
    # Ground with garden
    g = [iso(0,0,0,400,320), iso(7,0,0,400,320), iso(7,6,0,400,320), iso(0,6,0,400,320)]
    parts.append(face(g, "#d4e8cc", "#b4c8ac"))
    # Wide garden path
    path = [iso(2.5,-0.5,0,400,320), iso(4.0,-0.5,0,400,320),
            iso(4.0,0.5,0,400,320), iso(2.5,0.5,0,400,320)]
    parts.append(face(path,"#d8cfc0","#b8b0a0"))
    # Accessibility ramp
    ramp = [iso(2.5,-0.3,0,400,320), iso(3.8,-0.3,0,400,320),
            iso(3.8,0.3,0.3,400,320), iso(2.5,0.3,0.3,400,320)]
    parts.append(face(ramp,"#c8c0b0","#a8a098",1.0))
    # Main body (no steps, all ground level)
    parts.append(box(0.3,0.3,6.4,5.4,2.4,"#f4f2f0","#e8e4e0","#dcd8d4"))
    # Wide doorways (double-width doors)
    parts.append(door(2.5,0.3,0,'y',"#8b6a3e"))
    parts.append(door(3.1,0.3,0,'y',"#8b6a3e"))
    # Gable roof — gentle slope
    parts.append(roof_gable(0.3,0.3,6.4,5.4,2.4,3.3,"#c8b8b0","#a89890"))
    # Large accessible windows
    for yi in [0.8,2.8]:
        parts.append(window(6.7,yi,0.4,'x',1.0,0.8,"#b8d4f0"))
    # Garden features
    parts.append(tree(6.2,5.0,0.6,0.7,"#5a9e5a"))
    parts.append(tree(0.5,4.8,0.5,0.6,"#5a9e5a"))
    # Handrail on ramp
    rh = iso(2.5,-0.3,0.5,400,320); rh2 = iso(3.8,0.3,0.5,400,320)
    parts.append(f'<line x1="{rh[0]:.1f}" y1="{rh[1]:.1f}" x2="{rh2[0]:.1f}" y2="{rh2[1]:.1f}" stroke="#7a5a3a" stroke-width="3"/>')
    # Wheelchair symbol on door
    wc = iso(3.0,0.3,1.5,400,320)
    parts.append(f'<text x="{wc[0]:.1f}" y="{wc[1]:.1f}" font-size="16" fill="#4a7ab0" text-anchor="middle">♿</text>')
    return svg_wrap("\n".join(parts), "Concept Vale 3BR — Accessible design",
                    ["Temperate", "Wheelchair-friendly", "1 storey"], 1320, 1, 800, 560)

def h006_interior():
    rooms = [
        (0,0,3,2.5,'living','Living / Dining (open plan)'),
        (3,0,2.5,1.5,'kitchen','Kitchen'),
        (5.5,0,1.5,2.5,'bathroom','Bath (accessible)'),
        (0,2.5,2.5,3,'bedroom','Bed 1 (accessible)'),
        (2.5,2.5,2,2,'bedroom','Bed 2'),
        (4.5,2.5,2,2,'bedroom','Bed 3'),
        (2.5,4.5,2,1,'bathroom','Bath 2'),
        (4.5,4.5,2,1,'utility','Utility / Laundry'),
        (0,5.5,7,0.5,'corridor','Wide corridor (1.5m min)'),
    ]
    content = floor_plan(rooms, scale=48, cx=400, cy=280)
    return svg_wrap(content, "Concept Vale 3BR — Interior plan (accessible)",
                    ["Wide corridors", "3 bedroom", "1,320 sq ft"], 1320, 1, 800, 560)

# ─── MAIN ──────────────────────────────────────────────────────────────────────

houses = {
    "h001-exterior": h001_exterior,
    "h001-interior": h001_interior,
    "h002-exterior": h002_exterior,
    "h002-interior": h002_interior,
    "h003-exterior": h003_exterior,
    "h003-interior": h003_interior,
    "h004-exterior": h004_exterior,
    "h004-interior": h004_interior,
    "h005-exterior": h005_exterior,
    "h005-interior": h005_interior,
    "h006-exterior": h006_exterior,
    "h006-interior": h006_interior,
}

for name, fn in houses.items():
    svg = fn()
    path = os.path.join(OUT, f"{name}.svg")
    with open(path, "w") as f:
        f.write(svg)
    print(f"  ✓ {name}.svg")

print(f"\nAll {len(houses)} images generated in {OUT}")
