"""r/dataisbeautiful collage for rocket-launches: 2400 x 3200 px, light background. Numbers from data/results.json.
Labels sit on open sea or on the paper around the globe, with a white halo; no leader lines."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
from figstyle import *
import pandas as pd
import matplotlib.patheffects as pe
from matplotlib.patches import Patch, Circle, Wedge
from matplotlib.lines import Line2D

R = jload(f"{DATA}/results.json")
PORTS = port_rows()
BGc = "#F7F5F0"; SEAc = "#E9EFF2"; LANDc = "#E2DDD1"
HALO = [pe.withStroke(linewidth=4, foreground=SEAc)]
HALOP = [pe.withStroke(linewidth=4, foreground=BGc)]
pk, ob, src = R["peaks"], R["objects"], R["source"]
Y = pd.DataFrame(R["years"]).set_index("y")

fig = plt.figure(figsize=(12, 16.0), dpi=200, facecolor=BGc)
fig.text(.045, 0.9844, "Every rocket launch since Sputnik", fontproperties=DISP, fontsize=44, color=FG, va="top")
fig.text(.045, 0.9375, f"{src['n']:,} orbital launch attempts from {src['n_ports']} spaceports, 1957 to {src['last_year']}. The Cold War record of {pk['coldwar_n']} launches in {pk['coldwar_year']}\n"
         f"stood for {pk['first_over_coldwar'] - pk['coldwar_year']} years. In {pk['record_year']} the world launched {pk['record_n']}, more than half of them SpaceX Falcon 9s.",
         fontproperties=SERP, fontsize=14, color=FG, va="top", linespacing=1.45)

# ---- map
ax = fig.add_axes([0, 0.5062, 1, 0.3844])
outline(ax, fc=SEAc, ec="#C9CDD0", lw=.8); world(ax, lw=.3, land=LANDc, ec=BGc)
K = .95e6 / np.sqrt(max(p["n"] for p in PORTS))
la, lo = circle_ll(*NEMO, NEMO_R_KM); cx, cy = proj(lo, la)
ax.fill(cx, cy, fc=NAVY, alpha=.07, zorder=2); ax.plot(cx, cy, color=NAVY, lw=1.1, ls=(0, (5, 4)), zorder=2)
nx, ny = proj(NEMO[1], NEMO[0]); ax.scatter([nx], [ny], s=90, c=NAVY, ec="#fff", lw=1.6, zorder=8)
for p in sorted(PORTS, key=lambda r: -r["n"]):
    x, y = proj(p["lon"], p["lat"]); pie(ax, float(x), float(y), max(K * np.sqrt(p["n"]), 6e4), p["b"], [BCOL[b] for b in BN], lw=.9)
for g in R["stations"]:
    if g["lat"] is None: continue
    x, y = proj(g["lon"], g["lat"]); ax.scatter([x], [y], marker="D", s=34, c=NAVY if g["status"] == "D" else "#fff", ec=NAVY, lw=1.2, zorder=9)
PT = R["ports"]
# ---- labels: placed automatically on open sea, then checked.
# Rule: a label's box (with its halo) must stay at least LAND_MARGIN from every Natural Earth land polygon and must not
# touch any bubble or marker; a leader line, where one is needed, must not cross another label.
from shapely.geometry import shape as _shape, box as _box, Point as _Pt, LineString as _LS, Polygon as _Poly
from shapely.ops import unary_union, transform as _tf
from shapely.prepared import prep as _prep
LAND_MARGIN = 25e3
_land = []
for f in jload(f"{GEO}/ne_50m_land.geojson")["features"]:
    g = _shape(f["geometry"]); gs = g.geoms if g.geom_type == "MultiPolygon" else [g]
    for q in gs:
        xy = np.array(q.exterior.coords); x, y = EE.transform(np.clip(xy[:, 0], -179.99, 179.99), np.clip(xy[:, 1], -89.9, 89.9))
        _land.append(_Poly(np.column_stack([x, y])).buffer(0))
LAND = unary_union(_land).buffer(LAND_MARGIN); LANDP = _prep(LAND)
BUB = []   # (x, y, r) of every drawn bubble or marker
for p in PORTS:
    x, y = proj(p["lon"], p["lat"]); BUB.append((float(x), float(y), max(K * np.sqrt(p["n"]), 6e4)))
for g in R["stations"]:
    if g["lat"] is not None:
        x, y = proj(g["lon"], g["lat"]); BUB.append((float(x), float(y), 1.6e5))
BUB.append((float(nx), float(ny), 1.8e5))
BUBG = unary_union([_Pt(x, y).buffer(r) for x, y, r in BUB] + [_Poly(np.column_stack([cx, cy])).buffer(3e4)])   # bubbles, markers and the dashed Point Nemo zone
fig.canvas.draw(); REN = fig.canvas.get_renderer()
PLACED = []   # (name, text artist, shapely box)
LINES = []    # (name, LineString)


def tbox(t):
    bb = t.get_window_extent(REN).expanded(1.0, 1.0)
    (x0, y0), (x1, y1) = ax.transData.inverted().transform([[bb.x0 - 4, bb.y0 - 3], [bb.x1 + 4, bb.y1 + 3]])
    return _box(x0, y0, x1, y1)


def bad(b):
    x0, x1 = ax.get_xlim(); y0, y1 = ax.get_ylim()
    if not _box(x0 + 1e5, y0 + 1e5, x1 - 1e5, y1 - 1e5).contains(b): return True
    return LANDP.intersects(b) or BUBG.intersects(b) or any(b.intersects(o) for _, _, o in PLACED) or any(b.intersects(l) for _, l in LINES)


def place(name, s, prefs, ha="center", col=FG, size=10.5, w="medium", target=None, lead_gap=2.5e5, maxr=30, scan=None):
    """Try each preferred (lon, lat), then a widening ring of offsets around the first; keep the first clean spot.
    target: (lon, lat, r) of the bubble; a leader is drawn when the label sits more than lead_gap from its edge."""
    t = ax.text(0, 0, s, ha=ha, va="center", fontsize=size, color=col, family=MONO, linespacing=1.15, zorder=10, path_effects=HALO, fontweight=w)
    lon0, lat0 = prefs[0]
    if scan:   # every whole degree in a window, nearest to the first preference first
        cands = sorted([(lo, la) for lo in range(scan[0], scan[1] + 1) for la in range(scan[2], scan[3] + 1)], key=lambda q: (q[0] - lon0) ** 2 + (q[1] - lat0) ** 2)
    else: cands = list(prefs) + [(lon0 + dx, lat0 + dy) for r in range(1, maxr + 1) for dx in range(-r, r + 1) for dy in range(-r, r + 1) if max(abs(dx), abs(dy)) == r]
    for lon, lat in cands:
        if lon == "xy": x, y = lat              # a position on the paper, in map metres
        elif abs(lat) > 85: continue
        else: x, y = proj(((lon + 180) % 360) - 180, lat)
        t.set_position((float(x), float(y))); b = tbox(t)
        if bad(b): continue
        ln = None
        if target is not None:
            tx, ty = proj(target[0], target[1]); c = _Pt(float(tx), float(ty)); gap = b.distance(c) - target[2]
            if gap > lead_gap:
                from shapely.ops import nearest_points
                pb, _ = nearest_points(b, c); d = np.hypot(pb.x - c.x, pb.y - c.y)
                e = (c.x + (pb.x - c.x) * target[2] / d, c.y + (pb.y - c.y) * target[2] / d)
                ln = _LS([(pb.x, pb.y), e])
                if any(ln.intersects(o) for _, _, o in PLACED): continue
        PLACED.append((name, t, b))
        if ln is not None:
            LINES.append((name, ln)); ax.plot(*ln.xy, color=FG, lw=.75, zorder=9)
        return
    raise RuntimeError("no clean spot for " + name)


def tgt(port):
    p = PT[port]; return (p["lon"], p["lat"], max(K * np.sqrt(p["n"]), 6e4))


place("Plesetsk", f"PLESETSK\n{PT['Plesetsk']['n']:,}", [(0, 70)], target=tgt("Plesetsk"))
place("Baikonur", f"BAIKONUR\n{PT['Baikonur']['n']:,}", [(64, 12)], target=tgt("Baikonur"))
place("Cape", f"CAPE CANAVERAL\nand KENNEDY\n{PT['Cape Canaveral and Kennedy']['n']:,}", [(-62, 24)], "left", target=tgt("Cape Canaveral and Kennedy"))
place("Vandenberg", f"VANDENBERG\n{PT['Vandenberg']['n']:,}", [(-133, 31)], "right", target=tgt("Vandenberg"))
place("Kourou", f"KOUROU\n{PT['Kourou']['n']:,}", [(-44, 12)], "left", target=tgt("Kourou"))
place("Sriharikota", f"SRIHARIKOTA\n{PT['Sriharikota']['n']:,}", [(88, 4)], "center", target=tgt("Sriharikota"))
place("China", f"CHINA\nJiuquan {PT['Jiuquan']['n']}\nXichang {PT['Xichang']['n']}\nTaiyuan {PT['Taiyuan']['n']}\nWenchang {PT['Wenchang']['n']}", [(160, 34)], "center", col="#8A5E05", size=9.5, target=tgt("Jiuquan"), lead_gap=9e6, scan=(135, 178, 0, 52))
place("Tanegashima", f"JAPAN\nTanegashima\n{PT['Tanegashima']['n']}", [("xy", (x * 1e5, y * 1e5)) for y in range(76, 60, -2) for x in range(150, 120, -2)], "center", col="#A8436A", size=9.5, target=tgt("Tanegashima"), lead_gap=3e5, maxr=0)
place("Mahia", f"MAHIA (Rocket Lab) {PT['Mahia']['n']}", [(166, -48)], "right", size=10, target=tgt("Mahia"))
place("Nemo", "POINT NEMO\nspacecraft cemetery", [(-112, -21)], "center", col=NAVY, size=10.5, w="bold", target=(NEMO[1], NEMO[0], 1.8e5), lead_gap=3e6)
ST = {g["name"]: g for g in R["stations"]}
for nm, pref, ha in (("Tiangong 1", (-151, -13.6), "left"), ("Mir", (-165, -26.2), "left"), ("Tiangong 2", (-152, -36), "right"),
                     ("Salyut 2", (165, -13), "center"), ("Skylab", (124, -41), "center")):
    g = ST[nm]; place(nm, nm, [pref], ha, col=NAVY, size=9, w="normal", target=(g["lon"], g["lat"], 1.6e5), lead_gap=6e5, maxr=12)
# final check of every map label and leader line
for nm, t, b in PLACED:
    assert not LANDP.intersects(b) and not BUBG.intersects(b), nm
    x0, x1 = ax.get_xlim(); assert x0 < b.bounds[0] and b.bounds[2] < x1, nm
    assert not any(b.intersects(o) for n2, _, o in PLACED if n2 != nm), nm
for nm, l in LINES:
    assert not any(l.intersects(o) for n2, _, o in PLACED if n2 != nm), nm
print("labels ok:", [(nm, round(float(np.degrees(0)), 0)) for nm, _, _ in PLACED][:0] or len(PLACED), "leaders:", [n for n, _ in LINES])


# size key on the paper, bottom left corner outside the globe
kx0, ky0 = -1.62e7, -8.2e6
KEYT = []
for i, n in enumerate((100, 500, 1500)):
    r = K * np.sqrt(n); xc = kx0 + i * 1.3e6 + (0 if i < 2 else .35e6)
    ax.add_patch(Circle((xc, ky0 + r), r, fc="none", ec=FG, lw=.9, zorder=9))
    KEYT.append(ax.text(xc - (0 if i < 2 else 5e5), ky0 - 4e5, f"{n:,}" + (" launches" if i == 2 else ""), ha="center" if i < 2 else "left", fontsize=9, color=FG, zorder=10))
fig.canvas.draw()
for kt in KEYT:
    assert not LANDP.intersects(tbox(kt)) and not any(tbox(kt).intersects(o) for _, _, o in PLACED), "size key label"

# ---- legend (full names) under the map
LEG = [Patch(color=BCOL[b], label=b) for b in BN] + [
    Line2D([], [], ls="", marker="o", ms=9, mfc=NAVY, mec="#fff", label="Point Nemo, the point farthest from land"),
    Line2D([], [], ls="", marker="D", ms=7, mfc=NAVY, mec=NAVY, label="space station deorbited on purpose"),
    Line2D([], [], ls="", marker="D", ms=7, mfc="#fff", mec=NAVY, label="space station that fell on its own"),
    Line2D([], [], ls=(0, (4, 3)), color=NAVY, lw=1.2, label=f"{NEMO_R_KM:,} km around Point Nemo (indicative)")]
LP = SERP.copy(); LP.set_size(11.5)
fig.text(.045, 0.4938, "Circle area: orbital launch attempts from each spaceport, 1957 to 2026. Colour: who launched them (the launch agency's country).", fontsize=9.6, color=MUT, va="top")
fig.legend(handles=LEG, loc="upper left", bbox_to_anchor=(.035, 0.4781), ncol=3, frameon=False, prop=LP, handletextpad=.4, columnspacing=1.2, labelspacing=.55)

# ---- numbers row
nums = [(f"{src['n']:,}", NAVY, "orbital launch attempts\nsince Sputnik, 1957"),
        (f"{pk['record_n']}", HOT, f"in {pk['record_year']}, a record, {pk['record_vs_coldwar_pct']:.0f}%\nabove the {pk['coldwar_year']} Cold War peak"),
        (f"{pk['spx_2025_pct']:.0f}%", COOL, f"of {pk['record_year']}'s launches were\nSpaceX's ({pk['spx_2025']})"),
        (f"{ob['came_down_pct']:.0f}%", "#8C8478", f"of the {ob['n']:,} catalogued\nobjects have fallen back")]
for i, (big, col, small) in enumerate(nums):
    xx = .045 + i * .235
    fig.text(xx, 0.3969, big, fontproperties=DISP, fontsize=36, color=col, va="top")
    fig.text(xx, 0.3562, small, family=MONO, fontsize=10.5, color=FG, va="top", linespacing=1.4)

# ---- stacked area: launches per year
a = fig.add_axes([.075, 0.1531, .875, 0.1406]); a.set_facecolor(BGc)
base = np.zeros(len(Y))
for b in BN:
    a.fill_between(Y.index, base, base + Y[b].values, color=BCOL[b], lw=0, alpha=.95); base += Y[b].values
a.set_xlim(1957, 2026); a.set_ylim(0, 350); spines(a); a.tick_params(labelsize=10); a.grid(axis="y", color=RULE, lw=.8); a.set_axisbelow(True)
a.set_title("Orbital launch attempts per year, by who launched them", family=MONO, fontsize=13, color=FG, loc="left", pad=10)
for y, v, t, dx, dy, ha in ((pk["coldwar_year"], pk["coldwar_n"], f"{pk['coldwar_year']}: {pk['coldwar_n']}, the Cold War peak", 0, 45, "left"),
                            (pk["dip_year"], pk["dip_n"], f"{pk['dip_year']}: {pk['dip_n']}, the post Cold War low", 0, 75, "center"),
                            (pk["record_year"], pk["record_n"], f"{pk['record_year']}: {pk['record_n']}", -1.2, -4, "right")):
    a.plot([y], [v], "o", color=FG, ms=4, zorder=5)
    if ha == "left": a.plot([y, y], [v + 5, v + dy - 10], color=FG, lw=.7)
    a.text(y + dx - (0.6 if ha == "left" else 0), v + dy, t, ha=ha, va="center", fontsize=10, color=FG, path_effects=HALOP, zorder=6)
a.text(2022.6, 288, f"2026 to Sept.: {pk['y2026_n']}", ha="right", fontsize=9, color=MUT, path_effects=HALOP)
a.text(1978, 75, "Soviet Union and Russia", fontsize=10.5, color="#fff", fontweight="medium", ha="center")
a.text(1976, 9, "United States", fontsize=10.5, color="#fff", fontweight="medium", ha="center")
a.text(2015.8, 155, "China", fontsize=10.5, color="#9A6A06", fontweight="medium", ha="center", path_effects=HALOP)

# ---- small panels
DY = pd.DataFrame(R["down_years"]).set_index("y")
b2 = fig.add_axes([.075, 0.0688, .40, 0.047]); b2.set_facecolor(BGc)
b2.bar(DY.index, DY.n, color="#8C8478", width=.85); spines(b2); b2.tick_params(labelsize=9); b2.set_xlim(1956, 2027)
b2.set_title("Catalogued objects falling back each year", family=MONO, fontsize=11, color=FG, loc="left", pad=6)
b2.text(1960, 2300, f"2022: {ob['down_peak_n']:,}, mostly debris\nfrom a 2021 missile test", fontsize=9, color=FG, va="top")
b3 = fig.add_axes([.60, 0.0688, .36, 0.047]); b3.set_facecolor(BGc); b3.axis("off")
b3.set_title(f"Busiest spaceports in {pk['record_year']}", family=MONO, fontsize=11, color=FG, loc="left", pad=6)
for i, r in enumerate(R["busiest_2025"][:4]):
    nm = r["port"].replace(" and Kennedy", ""); yy = .88 - i * .25
    b3.text(0, yy, nm, fontsize=10, color=FG, va="center", transform=b3.transAxes)
    b3.barh([yy], [.5 * r["n"] / R["busiest_2025"][0]["n"]], left=.42, height=.15, color=HOT, transform=b3.transAxes)
    b3.text(.44 + .5 * r["n"] / R["busiest_2025"][0]["n"], yy, str(r["n"]), fontsize=9.5, va="center", transform=b3.transAxes)

fig.text(.045, .006, f"Source: GCAT, Jonathan C. McDowell, planet4589.org/space/gcat (CC BY 4.0), release {src['release']}; Point Nemo facts: Wikipedia; outlines: Natural Earth.\n"
         "Who launched = country of the launch agency as GCAT records it. Neighbouring sites merged (Cape Canaveral with Kennedy). 2026 is partial.\n"
         "Analysis and chart: Tristan Hotham, with Python and matplotlib  ·  maps.tristanhotham.com/rocket-launches", family=MONO, fontsize=8.4, color=MUT, linespacing=1.5, va="bottom")
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "every_rocket_launch.png")
fig.savefig(out, facecolor=BGc, dpi=200)
print("ok", out)
