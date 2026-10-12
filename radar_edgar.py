#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Radar de filings SEC (EDGAR) para el tablero GLL.
Cada corrida revisa, por emisora, los filings RECIENTES (ultimos ~3 dias) y marca
los que mueven precio: 8-K (hechos relevantes, con el tipo de evento), Form 4
(insiders), 13D/13G (stakes de activistas/grandes). Escribe radar.json.
Corre en GitHub Actions (EDGAR es gratis, sin API key). No usa IBKR ni LLM.
"""
import json, urllib.request, time, sys
from datetime import datetime, timedelta

UA = {"User-Agent": "Analisis GLL Radar contacto@mercadosgll.com"}
MES = ["ene","feb","mar","abr","may","jun","jul","ago","sep","oct","nov","dic"]

# Emisoras del tablero (US). Samsung (005930) excluida: coreana, no reporta a la SEC.
TICKERS = ["AMZN","GOOGL","MSFT","META","NVDA","TSM","ASML","AMD","MRVL","INTC","MU",
 "SNDK","WDC","CRWV","IREN","SPCX","WYFI","PLTR","NOW","APP","UPST","PYPL","COIN","MSTR",
 "UBER","CEG","VST","GEV","ETN","VRT","CAT","BE","NEE","FSLR","CCJ","OKLO","SMR","HIMS","SLS","HD",
 "LDOS","MMS","LUMN"]

# Items de un 8-K -> que significan (los que mas mueven precio)
ITEMS = {
 "1.01":"Acuerdo material nuevo","1.02":"Fin de acuerdo material","1.03":"Bancarrota",
 "2.01":"Adquisicion/venta completada","2.02":"Resultados (earnings)","2.03":"Deuda/obligacion material",
 "2.04":"Aceleracion de obligacion","2.05":"Costos de reestructura","2.06":"Deterioro de activos",
 "3.01":"Aviso de delisting","3.02":"Venta de valores (dilucion)","3.03":"Cambio a derechos de accionistas",
 "4.01":"Cambio de auditor","4.02":"Estados previos no confiables","5.01":"Cambio de control",
 "5.02":"Cambio en directivos/consejo","5.03":"Cambio de estatutos","5.07":"Votacion de accionistas",
 "7.01":"Regulation FD (divulgacion)","8.01":"Otros eventos relevantes","9.01":"Estados financieros/anexos"}

FORMS = {"8-K":"8-K","8-K/A":"8-K","4":"Form 4","4/A":"Form 4","3":"Form 3",
 "SC 13D":"13D","SC 13D/A":"13D","SC 13G":"13G","SC 13G/A":"13G","SC 14D9":"Tender"}

def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read()

def fmt(d):  # "YYYY-MM-DD" -> "DD-mmm"
    try:
        x=datetime.strptime(d,"%Y-%m-%d"); return f"{x.day}-{MES[x.month-1]}"
    except Exception: return d

def main():
    try:
        cmap = json.loads(get("https://www.sec.gov/files/company_tickers.json").decode("utf-8","replace"))
    except Exception as e:
        print(f"[fatal] no se pudo bajar el mapa de CIK: {e}", file=sys.stderr); return
    t2cik = {v["ticker"].upper(): str(v["cik_str"]).zfill(10) for v in cmap.values()}
    cutoff = (datetime.utcnow()-timedelta(days=3)).strftime("%Y-%m-%d")
    out = {}
    for tk in TICKERS:
        cik = t2cik.get(tk)
        if not cik: continue
        try:
            sub = json.loads(get(f"https://data.sec.gov/submissions/CIK{cik}.json").decode("utf-8","replace"))
        except Exception as e:
            print(f"[warn] {tk}: {e}", file=sys.stderr); time.sleep(0.2); continue
        r = sub.get("filings",{}).get("recent",{})
        forms=r.get("form",[]); dates=r.get("filingDate",[]); accs=r.get("accessionNumber",[]); items=r.get("items",[])
        sigs=[]
        for i in range(len(forms)):
            f=forms[i]
            if f not in FORMS or dates[i] < cutoff: continue
            acc=accs[i]; accn=acc.replace("-","")
            url=f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accn}/{acc}-index.htm"
            typ=FORMS[f]; desc=typ
            if f.startswith("8-K") and i < len(items) and items[i]:
                codes=[c.strip() for c in items[i].split(",") if c.strip()]
                desc="8-K: "+"; ".join(ITEMS.get(c,c) for c in codes)
            sigs.append({"type":typ,"t":desc,"d":fmt(dates[i]),"u":url})
            if len(sigs)>=6: break
        if sigs: out[tk]=sigs
        time.sleep(0.15)
    radar={"updated":f"{datetime.utcnow().day}-{MES[datetime.utcnow().month-1]}","source":"SEC EDGAR","tickers":out}
    json.dump(radar, open("radar.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"radar.json: {len(out)} emisoras con filings recientes (ultimos 3 dias)")

if __name__=="__main__":
    main()
