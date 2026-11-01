"""Header card, blog figures (release/blog/b_*.png) and paper figures (release/paper/f_*.png). Numbers from data/results.json."""
import pandas as pd
import matplotlib.patheffects as pe
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from figstyle import *

R = jload(f"{DATA}/results.json")
BL = os.path.join(ROOT, "release", "blog"); PA = os.path.join(ROOT, "release", "paper")
os.makedirs(BL, exist_ok=True); os.makedirs(PA, exist_ok=True)
Y = pd.DataFrame(R["years"]).set_index("y")
HALO = [pe.withStroke(linewidth=3.5, foreground=SEA)]
PORTS = port_rows()


def both(fig, name, blog=True):
    fig.savefig(os.path.join(PA, "f_" + name + ".png"), dpi=200, facecolor=fig.get_facecolor())
    if blog:
        fig.savefig(os.path.join(BL, "b_" + name + ".png"), dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)


def stack_years(ax, lw=0):
    ys = Y.index.values; base = np.zeros(len(ys))
    for b in BN:
        v = Y[b].values; ax.fill_between(ys, base, base + v, color=BCOL[b], lw=lw, alpha=.95, label=b); base = base + v
    ax.set_xlim(1957, R["source"]["last_year"]); ax.set_ylim(0, 345); spines(ax)


# ---------- launches per year by bloc ----------
fig = plt.figure(figsize=(11, 5.6), facecolor=BG); ax = fig.add_axes([.07, .1, .9, .74]); ax.set_facecolor(BG)
stack_years(ax); ax.grid(axis="y", color=RULE, lw=.8); ax.set_axisbelow(True)
pk = R["peaks"]
for y, v, t, ha, dy in ((pk["coldwar_year"], pk["coldwar_n"], f"{pk['coldwar_year']}: {pk['coldwar_n']}\nCold War peak", "center", 14),
                        (pk["dip_year"], pk["dip_n"], f"{pk['dip_year']}: {pk['dip_n']}\npost Cold War low", "center", 45),
                        (pk["record_year"], pk["record_n"], f"{pk['record_year']}: {pk['record_n']}, a record", "right", 4)):
    ax.plot([y], [v], "o", color=FG, ms=4); ax.text(y - (1 if ha == "right" else 0), v + dy, t, ha=ha, va="bottom", fontsize=10, color=FG)
ax.set_ylabel("orbital launch attempts")
fig.legend(handles=[Patch(color=BCOL[b], label=b) for b in BN], loc="upper left", bbox_to_anchor=(.06, .99), ncol=4, frameon=False, fontsize=10)
both(fig, "years")

# ---------- world map of spaceports ----------
K = 1.0e6 / np.sqrt(max(p["n"] for p in PORTS))
fig = plt.figure(figsize=(12, 6.4), facecolor=BG); ax = fig.add_axes([0, 0, 1, .93])
outline(ax, fc=SEA, ec="#C9CDD0"); world(ax, ec=BG)
for p in sorted(PORTS, key=lambda r: -r["n"]):
    x, y = proj(p["lon"], p["lat"]); pie(ax, float(x), float(y), K * np.sqrt(p["n"]), p["b"], [BCOL[b] for b in BN])
LAB = {"Plesetsk": (1.0e6, 5e5, "left"), "Baikonur": (-1.35e6, -4e5, "right"), "Cape Canaveral and Kennedy": (9.5e5, -4e5, "left"), "Vandenberg": (-8e5, 0, "right"),
       "Kourou": (5e5, -2e5, "left"), "Jiuquan": (0, 8e5, "center"), "Xichang": (-5e5, -6e5, "right"), "Taiyuan": (6e5, 4e5, "left"), "Sriharikota": (4e5, -7e5, "left"),
       "Tanegashima": (5e5, -2e5, "left"), "Mahia": (-5e5, -5e5, "right"), "Wenchang": (5e5, -4e5, "left")}
for nm, (dx, dy, ha) in LAB.items():
    p = next(q for q in PORTS if q["port"] == nm); x, y = proj(p["lon"], p["lat"])
    ax.text(x + dx, y + dy, f"{nm.replace(' and Kennedy', '')}\n{p['n']:,}", ha=ha, va="center", fontsize=9, color=FG, path_effects=HALO, zorder=6)
fig.text(.02, .96, f"Orbital launch attempts by spaceport, 1957 to {R['source']['last_year']}: circle area = launches, colours = who launched", fontsize=11, color=FG)
fig.legend(handles=[Patch(color=BCOL[b], label=b) for b in BN], loc="lower center", ncol=4, frameon=False, fontsize=9.5, bbox_to_anchor=(.5, -.01))
both(fig, "map")

# ---------- busiest ever and 2025 ----------
fig, axs = plt.subplots(1, 2, figsize=(11, 5), facecolor=BG); fig.subplots_adjust(left=.2, right=.97, wspace=.75, top=.88, bottom=.06)
for ax, rows, col, t in ((axs[0], R["busiest_ever"][:10], NAVY, f"1957 to {R['source']['last_year']}"), (axs[1], R["busiest_2025"][:10], HOT, "2025")):
    ax.set_facecolor(BG); nm = [r["port"].replace(" and Kennedy", " and KSC") for r in rows][::-1]; v = [r["n"] for r in rows][::-1]
    ax.barh(nm, v, color=col, height=.68)
    for i, vv in enumerate(v): ax.text(vv + max(v) * .015, i, f"{vv:,}", va="center", fontsize=9.5)
    ax.set_title(t, loc="left", fontsize=13, color=FG); ax.set_xticks([]); spines(ax); ax.spines["bottom"].set_visible(False); ax.tick_params(axis="y", length=0, labelsize=10)
both(fig, "ports")

# ---------- failures ----------
fig = plt.figure(figsize=(11, 4.6), facecolor=BG); ax = fig.add_axes([.07, .12, .84, .76]); ax.set_facecolor(BG)
ax.bar(Y.index, Y.fail, color=HOT, width=.8); ax.set_xlim(1956, 2027); spines(ax); ax.set_ylabel("failures per year", color=HOT)
a2 = ax.twinx(); D = R["decades"]
xs = [max(1957.5, d["dec"] + 5) if d["dec"] > 1950 else 1958.5 for d in D]
a2.plot(xs, [d["fail_pct"] for d in D], "-o", color=COOL, lw=2.2, ms=5)
for x, d in zip(xs, D): a2.text(x + 1, d["fail_pct"] + 2.5, f"{d['fail_pct']:.0f}%", ha="left", fontsize=10, color=COOL, fontweight="medium", path_effects=[pe.withStroke(linewidth=3.5, foreground=BG)], zorder=9)
a2.set_ylim(0, 66); a2.set_zorder(ax.get_zorder() + 1); a2.patch.set_visible(False); a2.set_ylabel("share failed, by decade", color=COOL); a2.spines["top"].set_visible(False)
both(fig, "fail")

# ---------- latitude and direction ----------
D = sorted([d for d in R["lat_main"] if d["n"] >= 8], key=lambda d: abs(d["lat"]))
fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 6.4), facecolor=BG, gridspec_kw={"width_ratios": [1.1, 1]}); fig.subplots_adjust(left=.19, right=.98, wspace=.06, top=.9, bottom=.14)
nm = [f"{d['port'].replace(' and Kennedy', '')} {abs(d['lat']):.0f}°{'S' if d['lat'] < 0 else 'N'}" for d in D][::-1]
a1.barh(nm, [d["v"] for d in D][::-1], color="#8C8478", height=.66); a1.set_facecolor(BG)
for i, d in enumerate(D[::-1]): a1.text(d["v"] + 6, i, str(d["v"]), va="center", fontsize=9)
a1.set_xlim(0, 540); a1.set_title("Earth's eastward push at the pad, m/s", loc="left", fontsize=11); spines(a1); a1.tick_params(axis="y", length=0, labelsize=9.5)
DC = [("eastward", "#E0A11B"), ("polar or sun-synchronous", COOL), ("westward", HOT)]
left = np.zeros(len(D))
for k, (lab, c) in enumerate(DC):
    v = np.array([(d[["east", "polar", "retro"][k]] or 0) for d in D][::-1]); a2.barh(range(len(D)), v, left=left, color=c, height=.66, label=lab); left += v
for i, d in enumerate(D[::-1]):
    if not d["n_inc"]: a2.text(2, i, "no orbit data", va="center", fontsize=8.5, color=MUT)
a2.set_yticks([]); a2.set_xlim(0, 100); a2.set_facecolor(BG); spines(a2); a2.set_title("Direction to low orbit, % of launches", loc="left", fontsize=11)
a2.legend(loc="upper center", bbox_to_anchor=(.45, -.06), ncol=3, frameon=False, fontsize=9)
both(fig, "lat")

# ---------- what came down per year ----------
DY = pd.DataFrame(R["down_years"]).set_index("y")
TN = [("P", "payloads"), ("R", "rocket stages"), ("C", "components"), ("D", "debris")]
fig = plt.figure(figsize=(11, 4.8), facecolor=BG); ax = fig.add_axes([.08, .12, .9, .72]); ax.set_facecolor(BG)
base = np.zeros(len(DY))
for t, n in TN:
    ax.bar(DY.index, DY[t], bottom=base, color=TYPE_COL[t], width=.85, label=n); base += DY[t].values
ax.plot(DY.index, DY.starlink, color=FG, lw=1.4, ls="--", label="of which Starlink satellites")
ob = R["objects"]
ax.text(2022, ob["down_peak_n"] + 40, f"2022: {ob['down_peak_n']:,}\n{R['asat']['y2022']:,} Kosmos 1408 fragments", ha="right", fontsize=9.5)
spines(ax); ax.set_xlim(1956, 2027); ax.set_ylabel("objects coming back"); ax.grid(axis="y", color=RULE); ax.set_axisbelow(True)
fig.legend(loc="upper left", bbox_to_anchor=(.08, .99), ncol=5, frameon=False, fontsize=9.5)
both(fig, "down")

# ---------- fates by type (paper only) ----------
FT = pd.read_csv(f"{DATA}/objects_by_fate.csv", index_col=0)
FC = [("Still in orbit", COOL), ("Re-entered", "#8C8478"), ("Landed or recovered", "#2E9A8C"), ("Deorbited on purpose", NAVY),
      ("Docked, berthed or joined another object", "#D46A8C"), ("Left Earth orbit", "#E0A11B"), ("Other (exploded, collided, retired or catalogue entries)", "#C9C2B6")]
rows = [TYPE_NAME[t] for t in "PRCD"]
fig = plt.figure(figsize=(11, 4), facecolor=BG); ax = fig.add_axes([.36, .3, .61, .62]); ax.set_facecolor(BG)
left = np.zeros(len(rows))
for f, c in FC:
    v = np.array([FT.loc[r, f] if f in FT.columns else 0 for r in rows], float); ax.barh(rows[::-1], v[::-1], left=left[::-1], color=c, label=f, height=.6); left += v
ax.set_xlabel("catalogued objects"); spines(ax); ax.tick_params(axis="y", length=0)
fig.legend(loc="lower center", ncol=3, frameon=False, fontsize=8.5, bbox_to_anchor=(.55, 0))
both(fig, "fates", blog=False)

# ---------- where things came down (GCAT places) ----------
RE = jload(f"{DATA}/reentries.json")["rows"]
A = np.array([[r[0], r[1], r[4]] for r in RE])
fig = plt.figure(figsize=(12, 6.6), facecolor=BG); ax = fig.add_axes([0, 0, 1, .92])
outline(ax, fc=SEA, ec="#C9CDD0"); world(ax, ec=BG)
la, lo = circle_ll(*NEMO, NEMO_R_KM); x, y = proj(lo, la)
ax.fill(x, y, fc=NAVY, alpha=.08, zorder=2); ax.plot(x, y, color=NAVY, lw=1.2, ls="--", zorder=2)
for k, (c, s, lab) in enumerate((("#7E7A73", 6, "re-entered (uncontrolled)"), (NAVY, 22, "deorbited on purpose"), ("#2E9A8C", 9, "landed or recovered"))):
    q = A[A[:, 2] == k]; x, y = proj(q[:, 1], q[:, 0]); ax.scatter(x, y, s=s, c=c, alpha=.55 if k != 1 else 1, lw=.3 if k == 1 else 0, edgecolor="#fff", zorder=3 + k, label=f"{lab} ({len(q):,})")
x, y = proj(NEMO[1], NEMO[0]); ax.scatter([x], [y], s=70, c=NAVY, ec="#fff", lw=1.5, zorder=8)
ax.text(x + 4e5, y - 3e5, "Point Nemo", fontsize=10, color=NAVY, path_effects=HALO, zorder=9, fontweight="medium")
for g in R["stations"]:
    if g["lat"] is None: continue
    x, y = proj(g["lon"], g["lat"]); ax.scatter([x], [y], marker="D", s=40, c=NAVY if g["status"] == "D" else "#fff", ec=NAVY, lw=1.3, zorder=9)
    off = {"Mir": (4e5, -3.5e5, "left"), "Tiangong 1": (4e5, -1e5, "left"), "Tiangong 2": (3e5, 2.5e5, "left"), "Skylab": (3e5, -4e5, "left"), "Salyut 2": (-3e5, 3e5, "right")}[g["name"]]
    ax.text(x + off[0], y + off[1], g["name"], ha=off[2], fontsize=9, color=FG, path_effects=HALO, zorder=9)
ax.legend(loc="lower left", bbox_to_anchor=(.40, .06), frameon=False, fontsize=9, markerscale=1.6)
fig.text(.02, .955, f"{len(RE):,} objects whose place of re-entry or landing GCAT records; diamonds: space stations; dashed: {NEMO_R_KM:,} km around Point Nemo", fontsize=10.5, color=FG)
both(fig, "reentry_map")

# ---------- header card 1200 x 630 ----------
fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=BG)
ax = fig.add_axes([.40, .30, .6, .62]); outline(ax, fc=SEA, ec="#C9CDD0", lw=.6); world(ax, lw=.2, ec=BG)
for p in sorted(PORTS, key=lambda r: -r["n"]):
    x, y = proj(p["lon"], p["lat"]); pie(ax, float(x), float(y), .85 * K * np.sqrt(p["n"]), p["b"], [BCOL[b] for b in BN], lw=.5)
x, y = proj(NEMO[1], NEMO[0]); ax.scatter([x], [y], s=40, c=NAVY, ec="#fff", lw=1.2, zorder=8)
la, lo = circle_ll(*NEMO, NEMO_R_KM); cx, cy = proj(lo, la); ax.plot(cx, cy, color=NAVY, lw=.9, ls="--", zorder=7)
ax.text(x + 5e5, y - 4e5, "Point Nemo", fontsize=9, color=NAVY, path_effects=HALO, zorder=9)
a2 = fig.add_axes([.45, .07, .52, .22]); a2.set_facecolor(BG); stack_years(a2); a2.set_yticks([]); a2.spines["left"].set_visible(False); a2.tick_params(labelsize=8)
a2.text(2024.5, 300, f"{pk['record_n']} in {pk['record_year']}", ha="right", fontsize=9, color=FG)
fig.text(.04, .86, "Up", fontproperties=DISP, fontsize=60, color=HOT, va="top")
fig.text(.04, .70, "and", fontproperties=DISP, fontsize=60, color=FG, va="top")
fig.text(.04, .54, "down", fontproperties=DISP, fontsize=60, color=COOL, va="top")
fig.text(.04, .36, f"Every orbital launch since Sputnik:\n{R['source']['n']:,} attempts, a record {pk['record_n']} in {pk['record_year']}.\nAnd where the hardware falls back.", fontproperties=SERP, fontsize=14, color=FG, va="top", linespacing=1.35)
fig.text(.04, .04, "maps.tristanhotham.com/rocket-launches", fontsize=11, color=MUT)
fig.savefig(os.path.join(ROOT, "header.png"), dpi=100, facecolor=BG)
plt.close(fig)
print("figures done", sorted(os.listdir(BL)), sorted(x for x in os.listdir(PA) if x.endswith(".png")))
