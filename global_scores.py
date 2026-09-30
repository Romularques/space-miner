"""Cliente do placar global usado somente na versão Pygbag/WebAssembly."""

import asyncio
import json
from dataclasses import dataclass, field

from web_config import SUPABASE_FUNCTION_URL, SUPABASE_PUBLISHABLE_KEY


@dataclass
class GlobalScores:
    """Acessa a Edge Function sem expor credenciais administrativas."""

    scores: list[dict[str, object]] = field(default_factory=list)
    ready: bool = False
    error: str | None = None

    @staticmethod
    def _sort_key(entry: dict[str, object]) -> tuple[int, int, int]:
        return (int(entry["score"]), int(entry["phase"]), int(entry["created_at_ms"]))

    @property
    def configured(self) -> bool:
        return bool(SUPABASE_FUNCTION_URL and SUPABASE_PUBLISHABLE_KEY)

    async def _request(self, method: str, body: dict[str, object] | None = None) -> dict[str, object] | None:
        """Executa fetch pelo bridge JS do Pygbag, sem bloquear o frame do jogo."""
        if not self.configured:
            self.error = "Ranking online ainda não configurado"
            return None
        try:
            import platform

            bridge = """
            window.SpaceMiner = window.SpaceMiner || {};
            window.SpaceMiner.request = function * (method, url, key, body) {
                let output = null;
                fetch(url, {
                    method: method,
                    headers: {"Content-Type": "application/json", "apikey": key},
                    body: body || undefined
                }).then(response => response.text().then(text => {
                    output = JSON.stringify({status: response.status, body: text});
                })).catch(error => { output = JSON.stringify({status: 0, body: String(error)}); });
                while (output === null) yield;
                yield output;
            };
            """
            platform.window.eval(bridge)  # type: ignore[attr-defined]
            payload = json.dumps(body) if body else None
            generator = platform.window.SpaceMiner.request(  # type: ignore[attr-defined]
                method, SUPABASE_FUNCTION_URL, SUPABASE_PUBLISHABLE_KEY, payload
            )
            response = json.loads(str(await platform.jsiter(generator)))  # type: ignore[attr-defined]
            if not 200 <= int(response["status"]) < 300:
                self.error = "Não foi possível atualizar o ranking"
                return None
            return json.loads(response["body"])
        except (Exception,):
            self.error = "Sem conexão com o ranking"
            return None

    async def refresh(self) -> None:
        payload = await self._request("GET")
        if payload and isinstance(payload.get("scores"), list):
            self.scores = payload["scores"]
            self.ready = True

    def qualifies(self, score: int, phase: int) -> bool:
        # O servidor repete esta validação na gravação; este é só o convite visual.
        if not self.ready:
            return True
        candidate = {"score": score, "phase": phase, "created_at_ms": 9_999_999_999_999}
        ranked = sorted([*self.scores, candidate], key=self._sort_key, reverse=True)[:10]
        return candidate in ranked

    async def add(self, initials: str, score: int, phase: int) -> None:
        payload = await self._request("POST", {"initials": initials, "score": score, "phase": phase})
        if payload and isinstance(payload.get("scores"), list):
            self.scores = payload["scores"]
            self.ready = True

    def submit_in_background(self, initials: str, score: int, phase: int) -> None:
        asyncio.create_task(self.add(initials, score, phase))
