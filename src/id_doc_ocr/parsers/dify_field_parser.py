from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any, Callable
from urllib import request as urllib_request
from urllib.error import HTTPError, URLError


class DifyFieldParserError(RuntimeError):
    pass


@dataclass(frozen=True)
class DifyFieldParserConfig:
    base_url: str
    api_key: str
    app_type: str = "workflow"
    endpoint: str | None = None
    response_mode: str = "blocking"
    user: str = "id-doc-ocr"
    timeout_seconds: float = 60.0

    @classmethod
    def from_env(cls, schema_name: str) -> "DifyFieldParserConfig":
        schema_env = _schema_env_name(schema_name)
        api_key = (
            os.getenv(f"ID_DOC_OCR_DIFY_{schema_env}_API_KEY")
            or os.getenv(f"DIFY_{schema_env}_API_KEY")
            or os.getenv("ID_DOC_OCR_DIFY_API_KEY")
            or os.getenv("DIFY_API_KEY")
        )
        if not api_key:
            raise DifyFieldParserError(
                f"Dify API key is required for schema '{schema_name}'. "
                f"Set ID_DOC_OCR_DIFY_{schema_env}_API_KEY or ID_DOC_OCR_DIFY_API_KEY."
            )

        app_type = (
            os.getenv(f"ID_DOC_OCR_DIFY_{schema_env}_APP_TYPE")
            or os.getenv("ID_DOC_OCR_DIFY_APP_TYPE")
            or "workflow"
        ).strip().lower()
        endpoint = os.getenv(f"ID_DOC_OCR_DIFY_{schema_env}_ENDPOINT") or os.getenv("ID_DOC_OCR_DIFY_ENDPOINT")
        timeout_raw = os.getenv(f"ID_DOC_OCR_DIFY_{schema_env}_TIMEOUT_SECONDS") or os.getenv(
            "ID_DOC_OCR_DIFY_TIMEOUT_SECONDS", "60"
        )
        try:
            timeout_seconds = float(timeout_raw)
        except ValueError:
            raise DifyFieldParserError(f"Invalid Dify timeout value: {timeout_raw}") from None

        return cls(
            base_url=(os.getenv("ID_DOC_OCR_DIFY_BASE_URL") or "https://api.dify.ai/v1").rstrip("/"),
            api_key=api_key,
            app_type=app_type,
            endpoint=endpoint,
            response_mode=os.getenv("ID_DOC_OCR_DIFY_RESPONSE_MODE", "blocking"),
            user=os.getenv("ID_DOC_OCR_DIFY_USER", "id-doc-ocr"),
            timeout_seconds=timeout_seconds,
        )

    def resolved_endpoint(self) -> str:
        if self.endpoint:
            return self.endpoint if self.endpoint.startswith("/") else f"/{self.endpoint}"
        if self.app_type == "workflow":
            return "/workflows/run"
        if self.app_type == "chat":
            return "/chat-messages"
        if self.app_type == "completion":
            return "/completion-messages"
        raise DifyFieldParserError(
            f"Unknown Dify app type: {self.app_type}. Supported values: workflow, chat, completion."
        )


class DifyFieldParser:
    def __init__(
        self,
        *,
        config_factory: Callable[[str], DifyFieldParserConfig] = DifyFieldParserConfig.from_env,
        urlopen: Callable[..., Any] | None = None,
    ) -> None:
        self._config_factory = config_factory
        self._urlopen = urlopen or urllib_request.urlopen

    def parse(self, *, plugin: Any, ocr_result: dict[str, Any], prompt_context: dict[str, Any] | None = None) -> dict[str, Any]:
        schema_name = plugin.get_schema_name()
        config = self._config_factory(schema_name)
        target_fields = _resolve_target_fields(schema_name, plugin)
        prompt_context = prompt_context or {}
        prompt_texts = prompt_context.get("prompt_texts") if isinstance(prompt_context.get("prompt_texts"), dict) else {}
        inputs = {
            "schema_name": schema_name,
            "plugin_name": getattr(getattr(plugin, "metadata", None), "name", schema_name),
            "ocr_text": _ocr_text(ocr_result),
            "ocr_lines": ocr_result.get("lines", []),
            "ocr_lines_json": json.dumps(ocr_result.get("lines", []), ensure_ascii=False),
            "target_fields": target_fields,
            "target_fields_json": json.dumps(target_fields, ensure_ascii=False),
            "recognition_type": prompt_context.get("recognition_type") or getattr(getattr(plugin, "metadata", None), "name", schema_name),
            "leave_type": prompt_context.get("leave_type"),
            "custom_prompt": prompt_context.get("custom_prompt") or prompt_texts.get("field_extraction") or "",
            "verification_prompt": prompt_context.get("verification_prompt") or prompt_texts.get("verification") or "",
            "prompt_texts": prompt_texts,
            "prompt_texts_json": json.dumps(prompt_texts, ensure_ascii=False),
        }
        response_payload = self._call_dify(config, inputs)
        fields = _extract_fields(response_payload)
        if not isinstance(fields, dict):
            raise DifyFieldParserError("Dify response did not contain a JSON object of fields.")
        return fields

    def _call_dify(self, config: DifyFieldParserConfig, inputs: dict[str, Any]) -> dict[str, Any]:
        payload = _build_payload(config, inputs)
        request = urllib_request.Request(
            f"{config.base_url}{config.resolved_endpoint()}",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "curl/8.7.1",
            },
            method="POST",
        )
        try:
            with self._urlopen(request, timeout=config.timeout_seconds) as response:
                raw_body = response.read().decode("utf-8")
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise DifyFieldParserError(f"Dify request failed with HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise DifyFieldParserError(f"Dify request failed: {exc.reason}") from exc
        except TimeoutError as exc:
            raise DifyFieldParserError("Dify request timed out.") from exc

        if config.response_mode == "streaming":
            return {"answer": _parse_streaming_answer(raw_body)}

        try:
            return json.loads(raw_body)
        except json.JSONDecodeError as exc:
            raise DifyFieldParserError("Dify response is not valid JSON.") from exc


def _schema_env_name(schema_name: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", schema_name).strip("_").upper()


def is_dify_configured(schema_name: str) -> bool:
    schema_env = _schema_env_name(schema_name)
    return bool(
        os.getenv(f"ID_DOC_OCR_DIFY_{schema_env}_API_KEY")
        or os.getenv(f"DIFY_{schema_env}_API_KEY")
        or os.getenv("ID_DOC_OCR_DIFY_API_KEY")
        or os.getenv("DIFY_API_KEY")
    )


def dify_configuration_message(schema_name: str) -> str:
    schema_env = _schema_env_name(schema_name)
    return (
        f"Dify parser is not configured for schema '{schema_name}'. "
        f"Set ID_DOC_OCR_DIFY_{schema_env}_API_KEY or ID_DOC_OCR_DIFY_API_KEY, "
        "then restart the backend."
    )


def _resolve_target_fields(schema_name: str, plugin: Any) -> list[str]:
    schema_env = _schema_env_name(schema_name)
    env_value = os.getenv(f"ID_DOC_OCR_DIFY_{schema_env}_TARGET_FIELDS") or os.getenv(
        "ID_DOC_OCR_DIFY_TARGET_FIELDS"
    )
    if env_value:
        return [field.strip() for field in env_value.split(",") if field.strip()]

    config = plugin.get_default_config() if callable(getattr(plugin, "get_default_config", None)) else {}
    fields = config.get("fields", []) if isinstance(config, dict) else []
    resolved: list[str] = []
    for item in fields:
        if isinstance(item, str):
            resolved.append(item)
        elif isinstance(item, dict) and item.get("name"):
            resolved.append(str(item["name"]))
    return resolved


def _ocr_text(ocr_result: dict[str, Any]) -> str:
    text = ocr_result.get("text")
    if isinstance(text, str):
        return text
    if isinstance(text, list):
        return "\n".join(str(item) for item in text if item)
    lines = ocr_result.get("lines") or []
    return "\n".join(str(line.get("text")) for line in lines if isinstance(line, dict) and line.get("text"))


def _build_payload(config: DifyFieldParserConfig, inputs: dict[str, Any]) -> dict[str, Any]:
    if config.app_type == "workflow":
        return {"inputs": inputs, "response_mode": config.response_mode, "user": config.user}
    query = _build_chat_query(inputs)
    if config.app_type == "chat":
        return {"inputs": inputs, "query": query, "response_mode": config.response_mode, "user": config.user}
    if config.app_type == "completion":
        return {"inputs": {**inputs, "query": query}, "response_mode": config.response_mode, "user": config.user}
    raise DifyFieldParserError(
        f"Unknown Dify app type: {config.app_type}. Supported values: workflow, chat, completion."
    )


def _build_chat_query(inputs: dict[str, Any]) -> str:
    target_fields = inputs.get("target_fields")
    if not isinstance(target_fields, list):
        target_fields = []
    field_template = {str(field): None for field in target_fields}
    output_template = {"fields": field_template}
    ocr_text = str(inputs.get("ocr_text") or "").strip()
    ocr_lines_json = str(inputs.get("ocr_lines_json") or "[]")
    schema_name = str(inputs.get("schema_name") or "")
    return "\n".join(
        [
            "You are an information extraction parser for leave-audit document OCR text.",
            f"Schema name: {schema_name}",
            f"Target fields JSON: {json.dumps(target_fields, ensure_ascii=False)}",
            "Custom extraction instructions:",
            str(inputs.get("custom_prompt") or "").strip() or "(none)",
            "Additional prompt texts JSON:",
            str(inputs.get("prompt_texts_json") or "{}"),
            "Return ONLY one valid JSON object. Do not include markdown, explanation, or extra keys.",
            "Use exactly this JSON shape and exactly these field names:",
            json.dumps(output_template, ensure_ascii=False),
            "If a value is unknown, set it to null. Do not invent placeholder field names.",
            "OCR text:",
            ocr_text,
            "OCR lines JSON:",
            ocr_lines_json,
        ]
    )


def _extract_fields(payload: dict[str, Any]) -> dict[str, Any]:
    candidates: list[Any] = [
        payload.get("fields"),
        payload.get("answer"),
    ]
    data = payload.get("data")
    if isinstance(data, dict):
        outputs = data.get("outputs")
        if isinstance(outputs, dict):
            candidates.extend(
                [
                    outputs.get("fields"),
                    outputs.get("result"),
                    outputs.get("text"),
                    outputs.get("answer"),
                    outputs,
                ]
            )

    for candidate in candidates:
        parsed = _parse_candidate(candidate)
        if isinstance(parsed, dict):
            fields = parsed.get("fields")
            return fields if isinstance(fields, dict) else parsed
    raise DifyFieldParserError("Dify response did not include extractable fields.")


def _parse_candidate(candidate: Any) -> Any:
    if isinstance(candidate, dict):
        return candidate
    if not isinstance(candidate, str):
        return None
    text = candidate.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None


def _parse_streaming_answer(raw_body: str) -> str:
    chunks: list[str] = []
    for line in raw_body.splitlines():
        line = line.strip()
        if not line.startswith("data:"):
            continue
        payload = line.removeprefix("data:").strip()
        if not payload or payload == "[DONE]":
            continue
        try:
            event = json.loads(payload)
        except json.JSONDecodeError:
            continue
        answer = event.get("answer")
        if isinstance(answer, str):
            chunks.append(answer)
    answer_text = "".join(chunks).strip()
    if not answer_text:
        raise DifyFieldParserError("Dify streaming response did not contain an answer.")
    return answer_text
