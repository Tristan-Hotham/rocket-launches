"""Every number used anywhere (data/results.json), the reusable data tables (data/*.csv) and the page data
(data/site.json, data/launches.json, data/reentries.json).

Definitions (see 01_clean.py for codes):
  * orbital launch attempt: GCAT LaunchCode O* or D*, excluding OE (pad explosion) and OA (abort before lift-off);
  * failure: outcome letter F (partial failures such as OF40 included);
  * year: launch year in UTC; LAST_YEAR (2026) is partial, the catalogue runs to late October;
  * Earth's rotation boost at a site: 465.1 m/s x cos(latitude), the eastward speed a rocket already has on the pad;
  * direction from orbit inclination: under 75 degrees = eastward (prograde), 75 to 105 = polar or sun-synchronous,
    over 105 = westward (retrograde);
  * located re-entry places: only GCAT's own Dest coordinates, never inferred. 'Near Point Nemo' = within NEMO_R_KM
    (2,500 km) of Point Nemo; the circle is my choice for counting and drawing, not an official boundary."""
import numpy as np, pandas as pd, html as _html
from shapely.geometry import shape, Point
from shapely.ops import unary_union
from shapely.prepared import prep
from common import *

O = pd.read_pickle(f"{WORK}/orbital.pkl").sort_values("jd").reset_index(drop=True)
A = pd.read_pickle(f"{WORK}/all.pkl")
P = pd.read_pickle(f"{WORK}/ports.pkl").set_index("port")
C = pd.read_pickle(f"{WORK}/satcat.pkl")
CHK = jload(f"{WORK}/checks.json")
BN = [b for b, _ in BLOCS]; BI = {b: i for i, b in enumerate(BN)}
YEARS = list(range(1957, LAST_YEAR + 1))
pc = lambda a, b: round(100 * a / b, 2) if b else None
R = {}

# ---------- source ----------
R["source"] = {"launch_rows": CHK["launch_rows"], "satcat_rows": CHK["satcat_rows"], "site_rows": CHK["site_rows"],
               "n": len(O), "ok": int(O.ok.sum()), "fail": int((O.ok == 0).sum()), "fail_pct": pc((O.ok == 0).sum(), len(O)),
               "ok_pct": pc(O.ok.sum(), len(O)), "deep": int(O.LaunchCode.str.startswith("D").sum()),
               "partial": int(O.partial.sum()), "pad_oe": CHK["pad_explosions_OE"], "abort_oa": CHK["aborts_OA"],
               "suborbital": int((~A.Launch_Tag.isin(O.Launch_Tag) & ~A.LaunchCode.isin(["OE", "OA", "!"])).sum()),
               "first_year": int(A.year.min()), "last_year": LAST_YEAR, "last_date": O.Launch_Date.iloc[-1][:11],
               "release": GCAT_REL, "update_year": GCAT_UPDATE, "n_ports": int(O.port.nunique()), "n_codes": int(O.Launch_Site.nunique()),
               "n_ok_inc": CHK["ok_with_inc"], "checks": CHK}
assert R["source"]["n"] == 7416 and R["source"]["last_date"].startswith("2026 Oct")

# ---------- before Sputnik ----------
pre = A[A.year < 1957]
v2 = A[A.LV_Type.isin(["A-4", "V-2", "A-4b"])]
sp = pre[pre.apogee >= 100].sort_values("Launch_Tag")
first_space = pre[pre.apogee >= 100].sort_values("jd").iloc[0]
R["before"] = {"pre1957": len(pre), "pre1957_space": int((pre.apogee >= 100).sum()), "v2": len(v2), "v2_first": int(v2.year.min()), "v2_last": int(v2.year.max()),
               "v2_1944": int((v2.year == 1944).sum()), "v2_1945": int((v2.year == 1945).sum()), "v2_us": int((v2.year >= 1946).sum()),
               "first_space_date": first_space.Launch_Date[:8].strip(), "first_space_lv": first_space.LV_Type, "first_space_apogee": int(first_space.apogee),
               "first_space_site": first_space.Launch_Site, "v2_max_apogee": int(v2.apogee.max())}
assert R["before"]["first_space_lv"] == "A-4" and R["before"]["first_space_site"] == "HVP"
s1 = O.iloc[0]
R["sputnik"] = {"date": "4 October 1957", "lv": s1.LV_Type, "tag": s1.Launch_Tag, "n1957": int((O.year == 1957).sum()),
                "fail1957": int(((O.year == 1957) & (O.ok == 0)).sum()), "n1958": int((O.year == 1958).sum()), "fail1958": int(((O.year == 1958) & (O.ok == 0)).sum())}
assert s1.Launch_Tag == "1957 ALP" and s1.Launch_Date.startswith("1957 Oct  4")

# ---------- per year and bloc ----------
yr = []
for y in YEARS:
    a = O[O.year == y]
    row = {"y": y, "n": len(a), "ok": int(a.ok.sum()), "fail": int((a.ok == 0).sum())}
    for b in BN:
        row[b] = int((a.bloc == b).sum())
    row["spx"] = int(a.agency1.eq("SPX").sum()); row["payloads"] = int(a.payloads.sum())
    yr.append(row)
R["years"] = yr
Y = pd.DataFrame(yr).set_index("y")
full = Y.loc[:LAST_YEAR - 1]
cold = Y.loc[1957:1991]
R["peaks"] = {"coldwar_year": int(cold.n.idxmax()), "coldwar_n": int(cold.n.max()),
              "su_year": int(Y["Soviet Union and Russia"].idxmax()), "su_n": int(Y["Soviet Union and Russia"].max()),
              "us_1960s_year": int(Y.loc[1957:1969, "United States"].idxmax()), "us_1960s_n": int(Y.loc[1957:1969, "United States"].max()),
              "dip_year": int(Y.loc[1992:2019].n.idxmin()), "dip_n": int(Y.loc[1992:2019].n.min()),
              "record_year": int(full.n.idxmax()), "record_n": int(full.n.max()),
              "y2026_n": int(Y.loc[LAST_YEAR].n), "y2020_n": int(Y.loc[2020].n), "y2015_n": int(Y.loc[2015].n), "y2010_n": int(Y.loc[2010].n),
              "y2000_n": int(Y.loc[2000].n), "y1990_n": int(Y.loc[1990].n), "y2019_n": int(Y.loc[2019].n),
              "su_1991": int(Y.loc[1991, "Soviet Union and Russia"]), "ru_2025": int(Y.loc[2025, "Soviet Union and Russia"])}
pk = R["peaks"]
pk["record_vs_coldwar_pct"] = round(100 * (pk["record_n"] / pk["coldwar_n"] - 1), 1)
pk["record_vs_dip_x"] = round(pk["record_n"] / pk["dip_n"], 1)
pk["us_2025"] = int(Y.loc[2025, "United States"]); pk["cn_2025"] = int(Y.loc[2025, "China"])
pk["spx_2025"] = int(Y.loc[2025, "spx"]); pk["spx_2025_pct"] = pc(Y.loc[2025, "spx"], Y.loc[2025, "n"])
pk["spx_total"] = int(O.agency1.eq("SPX").sum())
pk["us_2025_pct"] = pc(Y.loc[2025, "United States"], Y.loc[2025, "n"]); pk["cn_2025_pct"] = pc(Y.loc[2025, "China"], Y.loc[2025, "n"])
pk["since2020"] = int(O[O.year >= 2020].shape[0]); pk["since2020_pct"] = pc(pk["since2020"], len(O))
pk["starlink_missions_2025"] = int(O[(O.year == 2025) & O.Mission.str.contains("Starlink", case=False)].shape[0])
pk["payloads_2025"] = int(Y.loc[2025, "payloads"]); pk["payloads_1990"] = int(Y.loc[1990, "payloads"])
pk["f9_2025"] = int(((O.year == 2025) & O.LV_Type.str.startswith("Falcon 9")).sum())
pk["years_over_200"] = [int(y) for y in Y.index[Y.n > 200]]
pk["first_over_coldwar"] = int(Y.index[(Y.index > 1991) & (Y.n > pk["coldwar_n"])][0])
assert pk["record_year"] == 2025 and pk["coldwar_year"] == 1967 and pk["dip_year"] == 2004
assert pk["su_year"] < 1992

# ---------- blocs ----------
bl = []
for b in BN:
    a = O[O.bloc == b]
    yy = a.groupby("year").size()
    bl.append({"bloc": b, "n": len(a), "pct": pc(len(a), len(O)), "ok": int(a.ok.sum()), "fail": int((a.ok == 0).sum()),
               "fail_pct": pc((a.ok == 0).sum(), len(a)), "first": int(a.year.min()), "peak_year": int(yy.idxmax()), "peak_n": int(yy.max()),
               "since2020": int((a.year >= 2020).sum()), "y2025": int((a.year == 2025).sum())})
R["blocs"] = {r["bloc"]: r for r in bl}; R["blocs_list"] = bl
oth = O[O.bloc == "Others"]
R["others"] = [{"state": s, "n": int(n), "first": int(oth[oth.state == s].year.min())} for s, n in oth.state.value_counts().items()]
st_first = O.groupby("state").year.min().sort_values()
R["first_by_state"] = [{"state": s, "y": int(y)} for s, y in st_first.items()]
SU = O[O.state == "SU"]; RU = O[O.state == "RU"]
R["su_ru"] = {"su": len(SU), "ru": len(RU)}
R["europe"] = {"starsem_baikonur": int(((O.agency1 == "STSM") & (O.port == "Baikonur")).sum()), "kourou_soyuz": int(((O.port == "Kourou") & O.LV_Type.str.startswith("Soyuz")).sum())}

# ---------- decades and failures ----------
dec = []
for d in range(1950, 2030, 10):
    a = O[(O.year >= d) & (O.year < d + 10)]
    dec.append({"dec": d, "n": len(a), "fail": int((a.ok == 0).sum()), "fail_pct": pc((a.ok == 0).sum(), len(a))})
R["decades"] = dec
f10 = O[O.year <= 1966]
R["fail"] = {"first10_pct": pc((f10.ok == 0).sum(), len(f10)), "first10_n": len(f10),
             "y2010s_pct": [d for d in dec if d["dec"] == 2010][0]["fail_pct"], "y2020s_pct": [d for d in dec if d["dec"] == 2020][0]["fail_pct"],
             "y2025": int(Y.loc[2025, "fail"]), "y2025_pct": pc(Y.loc[2025, "fail"], Y.loc[2025, "n"])}
R["fail"]["y2020s_inv"] = round(100 / R["fail"]["y2020s_pct"])
nf = O[O.ok == 0].groupby("year").size()
R["fail"]["max_year"] = int(nf.idxmax()); R["fail"]["max_n"] = int(nf.max())

# ---------- spaceports ----------
ports = []
for name, host, codes in SPACEPORTS:
    a = O[O.port == name]
    if not len(a):
        continue
    yy = a.groupby("year").size()
    fam = a.family.value_counts()
    b = a.bloc.value_counts()
    lat, lon = float(P.loc[name, "lat"]), float(P.loc[name, "lon"])
    inc = a[a.orbit.isin(["LEO", "SSO", "ISS", "LSS", "MOL", "MEO"])].inc.dropna()
    ports.append({"port": name, "host": host, "lat": round(lat, 4), "lon": round(lon, 4), "n": len(a), "ok": int(a.ok.sum()), "fail": int((a.ok == 0).sum()),
                  "fail_pct": pc((a.ok == 0).sum(), len(a)), "first": int(a.year.min()), "last": int(a.year.max()), "first_date": a.Launch_Date.iloc[0][:11].strip(),
                  "first_mission": a.iloc[0].Mission, "first_lv": a.iloc[0].LV_Type,
                  "peak_year": int(yy.idxmax()), "peak_n": int(yy.max()), "since2020": int((a.year >= 2020).sum()), "y2025": int((a.year == 2025).sum()),
                  "y2026": int((a.year == 2026).sum()), "coldwar": int((a.year <= 1991).sum()),
                  "v_rot": round(EARTH_V * np.cos(np.radians(lat))), "abs_lat": round(abs(lat), 1),
                  "families": [[k, int(v)] for k, v in fam.head(5).items()], "blocs": [[k, int(v)] for k, v in b.items()],
                  "n_inc": int(len(inc)), "east": pc((inc < 75).sum(), len(inc)), "polar": pc(((inc >= 75) & (inc <= 105)).sum(), len(inc)),
                  "retro": pc((inc > 105).sum(), len(inc)), "min_inc": round(float(inc.min()), 1) if len(inc) else None,
                  "gto": int(a.orbit.isin(["GTO", "GEO"]).sum()), "codes": [c for c in codes if c in set(a.Launch_Site)],
                  "air": int((a.Platform != "-").sum() > 0 and name.endswith("(air launch)"))})
PT = pd.DataFrame(ports).sort_values("n", ascending=False)
PT.drop(columns=["families", "blocs", "codes"]).to_csv(f"{DATA}/spaceports.csv", index=False)
R["ports"] = {r["port"]: r for r in ports}
R["busiest_ever"] = [{"port": r.port, "n": int(r.n), "host": r.host} for r in PT.head(12).itertuples()]
P20 = PT.sort_values("since2020", ascending=False)
R["busiest_2020s"] = [{"port": r.port, "n": int(r.since2020), "host": r.host} for r in P20.head(12).itertuples()]
P25 = PT.sort_values("y2025", ascending=False)
R["busiest_2025"] = [{"port": r.port, "n": int(r.y2025), "host": r.host} for r in P25.head(10).itertuples()]
assert [r["port"] for r in R["busiest_ever"][:4]] == ["Plesetsk", "Baikonur", "Cape Canaveral and Kennedy", "Vandenberg"]
assert R["busiest_2020s"][0]["port"] == "Cape Canaveral and Kennedy"
cape = O[O.port == "Cape Canaveral and Kennedy"]
R["cape"] = {"cc": int((cape.Launch_Site == "CC").sum()), "ksc": int((cape.Launch_Site == "KSC").sum()), "spx_2025": int(((cape.year == 2025) & (cape.agency1 == "SPX")).sum()),
             "y2025_pct": pc(R["ports"]["Cape Canaveral and Kennedy"]["y2025"], Y.loc[2025, "n"])}
R["plesetsk"] = {"coldwar": R["ports"]["Plesetsk"]["coldwar"], "peak_year": R["ports"]["Plesetsk"]["peak_year"], "peak_n": R["ports"]["Plesetsk"]["peak_n"],
                 "since2020": R["ports"]["Plesetsk"]["since2020"]}
R["top4_share"] = pc(PT.head(4).n.sum(), len(O))
R["n_ports_2025"] = int((PT.y2025 > 0).sum())

# ---------- latitude and direction ----------
main = ["Kourou", "Sriharikota", "Wenchang", "Xichang", "Cape Canaveral and Kennedy", "Tanegashima", "Jiuquan", "Vandenberg", "Taiyuan",
        "Mahia", "Baikonur", "Vostochny", "Plesetsk", "Palmachim", "Wallops", "Starbase", "Semnan", "Naro", "Uchinoura", "Kapustin Yar"]
R["lat"] = {"kourou_v": R["ports"]["Kourou"]["v_rot"], "cape_v": R["ports"]["Cape Canaveral and Kennedy"]["v_rot"],
            "baikonur_v": R["ports"]["Baikonur"]["v_rot"], "plesetsk_v": R["ports"]["Plesetsk"]["v_rot"], "equator_v": round(EARTH_V),
            "kourou_minus_baikonur": R["ports"]["Kourou"]["v_rot"] - R["ports"]["Baikonur"]["v_rot"],
            "kourou_minus_cape": R["ports"]["Kourou"]["v_rot"] - R["ports"]["Cape Canaveral and Kennedy"]["v_rot"],
            "kourou_gto_pct": pc(R["ports"]["Kourou"]["gto"], R["ports"]["Kourou"]["n"]),
            "baikonur_gto_pct": pc(R["ports"]["Baikonur"]["gto"], R["ports"]["Baikonur"]["n"]),
            "plesetsk_gto_pct": pc(R["ports"]["Plesetsk"]["gto"], R["ports"]["Plesetsk"]["n"]),
            "cape_gto_pct": pc(R["ports"]["Cape Canaveral and Kennedy"]["gto"], R["ports"]["Cape Canaveral and Kennedy"]["n"])}
ok = O[O.ok == 1].copy()
ok["plat"] = ok.port.map(lambda p: abs(R["ports"][p]["lat"]))
ki = ok[ok.inc.notna() & ok.orbit.isin(["LEO", "SSO", "ISS", "LSS", "MOL", "MEO"])]
below = ki[ki.inc < ki.plat - 2]
R["dir"] = {"n": len(ki), "east_pct": pc((ki.inc < 75).sum(), len(ki)), "polar_pct": pc(((ki.inc >= 75) & (ki.inc <= 105)).sum(), len(ki)),
            "retro_pct": pc((ki.inc > 105).sum(), len(ki)), "below_lat": len(below), "below_lat_pct": pc(len(below), len(ki)),
                        "palmachim_retro": R["ports"]["Palmachim"]["retro"], "vandenberg_polar": R["ports"]["Vandenberg"]["polar"],
            "cape_east": R["ports"]["Cape Canaveral and Kennedy"]["east"], "plesetsk_polar": R["ports"]["Plesetsk"]["polar"]}
assert R["dir"]["palmachim_retro"] == 100
inc_rows = [[round(float(r.inc), 2), round(r.plat, 2), r.port, r.orbit, int(r.year)] for r in ki.itertuples()]
pd.DataFrame(inc_rows, columns=["inclination", "site_abs_lat", "spaceport", "orbit", "year"]).to_csv(f"{WORK}/inc.csv", index=False)
R["lat_main"] = [{"port": p, "lat": R["ports"][p]["lat"], "v": R["ports"][p]["v_rot"], "n": R["ports"][p]["n"], "east": R["ports"][p]["east"],
                  "polar": R["ports"][p]["polar"], "retro": R["ports"][p]["retro"], "n_inc": R["ports"][p]["n_inc"], "gto": R["ports"][p]["gto"]} for p in main]

# ---------- objects: what happened to everything catalogued ----------
C["fate"] = C.fate.astype(str)
fat = C.fate.value_counts()
R["objects"] = {"n": len(C), "fates": {k: int(v) for k, v in fat.items()},
                "types": {t: int((C.t == t).sum()) for t in "PRCDZ"},
                "in_orbit": int(fat["Still in orbit"]), "reentered": int(fat["Re-entered"]), "deorbited": int(fat["Deorbited on purpose"]),
                "landed": int(fat["Landed or recovered"]),
                "came_down": int(fat["Re-entered"] + fat["Deorbited on purpose"] + fat["Landed or recovered"])}
ob = R["objects"]
ob["came_down_pct"] = pc(ob["came_down"], ob["n"]); ob["in_orbit_pct"] = pc(ob["in_orbit"], ob["n"])
ob["deorbited_pct_of_down"] = pc(ob["deorbited"], ob["came_down"])
inorb = C[C.fate == "Still in orbit"]
ob["in_orbit_types"] = {t: int((inorb.t == t).sum()) for t in "PRCD"}
ob["in_orbit_starlink"] = int(inorb.Name.str.startswith("Starlink").sum())
ob["in_orbit_debris_pct"] = pc((inorb.t == "D").sum(), len(inorb))
down = C[C.fate.isin(["Re-entered", "Deorbited on purpose", "Landed or recovered"])]
dy = []
for y in YEARS:
    a = down[down.d_y == y]
    row = {"y": y, "n": len(a)}
    for t in "PRCD":
        row[t] = int((a.t == t).sum())
    row["starlink"] = int(a.Name.str.startswith("Starlink").sum())
    dy.append(row)
R["down_years"] = dy
DY = pd.DataFrame(dy).set_index("y")
dfull = DY.loc[:LAST_YEAR - 1]
ob["down_peak_year"] = int(dfull.n.idxmax()); ob["down_peak_n"] = int(dfull.n.max())
ob["down_2025"] = int(DY.loc[2025, "n"]); ob["down_2025_starlink"] = int(DY.loc[2025, "starlink"]); ob["down_2025_starlink_pct"] = pc(DY.loc[2025, "starlink"], DY.loc[2025, "n"])
ob["down_2026"] = int(DY.loc[2026, "n"]); ob["down_2019"] = int(DY.loc[2019, "n"])
ob["down_since2020"] = int(DY.loc[2020:].n.sum()); ob["down_since2020_pct"] = pc(ob["down_since2020"], ob["came_down"])
ob["down_starlink_total"] = int(down.Name.str.startswith("Starlink").sum())
ob["starlink_total"] = int(C.Name.str.startswith("Starlink").sum())
ob["down_no_date"] = int(down.d_y.isna().sum())
pay_down = down[down.t == "P"]
ob["down_payload"] = len(pay_down); ob["down_stage"] = int((down.t == "R").sum()); ob["down_debris"] = int((down.t == "D").sum()); ob["down_comp"] = int((down.t == "C").sum())
ob["mass_known_down_t"] = round(float(down[down.t.isin(["P", "R"])].mass.fillna(0).sum()) / 1000)
asat = down[(down.t == "D") & down.Name.str.contains("Kosmos-1408")]
R["asat"] = {"test_year": 2021, "first_down_2021": int((asat.d_y == 2021).sum()), "n": len(asat), "y2022": int((asat.d_y == 2022).sum()), "y2022_pct": pc((asat.d_y == 2022).sum(), DY.loc[2022, "n"])}
assert ob["down_peak_year"] == 2022 and R["asat"]["y2022"] > 1000 and R["asat"]["first_down_2021"] > 0 and asat[asat.d_y < 2021].shape[0] <= 4   # a few older fragments fell earlier; the test debris starts falling in 2021
# the heaviest things to come down (payloads and stages with a mass)
hv = down[down.t.isin(["P", "R"]) & down.mass.notna()].sort_values("mass", ascending=False)
R["heaviest_down"] = [{"name": r.Name, "t": round(r.mass / 1000, 1), "y": int(r.d_y) if not np.isnan(r.d_y) else None, "fate": r.fate, "dest": r.Dest}
                      for r in hv.head(12).itertuples()]

# ---------- where things came down: GCAT's own locations ----------
land = prep(unary_union([shape(f["geometry"]) for f in jload(f"{GEO}/ne_50m_land.geojson")["features"]]))
loc = C[C.d_lat.notna()].copy()


def gc_km(lat1, lon1, lat2, lon2):
    p1, p2, l1, l2 = map(np.radians, (lat1, lat2, lon1, lon2))
    return 6371.0 * 2 * np.arcsin(np.sqrt(np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin((l2 - l1) / 2) ** 2))


loc["on_land"] = [int(land.contains(Point(lo, la))) for la, lo in zip(loc.d_lat, loc.d_lon)]
loc["km_nemo"] = gc_km(loc.d_lat.values, loc.d_lon.values, NEMO[0], NEMO[1])
loc["near_nemo"] = (loc.km_nemo <= NEMO_R_KM).astype(int)
cap_share = (1 - np.cos(NEMO_R_KM / 6371.0)) / 2           # share of the Earth's surface inside the circle
unc = loc[loc.fate == "Re-entered"]; ctl = loc[loc.fate == "Deorbited on purpose"]; lnd = loc[loc.fate == "Landed or recovered"]
R["located"] = {"n": len(loc), "pct_of_down": pc(len(loc), ob["came_down"]), "since2020": int((loc.d_y >= 2020).sum()),
                "since2020_pct": pc((loc.d_y >= 2020).sum(), len(loc)), "approx": int(loc.d_approx.sum()),
                "reentered": len(unc), "deorbited": len(ctl), "landed": len(lnd),
                "unc_sea_pct": pc((unc.on_land == 0).sum(), len(unc)), "unc_land": int(unc.on_land.sum()),
                "unc_near_nemo": int(unc.near_nemo.sum()), "unc_near_nemo_pct": pc(unc.near_nemo.sum(), len(unc)),
                "circle_share_pct": round(100 * cap_share, 2), "nemo_r_km": NEMO_R_KM,
                "ctl_near_nemo": int(ctl.near_nemo.sum()), "ctl_south_pacific": int(((ctl.d_lat < -20) & (ctl.d_lon < -100)).sum() + ((ctl.d_lat < -20) & (ctl.d_lon > 160)).sum()),
                "unc_starlink": int(unc.Name.str.startswith("Starlink").sum()),
                "unc_abs_lat_median": round(float(unc.d_lat.abs().median()), 1),
                "unc_tropics_pct": pc((unc.d_lat.abs() <= 23.44).sum(), len(unc)), "earth_tropics_pct": round(100 * np.sin(np.radians(23.44)), 1),
                "ocean_pct_earth": 71}
lo_ = R["located"]
lo_["nemo_ratio"] = round(lo_["unc_near_nemo_pct"] / lo_["circle_share_pct"], 2)
dtext = C[(C.d_text != "")].d_text.value_counts()
lo_["text_only"] = int(dtext.sum()); lo_["por"] = int(sum(v for k, v in dtext.items() if re.search(r"\bPOR\b", k)))
loc_out = loc[["JCAT", "Name", "Type", "t", "Launch_Tag", "LDate", "DDate", "d_y", "Status", "fate", "Dest", "d_lat", "d_lon", "d_approx", "on_land", "km_nemo", "mass"]]
loc_out.rename(columns={"t": "type_letter", "d_y": "down_year", "d_lat": "lat", "d_lon": "lon", "d_approx": "approx_flag", "mass": "mass_kg"}).round({"km_nemo": 0}).to_csv(f"{DATA}/reentry_places.csv", index=False)

# ---------- the South Pacific graveyard: GCAT facts for named craft ----------
names = ["Salyut", "Salyut-2", "Salyut-3", "Salyut-4", "Salyut-5", "Salyut-6", "Salyut-7", "Skylab Orbital Workshop", "Mir", "Tiangong 1", "Tiangong 2"]
gy = []
for n in names:
    r = C[(C.Name == n) & (C.t == "P")].iloc[0]
    gy.append({"name": "Salyut 1" if n == "Salyut" else n.replace("-", " ").replace(" Orbital Workshop", ""), "launched": int(r.ldate_y), "down": r.DDate[:11].strip(),
               "down_y": int(r.d_y), "status": r.Status, "fate": r.fate, "dest": r.Dest, "mass_t": round(r.mass / 1000, 1),
               "lat": None if np.isnan(r.d_lat) else round(float(r.d_lat), 2), "lon": None if np.isnan(r.d_lon) else round(float(r.d_lon), 2)})
R["stations"] = gy
G = {g["name"]: g for g in gy}
assert G["Mir"]["status"] == "D" and G["Mir"]["down"] == "2001 Mar 23" and G["Salyut 7"]["dest"] == "Argentina" and G["Tiangong 1"]["status"] == "R"
assert all(G[f"Salyut {k}"]["dest"] == "POR" and G[f"Salyut {k}"]["status"] == "D" for k in (1, 3, 4, 5, 6))
cargo = {"Progress": C[(C.t == "P") & C.Name.str.match(r"^Progress\b")], "ATV": C[(C.t == "P") & C.Name.isin(["Jules Verne", "Johannes Kepler", "Edoardo Amaldi", "Albert Einstein", "Georges Lemaitre"])],
         "HTV": C[(C.t == "P") & (C.Name.str.match(r"^(Kounotori \d+ gouki|HTV \d+|HTV-X\d)$"))]}
R["cargo"] = {k: len(v) for k, v in cargo.items()}
R["cargo"]["progress_first"] = int(cargo["Progress"].ldate_y.min()); R["cargo"]["atv_first"] = int(cargo["ATV"].ldate_y.min()); R["cargo"]["atv_last"] = int(cargo["ATV"].ldate_y.max())
R["cargo"]["htv_first"] = int(cargo["HTV"].ldate_y.min())
assert R["cargo"]["ATV"] == 5
R["cargo"]["progress_fates"] = cargo["Progress"].Status.value_counts().to_dict()

# ---------- Wikipedia facts (quoted, CC BY-SA) ----------
def wtext(f):
    h = jload(f"{RAW}/{f}")["html"]
    h = re.sub(r"<style.*?</style>|<sup.*?</sup>", "", h, flags=re.S)
    return re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", " ", h)).replace("\xa0", " ").replace("\u200b", "").replace("\ufeff", ""))


wn, wc = wtext("wiki_Point_Nemo.json"), wtext("wiki_Spacecraft_cemetery.json")
for s in ("48.8767°S 123.3933°W", "2,688 km", "Lukatela", "1992", "2031"):
    assert s in wn, s
for s in ("Mir and six Salyut stations", "more than 263 spacecraft were disposed in this area between 1971 and 2016", "At least 264 spacecraft",
          "nearly 200 pieces of Russian spacecraft debris", "Progress cargo craft", "H-II Transfer Vehicle", "Automated Transfer Vehicle",
          "Tiangong-1", "over 2,600 kilometres", "March of 2001"):
    assert s in wc, s
R["wiki"] = {"nemo_lat": 48.8767, "nemo_lon": 123.3933, "nemo_km": "2,688", "found_by": "Hrvoje Lukatela", "found_year": 1992, "iss_year": 2031,
             "n_disposed": "more than 260", "years": "1971 to 2016", "russian": "nearly 200", "islands_km": "2,600",
             "revid_nemo": jload(f"{RAW}/wiki_Point_Nemo.json")["revid"], "revid_cem": jload(f"{RAW}/wiki_Spacecraft_cemetery.json")["revid"],
             "revid_port": jload(f"{RAW}/wiki_Spaceport.json")["revid"], "revid_list": jload(f"{RAW}/wiki_List_of_rocket_launch_sites.json")["revid"]}
R["meta"] = {"page": PAGE, "repo": REPO, "doi": DOI, "blog": BLOG, "slug": SLUG, "gcat": GCAT_URL, "nemo": list(NEMO)}

# ---------- clean data out ----------
out = O.copy()
out["spaceport_lat"] = out.port.map(lambda p: R["ports"][p]["lat"]); out["spaceport_lon"] = out.port.map(lambda p: R["ports"][p]["lon"])
out["outcome"] = np.where(out.ok == 1, "success", "failure")
out[["Launch_Tag", "Launch_Date", "year", "LV_Type", "family", "Flight", "Mission", "Launch_Site", "Launch_Pad", "port", "spaceport_lat", "spaceport_lon",
     "Agency", "state", "bloc", "LaunchCode", "outcome", "FailCode", "orbit", "inc", "payloads", "objects"]] \
    .rename(columns={"port": "spaceport", "bloc": "country_or_bloc", "state": "agency_state", "inc": "first_payload_inclination", "Launch_Site": "gcat_site"}) \
    .to_csv(f"{DATA}/orbital_launches.csv", index=False)
pd.DataFrame(yr).rename(columns={"y": "year", "n": "attempts", "ok": "successes", "fail": "failures", "spx": "spacex", "payloads": "payloads_catalogued"}).to_csv(f"{DATA}/launches_by_year.csv", index=False)
pd.DataFrame(dy).rename(columns={"y": "year", "n": "came_down", "P": "payloads", "R": "rocket_stages", "C": "components", "D": "debris", "starlink": "starlink"}).to_csv(f"{DATA}/reentries_by_year.csv", index=False)
fy = C.groupby(["t", "fate"]).size().unstack(fill_value=0)
fy.index = [TYPE_NAME.get(i, i) for i in fy.index]; fy.to_csv(f"{DATA}/objects_by_fate.csv")
pd.DataFrame(gy).to_csv(f"{DATA}/space_stations_fate.csv", index=False)

# ---------- page data ----------
PN = [p["port"] for p in sorted(ports, key=lambda r: -r["n"])]; PI = {p: i for i, p in enumerate(PN)}
cnt = O.groupby(["port", "year", "bloc"]).agg(n=("ok", "size"), f=("ok", lambda s: int((s == 0).sum()))).reset_index()
yearly = {p: [] for p in PN}
for r in cnt.itertuples():
    yearly[r.port].append([int(r.year), BI[r.bloc], int(r.n), int(r.f)])
cm = jload(f"{WORK}/countries.json")
site = {"blocs": BLOCS, "ports": [[p, R["ports"][p]["host"], R["ports"][p]["lat"], R["ports"][p]["lon"], R["ports"][p]["n"], R["ports"][p]["fail"],
                                   R["ports"][p]["first"], R["ports"][p]["last"], R["ports"][p]["v_rot"], R["ports"][p]["families"], R["ports"][p]["first_date"],
                                   R["ports"][p]["first_mission"], R["ports"][p]["since2020"], R["ports"][p]["y2025"], R["ports"][p]["east"], R["ports"][p]["polar"], R["ports"][p]["retro"],
                                   R["ports"][p]["codes"], R["ports"][p]["peak_year"], R["ports"][p]["peak_n"]] for p in PN],
        "yearly": [yearly[p] for p in PN], "cpos": {i: [v["lx"], v["ly"], v["pop"]] for i, v in cm.items()}, "cname": {i: v["name"] for i, v in cm.items()},
        "nemo": list(NEMO), "nemo_r": NEMO_R_KM, "stations": gy}
jsave(site, f"{DATA}/site.json")
def label(f, m):
    f, m = ("" if f == "-" else f), ("" if m == "-" else m)
    return f if not m or m == f else (m if not f else f"{f} ({m})")


LVI = {v: i for i, v in enumerate(sorted(O.LV_Type.unique()))}
rows = [[r.Launch_Tag, r.Launch_Date[:11].strip(), PI[r.port], BI[r.bloc], int(r.ok), LVI[r.LV_Type], label(r.Flight, r.Mission), r.orbit] for r in O.itertuples()]
jsave({"cols": ["tag", "date", "port", "bloc", "ok", "lv", "mission", "orbit"], "lv": sorted(LVI, key=LVI.get), "rows": rows}, f"{DATA}/launches.json")
rr = [[round(float(r.d_lat), 2), round(float(r.d_lon), 2), int(r.d_y) if not np.isnan(r.d_y) else 0, r.t, {"Re-entered": 0, "Deorbited on purpose": 1, "Landed or recovered": 2}[r.fate],
       r.Name, int(r.d_approx), r.DDate[:11].strip()] for r in loc.sort_values("d_y").itertuples()]
jsave({"cols": ["lat", "lon", "year", "type", "fate", "name", "approx", "date"], "rows": rr}, f"{DATA}/reentries.json")
jsave(R, f"{DATA}/results.json", indent=1)
print("results ok", {k: os.path.getsize(f"{DATA}/{k}") // 1024 for k in ("site.json", "launches.json", "reentries.json", "results.json")})
print(R["peaks"]); print(R["before"]); print(R["fail"]); print(R["lat"]); print(R["dir"]); print(R["located"]); print(ob)
print(R["busiest_ever"][:8]); print(R["busiest_2020s"][:8]); print(R["busiest_2025"][:6]); print(R["cargo"]); print(R["others"])
