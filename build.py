#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Actualizacion diaria de precios del tablero GLL.
Lee index.html, baja el ultimo cierre (y el previo) de cada emisora desde Stooq
(sin API key), recalcula precio / variacion del dia / fecha, y reescribe index.html.
Si una descarga falla, CONSERVA el precio anterior (nunca rompe el tablero).
Corre en GitHub Actions; Netlify/GitHub Pages redeploya al hacer commit.
"""
import json, re, sys, urllib.request, io, csv
from datetime import datetime

HTML = "index.html"

# ticker (campo "tk" del tablero) -> simbolo Stooq. None = no se baja (precio fijo).
STOOQ = {
 "AMZN":"amzn.us","GOOGL":"googl.us","MSFT":"msft.us","META":"meta.us","NVDA":"nvda.us",
 "TSM":"tsm.us","ASML":"asml.us","AMD":"amd.us","MRVL":"mrvl.us","INTC":"intc.us",
 "005930":None,  # Samsung (KRX, en wones) -> precio fijo
 "MU":"mu.us","SNDK":"sndk.us","WDC":"wdc.us","CRWV":"crwv.us","IREN":"iren.us",
 "SPCX":"spcx.us","WYFI":"wyfi.us","PLTR":"pltr.us","NOW":"now.us","APP":"app.us",
 "UPST":"upst.us","PYPL":"pypl.us","COIN":"coin.us","MSTR":"mstr.us","UBER":"uber.us",
 "CEG":"ceg.us","VST":"vst.us","GEV":"gev.us","ETN":"etn.us","VRT":"vrt.us","CAT":"cat.us",
 "BE":"be.us","NEE":"nee.us","FSLR":"fslr.us","CCJ":"ccj.us","OKLO":"oklo.us","SMR":"smr.us",
 "HIMS":"hims.us","SLS":"sls.us","HD":"hd.us",
}
MES = ["ene","feb","mar","abr","may","jun","jul","ago","sep","oct","nov","dic"]

def fetch_stooq(sym):
    """Devuelve (last_close, prev_close, fecha_datetime) o None si falla."""
    url = f"https://stooq.com/q/d/l/?s={sym}&i=d"
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        raw = urllib.request.urlopen(req, timeout=30).read().decode("utf-8","replace")
        rows = list(csv.DictReader(io.StringIO(raw)))
        rows = [r for r in rows if r.get("Close") and r["Close"] not in ("N/D","")]
        if len(rows) < 2:
            return None
        last, prev = rows[-1], rows[-2]
        lc, pc = float(last["Close"]), float(prev["Close"])
        d = datetime.strptime(last["Date"], "%Y-%m-%d")
        return lc, pc, d
    except Exception as e:
        print(f"  [warn] {sym}: {e}", file=sys.stderr)
        return None

def extract_array(html, marker):
    """Extrae el literal [...] que sigue a `marker` con conteo de corchetes (respeta strings)."""
    i = html.index(marker) + len(marker)
    while html[i] != "[":
        i += 1
    start = i; depth = 0; instr = False; esc = False
    while i < len(html):
        c = html[i]
        if instr:
            if esc: esc = False
            elif c == "\\": esc = True
            elif c == '"': instr = False
        else:
            if c == '"': instr = True
            elif c == "[": depth += 1
            elif c == "]":
                depth -= 1
                if depth == 0:
                    return start, i+1, html[start:i+1]
        i += 1
    raise ValueError("array no cerrado")

def main():
    html = open(HTML, encoding="utf-8").read()
    s, e, lit = extract_array(html, "const D=")
    data = json.loads(lit)
    updated = 0
    for row in data:
        tk = row.get("tk")
        sym = STOOQ.get(tk)
        if not sym:
            continue
        r = fetch_stooq(sym)
        if not r:
            continue  # conserva precio anterior
        lc, pc, d = r
        chg = (lc - pc) / pc * 100 if pc else 0.0
        row["px"] = f"${lc:,.2f}"
        row["ch"] = f"{'+' if chg>=0 else ''}{chg:.1f}%"
        row["dir"] = 1 if chg >= 0 else -1
        row["as"] = f"{d.day}-{MES[d.month-1]}"
        updated += 1
        print(f"  {tk}: {row['px']} ({row['ch']}) {row['as']}")
    newlit = json.dumps(data, ensure_ascii=False)
    out = html[:s] + newlit + html[e:]
    open(HTML, "w", encoding="utf-8").write(out)
    print(f"Listo. Emisoras actualizadas: {updated}/{len(data)}")
    # codigo de salida 0 siempre; el workflow decide si hubo cambios via git diff

if __name__ == "__main__":
    main()
