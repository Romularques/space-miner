import { createSupabaseContext } from "npm:@supabase/server";

const headers = {
  "Content-Type": "application/json",
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
};
const limit = 10;

function response(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers });
}

Deno.serve(async (request) => {
  if (request.method === "OPTIONS") return new Response("ok", { headers });
  // Aceita exclusivamente a chave publishable atual e obtém um cliente admin
  // somente dentro da Edge Function. A chave secret nunca vai ao navegador.
  const { data: context, error: authError } = await createSupabaseContext(request, {
    auth: "publishable",
  });
  if (authError) return response({ error: "unauthorized" }, authError.status);
  const database = context.supabaseAdmin;

  if (request.method === "GET") {
    const { data, error } = await database.from("leaderboard")
      .select("initials, score, phase, created_at_ms")
      .order("score", { ascending: false }).order("phase", { ascending: false })
      .order("created_at_ms", { ascending: false }).limit(limit);
    return error ? response({ error: "database error" }, 500) : response({ scores: data });
  }

  if (request.method !== "POST") return response({ error: "method not allowed" }, 405);
  const { initials, score, phase } = await request.json().catch(() => ({}));
  if (typeof initials !== "string" || !/^[A-Za-z]{3}$/.test(initials)
      || !Number.isInteger(score) || !Number.isInteger(phase)
      || score < -999999 || score > 999999 || phase < 1 || phase > 999) {
    return response({ error: "invalid score" }, 400);
  }
  const created_at_ms = Date.now();
  const { error } = await database.from("leaderboard").insert({
    initials: initials.toUpperCase(), score, phase, created_at_ms,
  });
  if (error) return response({ error: "database error" }, 500);

  // Mantém permanentemente apenas as dez posições que aparecem no jogo.
  const { data, error: selectError } = await database.from("leaderboard")
    .select("id, initials, score, phase, created_at_ms")
    .order("score", { ascending: false }).order("phase", { ascending: false })
    .order("created_at_ms", { ascending: false });
  if (selectError || !data) return response({ error: "database error" }, 500);
  const discarded = data.slice(limit).map((entry) => entry.id);
  if (discarded.length) await database.from("leaderboard").delete().in("id", discarded);
  return response({ scores: data.slice(0, limit).map(({ id, ...entry }) => entry) });
});
