// worker-cors.js — free-image-generation-api (saurav-z) with browser access added.
// Original: https://github.com/saurav-z/free-image-generation-api (MIT License)
// Only change vs the original: CORS headers + OPTIONS handling, so a website
// (like your editor on GitHub Pages) is allowed by the browser to call it.
// Paste this whole file into your Cloudflare Worker instead of the default code.

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Authorization, Content-Type",
  "Access-Control-Max-Age": "86400",
};

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json", ...CORS },
  });
}

export default {
  async fetch(request, env) {
    // Browser preflight (the browser asks permission before sending the real request)
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: CORS });
    }

    const API_KEY = env.API_KEY;
    const url = new URL(request.url);
    const auth = request.headers.get("Authorization");

    // Simple API key check
    if (auth !== `Bearer ${API_KEY}`) {
      return json({ error: "Unauthorized" }, 401);
    }

    // Only allow POST requests to /
    if (request.method !== "POST" || url.pathname !== "/") {
      return json({ error: "Not allowed" }, 405);
    }

    try {
      const { prompt } = await request.json();

      if (!prompt) return json({ error: "Prompt is required" }, 400);

      // Choose a model from this list (free on Cloudflare Workers AI):
      // "@cf/black-forest-labs/flux-1-schnell"          <- default: fast + good
      // "@cf/lykon/dreamshaper-8-lcm"
      // "@cf/bytedance/stable-diffusion-xl-lightning"
      // "@cf/stabilityai/stable-diffusion-xl-base-1.0"
      // "@cf/runwayml/stable-diffusion-v1-5-img2img"
      // "@cf/runwayml/stable-diffusion-v1-5-inpainting"

      const result = await env.AI.run(
        "@cf/black-forest-labs/flux-1-schnell",
        { prompt }
      );

      // flux-1-schnell answers with a JSON object {image: "<base64>"} -
      // decode it to real JPEG bytes. SDXL-family models answer with raw
      // image bytes directly, which we pass through unchanged.
      if (result && typeof result === "object" && typeof result.image === "string") {
        const img = Uint8Array.from(atob(result.image), (m) => m.codePointAt(0));
        return new Response(img, {
          headers: { "Content-Type": "image/jpeg", ...CORS },
        });
      }
      return new Response(result, {
        headers: { "Content-Type": "image/jpeg", ...CORS },
      });
    } catch (err) {
      return json({ error: "Failed to generate image", details: err.message }, 500);
    }
  },
};
