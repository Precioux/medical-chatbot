# NLLB-200 1.3B medical MT safety test (2026-11-25)

50 Chandra-extracted guideline chunks (out/mt_safety/chunks.jsonl). Script: mt_safety_test.py.

## Raw NLLB (no pre/post-processing)
| Check | Khmer | Lao | Vietnamese |
|---|---|---|---|
| Numbers preserved, strict | 126/144 (88%) | 123/144 (85%) | 109/144 (76%) |
| Numbers preserved, locale-aware (0,5 = 0.5) | 131/144 (91%) | 123/144 (85%) | 122/144 (85%) |
| Spurious extra numbers in translation | 14 | 19 | 34 |
| Negation present (chunks with EN negation) | 23/25 (92%) | 23/25 (92%) | 24/25 (96%) |
| Negation count >= EN count | 22/25 (88%) | 23/25 (92%) | 24/25 (96%) |
| Drug names kept in Latin script, exact | 48/58 (83%) | 57/58 (98%) | 57/58 (98%) |
| Drug names Latin exact or close (>=0.8) | 48/58 (83%) | 57/58 (98%) | 58/58 (100%) |
| Drug names, Latin or recovered in back-translation | 58/58 (100%) | 58/58 (100%) | 58/58 (100%) |
| Units preserved | 62/65 (95%) | 65/65 (100%) | 65/65 (100%) |
| Back-translation BLEU | 34.3 | 51.4 | 51.8 |
| Back-translation chrF++ | 56.4 | 68.4 | 69.3 |
| BT: numbers recovered | 123/144 (85%) | 128/144 (89%) | 124/144 (86%) |
| BT: negation recovered | 23/25 (92%) | 23/25 (92%) | 23/25 (92%) |
| BT: units recovered | 63/65 (97%) | 65/65 (100%) | 65/65 (100%) |
| **Chunks with ALL checks passing** | 41/50 (82%) | 40/50 (80%) | 40/50 (80%) |

## Fixed pipeline (en-dash->hyphen, better sentence split, loop retry, source-aware decimal repair)
| Check | Khmer | Lao | Vietnamese |
|---|---|---|---|
| Numbers preserved, strict | 139/144 (97%) | 140/144 (97%) | 122/144 (85%) |
| Numbers preserved, locale-aware (0,5 = 0.5) | 144/144 (100%) | 144/144 (100%) | 144/144 (100%) |
| Spurious extra numbers in translation | 7 | 4 | 22 |
| Negation present (chunks with EN negation) | 23/25 (92%) | 24/25 (96%) | 25/25 (100%) |
| Negation count >= EN count | 22/25 (88%) | 24/25 (96%) | 25/25 (100%) |
| Drug names kept in Latin script, exact | 47/58 (81%) | 57/58 (98%) | 57/58 (98%) |
| Drug names Latin exact or close (>=0.8) | 47/58 (81%) | 57/58 (98%) | 58/58 (100%) |
| Drug names, Latin or recovered in back-translation | 58/58 (100%) | 58/58 (100%) | 58/58 (100%) |
| Units preserved | 60/65 (92%) | 65/65 (100%) | 65/65 (100%) |
| Back-translation BLEU | 39.8 | 50.3 | 52.2 |
| Back-translation chrF++ | 59.3 | 68.7 | 70.2 |
| BT: numbers recovered | 135/144 (94%) | 141/144 (98%) | 137/144 (95%) |
| BT: negation recovered | 23/25 (92%) | 24/25 (96%) | 24/25 (96%) |
| BT: units recovered | 61/65 (94%) | 65/65 (100%) | 65/65 (100%) |
| **Chunks with ALL checks passing** | 45/50 (90%) | 49/50 (98%) | 50/50 (100%) |

## Clinical-term recovery in back-translation (lower bound; BT paraphrase counts as miss)
raw: khm 45/69 (65%), lao 59/69 (86%), vie 51/69 (74%) | fixed: khm 49/69 (71%), lao 60/69 (87%), vie 50/69 (72%)
intubation lost in all 3 languages (2/2); IM route mistranslated in khm/vie.


## Glossary experiment (2026-11-25)

Variants: **fixed** = pre/post-processing only; **glossary** = fixed + placeholder (`TERM1`) substitution of
`data/medical_glossary.json` entries with `use=true` + drug names/abbreviations kept verbatim;
**protect** = fixed + only drug names/abbreviations kept verbatim (adjacent protected tokens masked as one unit).
Script: `glossary_mt.py --translate [--protect-only]`; scored with `mt_safety_test.py --score --variant glossary|protect`.

| Metric | Variant | Khmer | Lao | Vietnamese |
|---|---|---|---|---|
| Numbers (locale-aware) | fixed | 144/144 | 144/144 | 144/144 |
| Numbers (locale-aware) | glossary | 142/144 | 144/144 | 144/144 |
| Numbers (locale-aware) | protect | 142/144 | 144/144 | 144/144 |
| Negation present | fixed | 23/25 | 24/25 | 25/25 |
| Negation present | glossary | 24/25 | 24/25 | 25/25 |
| Negation present | protect | 24/25 | 24/25 | 25/25 |
| Drug names in Latin (exact) | fixed | 47/58 | 57/58 | 57/58 |
| Drug names in Latin (exact) | glossary | 58/58 | 58/58 | 58/58 |
| Drug names in Latin (exact) | protect | 58/58 | 58/58 | 58/58 |
| Units | fixed | 60/65 | 65/65 | 65/65 |
| Units | glossary | 59/65 | 65/65 | 65/65 |
| Units | protect | 59/65 | 65/65 | 65/65 |
| BT clinical terms (lower bound) | fixed | 49/69 | 60/69 | 50/69 |
| BT clinical terms (lower bound) | glossary | 50/69 | 60/69 | 50/69 |
| BT clinical terms (lower bound) | protect | 50/69 | 57/69 | 51/69 |
| Chunks all checks pass | fixed | 45/50 | 49/50 | 50/50 |
| Chunks all checks pass | glossary | 45/50 | 49/50 | 50/50 |
| Chunks all checks pass | protect | 45/50 | 49/50 | 50/50 |
| BT BLEU / chrF++ | fixed | 39.8 / 59.3 | 50.3 / 68.7 | 52.2 / 70.2 |
| BT BLEU / chrF++ | glossary | 41.5 / 60.0 | 52.0 / 69.4 | 52.3 / 70.3 |
| BT BLEU / chrF++ | protect | 41.4 / 60.0 | 50.1 / 68.2 | 53.0 / 70.8 |

Glossary sources actually available: MOH English-Lao glossary (OCR: Tesseract lao+eng primary, Chandra cross-check;
1017 entries, 146 auto-applied, 12 fire on the 50 chunks), Wikidata Vietnamese (48 auto-applied, ~27 fire). No Khmer
source could be downloaded (SIL behind Cloudflare, Sary Hem only on pdfdrive). Nothing is native-speaker reviewed.

Findings: the glossaries do not cover the terms that fail (intubation, infusion, saline, IV/IM, bolus, contraindicated,
wean, neonate), so clinical-term recovery is unchanged. Placeholder substitution split noun phrases and caused new
meaning errors ("alternative to DHP CCBs" -> "CCBs instead of DHP"; vi "pregnancy, bleeding disorders" -> "pregnancy
disorders, bleeding"). The measurable gain (Khmer drug names 81% -> 100%, +1.5 BLEU) comes from the do-not-translate list.
