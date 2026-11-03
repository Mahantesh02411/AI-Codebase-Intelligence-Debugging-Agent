from __future__ import annotations
import itertools

from .base import LLM
from .types import LLMRequest, LLMResponse, ToolCall, Usage


class GeminiLLM(LLM):
    """Google Gemini via google-genai: function calling + JSON mode + usage metadata."""
    name = "gemini"
    default_model = "gemini-2.0-flash"  # override with LLM_MODEL

    def __init__(self, api_key: str = "", model: str = "", *, client=None, genai=None, **kw) -> None:
        super().__init__(model, **kw)
        if genai is None:
            from google import genai as _genai  # lazy import: optional dependency
            genai = _genai
        self._genai = genai
        self.client = client or genai.Client(api_key=api_key)
        self._ids = itertools.count(1)

    def _contents(self, req: LLMRequest) -> list:
        t = self._genai.types
        out: list = []
        for m in req.messages:
            if m.role == "assistant":
                # echo the provider's own content object when we have it: Gemini needs its thought signatures on function calls
                if m.raw is not None and isinstance(m.raw, t.Content):
                    out.append(m.raw)
                    continue
                parts = ([t.Part(text=m.content)] if m.content else []) + [t.Part(function_call=t.FunctionCall(name=c.name, args=c.args)) for c in m.tool_calls]
                out.append(t.Content(role="model", parts=parts or [t.Part(text="")]))
            elif m.role == "tool":
                part = t.Part.from_function_response(name=m.name or "tool", response={"result": m.content})
                if out and out[-1].role == "user" and out[-1].parts and out[-1].parts[0].function_response is not None:
                    out[-1].parts.append(part)   # several results to one multi-call turn travel together
                else:
                    out.append(t.Content(role="user", parts=[part]))
            else:
                import base64
                parts = [t.Part(text=m.content)] + [t.Part.from_bytes(data=base64.b64decode(i["data"]), mime_type=i["media_type"]) for i in m.images]
                out.append(t.Content(role="user", parts=parts))
        return out

    def _complete(self, req: LLMRequest, model: str) -> LLMResponse:
        t = self._genai.types
        cfg: dict = {"system_instruction": req.system or None, "temperature": req.temperature, "max_output_tokens": req.max_tokens,
                     "http_options": t.HttpOptions(timeout=int(self.timeout * 1000))}
        if req.tools:
            cfg["tools"] = [t.Tool(function_declarations=[t.FunctionDeclaration(name=x.name, description=x.description,
                                                                                parameters_json_schema=x.parameters) for x in req.tools])]
            cfg["automatic_function_calling"] = t.AutomaticFunctionCallingConfig(disable=True)   # the agent runs the tools, not the SDK
            cfg["tool_config"] = t.ToolConfig(function_calling_config=t.FunctionCallingConfig(mode="ANY" if req.require_tool else "AUTO"))
        elif req.json_mode:
            cfg["response_mime_type"] = "application/json"
        r = self.client.models.generate_content(model=model, contents=self._contents(req), config=t.GenerateContentConfig(**cfg))
        text, calls, content = "", [], None
        cands = getattr(r, "candidates", None) or []
        if cands and getattr(cands[0], "content", None) is not None:
            content = cands[0].content
            for p in content.parts or []:
                if getattr(p, "function_call", None):
                    fc = p.function_call
                    calls.append(ToolCall(getattr(fc, "id", None) or f"call_{next(self._ids)}", fc.name, dict(fc.args or {})))
                elif getattr(p, "text", None) and not getattr(p, "thought", False):
                    text += p.text
        if not text and not calls:
            text = getattr(r, "text", None) or ""
        u = getattr(r, "usage_metadata", None)
        usage = Usage(getattr(u, "prompt_token_count", 0) or 0,
                      (getattr(u, "candidates_token_count", 0) or 0) + (getattr(u, "thoughts_token_count", 0) or 0)) if u else Usage()
        reason = str(getattr(cands[0], "finish_reason", "") or "") if cands else ""
        return LLMResponse(text=text, tool_calls=calls, model=model, usage=usage, finish_reason=reason, raw=content)
