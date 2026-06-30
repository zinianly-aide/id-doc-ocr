import json

from fastapi.testclient import TestClient

from id_doc_ocr.service.app import ServiceSettings, create_app


class FakeDifyResponse:
    def __init__(self, payload: dict):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        if isinstance(self.payload, str):
            return self.payload.encode("utf-8")
        return json.dumps(self.payload, ensure_ascii=False).encode("utf-8")


def test_infer_can_use_dify_field_parser_backend(monkeypatch):
    calls = []

    def fake_urlopen(request, timeout):
        calls.append(
            {
                "url": request.full_url,
                "timeout": timeout,
                "headers": dict(request.header_items()),
                "body": json.loads(request.data.decode("utf-8")),
            }
        )
        return FakeDifyResponse(
            {
                "data": {
                    "outputs": {
                        "fields": {
                            "hospital_name": "测试医院",
                            "diagnosis": ["上呼吸道感染"],
                            "issue_date": "2026-05-20",
                            "patient_name": "张三",
                        }
                    }
                }
            }
        )

    monkeypatch.setenv("ID_DOC_OCR_DIFY_API_KEY", "app-test")
    monkeypatch.setenv("ID_DOC_OCR_DIFY_BASE_URL", "https://dify.example.test/v1")
    monkeypatch.setenv("ID_DOC_OCR_DIFY_DIAGNOSIS_PROOF_TARGET_FIELDS", "hospital_name,diagnosis,issue_date")
    monkeypatch.setattr("id_doc_ocr.parsers.dify_field_parser.urllib_request.urlopen", fake_urlopen)

    settings = ServiceSettings(
        default_ocr_backend="mock",
        default_vlm_backend="mock",
        default_detector_backend="mock",
        default_rectify_backend="mock",
        default_field_parser_backend="plugin",
    )
    client = TestClient(create_app(settings))
    response = client.post(
        "/infer",
        data={
            "plugin_name": "diagnosis_proof",
            "ocr_backend": "mock",
            "vlm_backend": "mock",
            "field_parser_backend": "dify",
        },
        files={"file": ("sample.jpg", b"fake-image-bytes", "image/jpeg")},
    )

    assert response.status_code == 200
    result = response.json()["result"]
    assert result["field_parser_backend"] == "dify"
    assert result["parsed_fields"]["hospital_name"] == "测试医院"
    assert result["parsed_fields"]["diagnosis"] == ["上呼吸道感染"]
    assert result["validation"]["accepted"] is True
    assert len(calls) == 1
    assert calls[0]["url"] == "https://dify.example.test/v1/workflows/run"
    assert calls[0]["headers"]["Authorization"] == "Bearer app-test"
    assert calls[0]["headers"]["User-agent"] == "curl/8.7.1"
    assert calls[0]["body"]["inputs"]["schema_name"] == "diagnosis_proof"
    assert calls[0]["body"]["inputs"]["target_fields"] == ["hospital_name", "diagnosis", "issue_date"]
    assert calls[0]["body"]["inputs"]["custom_prompt"] == ""


def test_dify_field_parser_sends_custom_prompt_context_to_workflow():
    calls = []

    def fake_urlopen(request, timeout):
        calls.append(json.loads(request.data.decode("utf-8")))
        return FakeDifyResponse({"data": {"outputs": {"fields": {"patient_name": "张三"}}}})

    class Plugin:
        metadata = type("Metadata", (), {"name": "diagnosis_proof"})()

        def get_schema_name(self):
            return "diagnosis_proof"

        def get_default_config(self):
            return {"fields": [{"name": "patient_name"}]}

    parser = __import__(
        "id_doc_ocr.parsers.dify_field_parser",
        fromlist=["DifyFieldParser", "DifyFieldParserConfig"],
    )
    field_parser = parser.DifyFieldParser(
        config_factory=lambda schema_name: parser.DifyFieldParserConfig(
            base_url="https://dify.example.test/v1",
            api_key="app-test",
            app_type="workflow",
        ),
        urlopen=fake_urlopen,
    )

    fields = field_parser.parse(
        plugin=Plugin(),
        ocr_result={"text": "姓名 张三"},
        prompt_context={
            "recognition_type": "diagnosis_proof",
            "leave_type": "SICK",
            "prompt_texts": {"field_extraction": "优先抽取患者姓名", "verification": "核对病假日期"},
        },
    )

    assert fields == {"patient_name": "张三"}
    inputs = calls[0]["inputs"]
    assert inputs["custom_prompt"] == "优先抽取患者姓名"
    assert inputs["verification_prompt"] == "核对病假日期"
    assert inputs["recognition_type"] == "diagnosis_proof"
    assert inputs["leave_type"] == "SICK"


def test_dify_field_parser_accepts_streaming_chat_response():
    calls = []

    def fake_urlopen(request, timeout):
        calls.append(json.loads(request.data.decode("utf-8")))
        first = json.dumps({"event": "agent_message", "answer": "```json\n{\"fields\":{\"patient_name\":\"张三\""})
        second = json.dumps({"event": "agent_message", "answer": ",\"issue_date\":\"2026-05-20\"}}\n```"})
        return FakeDifyResponse(
            f"data: {first}\n\n"
            f"data: {second}\n\n"
        )

    class Plugin:
        def get_schema_name(self):
            return "diagnosis_proof"

        def get_default_config(self):
            return {}

    parser = __import__(
        "id_doc_ocr.parsers.dify_field_parser",
        fromlist=["DifyFieldParser", "DifyFieldParserConfig"],
    )
    field_parser = parser.DifyFieldParser(
        config_factory=lambda schema_name: parser.DifyFieldParserConfig(
            base_url="https://dify.example.test/v1",
            api_key="app-test",
            app_type="chat",
            response_mode="streaming",
        ),
        urlopen=fake_urlopen,
    )

    fields = field_parser.parse(
        plugin=Plugin(),
        ocr_result={"text": "姓名 张三"},
        prompt_context={"prompt_texts": {"field_extraction": "只返回病假证明字段"}},
    )

    assert fields == {"patient_name": "张三", "issue_date": "2026-05-20"}
    assert calls[0]["query"].startswith("You are an information extraction parser")
    assert '"fields": {}' in calls[0]["query"]
    assert "Do not invent placeholder field names." in calls[0]["query"]
    assert "只返回病假证明字段" in calls[0]["query"]
