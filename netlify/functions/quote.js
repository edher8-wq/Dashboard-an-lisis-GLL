// Proxy de cotizaciones: la API key vive en el servidor (variable de entorno
// FINNHUB_KEY de Netlify) y NUNCA se envía al navegador.
// Usa el módulo nativo https (sin depender de fetch global) para funcionar
// en cualquier versión del runtime de funciones de Netlify.
const https = require("https");

exports.handler = async (event) => {
  const symbol = ((event.queryStringParameters && event.queryStringParameters.symbol) || "").toUpperCase();
  if (!/^[A-Z0-9.\-]{1,10}$/.test(symbol)) {
    return resp(400, { error: "bad symbol" });
  }
  const key = process.env.FINNHUB_KEY;
  if (!key) return resp(500, { error: "no key configured" });
  try {
    const data = await get(
      "https://finnhub.io/api/v1/quote?symbol=" + encodeURIComponent(symbol) + "&token=" + key
    );
    const j = JSON.parse(data);
    return resp(200, { c: j.c, d: j.d, dp: j.dp, pc: j.pc });
  } catch (e) {
    return resp(502, { error: "upstream", detail: String((e && e.message) || e) });
  }
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
    const req = https.get(url, { timeout: 8000, headers: { "User-Agent": "mercadosgll/1.0", "Accept": "application/json" } }, (r) => {
      let d = "";
      r.on("data", (c) => (d += c));
      r.on("end", () => resolve(d));
    });
    req.on("error", reject);
    req.on("timeout", () => {
      req.destroy();
      reject(new Error("timeout"));
    });
  });
};
