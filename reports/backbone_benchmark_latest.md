# Backbone benchmark report

- generated_at: `2026-04-09T14:21:14.795782+00:00`
- manifest: `backbone-benchmark-seed` v`0.1.0`
- cases: `4`

## Backend summary

| Backend | Cases | Success | Validator accepted | Avg warnings | Key field hit rate | Decision distribution |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| ocr=mock,vlm=mock | 4 | 100.00% | 50.00% | 3.00 | 63.33% | {"review": 4} |
| ocr=paddleocr,vlm=mock | 4 | 100.00% | 75.00% | 1.75 | 86.67% | {"review": 4} |
| ocr=rapidocr,vlm=mock | 4 | 100.00% | 75.00% | 1.75 | 86.67% | {"review": 4} |

## Track summary

### live_image

| Backend | Cases | Success | Validator accepted | Avg warnings | Key field hit rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| ocr=mock,vlm=mock | 1 | 100.00% | 0.00% | 6.00 | 12.50% |
| ocr=paddleocr,vlm=mock | 1 | 100.00% | 100.00% | 1.00 | 100.00% |
| ocr=rapidocr,vlm=mock | 1 | 100.00% | 100.00% | 1.00 | 100.00% |

### synthetic_control

| Backend | Cases | Success | Validator accepted | Avg warnings | Key field hit rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| ocr=mock,vlm=mock | 3 | 100.00% | 66.67% | 2.00 | 81.82% |
| ocr=paddleocr,vlm=mock | 3 | 100.00% | 66.67% | 2.00 | 81.82% |
| ocr=rapidocr,vlm=mock | 3 | 100.00% | 66.67% | 2.00 | 81.82% |

## Per-case highlights

- `ocr=mock,vlm=mock` / `boarding_pass_live_public_00006737` (live_image, image): decision=`review`, validator_accepted=`False`, warnings=`6`, key_fields=`1/8`
- `ocr=mock,vlm=mock` / `china_id_front_control` (synthetic_control, ocr_result): decision=`review`, validator_accepted=`True`, warnings=`1`, key_fields=`7/7`
- `ocr=mock,vlm=mock` / `passport_td3_control` (synthetic_control, ocr_result): decision=`review`, validator_accepted=`True`, warnings=`1`, key_fields=`10/10`
- `ocr=mock,vlm=mock` / `medical_record_control` (synthetic_control, ocr_result): decision=`review`, validator_accepted=`False`, warnings=`4`, key_fields=`1/5`
- `ocr=rapidocr,vlm=mock` / `boarding_pass_live_public_00006737` (live_image, image): decision=`review`, validator_accepted=`True`, warnings=`1`, key_fields=`8/8`
- `ocr=rapidocr,vlm=mock` / `china_id_front_control` (synthetic_control, ocr_result): decision=`review`, validator_accepted=`True`, warnings=`1`, key_fields=`7/7`
- `ocr=rapidocr,vlm=mock` / `passport_td3_control` (synthetic_control, ocr_result): decision=`review`, validator_accepted=`True`, warnings=`1`, key_fields=`10/10`
- `ocr=rapidocr,vlm=mock` / `medical_record_control` (synthetic_control, ocr_result): decision=`review`, validator_accepted=`False`, warnings=`4`, key_fields=`1/5`
- `ocr=paddleocr,vlm=mock` / `boarding_pass_live_public_00006737` (live_image, image): decision=`review`, validator_accepted=`True`, warnings=`1`, key_fields=`8/8`
- `ocr=paddleocr,vlm=mock` / `china_id_front_control` (synthetic_control, ocr_result): decision=`review`, validator_accepted=`True`, warnings=`1`, key_fields=`7/7`
- `ocr=paddleocr,vlm=mock` / `passport_td3_control` (synthetic_control, ocr_result): decision=`review`, validator_accepted=`True`, warnings=`1`, key_fields=`10/10`
- `ocr=paddleocr,vlm=mock` / `medical_record_control` (synthetic_control, ocr_result): decision=`review`, validator_accepted=`False`, warnings=`4`, key_fields=`1/5`
