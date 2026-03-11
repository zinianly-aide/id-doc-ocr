def convert_label_studio_to_internal(payload: dict) -> dict:
    return {
        "source": "label_studio",
        "raw": payload,
    }
