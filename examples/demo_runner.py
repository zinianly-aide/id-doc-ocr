from id_doc_ocr import plugins  # noqa: F401
from id_doc_ocr.pipeline.runner import DemoPipelineRunner


if __name__ == "__main__":
    runner = DemoPipelineRunner()
    result = runner.run(
        plugin_name="train_ticket",
        image=b"demo",
        fields={
            "ticket_number": "1234567890",
            "train_number": "G1234",
            "departure_station": "Shanghai",
            "arrival_station": "Hangzhou",
            "departure_time": "2026-03-11 09:00",
        },
    )
    print(result)
