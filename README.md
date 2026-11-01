# Up and down: every orbital launch since Sputnik, and where it all comes back

A map and analysis of all 7,416 orbital launch attempts from Sputnik (4 October 1957) to 2026 Oct 27 in Jonathan McDowell's General Catalog of Artificial Space Objects (GCAT): who launched them, from which of 46 spaceports, how often they failed, and what has come back down, including the spacecraft cemetery around Point Nemo in the South Pacific.

Interactive page: https://maps.tristanhotham.com/rocket-launches/
Paper: https://doi.org/10.5281/zenodo.23857612
Blog post: https://blog.tristanhotham.com/2026/10/31/rocket-launches/

## Headline results

- Launches: 7,416 orbital launch attempts, 507 (6.8%) failed. Cold War peak 139 in 1967; post Cold War low 54 in 2004; record 329 in 2025 (137% above the old peak, 6.1 times the low). 20% of all launches have happened since 2020.
- Who: SpaceX made 170 of the 329 attempts in 2025 (52%); China 92; Russia 17. Over the whole period the Soviet Union and Russia made 45% of attempts, the United States 33% and China 11%.
- Spaceports: Plesetsk (1,686), Baikonur (1,558), Cape Canaveral with Kennedy (1,393) and Vandenberg (938) hold 75% of all attempts. In 2025 Florida hosted 109 (33%); Mahia, New Zealand 17, more than Baikonur (6).
- Latitude: Earth's eastward push is 463 m/s at Kourou, 323 m/s at Baikonur; 70% of Kourou's launches head towards geostationary orbit, 18% of Baikonur's. Palmachim (Israel) launches only westward.
- Coming down: 34,974 of 69,999 catalogued objects (50%) have come back; only 183 were deliberately deorbited. Peak year 2022 (2,470, 1,379 of them Kosmos 1408 fragments). In 2025, 36% of returns were Starlink satellites.
- Where: of 2,033 uncontrolled re-entries with a GCAT place, 76% fell over the sea and 5.1% within 2,500 km of Point Nemo (a circle covering 3.8% of the Earth). The spacecraft cemetery takes the few big controlled returns, not junk in general.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/04_build_site.py`; page data embedded, `data/launches.json` and `data/reentries.json` loaded by the page). |
| `header.png` | Social card, 1200 x 630. |
| `data/orbital_launches.csv` | All 7,416 orbital launch attempts: GCAT tag, date, vehicle, mission, GCAT site and spaceport (with coordinates), agency and its state, country or bloc, launch code, outcome, orbit class, first payload inclination, payloads and objects catalogued. |
| `data/spaceports.csv` | Per spaceport: host country, coordinates, attempts, failures, first and last year, busiest year, since 2020, 2025, rotation speed, direction shares, launches towards geostationary orbit. |
| `data/launches_by_year.csv` | Attempts, successes, failures, by bloc, SpaceX and payloads catalogued, per year. |
| `data/reentries_by_year.csv` | Catalogued objects that re-entered, were deorbited or landed, per year and type, and Starlink satellites among them. |
| `data/reentry_places.csv` | The 2,136 objects whose place of re-entry or landing GCAT writes as coordinates, with the original text, land or sea, and distance to Point Nemo. |
| `data/objects_by_fate.csv` | Catalogued objects by type and fate. |
| `data/space_stations_fate.csv` | GCAT's record for every Salyut, Skylab, Mir and Tiangong station. |
| `data/results.json` | Every number used in the page, paper, blog, collage and post. |
| `data/site.json`, `data/launches.json`, `data/reentries.json`, `data/world.json`, `data/cities.json` | Page data. |
| `code/` | Scripts, run in order (below), and the page, paper and blog templates. |
| `release/` | Paper PDF and LaTeX source with figures (`paper/`), blog post, figures and meta (`blog/`), Zenodo files (`zenodo/`). |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |
| `qa/` | Screenshots of the page at desktop and phone widths. |

## Method in brief

- Orbital launch attempt: GCAT launch code O (orbital) or D (deep space), excluding OE (pad explosion before launch, 11) and OA (abort before lift-off, 6). Failure: outcome F, including partial failures. Earlier suborbital flights, including 628 German A-4 (V-2) launches from 1942, are context only.
- Who launched: state of the first agency GCAT lists (orgs.tsv), grouped into eight blocs. This is GCAT's agency view, so Rocket Lab counts for New Zealand and Starsem's Soyuz flights from Baikonur for Europe.
- Spaceports: GCAT site codes merged where renamed or adjacent (e.g. NIIP-5 and GIK-5 at Baikonur; Cape Canaveral with Kennedy). Air launches at the airfield.
- Direction: inclination of the first payload (successful launches to low and medium orbit). GCAT has no launch azimuths.
- Fates: satcat status grouped (R re-entered, D deorbited, L landed, DK docked...). Re-entry places only where GCAT's destination field gives coordinates; nothing inferred. The 2,500 km circle around Point Nemo is an indicative device, not a boundary.
- Caveats: GCAT judgements are followed; the main catalogue omits objects without standard catalogue numbers; fates after docking (cargo ship deorbits) are in GCAT's event catalogues, not used; 2026 is partial (to 2026 Oct 27).

## How to rerun

Needs Python 3 with numpy, pandas, shapely, pyproj, matplotlib and fontTools, xelatex and pdftotext; node with Playwright for `code/qa.js`. Raw inputs are read in place (paths in `code/common.py`): GCAT TSVs and Wikipedia pages in `/home/claude/newdata/raw8/launches/`, Natural Earth in `/home/claude/newdata/raw/geo/`. Intermediate files go to `/dev/shm/rocketlaunches/work` (set `RLTMP` to change).

```
python3 code/01_clean.py        # read GCAT, orbital attempts, blocs, spaceports, object fates and places
python3 code/02_geo.py          # outlines and city labels
python3 code/03_results.py      # results.json, data tables, page data
python3 code/04_build_site.py   # index.html
python3 code/05_figures.py      # header, blog and paper figures
python3 code/06_paper.py        # paper PDF
python3 reddit/collage.py       # collage
python3 code/07_readme.py       # README, LICENSE, Reddit post
python3 code/08_release.py      # blog post, Zenodo files
```

## Sources and licences

- Jonathan C. McDowell, General Catalog of Artificial Space Objects (GCAT), release 1.8.8, https://planet4589.org/space/gcat. CC BY 4.0. Data from GCAT (J. McDowell, planet4589.org/space/gcat).
- Wikipedia: "Pole of inaccessibility" (Point Nemo), "Spacecraft cemetery", "Spaceport", "List of rocket launch sites". CC BY-SA 4.0. Used for facts quoted in the text; no Wikipedia text is reproduced.
- Natural Earth countries, land and populated places (https://www.naturalearthdata.com/). Public domain.
- Base map tiles on the page: © Esri.

## Citation

Hotham, T. (2026) Up and down: seventy years of orbital launches and where space hardware comes back to Earth. Zenodo. https://doi.org/10.5281/zenodo.23857612

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
