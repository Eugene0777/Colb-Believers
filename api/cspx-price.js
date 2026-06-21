const BNB_RPC_URLS = [
  "https://bsc-dataseed.binance.org",
  "https://bsc-dataseed1.binance.org",
  "https://binance.llamarpc.com"
];

const CSPX = {
  symbol: "CSPX",
  label: "CSPX NAV",
  network: "BNB Chain",
  tokenAddress: "0xDeAa0f353C507A2F0d9b92d20e3fF0FF06f3ACe9",
  aggregatorAddress: "0xd1e71C9d3991213b26Af0cA2D2fc52D8A1f04f0D",
  docsUrl: "https://docs.colb.finance/products/tokenized-pre-ipos/cspx-tokenized-spacex"
};

const SELECTORS = {
  decimals: "0x313ce567",
  latestRoundData: "0xfeaf968c"
};

function send(res, statusCode, payload) {
  res.statusCode = statusCode;
  res.setHeader("content-type", "application/json; charset=utf-8");
  res.setHeader("cache-control", "s-maxage=60, stale-while-revalidate=300");
  res.end(JSON.stringify(payload));
}

async function rpcCall(rpcUrl, to, data) {
  const response = await fetch(rpcUrl, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      jsonrpc: "2.0",
      id: 1,
      method: "eth_call",
      params: [{ to, data }, "latest"]
    })
  });

  const payload = await response.json();
  if (payload.error) throw new Error(payload.error.message || "RPC call failed");
  if (!payload.result || payload.result === "0x") throw new Error("Empty RPC result");
  return payload.result;
}

function decodeUnsigned(hex) {
  return BigInt(hex);
}

function decodeSignedWord(word) {
  let value = BigInt(`0x${word}`);
  const signBit = 1n << 255n;
  const maxUint = 1n << 256n;
  if (value >= signBit) value -= maxUint;
  return value;
}

function decodeLatestRoundData(hex) {
  const clean = hex.replace(/^0x/, "");
  if (clean.length < 64 * 5) throw new Error("Unexpected latestRoundData result");

  return {
    roundId: BigInt(`0x${clean.slice(0, 64)}`).toString(),
    answer: decodeSignedWord(clean.slice(64, 128)),
    startedAt: Number(BigInt(`0x${clean.slice(128, 192)}`)),
    updatedAt: Number(BigInt(`0x${clean.slice(192, 256)}`)),
    answeredInRound: BigInt(`0x${clean.slice(256, 320)}`).toString()
  };
}

function formatUnits(value, decimals) {
  const negative = value < 0n;
  const absolute = negative ? -value : value;
  const base = 10n ** BigInt(decimals);
  const integer = absolute / base;
  const fraction = (absolute % base).toString().padStart(decimals, "0").replace(/0+$/, "");
  const formatted = fraction ? `${integer}.${fraction}` : integer.toString();
  return negative ? `-${formatted}` : formatted;
}

async function readCspxPrice() {
  let lastError;

  for (const rpcUrl of BNB_RPC_URLS) {
    try {
      const [decimalsHex, roundDataHex] = await Promise.all([
        rpcCall(rpcUrl, CSPX.aggregatorAddress, SELECTORS.decimals),
        rpcCall(rpcUrl, CSPX.aggregatorAddress, SELECTORS.latestRoundData)
      ]);

      const decimals = Number(decodeUnsigned(decimalsHex));
      const roundData = decodeLatestRoundData(roundDataHex);
      if (roundData.answer <= 0n) throw new Error("Oracle price is not positive");

      const price = formatUnits(roundData.answer, decimals);
      const updatedAtIso = new Date(roundData.updatedAt * 1000).toISOString();

      return {
        ...CSPX,
        price,
        priceUsd: `$${Number(price).toLocaleString("en-US", {
          minimumFractionDigits: 2,
          maximumFractionDigits: 6
        })}`,
        decimals,
        roundId: roundData.roundId,
        updatedAt: updatedAtIso,
        source: "Colb SpaceX Aggregator",
        rpcUrl
      };
    } catch (error) {
      lastError = error;
    }
  }

  throw lastError || new Error("Could not read CSPX price");
}

export default async function handler(req, res) {
  if (req.method !== "GET") {
    send(res, 405, { error: "Method not allowed" });
    return;
  }

  try {
    const data = await readCspxPrice();
    send(res, 200, data);
  } catch (error) {
    send(res, 502, {
      error: "CSPX price is temporarily unavailable.",
      detail: error.message
    });
  }
}
