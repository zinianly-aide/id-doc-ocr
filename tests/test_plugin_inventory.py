from id_doc_ocr.tools.plugin_inventory import build_plugin_inventory


def test_plugin_inventory_exposes_maturity_regression_and_trial_profile():
    inventory = build_plugin_inventory()

    assert inventory
    boarding_pass = next(item for item in inventory if item["name"] == "boarding_pass")
    china_id = next(item for item in inventory if item["name"] == "china_id")

    assert boarding_pass["maturity"]["level"] in {"beta", "production_candidate"}
    assert boarding_pass["regression"]["fixture_count"] >= 1
    assert boarding_pass["regression"]["live_image_fixture_count"] >= 1
    assert boarding_pass["trial_profile"]["ocr_backend"] in {"rapidocr", "paddleocr"}
    assert boarding_pass["trial_profile"]["detector_backend"] == "pil"
    assert china_id["trial_profile"]["ocr_backend"] == "paddleocr"
    assert "reason" in china_id["maturity"]
