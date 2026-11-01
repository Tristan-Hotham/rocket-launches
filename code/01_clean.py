"""Read the GCAT launch list, sites, organisations, launch vehicles and main object catalogue; keep the orbital launch
attempts; give each a spaceport, a launching country or bloc, an outcome and (from the catalogue) the inclination of its
first payload; and clean the object catalogue's fates and decay dates.

Orbital launch attempts. GCAT's LaunchCode starts with a letter for the kind of flight and a letter for the outcome.
  * kind: O = orbital launch, D = launch to deep space (beyond Earth orbit). Both are orbital launch attempts. All other
    letters are suborbital: S (science rockets), M (missiles), A (low atmospheric), H (high suborbital), T (vehicle tests),
    R (re-entry tests), Y (crewed rocket planes such as the X-15), N (near-orbital tests such as early Starship flights),
    L (lofted missile tests), X (launches from the Moon), and ! (placeholder rows that GCAT marks "Not real").
  * outcome: S = success, F = failure. A number after it (OS75, OF40) is GCAT's success fraction for a partial success
    or failure; I keep the letter (OS75 counts as a success, OF40 as a failure).
  * OE (vehicle exploded on the pad before launch) and OA (launch aborted, no lift-off) are not launch attempts and are
    left out.
Launching country or bloc: the state code (orgs.tsv) of the first agency listed for the launch. This is GCAT's view of
who launched it, so Rocket Lab's Electron flights from Mahia count for New Zealand (Rocket Lab's New Zealand company),
Starsem's Soyuz flights from Baikonur count for Europe (France), and Sea Launch for "Others" (Cayman Islands).
Spaceport: site codes merged as in common.SPACEPORTS. Air launches (Pegasus, LauncherOne) are placed at the airfield
GCAT gives as the launch site.
Inclination: the inclination of the first payload of the launch in the object catalogue (successful launches only).

Object catalogue (satcat). Each object's Status is grouped as in common.STATUS_GROUP; DDate is the date its first phase
ended (re-entry, deorbit, landing, docking...). The Dest field holds, for some objects that came down, GCAT's rough
place of re-entry or landing (for example '178.4E 61.9S', '29 44N 69 45W', 'POR' for the Pacific Ocean region); I parse
the ones written as coordinates and keep the text for the rest. No place is inferred where GCAT gives none."""
import numpy as np, pandas as pd
from common import *

L0 = read_gcat("launch")
S0 = read_gcat("sites")
O0 = read_gcat("orgs")
V0 = read_gcat("lv")
C0 = read_gcat("satcat")
chk = {"launch_rows": len(L0), "site_rows": len(S0), "org_rows": len(O0), "lv_rows": len(V0), "satcat_rows": len(C0)}
upd = open(f"{RAW}/gcat_launch.tsv", encoding="utf-8").read(4000).splitlines()[1]
assert "2026 Oct 29" in upd, upd
chk["updated"] = upd.replace("#", "").strip()

L = L0.copy()
L["year"] = L.Launch_Date.str[:4].astype(int)
L["jd"] = pd.to_numeric(L.Launch_JD, errors="coerce")
L["kind"] = L.LaunchCode.str[0]
L["res"] = L.LaunchCode.str[1].fillna("")
L["apogee"] = pd.to_numeric(L.Apogee.replace("-", np.nan), errors="coerce")
chk["codes"] = L.LaunchCode.value_counts().to_dict()
chk["kinds"] = L.kind.value_counts().to_dict()
orbital = L.kind.isin(["O", "D"]) & ~L.LaunchCode.isin(["OE", "OA"])
chk["pad_explosions_OE"] = int((L.LaunchCode == "OE").sum()); chk["aborts_OA"] = int((L.LaunchCode == "OA").sum())
O = L[orbital].copy()
assert set(O.res) <= {"S", "F"}, set(O.res)
O["ok"] = (O.res == "S").astype(int)
O["partial"] = O.LaunchCode.str.len().gt(2).astype(int)

# agency -> state -> bloc
ORG = O0.drop_duplicates("Code").set_index("Code")
O["agency1"] = O.Agency.str.split("/").str[0].str.rstrip("?")
O["state"] = O.agency1.map(lambda a: AGENCY_STATE_FIX.get(a, ORG.StateCode.get(a)))
assert O.state.notna().all(), O[O.state.isna()].Agency.unique()
O["bloc"] = O.state.map(lambda s: STATE_BLOC.get(s, "Others"))
chk["others_states"] = O[O.bloc == "Others"].state.value_counts().to_dict()

# sites -> spaceports
SITE = S0.drop_duplicates("Site").set_index("Site")
miss = sorted(set(O.Launch_Site) - set(SITE_PORT))
assert not miss, miss
O["port"] = O.Launch_Site.map(SITE_PORT)
num = lambda v: float(v) if v not in ("", "-") else np.nan
ports = []
for name, host, codes in SPACEPORTS:
    used = O[O.Launch_Site.isin(codes)].Launch_Site.value_counts()
    main = used.index[0] if len(used) else codes[0]
    if main == "TYSC?": main = "TYSC"
    r = SITE.loc[main]
    ports.append({"port": name, "host": host, "codes": codes, "main_code": main, "lat": num(r.Latitude), "lon": num(r.Longitude),
                  "gcat_name": r.Name, "site_state": r.StateCode})
P = pd.DataFrame(ports)
assert P.lat.notna().all() and P.lon.notna().all()

# launch vehicle family
LV = V0.drop_duplicates("LV_Name").set_index("LV_Name")
O["family"] = O.LV_Type.map(LV.LV_Family).fillna(O.LV_Type).str.strip()

# orbit class from the Category field ('Sat LEO O', 'Sat GTO SO 1'...)
O["orbit"] = O.Category.str.split().str[1].fillna("")

# ---------- object catalogue ----------
C = C0.copy()
C["t"] = C.Type.str[0]
C["ldate_y"] = pd.to_numeric(C.LDate.str[:4], errors="coerce")
C["d_y"] = pd.to_numeric(C.DDate.str[:4], errors="coerce")
C["fate"] = C.Status.map(STATUS_GROUP).fillna("Other (exploded, collided, retired or catalogue entries)")
C["inc"] = pd.to_numeric(C.Inc.replace("-", np.nan), errors="coerce")
C["mass"] = pd.to_numeric(C.Mass.replace("-", np.nan), errors="coerce")
chk["status"] = C.Status.value_counts().to_dict()


def parse_place(s):
    """'51.0N 44.75E', '29 44N 69 45W', '160W 9S?', '72.0E 49.7N' -> (lat, lon, approx); else None."""
    approx = "?" in s
    t = s.replace("?", "").strip()
    if not t or not re.fullmatch(r"[\d.\sNSEW]+", t) or not re.search(r"\d", t):
        return None
    lat = lon = None; buf = []
    for n, h in re.findall(r"(\d+(?:\.\d+)?)([NSEW])?", t):
        buf.append(float(n))
        if h:
            v = buf[0] + (buf[1] / 60 if len(buf) > 1 else 0); buf = []
            if h in "NS": lat = v if h == "N" else -v
            else: lon = v if h == "E" else -v
    if lat is None or lon is None or abs(lat) > 90 or abs(lon) > 180:
        return None
    return lat, lon, approx


down = C.fate.isin(["Re-entered", "Deorbited on purpose", "Landed or recovered"])
pp = C.Dest.where(down & (C.Dest != "-"), "").map(lambda s: parse_place(s) if s else None)
C["d_lat"] = pp.map(lambda p: p[0] if p else np.nan)
C["d_lon"] = pp.map(lambda p: p[1] if p else np.nan)
C["d_approx"] = pp.map(lambda p: int(p[2]) if p else 0)
C["d_text"] = C.Dest.where(down & (C.Dest != "-") & C.d_lat.isna(), "")
chk["down_with_dest"] = int((down & (C.Dest != "-")).sum()); chk["down_with_coords"] = int(C.d_lat.notna().sum())

# first payload inclination per launch (orbital, successful)
pay = C[C.t == "P"].sort_values("JCAT")
first = pay.groupby("Launch_Tag").first()
O["inc"] = O.Launch_Tag.map(first.inc)
O["payloads"] = O.Launch_Tag.map(pay.groupby("Launch_Tag").size()).fillna(0).astype(int)
O["objects"] = O.Launch_Tag.map(C.groupby("Launch_Tag").size()).fillna(0).astype(int)
O.loc[O.ok == 0, "inc"] = np.nan
chk["ok_with_inc"] = int(O.inc.notna().sum()); chk["ok"] = int(O.ok.sum())

# keep what we need
assert O.jd.notna().all()
keepL = ["Launch_Tag", "jd", "Launch_Date", "year", "LV_Type", "family", "Flight", "Mission", "Launch_Site", "Launch_Pad", "Platform",
         "Agency", "agency1", "state", "bloc", "port", "LaunchCode", "ok", "partial", "FailCode", "Category", "orbit", "inc", "payloads", "objects", "Notes"]
O[keepL].to_pickle(f"{WORK}/orbital.pkl")
L[["Launch_Tag", "jd", "Launch_Date", "year", "LV_Type", "Launch_Site", "kind", "res", "apogee", "Category", "LaunchCode"]].to_pickle(f"{WORK}/all.pkl")
P.to_pickle(f"{WORK}/ports.pkl")
C[["JCAT", "Satcat", "Launch_Tag", "Piece", "Type", "t", "Name", "PLName", "LDate", "ldate_y", "DDate", "d_y", "Status", "fate", "Dest",
   "Owner", "State", "mass", "inc", "d_lat", "d_lon", "d_approx", "d_text", "OpOrbit"]].to_pickle(f"{WORK}/satcat.pkl")
SITE.reset_index()[["Site", "Name", "StateCode", "Longitude", "Latitude"]].to_pickle(f"{WORK}/sites.pkl")
jsave(chk, f"{WORK}/checks.json", indent=1)
print("orbital attempts", len(O), "ok", int(O.ok.sum()), "years", O.year.min(), O.year.max(), "ports", len(P))
print(O.bloc.value_counts().to_dict())
print("satcat", len(C), C.fate.value_counts().to_dict(), "located down", chk["down_with_coords"])
