// Índices + BTC en vivo vía Yahoo Finance (gratis, sin API key), del lado servidor
// (sin CORS). Devuelve { "^IXIC":{px,dp}, ... }. Nasdaq/Nasdaq100/S&P/SOXX/BTC.
const https = require("https");

const SYMS = ["^IXIC", "^NDX", "^GSPC", "SOXX", "BTC-USD"];

exports.handler = async () => {
  const out = {};
  await Promise.all(
    SYMS.map(async (s) => {
      try {
        const raw = await get(
          "https://query1.finance.yahoo.com/v8/finance/chart/" +
            encodeURIComponent(s) +
            "?interval=5m&range=1d"
        );
        const j = JSON.parse(raw);
        const res = j && j.chart && j.chart.result && j.chart.result[0];
        const m = res && res.meta;
        if (m && typeof m.regularMarketPrice === "number") {
          const prev =
            typeof m.chartPreviousClose === "number"
              ? m.chartPreviousClose
              : typeof m.previousClose === "number"
              ? m.previousClose
              : m.regularMarketPrice;
          const dp = prev ? ((m.regularMarketPrice - prev) / prev) * 100 : 0;
          out[s] = { px: m.regularMarketPrice, dp: dp };
        }
      } catch (e) {
        /* omite el símbolo que falle */
      }
    })
  );
  return resp(200, out);
};

function resp(code, obj) {
  return {
    statusCode: code,
    headers: {
      "Content-Type": "application/json",
      "Cache-Control": "public, max-age=20",
      "Access-Control-Allow-Origin": "*"
    },
    body: JSON.stringify(obj)
  };
}

function get(url) {
  return new Promise((resolve, reject) => {
    const req = https.get(
      url,
      {
        timeout: 8000,
        headers: {
          "User-Agent":
            "Mozilla/5.0 (compatible; mercadosgll/1.0; +https://mercadosgll.com)",
          Accept: "application/json"
        }
      },
      (r) => {
        let d = "";
        r.on("data", (c) => (d += c));
        r.on("end", () => resolve(d));
      }
    );
    req.on("error", reject);
    req.on("timeout", () => {
      req.destroy();
      reject(new Error("timeout"));
    });
  });
}
