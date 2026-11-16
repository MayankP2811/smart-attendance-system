"""Draw docs/images/classroom-setup.svg: where each part of the system sits.

Left: the corridor, with the fingerprint sensor and LCD next to the classroom door.
Right: the classroom seen from the front wall, where the camera hangs above the board
and photographs every student. The Raspberry Pi sits in a box in between.

    python scripts/draw_classroom.py
"""
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "docs" / "images" / "classroom-setup.svg"

SKIN = ["#f1c7a5", "#c89574", "#e0ac85", "#a8714f", "#f3d0b5", "#d9a37c"]
HAIR = ["#2b2b4a", "#1d1d1d", "#5a3a22", "#3b3054", "#1d1d1d", "#4a2f1f"]
SHIRT = ["#7380ec", "#2fd6a0", "#f2b33d", "#e88aa6", "#5aa9e6", "#9b8cf0", "#4cc38a"]


def student(x, y, s, i, absent=False):
    """Head and shoulders of a student sitting behind a desk, centred at x; y = desk top."""
    if absent:
        return (f'<rect x="{x - 26 * s:.1f}" y="{y - 52 * s:.1f}" width="{52 * s:.1f}" height="{46 * s:.1f}" rx="{8 * s:.1f}" '
                f'fill="#cfc6b8"/><rect x="{x - 26 * s:.1f}" y="{y - 52 * s:.1f}" width="{52 * s:.1f}" height="{10 * s:.1f}" '
                f'rx="{5 * s:.1f}" fill="#b9ae9c"/>')
    hx, hy, r = x, y - 58 * s, 17 * s
    long_hair = i % 3 == 1
    parts = [
        f'<path d="M{x - 30 * s:.1f} {y:.1f}c{2 * s:.1f} {-26 * s:.1f} {14 * s:.1f} {-36 * s:.1f} {30 * s:.1f} {-36 * s:.1f}'
        f's{28 * s:.1f} {10 * s:.1f} {30 * s:.1f} {36 * s:.1f}z" fill="{SHIRT[i % len(SHIRT)]}"/>',
    ]
    if long_hair:
        parts.append(f'<path d="M{hx - r * 1.05:.1f} {hy:.1f}v{r * 1.3:.1f}h{r * 2.1:.1f}v{-r * 1.3:.1f}z" fill="{HAIR[i % 6]}"/>')
    parts += [
        f'<circle cx="{hx:.1f}" cy="{hy:.1f}" r="{r:.1f}" fill="{SKIN[i % 6]}"/>',
        f'<path d="M{hx - r:.1f} {hy - 2 * s:.1f}c0 {-14 * s:.1f} {8 * s:.1f} {-20 * s:.1f} {r:.1f} {-20 * s:.1f}'
        f's{r:.1f} {6 * s:.1f} {r:.1f} {18 * s:.1f}c{-6 * s:.1f} {-6 * s:.1f} {-14 * s:.1f} {-8 * s:.1f} {-22 * s:.1f} {-7 * s:.1f}'
        f'c{-6 * s:.1f} {1 * s:.1f} {-9 * s:.1f} {4 * s:.1f} {-12 * s:.1f} {9 * s:.1f}z" fill="{HAIR[i % 6]}"/>',
        f'<circle cx="{hx - 6 * s:.1f}" cy="{hy + 2 * s:.1f}" r="{1.8 * s:.1f}" fill="#2d3250"/>',
        f'<circle cx="{hx + 6 * s:.1f}" cy="{hy + 2 * s:.1f}" r="{1.8 * s:.1f}" fill="#2d3250"/>',
        f'<path d="M{hx - 5 * s:.1f} {hy + 9 * s:.1f}q{5 * s:.1f} {4 * s:.1f} {10 * s:.1f} 0" stroke="#7a4b3a" '
        f'stroke-width="{1.5 * s:.1f}" fill="none" stroke-linecap="round"/>',
    ]
    return "".join(parts)


def classroom_rows():
    """Four rows of desks; the back row is smaller and higher (simple perspective)."""
    out = []
    rows = [  # scale, desk top y, number of students, seats left empty
        (0.56, 342, 6, {4}),
        (0.70, 418, 6, set()),
        (0.85, 512, 5, {1}),
        (1.00, 622, 5, set()),
    ]
    idx = 0
    for s, y, n, empty in rows:
        width = 640 * s + 120
        x0 = 840 - width / 2
        step = width / n
        for k in range(n):
            x = x0 + step * (k + 0.5)
            out.append(student(x, y, s, idx, absent=k in empty))
            idx += 1
        out.append(f'<rect x="{x0 - 6:.1f}" y="{y:.1f}" width="{width + 12:.1f}" height="{26 * s:.1f}" rx="{5 * s:.1f}" fill="#b07a4f"/>')
        out.append(f'<rect x="{x0 - 6:.1f}" y="{y:.1f}" width="{width + 12:.1f}" height="{6 * s:.1f}" rx="{3 * s:.1f}" fill="#c99366"/>')
        for k in range(n + 1):
            lx = x0 + step * k
            out.append(f'<rect x="{lx - 3 * s:.1f}" y="{y + 26 * s:.1f}" width="{6 * s:.1f}" height="{40 * s:.1f}" fill="#7d5636"/>')
    return "\n    ".join(out)


def badge(x, y, n, title, lines, color="#1fb57d", width=302):
    h = 30 + 20 * len(lines)
    txt = "".join(f'<text x="{x + 46}" y="{y + 44 + 20 * i}" font-size="13" fill="#3c4a5f">{t}</text>' for i, t in enumerate(lines))
    return (f'<g><rect x="{x}" y="{y}" width="{width}" height="{h + 8}" rx="14" fill="#fff" stroke="#dde3ee"/>'
            f'<circle cx="{x + 24}" cy="{y + 25}" r="14" fill="{color}"/><text x="{x + 24}" y="{y + 30}" text-anchor="middle" '
            f'font-size="14" font-weight="700" fill="#fff">{n}</text>'
            f'<text x="{x + 46}" y="{y + 30}" font-size="14" font-weight="700" fill="#2d3250">{title}</text>{txt}</g>')


def main():
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 820" font-family="Poppins, Segoe UI, Helvetica, Arial, sans-serif">
  <title>Where the parts go: fingerprint sensor at the door, camera on the classroom wall, Raspberry Pi in between</title>
  <desc>A teacher scans a finger on the sensor outside the classroom door, and the LCD above it shows the lecture. Inside, a camera
  above the board photographs all the students at random moments during the lecture. A Raspberry Pi in a box on the wall between
  them matches the faces and saves the attendance to MySQL, which the website shows to students and faculty.</desc>
  <defs>
    <linearGradient id="fov" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3fdc9f" stop-opacity=".45"/>
      <stop offset="1" stop-color="#3fdc9f" stop-opacity=".06"/></linearGradient>
    <linearGradient id="corr" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e3e9f4"/><stop offset="1" stop-color="#d3dcec"/></linearGradient>
    <filter id="sh"><feDropShadow dx="0" dy="4" stdDeviation="5" flood-color="#1b2a4a" flood-opacity=".18"/></filter>
  </defs>
  <rect width="1280" height="820" fill="#f6f6f9"/>

  <!-- ===================== corridor ===================== -->
  <rect x="0" y="0" width="390" height="720" fill="url(#corr)"/>
  <rect x="0" y="640" width="390" height="80" fill="#c3ccdb"/>
  <text x="24" y="40" font-size="13" font-weight="700" letter-spacing="2" fill="#5b6b82">CORRIDOR · OUTSIDE THE DOOR</text>
  <!-- door -->
  <rect x="44" y="212" width="196" height="430" rx="4" fill="#5b4a3a"/>
  <rect x="58" y="226" width="168" height="416" fill="#a77b55"/>
  <rect x="74" y="250" width="136" height="150" rx="4" fill="#b98c64"/><rect x="74" y="420" width="136" height="190" rx="4" fill="#b98c64"/>
  <rect x="96" y="268" width="92" height="60" rx="4" fill="#cfe4f5" opacity=".9"/>
  <circle cx="204" cy="440" r="7" fill="#e3c04a"/>
  <rect x="86" y="176" width="112" height="28" rx="6" fill="#2d3250"/><text x="142" y="195" text-anchor="middle" font-size="13" font-weight="700" fill="#fff">ROOM 304</text>
  <!-- LCD + fingerprint sensor on the wall next to the door -->
  <g filter="url(#sh)">
    <rect x="262" y="280" width="116" height="52" rx="6" fill="#0e3a20"/>
    <rect x="268" y="286" width="104" height="40" rx="3" fill="#1f6b3d"/>
  </g>
  <text x="274" y="302" font-family="Menlo, Consolas, monospace" font-size="11" fill="#c8ffd8">Welcome maths</text>
  <text x="274" y="318" font-family="Menlo, Consolas, monospace" font-size="11" fill="#c8ffd8">Lecture started</text>
  <g filter="url(#sh)"><rect x="286" y="352" width="66" height="86" rx="12" fill="#2d3250"/></g>
  <rect x="298" y="364" width="42" height="50" rx="8" fill="#0d1a2f"/>
  <g transform="translate(305 372)" stroke="#5be3a8" stroke-width="2.4" fill="none" stroke-linecap="round">
    <path d="M6 30c0-9 3-14 8-14s8 5 8 14"/><path d="M1 28c0-14 6-21 13-21s13 7 13 21"/><path d="M11 34c0-6 1-10 3-10s3 4 3 11"/>
  </g>
  <circle cx="319" cy="426" r="4" fill="#3fdc9f"/>
  <!-- teacher scanning -->
  <g>
    <ellipse cx="170" cy="700" rx="62" ry="10" fill="#000" opacity=".08"/>
    <path d="M128 700l8-150h70l8 150z" fill="#2d3250"/>
    <path d="M118 560c4-60 26-86 53-86s49 26 53 86z" fill="#7380ec"/>
    <path d="M206 500c30 0 60-36 84-90" stroke="#7380ec" stroke-width="22" fill="none" stroke-linecap="round"/>
    <circle cx="294" cy="402" r="11" fill="#e0ac85"/>
    <rect x="126" y="520" width="40" height="52" rx="4" fill="#f2b33d" transform="rotate(-8 146 546)"/>
    <circle cx="171" cy="440" r="30" fill="#e0ac85"/>
    <path d="M140 436c0-26 14-38 31-38s31 12 31 34c-8-9-22-12-36-11-11 1-20 6-26 15z" fill="#3b3054"/>
  </g>
  <path d="M300 395 l10 -12 M308 405 l14 -6" stroke="#3fdc9f" stroke-width="3" stroke-linecap="round"/>

  <!-- ===================== classroom ===================== -->
  <polygon points="412,0 1280,0 1280,720 412,720" fill="#efe9de"/>
  <polygon points="412,0 1280,0 1150,70 540,70" fill="#f7f3ec"/>
  <polygon points="412,0 540,70 540,300 412,720" fill="#e4dccd"/>
  <polygon points="1280,0 1150,70 1150,300 1280,720" fill="#e4dccd"/>
  <rect x="540" y="70" width="610" height="230" fill="#f3eee4"/>
  <polygon points="540,300 1150,300 1280,720 412,720" fill="#d9cbb5"/>
  <g stroke="#cbbba1" stroke-width="2">
    <path d="M620 300 L560 720"/><path d="M720 300 L700 720"/><path d="M845 300 L845 720"/><path d="M970 300 L990 720"/><path d="M1070 300 L1130 720"/>
    <path d="M512 380 H1176"/><path d="M480 480 H1206"/><path d="M445 600 H1240"/>
  </g>
  <!-- back wall: windows, clock, notice board -->
  <g fill="#cfe4f5" stroke="#fff" stroke-width="4">
    <rect x="578" y="104" width="110" height="120" rx="4"/><rect x="1004" y="104" width="110" height="120" rx="4"/></g>
  <path d="M633 104v120M578 164h110M1059 104v120M1004 164h110" stroke="#fff" stroke-width="3"/>
  <circle cx="975" cy="134" r="18" fill="#fff" stroke="#2d3250" stroke-width="4"/><path d="M975 134v-10M975 134l7 4" stroke="#2d3250" stroke-width="3" stroke-linecap="round"/>
  <rect x="742" y="160" width="206" height="90" rx="6" fill="#d8b98a"/><g fill="#fff"><rect x="756" y="172" width="54" height="40"/><rect x="822" y="176" width="44" height="58"/><rect x="878" y="170" width="56" height="34"/></g>
  <!-- the camera's view -->
  <polygon points="845,96 430,720 1265,720" fill="url(#fov)"/>
  <path d="M845 96 L430 720 M845 96 L1265 720" stroke="#1fb57d" stroke-width="2" stroke-dasharray="7 6" fill="none"/>
  <!-- students -->
    {classroom_rows()}
  <!-- camera on the front wall (the viewer's wall), above the board -->
  <rect x="780" y="0" width="130" height="16" fill="#2d3250"/>
  <rect x="838" y="14" width="14" height="40" fill="#2d3250"/>
  <g filter="url(#sh)">
    <rect x="800" y="46" width="92" height="56" rx="12" fill="#2d3250"/>
    <circle cx="846" cy="80" r="21" fill="#7380ec"/><circle cx="846" cy="80" r="10" fill="#0d1a2f"/><circle cx="842" cy="76" r="3" fill="#fff"/>
    <circle cx="880" cy="58" r="4" fill="#ff5a5a"/>
  </g>

  <!-- ===================== dividing wall with the Raspberry Pi ===================== -->
  <rect x="390" y="0" width="22" height="720" fill="#b8c2d3"/>
  <g filter="url(#sh)">
    <rect x="356" y="96" width="92" height="76" rx="10" fill="#fff" stroke="#c9d1df"/>
  </g>
  <rect x="368" y="108" width="68" height="44" rx="5" fill="#1f6b3d"/>
  <rect x="392" y="118" width="20" height="20" rx="2" fill="#2b2b2b"/>
  <g fill="#e3c04a"><circle cx="374" cy="113" r="2"/><circle cx="381" cy="113" r="2"/><circle cx="388" cy="113" r="2"/><circle cx="395" cy="113" r="2"/></g>
  <text x="402" y="166" text-anchor="middle" font-size="10" font-weight="700" fill="#2d3250">Raspberry Pi</text>
  <path d="M378 172 V286" stroke="#5b6b82" stroke-width="3" stroke-dasharray="6 5" fill="none"/>
  <path d="M330 172 V280 M330 172 H378" stroke="#5b6b82" stroke-width="3" stroke-dasharray="6 5" fill="none"/>
  <path d="M448 120 H780" stroke="#5b6b82" stroke-width="3" stroke-dasharray="6 5" fill="none"/>
  <!-- wifi to the website -->
  <g transform="translate(402 70)" fill="none" stroke="#7380ec" stroke-width="3" stroke-linecap="round">
    <path d="M-14 0a20 20 0 0 1 28 0"/><path d="M-24 -9a34 34 0 0 1 48 0"/></g>

  <!-- ===================== labels ===================== -->
  <rect x="0" y="720" width="1280" height="100" fill="#f6f6f9"/>
  {badge(16, 732, 1, "Faculty scans a finger at the door", ["The finger tells which subject's lecture", "starts. The LCD greets the teacher."])}
  {badge(332, 732, 2, "Camera on the wall, inside", ["Photographs the whole class at random", "moments in the lecture (6 per hour)."], "#7380ec")}
  {badge(648, 732, 3, "Raspberry Pi in between", ["Matches every face and saves the", "result to MySQL after each photo."], "#2d3250")}
  {badge(964, 732, 4, "Present = seen in at least 60 %", ["Leaving early shows up as absent.", "The website updates straight away."], "#e5484d")}
</svg>
'''
    OUT.write_text(svg, encoding="utf-8")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
