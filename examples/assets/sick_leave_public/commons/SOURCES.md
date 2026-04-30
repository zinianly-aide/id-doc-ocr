# Public sick-leave-adjacent sample sources

Downloaded on 2026-04-30 from Wikimedia Commons public files.

These are not all exact Chinese sick-leave certificates. They are public medical-document-adjacent assets intended to supplement the sample pool for:
- medical certificate / diagnosis proof analogs
- prescription / medical form OCR stress cases
- medical-record / illness-history edge cases

## Downloaded files

| Local file | Wikimedia title | License | Source URL | Suggested bucket |
|---|---|---|---|---|
| `certificado_medico.jpg` | `File:Certificado médico.jpg` | Public domain | https://commons.wikimedia.org/wiki/File:Certificado_m%C3%A9dico.jpg | Normal / Edge |
| `medical_care_card_usa_sample.jpg` | `File:Medical Care Card USA Sample.JPG` | Public domain | https://commons.wikimedia.org/wiki/File:Medical_Care_Card_USA_Sample.JPG | Edge |
| `online_prescription_laptop.jpg` | `File:An online prescription being issued on a laptop screen.jpg` | CC BY 2.0 | https://commons.wikimedia.org/wiki/File:An_online_prescription_being_issued_on_a_laptop_screen.jpg | Edge |
| `online_prescription_mobile.jpg` | `File:An online prescription being made on a mobile phone.jpg` | CC BY 2.0 | https://commons.wikimedia.org/wiki/File:An_online_prescription_being_made_on_a_mobile_phone.jpg | Edge |
| `handwritten_prescription_1940.jpg` | `File:Håndskrevet resept (1940).jpg` | CC BY-SA 4.0 | https://commons.wikimedia.org/wiki/File:H%C3%A5ndskrevet_resept_(1940).jpg | Abnormal / Edge |
| `handwritten_prescription_1935_thumb.jpg` | `File:Håndskrevet resept (1935).jpg` (thumbnail) | CC BY-SA 4.0 | https://commons.wikimedia.org/wiki/File:H%C3%A5ndskrevet_resept_(1935).jpg | Abnormal / Edge |
| `kassenrezept_at.jpg` | `File:Kassenrezept-AT.jpg` | Public domain | https://commons.wikimedia.org/wiki/File:Kassenrezept-AT.jpg | Edge |
| `privatrezept_blancorezept_thumb.jpg` | `File:Privatrezept Blancorezept blaues rezept.jpg` (thumbnail) | CC BY 4.0 | https://commons.wikimedia.org/wiki/File:Privatrezept_Blancorezept_blaues_rezept.jpg | Edge |
| `illness_history_thumb.jpg` | `File:Illness history.jpg` (thumbnail) | CC BY-SA 2.0 | https://commons.wikimedia.org/wiki/File:Illness_history.jpg | Abnormal / Edge |

## Notes

- `thumb` files were fetched as Wikimedia thumbnail variants because full-resolution downloads were rate-limited.
- These assets should be marked as `真实` only if your operating definition is “public non-mock image from the internet”.
- They should not automatically be treated as exact `diagnosis_proof` positives. Several are better suited as `medical_record`, `Edge`, or `Abnormal` supplementary cases.
- Before adding any of them into `docs/pilot-sick-leave-samples-v1.md`, run OCR / analyze / verify and record the observed `doc_type` and `verify_status` instead of assuming them.

## Fetch attempt that failed due Wikimedia rate limit

- `File:Medical case history of Robert Wilson, patient at Wellcome L0033815.jpg`
