// Proxy de cotizaciones: la API key vive en el servidor (variable de entorno
// FINNHUB_KEY de Netlify) y NUNCA se envía al navegador.
exports.handler = async (event) => {
  const symbol = ((event.queryStringParameters && event.queryStringParameters.symbol) || "").toUpperCase();
  if (!/^[A-Z0-9.\-]{1,10}$/.test(symbol)) {
    return { statusCode: 400, body: JSON.stringify({ error: "bad symbol" }) };
  }
  const key = process.env.FINNHUB_KEY;
  if (!key) return { statusCode: 500, body: JSON.stringify({ error: "no key configured" }) };
  try {
    const r = await fetch("https://finnhub.io/api/v1/quote?symbol=" + encodeURIComponent(symbol) + "&token=" + key);
    const j = await r.json();
    return {
      statusCode: 200,
      headers: {
        "Content-Type": "application/json",
        "Cache-Control": "public, max-age=20",
        "Access-Control-Allow-Origin": "*"
      },
      body: JSON.stringify({ c: j.c, d: j.d, dp: j.dp, pc: j.pc })
    };
  } catch (e) {
    return { statusCode: 502, body: JSON.stringify({ error: "upstream" }) };
  }
};
