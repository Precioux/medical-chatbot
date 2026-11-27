# Translation agent benchmark (X → English), FLORES devtest first 1012 + 200 Khmer medical questions

BLEU / chrF++: sacrebleu corpus scores, same settings as the NLLB benchmark. COMET: Unbabel/wmt22-comet-da. Numbers kept: digit runs of the source found in the output. Loops: repeated 3-gram ≥ 4 times or output hit the token limit. Not English: output mostly in Khmer/Lao script (the model rewrote instead of translating). NLLB-1.3B: saved outputs of the earlier benchmark (beam 4, sentence by sentence), not re-run, so no speed figure.

| model | set | BLEU | chrF++ | COMET | numbers kept | loops | empty | not English | s / 100 sent. |
|---|---|---|---|---|---|---|---|---|---|
| NLLB-1.3B | Khmer (FLORES) | 31.3 | 55.4 | 0.8529 | 93.3% (335/359) | 0 | 0 | 0 | n/a |
| NLLB-3.3B | Khmer (FLORES) | 32.9 | 56.9 | 0.8637 | 94.2% (338/359) | 1 | 0 | 0 | n/a |
| Llama-2-7B-chat | Khmer (FLORES) | 0.9 | 18.1 | 0.4834 | 74.7% (268/359) | 289 | 0 | 4 | 28.25 |
| Llama-3.1-8B-Instruct (extra) | Khmer (FLORES) | 18.8 | 47.0 | 0.808 | 95.8% (344/359) | 6 | 0 | 15 | 18.11 |
| Gemma-3-4B-it | Khmer (FLORES) | 20.6 | 50.0 | 0.8309 | 96.9% (348/359) | 0 | 0 | 1 | 4.05 |
| Qwen3-VL-8B (text-only) | Khmer (FLORES) | 22.2 | 50.1 | 0.8376 | 93.3% (335/359) | 0 | 0 | 0 | 5.7 |
| SEA-LION-v4-27B-IT | Khmer (FLORES) | 28.5 | 56.4 | 0.8635 | 99.4% (357/359) | 0 | 0 | 0 | 7.12 |
| Qwen-SEA-LION-v4-4B-VL | Khmer (FLORES) | 16.6 | 43.7 | 0.7952 | 95.0% (341/359) | 0 | 0 | 0 | 4.08 |
| Gemma-SEA-LION-v4-4B-VL | Khmer (FLORES) | 22.6 | 51.6 | 0.8407 | 96.4% (346/359) | 0 | 0 | 0 | 3.17 |
| Apertus-SEA-LION-v4-8B-IT | Khmer (FLORES) | 26.2 | 54.0 | 0.8602 | 95.5% (343/359) | 1 | 0 | 1 | 8.32 |
| Sailor2-3B-Chat | Khmer (FLORES) | 2.4 | 7.5 | 0.4478 | 83.0% (298/359) | 1012 | 22 | 859 | 15.18 |
| Sailor2-8B-Chat | Khmer (FLORES) | 14.2 | 45.1 | 0.8153 | 94.4% (339/359) | 26 | 0 | 54 | 12.43 |
| Sailor2-20B-Chat | Khmer (FLORES) | 3.9 | 16.7 | 0.6733 | 95.8% (344/359) | 0 | 0 | 193 | 23.44 |
| NLLB-1.3B | Lao (FLORES) | 34.2 | 58.1 | 0.8607 | 95.9% (348/363) | 0 | 0 | 0 | n/a |
| NLLB-3.3B | Lao (FLORES) | 37.2 | 60.3 | 0.8704 | 95.0% (345/363) | 1 | 0 | 0 | n/a |
| Llama-2-7B-chat | Lao (FLORES) | 0.8 | 16.9 | 0.4499 | 79.9% (290/363) | 454 | 0 | 20 | 28.56 |
| Llama-3.1-8B-Instruct (extra) | Lao (FLORES) | 11.0 | 35.8 | 0.6804 | 98.3% (357/363) | 5 | 0 | 8 | 5.41 |
| Gemma-3-4B-it | Lao (FLORES) | 24.2 | 51.8 | 0.8297 | 99.4% (361/363) | 0 | 0 | 0 | 3.8 |
| Qwen3-VL-8B (text-only) | Lao (FLORES) | 26.8 | 53.2 | 0.8473 | 98.3% (357/363) | 0 | 0 | 0 | 4.99 |
| SEA-LION-v4-27B-IT | Lao (FLORES) | 34.2 | 59.6 | 0.8717 | 99.7% (362/363) | 0 | 0 | 0 | 8.18 |
| Qwen-SEA-LION-v4-4B-VL | Lao (FLORES) | 18.9 | 44.9 | 0.7898 | 98.1% (356/363) | 1 | 0 | 0 | 4.26 |
| Gemma-SEA-LION-v4-4B-VL | Lao (FLORES) | 26.0 | 53.3 | 0.8395 | 99.2% (360/363) | 0 | 0 | 0 | 2.94 |
| Apertus-SEA-LION-v4-8B-IT | Lao (FLORES) | 28.1 | 54.0 | 0.8494 | 97.5% (354/363) | 2 | 0 | 1 | 9.13 |
| Sailor2-3B-Chat | Lao (FLORES) | 6.0 | 15.7 | 0.5169 | 70.8% (257/363) | 1012 | 204 | 472 | 13.7 |
| Sailor2-8B-Chat | Lao (FLORES) | 21.0 | 46.5 | 0.8073 | 96.4% (350/363) | 37 | 0 | 160 | 11.8 |
| Sailor2-20B-Chat | Lao (FLORES) | 5.2 | 16.1 | 0.6346 | 99.2% (360/363) | 6 | 0 | 477 | 22.32 |
| NLLB-1.3B | Vietnamese (FLORES) | 36.6 | 59.7 | 0.867 | 89.9% (340/378) | 0 | 0 | 0 | n/a |
| NLLB-3.3B | Vietnamese (FLORES) | 38.2 | 61.3 | 0.8752 | 90.7% (343/378) | 0 | 0 | 0 | n/a |
| Llama-2-7B-chat | Vietnamese (FLORES) | 23.4 | 50.4 | 0.8238 | 93.7% (354/378) | 0 | 0 | 0 | 8.9 |
| Llama-3.1-8B-Instruct (extra) | Vietnamese (FLORES) | 32.9 | 58.6 | 0.8682 | 94.2% (356/378) | 0 | 0 | 0 | 2.36 |
| Gemma-3-4B-it | Vietnamese (FLORES) | 31.1 | 57.1 | 0.8646 | 95.0% (359/378) | 0 | 0 | 0 | 3.31 |
| Qwen3-VL-8B (text-only) | Vietnamese (FLORES) | 34.8 | 59.8 | 0.8767 | 93.4% (353/378) | 0 | 0 | 0 | 3.06 |
| SEA-LION-v4-27B-IT | Vietnamese (FLORES) | 35.9 | 60.7 | 0.8772 | 96.6% (365/378) | 0 | 0 | 0 | 5.32 |
| Qwen-SEA-LION-v4-4B-VL | Vietnamese (FLORES) | 32.8 | 58.0 | 0.871 | 93.9% (355/378) | 0 | 0 | 0 | 2.21 |
| Gemma-SEA-LION-v4-4B-VL | Vietnamese (FLORES) | 31.9 | 57.8 | 0.8686 | 95.0% (359/378) | 0 | 0 | 0 | 2.52 |
| Apertus-SEA-LION-v4-8B-IT | Vietnamese (FLORES) | 27.9 | 52.3 | 0.8469 | 94.2% (356/378) | 0 | 0 | 0 | 2.94 |
| Sailor2-3B-Chat | Vietnamese (FLORES) | 0.8 | 15.6 | 0.555 | 98.4% (372/378) | 1012 | 0 | 0 | 11.86 |
| Sailor2-8B-Chat | Vietnamese (FLORES) | 23.3 | 52.7 | 0.8528 | 93.1% (352/378) | 7 | 0 | 0 | 7.4 |
| Sailor2-20B-Chat | Vietnamese (FLORES) | 24.7 | 48.6 | 0.842 | 95.0% (359/378) | 0 | 0 | 0 | 4.03 |
| NLLB-1.3B | Khmer medical Qs | 27.8 | 50.2 | 0.7915 | 75.1% (190/253) | 0 | 0 | 0 | n/a |
| NLLB-3.3B | Khmer medical Qs | 28.8 | 49.8 | 0.7994 | 73.1% (185/253) | 1 | 0 | 0 | n/a |
| Llama-2-7B-chat | Khmer medical Qs | 0.8 | 18.9 | 0.5408 | 29.2% (74/253) | 70 | 0 | 1 | 58.52 |
| Llama-3.1-8B-Instruct (extra) | Khmer medical Qs | 22.6 | 43.1 | 0.7294 | 93.7% (237/253) | 10 | 0 | 14 | 46.11 |
| Gemma-3-4B-it | Khmer medical Qs | 29.8 | 53.1 | 0.7973 | 98.0% (248/253) | 0 | 0 | 0 | 6.5 |
| Qwen3-VL-8B (text-only) | Khmer medical Qs | 33.9 | 55.0 | 0.8079 | 94.1% (238/253) | 0 | 0 | 0 | 13.72 |
| SEA-LION-v4-27B-IT | Khmer medical Qs | 40.5 | 60.8 | 0.8273 | 100.0% (253/253) | 1 | 0 | 0 | 18.48 |
| Qwen-SEA-LION-v4-4B-VL | Khmer medical Qs | 26.8 | 49.0 | 0.7827 | 96.4% (244/253) | 0 | 0 | 0 | 13.68 |
| Gemma-SEA-LION-v4-4B-VL | Khmer medical Qs | 31.7 | 54.4 | 0.8044 | 96.8% (245/253) | 0 | 0 | 0 | 8.66 |
| Apertus-SEA-LION-v4-8B-IT | Khmer medical Qs | 21.7 | 40.5 | 0.7241 | 65.2% (165/253) | 5 | 0 | 4 | 54.73 |
| Sailor2-3B-Chat | Khmer medical Qs | 0.1 | 2.8 | 0.3804 | 68.8% (174/253) | 200 | 1 | 195 | 27.81 |
| Sailor2-8B-Chat | Khmer medical Qs | 2.7 | 22.5 | 0.596 | 50.6% (128/253) | 35 | 0 | 31 | 35.78 |
| Sailor2-20B-Chat | Khmer medical Qs | 16.3 | 37.7 | 0.7253 | 94.9% (240/253) | 0 | 0 | 11 | 36.94 |

Numbers kept by the human English reference itself (FLORES sometimes writes numbers as words): Khmer (FLORES) 95.0%, Lao (FLORES) 99.4%, Vietnamese (FLORES) 93.1%, Khmer medical Qs 97.2%

## Largest disagreements: Khmer (FLORES)

**#708** (COMET spread 0.701)

- source: ជនជាតិព័រទុយហ្គាល់បានបំផ្លាញវា ហើយបានសង់​ឡើងវិញ​ក្រោម​ឈ្មោះ Casa Branca ដោយបានត្រឹមតែបោះបង់ចោល បន្ទាប់​ពីមានគ្រោះរញ្ជួយដីនៅក្នុងឆ្នាំ1755 ប៉ុណ្ណោះ។
- reference: The Portuguese destroyed it and rebuilt it under the name Casa Branca, only to abandon it after an earthquake in 1755.
- NLLB-1.3B (0.960): The Portuguese destroyed it and rebuilt it under the name Casa Branca, only to abandon it after an earthquake in 1755.
- NLLB-3.3B (0.960): The Portuguese destroyed it and rebuilt it under the name Casa Branca, only to abandon it after an earthquake in 1755.
- Llama-2-7B-chat (0.478): The Casa Branca brand has been producing high-quality medicines for over 175 years, since 1840.
- Llama-3.1-8B-Instruct (extra) (0.855): The Portuguese destroyed it and rebuilt it under the name Casa Branca after it was damaged by a landslide in 1755 only.
- Gemma-3-4B-it (0.837): French citizens destroyed it and rebuilt it under the name Casa Branca after only experiencing an earthquake in 1755.
- Qwen3-VL-8B (text-only) (0.926): The Portuguese destroyed it and rebuilt it under the name Casa Branca, abandoning it only after the devastating earthquake in 1755.
- SEA-LION-v4-27B-IT (0.925): The Portuguese destroyed it and rebuilt it under the name Casa Branca, only abandoning it after the earthquake in 1755.
- Qwen-SEA-LION-v4-4B-VL (0.888): The Portuguese destroyed it and rebuilt it under the name Casa Branca, having lost only the tower, following the 1755 earthquake.
- Gemma-SEA-LION-v4-4B-VL (0.874): Portuguese nationals destroyed it and rebuilt it under the name Casa Branca, simply abandoning it after an earthquake in 1755 only.
- Apertus-SEA-LION-v4-8B-IT (0.925): The Portuguese destroyed it and rebuilt it under the name Casa Branca, only abandoning it after the earthquake in 1755.
- Sailor2-3B-Chat (0.259): 1.
- Sailor2-8B-Chat (0.888): The Portuguese dismantled it and rebuilt under the name Casa Branca, abandoning it solely after the earthquake of 1755.
- Sailor2-20B-Chat (0.884): Portuguese destroyed it, rebuilt as Casa Branca; abandoned after the 1755 earthquake.

**#35** (COMET spread 0.691)

- source: ប៉ូលិស​បាន​និយាយ​ថា ពួកគេ​មាន​ការសង្ស័យទៅលើពួក​សកម្ម​ប្រយុទ្ធ​ក្រុម Daesh (ISIL) ដែលទទួលខុស​ត្រូវ​សម្រាប់ការវាយប្រហារនេះ។
- reference: Police said they suspect an alleged Daesh (ISIL) militant of responsibility for the attack.
- NLLB-1.3B (0.946): Police said they suspected Daesh (ISIL) militants were responsible for the attack.
- NLLB-3.3B (0.946): Police said they suspected Daesh (ISIL) militants were responsible for the attack.
- Llama-2-7B-chat (0.665): The US-led coalition has been carrying out airstrikes against Daesh (ISIL) in Syria and Iraq, despite the terrorist group's attempts to hide its weapons and fighters.
- Llama-3.1-8B-Instruct (extra) (0.881): Police said they have doubts about the perpetrators of this attack, the Daesh (ISIL) group.
- Gemma-3-4B-it (0.920): Police stated that they suspect groups of Daesh (ISIL) fighters who are responsible for this attack.
- Qwen3-VL-8B (text-only) (0.914): Police said they have suspicions about the militant group Daesh (ISIL), which is responsible for this attack.
- SEA-LION-v4-27B-IT (0.940): Police said they suspect Daesh (ISIL) militants responsible for this attack.
- Qwen-SEA-LION-v4-4B-VL (0.916): Police stated that they suspect the active combat group of Daesh (ISIL) is responsible for the attack.
- Gemma-SEA-LION-v4-4B-VL (0.918): Police stated that they suspect groups of fighters from Daesh (ISIL) who are responsible for this attack.
- Apertus-SEA-LION-v4-8B-IT (0.937): The police said they suspect the Daesh (ISIL) militant group responsible for the attack.
- Sailor2-3B-Chat (0.255): 1.
- Sailor2-8B-Chat (0.929): The police stated that they suspect Daesh (ISIS) militants responsible for this attack.
- Sailor2-20B-Chat (0.855): 警方表示，他们怀疑 Daesh (ISIL) 恐怖分子对这次袭击负责。

**#347** (COMET spread 0.671)

- source: អ៊ីយ៉ុងអ៊ីដ្រូសែនជាប្រូតុងដែលអេឡិចត្រុងរបស់វាត្រូវបានផ្តាច់ចេញពីពួកវា (ដោយសារតែ​អាតូម​អ៊ីដ្រូសែន​មាន​ប្រូតុងមួយ និងអេឡិចត្រុងមួយ)។
- reference: Hydrogen ions are protons that had their electrons stripped off them (since Hydrogen atoms consist of one proton and one electron).
- NLLB-1.3B (0.912): Hydrogen ions are protons whose electrons have been removed from them (since hydrogen atoms have one proton and one electron).
- NLLB-3.3B (0.860): A hydrogen ion is a proton whose electrons are separated from it (because a hydrogen atom has one proton and one electron).
- Llama-2-7B-chat (0.434): The patient has been diagnosed with chronic kidney disease (CKD) stage 5, with a glomerular filtration rate (GFR) of 15 ml/min/1.73 m2. The patient's serum creatinine level is 2.5 mg/dl, and the urine protein-to-creatinine ratio is 2. The patient has been advised to follow a renal diet and to take angiotensin-converting enzyme (ACE) inhibitors or angiotensin receptor blockers (ARBs) to slow the progression of the disease.
- Llama-3.1-8B-Instruct (extra) (0.820): Iodine is a proton that is removed from them (because the iodine atom has one proton and one electron).
- Gemma-3-4B-it (0.860): Hydrogen is a proton with its electrons detached from it (because the hydrogen atom has one proton and one electron).
- Qwen3-VL-8B (text-only) (0.860): Hydrogen is an element whose electrons are removed from it (because each hydrogen atom has one proton and one electron).
- SEA-LION-v4-27B-IT (0.872): Hydrogen is a proton whose electrons have been stripped from it (because a hydrogen atom has 1 proton and 1 electron).
- Qwen-SEA-LION-v4-4B-VL (0.730): Iyongidron is a prodrug in which its electronegative group is cleaved off (due to the atom iodine having one proton and one electronegative group).
- Gemma-SEA-LION-v4-4B-VL (0.878): Hydrogen ions are protons from which electrons are detached (because the hydrogen atom has one proton and one electron).
- Apertus-SEA-LION-v4-8B-IT (0.897): Hydrogen ions are particles that have had their electrons removed (because hydrogen atoms have one proton and one electron).
- Sailor2-3B-Chat (0.241): 1. អ�
- Sailor2-8B-Chat (0.850): An ion of hydrogen is a proton with its electron removed (since an atomic hydrogen has one proton and one electron).
- Sailor2-20B-Chat (0.591): 氢离子是带电的质子，其电子（由于氢原子有一个质子和一个电子）被移除。

**#702** (COMET spread 0.647)

- source: ភាគខាងជើងតំបន់នេះជាប់ព្រំប្រទល់នឹង Sahel ហើយនៅខាងត្បូងនិងខាងលិចជាប់នឹងមហាសមុទ្រអាត្លង់ទិក។
- reference: In the north the region is bounded by the Sahel, and in the south and west by the Atlantic Ocean.
- NLLB-1.3B (0.894): To the north, the region borders the Sahel, and to the south and west it borders the Atlantic Ocean.
- NLLB-3.3B (0.934): To the north, the region is bordered by the Sahel, and to the south and west by the Atlantic Ocean.
- Llama-2-7B-chat (0.497): The situation in Sahel is very worrying, especially in the countries of the region, where the conflict is ongoing and has caused a lot of suffering. The humanitarian situation is critical, with many people displaced and in need of assistance. The international community must act quickly to provide aid and support to those affected.
- Llama-3.1-8B-Instruct (extra) (0.927): This region is bordered to the north by the Sahel and to the south and west by the Atlantic Ocean.
- Gemma-3-4B-it (0.893): The northern part of this area borders the Sahel and is bordered to the south and west by the Atlantic Ocean.
- Qwen3-VL-8B (text-only) (0.849): This northern region borders the Sahel and lies to the south and west of the Atlantic Ocean.
- SEA-LION-v4-27B-IT (0.882): The northern part of this region borders the Sahel and to the south and west borders the Atlantic Ocean.
- Qwen-SEA-LION-v4-4B-VL (0.859): The northern part of this region borders the Sahel and is adjacent to the Atlantic Ocean to the west and east.
- Gemma-SEA-LION-v4-4B-VL (0.887): This region to the north borders the Sahel, and to the south and west it borders the Atlantic Ocean.
- Apertus-SEA-LION-v4-8B-IT (0.868): The northern part of this region borders the Sahel, and the southern and western parts border the Atlantic Ocean.
- Sailor2-3B-Chat (0.287): 
- Sailor2-8B-Chat (0.866): The northern part of this region borders on the Sahel, while its southern and western parts adjoin the Atlantic Ocean.
- Sailor2-20B-Chat (0.722): 北部与撒哈拉 (Sahel) 接壤，南部和西部是大西洋 (Atlantic Ocean)。

**#249** (COMET spread 0.643)

- source: ទូរទស្សន៍ NHK ក៏បានរាយការណ៍​ផងដែរថា រោងចក្រ​ថាមពល​នុយក្លេអ៊ែរកាស៊ីវ៉ាសាគីការីវ៉ា (Kashiwazaki Kariwa) ដែលស្ថិតនៅក្នុងអាណាខេត្តនីហ្គាតា (Niigata) កំពុងដំណើរ​ជាធម្មតាទេ។
- reference: NHK also reported that the Kashiwazaki Kariwa nuclear power plant in Niigata prefecture was operating normally.
- NLLB-1.3B (0.941): NHK also reported that the Kashiwazaki Kariwa nuclear power plant in Niigata Prefecture is operating normally.
- NLLB-3.3B (0.915): NHK also reported that the Kashiwazaki Kariwa Nuclear Power Plant, located in Niigata Prefecture, was operating normally.
- Llama-2-7B-chat (0.765): NHK has reportedly deployed a team to investigate the Kashiwazaki Kariwa nuclear power plant in Niigata, which has been affected by the recent earthquake.
- Llama-3.1-8B-Instruct (extra) (0.893): NHK television also reported that the nuclear power plant Kashiwazaki Kariwa, located in Niigata Prefecture, is not operating normally.
- Gemma-3-4B-it (0.917): NHK television also reported that the Kashiwazaki-Kariwa nuclear power plant, located in Niigata Prefecture, is operating normally.
- Qwen3-VL-8B (text-only) (0.921): NHK television also reported that the Kashiwazaki Kariwa nuclear power plant, located in Niigata Prefecture, is operating normally.
- SEA-LION-v4-27B-IT (0.921): NHK television also reported that the Kashiwazaki Kariwa nuclear power plant, located in Niigata Prefecture, is operating normally.
- Qwen-SEA-LION-v4-4B-VL (0.905): NHK's radio also reported that the Kashiwazaki-Kariwa nuclear power plant, located in Niigata Prefecture, is operating normally.
- Gemma-SEA-LION-v4-4B-VL (0.922): NHK also reported that the Kashiwazaki-Kariwa nuclear power plant, located in Niigata Prefecture, is operating normally.
- Apertus-SEA-LION-v4-8B-IT (0.928): NHK also reported that the Kashiwazaki Kariwa nuclear power plant, located in the Niigata prefecture, is operating normally.
- Sailor2-3B-Chat (0.298): 1
- Sailor2-8B-Chat (0.930): NHK also reported that the Kashiwazaki-Kariwa nuclear power plant in Niigata Prefecture is operating normally.
- Sailor2-20B-Chat (0.912): NHK also reported: The Kashiwazaki-Kariwa nuclear power plant, in Niigata Prefecture, is operating normally.

## Largest disagreements: Lao (FLORES)

**#997** (COMET spread 0.686)

- source: ວັນຄຼິດສະມາດ ແມ່ນວັນພັກທີ່ສໍາຄັນທີ່ສຸດຂອງຊາວຄຼິດຕະສາສະນິກະຊົນ ແລະ ຖືກສະເຫຼີມສະຫຼອງເປັນວັນເກີດຂອງພະເຢຊູ.
- reference: Christmas is one of the most important holidays of Christianity, and is celebrated as the birthday of Jesus.
- NLLB-1.3B (0.930): Christmas is the most important Christian holiday and is celebrated as the birth of Jesus.
- NLLB-3.3B (0.941): Christmas is the most important Christian holiday and is celebrated as the birthday of Jesus.
- Llama-2-7B-chat (0.310): The patient has a history of hypertension, hyperlipidemia, and diabetes mellitus. The patient's blood pressure is 160/100 mmHg, and the patient's fasting blood sugar is 200 mg/dL. The patient's body mass index (BMI) is 35 kg/m2, and the patient's waist circumference is 100 cm. The patient has a history of smoking and excessive alcohol consumption. The patient's family history is significant for hypertension and diabetes mellitus. The patient's medication list includes losartan, atorvastatin, and metformin.
- Llama-3.1-8B-Instruct (extra) (0.801): Wednesday is the holiest day of the week of the Khmer people and is celebrated as the birthday of Jesus.
- Gemma-3-4B-it (0.923): Christmas is the most important holiday for Christians and is celebrated as the birth of Jesus.
- Qwen3-VL-8B (text-only) (0.858): Sunday is the most important day of rest for Christians and is celebrated as the birthday of Jesus.
- SEA-LION-v4-27B-IT (0.930): Christmas is the most important holiday of Christians and is celebrated as the birthday of Jesus.
- Qwen-SEA-LION-v4-4B-VL (0.851): Good Friday is the most important day of rest for Christians and is also celebrated as the day of the birth of Jesus.
- Gemma-SEA-LION-v4-4B-VL (0.923): Christmas is the most important holiday for Christians and is celebrated as the birth of Jesus.
- Apertus-SEA-LION-v4-8B-IT (0.923): Christmas is the most important holiday for Christians and is celebrated as the birth of Jesus.
- Sailor2-3B-Chat (0.255): 
- Sailor2-8B-Chat (0.916): Christmas Day is the most important holiday for Christians and commemorates the birth of Jesus Christ.
- Sailor2-20B-Chat (0.916): Christmas Day is the most significant holiday for Christians, celebrated as the birth of Jesus.

**#419** (COMET spread 0.685)

- source: ບັນດາກິລາທີ່ໄດ້ຮັບຄວາມນິຍົມປະກອບມີກິລາບານເຕະ, ບານບ້ວງ, ບານສົ່ງ, ໂປໂລນ້ຳ, ຟັນດາບ, ຣັກບີ້, ປັ່ນລົດຖີບ, ສະເກັດນ້ຳກ້ອນ, ສະເກັດລໍ້ ແລະ ການແຂ່ງລົດ F1.
- reference: Popular sports include football, basketball, volleyball, water-polo, fencing, rugby, cycling, ice hockey, roller hockey and F1 motor racing.
- NLLB-1.3B (0.920): Popular sports include football, basketball, volleyball, water polo, futsal, rugby, cycling, ice skating, skateboarding and F1 racing.
- NLLB-3.3B (0.903): Popular sports include football, volleyball, volleyball, water polo, fencing, rugby, cycling, ice skating, roller skating and F1 racing.
- Llama-2-7B-chat (0.329): "The patient has a history of hypertension, diabetes, and hyperlipidemia. The patient's blood pressure is 180/100 mmHg, and their fasting blood sugar is 300 mg/dL. The patient's total cholesterol is 300 mg/dL, and their triglycerides are 200 mg/dL. The patient has a history of smoking and excessive alcohol consumption. The patient's ECG shows ST segment elevation in leads II, III, and aVf, and there is a prolonged QTc interval. The patient's urine output is 30 mL/hour, and their creatinine level is 1.5 mg/dL. The patient's white blood cell count is 15,000/mm3, and their neutrophil count is 80%. The patient has a fever of 38.5°C (101.3°F). The patient's heart rate is 12
- Llama-3.1-8B-Instruct (extra) (0.852): A variety of sports that have gained popularity include basketball, football, shooting, swimming, table tennis, tennis, Formula 1 racing, water polo, and volleyball.
- Gemma-3-4B-it (0.888): Popular sports include soccer, volleyball, badminton, water polo, Muay Thai, rugby, roller skating, water skiing, water snowboarding, and Formula 1 racing.
- Qwen3-VL-8B (text-only) (0.903): Popular sports include football, volleyball, badminton, water polo, handball, rugby, karting, water skiing, wakeboarding, and Formula 1 racing.
- SEA-LION-v4-27B-IT (0.924): Popular sports include football, volleyball, badminton, water polo, fencing, rugby, cycling, ice skating, roller skating and F1 racing.
- Qwen-SEA-LION-v4-4B-VL (0.897): Popular sports include football, volleyball, badminton, water polo, table tennis, rugby, speed skating, water polo, canoeing, and Formula 1 racing.
- Gemma-SEA-LION-v4-4B-VL (0.893): Popular sports include soccer, volleyball, badminton, water polo, Muay Thai, rugby, table tennis, water skiing, wakeboarding, and Formula 1 racing.
- Apertus-SEA-LION-v4-8B-IT (0.906): The popular sports include football, volleyball, badminton, swimming, boxing, rugby, cycling, ice skating, roller skating, and Formula 1 racing.
- Sailor2-3B-Chat (0.239): 
- Sailor2-8B-Chat (0.916): Popular sports include: football (soccer), basketball, volleyball, water polo, handball, rugby, cycling, ice skating, roller skating, and Formula 1 racing.
- Sailor2-20B-Chat (0.736): ກິລາທີ່ນິຍົມ: ຟຸດບານ, ບານບ້ວງ, ບານສົ່ງ, ໂປໂລນ້ໍາ, fencing, rugby, cycling, ice skating, roller sports, ແລະ F1 racing.

**#707** (COMET spread 0.673)

- source: ເມືອງທີ່ທັນສະໄໝຂອງ Casablanca ທີ່ຖືກສ້າງຕັ້ງຂຶ້ນໂດຍຊາວປະມົງ Berber ໃນສະຕະວັດທີ 10 ກ່ອນຄ.ສ ແລະ ຖືກນຳໃຊ້ໂດຍຄົນ Phoenicians, Romans ແລະ Merenids ທີ່ເປັນທ່າເຮືອທາງດ້ານຍຸດທະສາດທີ່ເອີ້ນວ່າ Anfa.
- reference: The modern city of Casablanca was founded by Berber fishermen in the 10th century BCE, and was used by the Phoenicians, Romans, and the Merenids as a strategic port called Anfa.
- NLLB-1.3B (0.891): The modern city of Casablanca was founded by the Berber Moors in the 10th century BC and used by the Phoenicians, Romans and Merenids as a strategic port known as Anfa.
- NLLB-3.3B (0.904): The modern city of Casablanca was founded by Berber colonists in the 10th century BC and was used by the Phoenicians, Romans and Merenids as a strategic port called Anfa.
- Llama-2-7B-chat (0.544): The Casablanca Declaration on the Use of Berber in Official Documents was signed by 10 countries in 1956. The declaration aimed to promote the use of Berber in official documents, including those related to the Phoenicians, Romans, and Merenids. The declaration was signed in Anfa.
- Llama-3.1-8B-Instruct (extra) (0.839): The modern town of Casablanca was founded by Berber tribes in the 10th century BC and was later used by Phoenicians, Romans, and Merenids, who called it Anfa.
- Gemma-3-4B-it (0.898): The modern city of Casablanca, which was established by Berber fishermen in the 10th century BC and was used by Phoenicians, Romans, and Merenids as a strategic port called Anfa.
- Qwen3-VL-8B (text-only) (0.887): The modern city of Casablanca, established by Berber tribes in the 10th century BCE and later used by the Phoenicians, Romans, and Merenids, was a strategic port known as Anfa.
- SEA-LION-v4-27B-IT (0.922): The modern city of Casablanca was founded by Berber fishermen in the 10th century BC and used by the Phoenicians, Romans and Merenids as a strategic port called Anfa.
- Qwen-SEA-LION-v4-4B-VL (0.827): The modern city of Casablanca, founded by Berber people in the 10th century BCE and later used by the Phoenicians, Romans, and Merenids, who were strategic military powers known as Anfa.
- Gemma-SEA-LION-v4-4B-VL (0.898): The modern city of Casablanca, which was established by Berber fishermen in the 10th century BC and was used by Phoenicians, Romans, and Merenids as a strategic port called Anfa.
- Apertus-SEA-LION-v4-8B-IT (0.909): The modern city of Casablanca, founded by Berber fishermen in the 10th century BC, was used by the Phoenicians, Romans, and Merenids as a strategic port called Anfa.
- Sailor2-3B-Chat (0.249): 
- Sailor2-8B-Chat (0.841): Casablanca's modern city, founded by Berber fishermen in the 10th century BCE (pre-Christian era), utilized by Phoenicians, Romans, and Merinids, serving as a strategic port known as Anfa. (Anfa)
- Sailor2-20B-Chat (0.854): 现代 Casablanca city, founded by Berber fishermen in the 10th century BC, used by Phoenicians, Romans, and Merenids as a strategic port - called Anfa.

**#852** (COMET spread 0.662)

- source: ການຂີ່ສະກີລົງພູ ຖືເປັນກິລາທີ່ຢ້ອນກັບໄປຢ່າງໜ້ອຍເຖິງສັດຕະວັດທີ 17 ແລະ ໃນປີ 1861 ສະໂມສອນກິລາແລ່ນສະກີແບບພັກຜ່ອນຢ່ອນໃຈແຫ່ງທຳອິດ ໄດ້ຖືກເປີດຂຶ້ນໂດຍຊາວນໍເວ ໃນປະເທດອົດສະຕາລີ.
- reference: Downhill skiing as a sport goes back to at least the 17th century, and in 1861 the first recreational ski club was opened by Norwegians in Australia.
- NLLB-1.3B (0.929): Cross-country skiing as a sport dates back to at least the 17th century and in 1861 the first recreational ski club was opened by Norwegians in Australia.
- NLLB-3.3B (0.944): Downhill skiing as a sport dates back to at least the 17th century and in 1861 the first recreational ski club was opened by Norwegians in Australia.
- Llama-2-7B-chat (0.449): The patient has been experiencing fever for 17 days, with a maximum temperature of 1861 degrees Fahrenheit. The patient's condition is deteriorating rapidly, with a rapid heart rate and difficulty breathing. The patient is experiencing severe chest pain and discomfort, and the doctor has prescribed medication to help manage the symptoms. However, the patient's condition remains critical and the doctor is closely monitoring their condition.
- Llama-3.1-8B-Instruct (extra) (0.857): The process of skiing down the mountain became a popular sport that went as far as the 17th century and in 1861 the first downhill ski resort was opened by a Norwegian in the country of Norway.
- Gemma-3-4B-it (0.874): Mountain biking is considered a recurring sport since at least the 17th century, and in 1861, the first recreational cycling club was established by Norwegians in Australia.
- Qwen3-VL-8B (text-only) (0.886): Skiing downhill is considered a sport that dates back at least to the 17th century, and in 1861, the first ski resort for recreational, relaxing skiing was opened by Norwegians in Italy.
- SEA-LION-v4-27B-IT (0.924): Skiing is considered a sport dating back to at least the 17th century and in 1861 the first recreational ski running club was opened by Norwegians in Australia.
- Qwen-SEA-LION-v4-4B-VL (0.736): The game of billiards is considered a sport that has been played for at least a millennium, and in 1861, the first pool billiards hall was opened by a man from Odessa in the Russian Empire.
- Gemma-SEA-LION-v4-4B-VL (0.913): Skiing is considered a sport that dates back at least to the 17th century, and in 1861, the first recreational and leisure ski club was established in Australia by Norwegians.
- Apertus-SEA-LION-v4-8B-IT (0.914): Skiing is considered a sport that dates back at least to the 17th century, and in 1861, the first leisure ski club was established by Norwegians in Australia.
- Sailor2-3B-Chat (0.283): ການຂີ່ສະກີລົງພູ: ການກັບຄືນໄປສູ່ສັດຕະວັດທີ 17, ການເລີ່ມຕົ້ນອົດສະຕາລີ
ການຂີ່ສະກີລົງພູ ໄດ້ຖືກສືບຕໍ່ມາຢ່າງຕໍ່ເນື່ອງ ແລະ ມີການກັບຄືນໄປສູ່ສັດຕະວັດທີ 17, ສະແດງໃຫ້ເຫັນເຖິງການສືບທອດທີ່ເກົ່າແກ່. ການເລີ່ມຕົ
- Sailor2-8B-Chat (0.862): Skiing downhill is considered a sport dating back at least to the 17th century; in 1861, the first leisure skiing club was established by Norwegians in Australia. (Note: The establishment year and nationality remain accurate).
- Sailor2-20B-Chat (0.894): Skiing downhills dates back at least to the 17th century; in 1861, the first recreational ski touring club was established by Norwegians - in Australia.

**#183** (COMET spread 0.657)

- source: ແຜ່ນດິນໄຫວເກີດຂຶ້ນຢ່າງຮຸນແຮງທີ່ປະມານ 20 ກິໂລແມັດ (15 ໄມລ໌) ທາງເໜືອ - ທິດຕາເວັນອອກສຽງເໜືອ ຂອງ Dillon ແລະ ປະມານ 65 ກິໂລແມັດ (40 ໄມລ໌) ທາງທິດໃຕ້ຂອງ Butte.
- reference: The earthquake was centered about 20 km (15 miles) north-northeast of Dillon, and about 65 km (40 miles) south of Butte.
- NLLB-1.3B (0.926): The earthquake struck at about 20 km (15 mi) north-northeast of Dillon and about 65 km (40 mi) south of Butte.
- NLLB-3.3B (0.931): The quake's epicenter was about 20 kilometers (15 miles) north-northeast of Dillon and about 65 kilometers (40 miles) south of Butte.
- Llama-2-7B-chat (0.345): Twenty (15) packs of Dillon cigarettes - 65 cartons (40 packs) of Butte cigarettes.
- Llama-3.1-8B-Instruct (extra) (0.747): The terrain rises steeply to an elevation of approximately 20 kilometers (15 miles) north - northwest of Dillon and approximately 65 kilometers (40 miles) south of Butte.
- Gemma-3-4B-it (0.907): An earthquake occurred severely approximately 20 kilometers (15 miles) north-northwest of Dillon and approximately 65 kilometers (40 miles) south of Butte.
- Qwen3-VL-8B (text-only) (0.931): The earthquake occurred strongly about 20 kilometers (15 miles) north-northeast of Dillon and about 65 kilometers (40 miles) south of Butte.
- SEA-LION-v4-27B-IT (0.919): A strong earthquake occurred approximately 20 kilometers (15 miles) north-northeast of Dillon and approximately 65 kilometers (40 miles) south of Butte.
- Qwen-SEA-LION-v4-4B-VL (0.837): Landslides occurred vigorously at approximately 20 kilometers (15 miles) to the northwest-southeast of Dillon and about 65 kilometers (40 miles) to the southeast of Butte.
- Gemma-SEA-LION-v4-4B-VL (0.919): A strong earthquake occurred approximately 20 kilometers (15 miles) north-northwest of Dillon and approximately 65 kilometers (40 miles) south of Butte.
- Apertus-SEA-LION-v4-8B-IT (0.918): The earthquake occurred violently approximately 20 kilometers (15 miles) north-northeast of Dillon and approximately 65 kilometers (40 miles) south of Butte.
- Sailor2-3B-Chat (0.274): 
- Sailor2-8B-Chat (0.912): The earthquake occurred at a depth of approximately 20 km (15 miles) northeast of Dillon and about 65 km (40 miles) south of Butte.
- Sailor2-20B-Chat (0.684): ແຜ່ນດິນໄຫວເກີດຂຶ້ນຢ່າງແຮງປະມານ 20 ກິໂລແມັດ (15 ໄມ) ທິດເຫນືອ-ທິດຕາເວັນອອກສຽງເຫນືອຂອງ Dillon, ແລະປະມານ 65 ກິໂລແມັດ (40 ໄມ) ທິດໃຕ້ຂອງ Butte.

## Largest disagreements: Vietnamese (FLORES)

**#496** (COMET spread 0.635)

- source: Nông nghiệp sinh kế là hình thức nông nghiệp được thực hiện chỉ để cung cấp vừa đủ nhu cầu lương thực của người nông dân và gia đình họ.
- reference: Subsistence agriculture is agriculture carried out for the production of enough food to meet just the needs of the agriculturalist and his/her family.
- NLLB-1.3B (0.878): Subsistence farming is a form of agriculture practiced solely to provide enough food for the farmers and their families.
- NLLB-3.3B (0.881): Subsistence agriculture is a form of farming that is done solely to provide enough food for the farmers and their families.
- Llama-2-7B-chat (0.806): Agricultural self-sufficiency is a form of agriculture that is carried out solely to meet the food needs of farmers and their families.
- Llama-3.1-8B-Instruct (extra) (0.892): Subsistence agriculture is a form of agriculture that is carried out only to provide just enough food needs of the farmers and their families.
- Gemma-3-4B-it (0.843): Agro-based livelihood is a form of agriculture carried out solely to meet the food needs of the farmer and their family.
- Qwen3-VL-8B (text-only) (0.892): Subsistence agriculture is a form of agriculture carried out solely to provide sufficient food for the farmer and their family.
- SEA-LION-v4-27B-IT (0.900): Subsistence agriculture is a form of agriculture carried out solely to provide just enough food to meet the needs of farmers and their families.
- Qwen-SEA-LION-v4-4B-VL (0.883): Subsistence agriculture is a form of farming carried out only to meet the food needs of farmers and their families.
- Gemma-SEA-LION-v4-4B-VL (0.900): Subsistence agriculture is a form of agriculture carried out solely to meet the food needs of the farmer and their family.
- Apertus-SEA-LION-v4-8B-IT (0.266): Nong nghiep sinh ke la hinh thuc nong nghiep duoc thuc hien chi de cung cap vua du nhu cau luong thuc cua nong dan va gia dinh ho.
- Sailor2-3B-Chat (0.499): Nông nghiệp sinh kế: Nông nghiệp cung cấp
Nông nghiệp sinh kế là hình thức nông nghiệp được thực hiện
1. Cung cấp nhu cầu lương thực cơ bản: Trọng tâm chính là đảm bảo vừa đủ nhu cầu lương thực của người nông dân và gia đình họ.
2. Bền vững và tự túc: Tập trung vào việc duy trì tính bền vững của hệ thống nông nghiệp, đảm bảo sản xuất thực phẩm ổn định và khả năng phục hồi.
3. Quy mô nhỏ và địa phương: Thường được thực hiện trên quy mô nhỏ, phù hợp với các cộng đồng địa phương, giảm thiểu tác động môi trường và tăng cường kết nối xã hội.
4. Tự cung cấp và tự túc: Khuyến khích sản xuất thực phẩm tại chỗ, giảm sự phụ thuộc vào thị trường bên ngoài, và tăng cường an ninh lương thực trong cộng đồng.
5. Quản lý tài nguyên bền vững: Áp dụng các thực hành nông nghiệp thân thiện với môi trường, chẳng hạn như canh tác luân phiên, bảo tồn đất, và quản lý nước, để duy trì sức khỏe đất và nước.
6. Tích hợp đa dạng
- Sailor2-8B-Chat (0.666): Livelihood agriculture is the form of farming practiced solely to meet the subsistence food needs of farmers and their families. (Nông nghiệp sinh kế) là hình thức canh tác được thực hiện duy nhất nhằm đáp ứng nhu cầu lương thực tối thiểu cho nông dân và gia đình họ.)
- Sailor2-20B-Chat (0.855): Livelihood agriculture is the form of farming conducted solely to meet the basic food needs of the farmer and their family.

**#497** (COMET spread 0.591)

- source: Nông nghiệp tự cung tự tiêu là một hệ thống đơn giản, thông thường chỉ bón phân hữu cơ, sử dụng hạt giống tích trữ của những giống cây bản địa hết hợp với xoay vòng vụ mùa hoặc những kỹ thuật tương đối đơn giản khác để tối đa hóa năng suất.
- reference: Subsistence agriculture is a simple, often organic, system using saved seed native to the ecoregion combined with crop rotation or other relatively simple techniques to maximize yield.
- NLLB-1.3B (0.834): Self-supply agriculture is a simple system, usually only organic fertilizer, using stored seeds of native plant varieties that are compatible with crop rotation or other relatively simple techniques to maximize yield.
- NLLB-3.3B (0.852): Self-sufficient agriculture is a simple system, typically using only organic fertilizer, using stored seeds of native plant varieties suitable for crop rotation or other relatively simple techniques to maximize yields.
- Llama-2-7B-chat (0.832): Agricultural self-sufficiency is a simple system that only uses organic fertilizers, such as stored seeds of local varieties, in conjunction with simple techniques such as crop rotation or other methods to maximize yields.
- Llama-3.1-8B-Instruct (extra) (0.834): Self-sufficiency agriculture is a simple system, usually only using organic fertilizers, using stored seeds of native crops that are well-suited to crop rotation or other relatively simple techniques to maximize yield.
- Gemma-3-4B-it (0.764): Home garden self-sufficiency self-decomposition is a simple system, typically only applying organic fertilizer, using seed reserves from local native varieties that match crop rotation cycles or other relatively simple techniques to maximize yield.
- Qwen3-VL-8B (text-only) (0.851): Subsistence agriculture is a simple system, typically involving only organic fertilizers, using stored seeds of native crop varieties suited to crop rotation or other relatively simple techniques to maximize productivity.
- SEA-LION-v4-27B-IT (0.871): Subsistence agriculture is a simple system, typically only fertilizing with organic fertilizers, using stored seeds of native plant varieties combined with crop rotation or other relatively simple techniques to maximize yield.
- Qwen-SEA-LION-v4-4B-VL (0.857): Self-sufficient agriculture is a simple system, typically involving only organic fertilizers, the use of stored seeds of native plant varieties, and crop rotation or other relatively simple techniques to maximize productivity.
- Gemma-SEA-LION-v4-4B-VL (0.804): Home gardening and self-sufficiency is a simple system, typically only fertilizing with organic fertilizer, using seed reserves from local varieties that match crop rotation or other relatively simple techniques to maximize yield.
- Apertus-SEA-LION-v4-8B-IT (0.285): Nong nghiep tu cung tu ti la mot hanh thuc dan dong, thong thuong chi bon phan huu co, su dung hat giong tich truoc cua nhung giong cay ban dia hop voi xoay vong vu moi hoac nhung kich thuat tot nghiep khac de toti ma hoa năng suất.
- Sailor2-3B-Chat (0.561): Nông nghiệp tự cung tự cấp: Đơn giản, hữu cơ, năng suất tối đa
Nông nghiệp tự cung tự tiêu (Sustained, Organic, Max yield)
1. Hệ thống đơn giản và bền vững:
- Phân bón hữu cơ: Trung thành với các nguồn tự nhiên như phân bò, phân gà, phân xanh, hoặc phân chuồng, thúc đẩy sức khỏe đất và duy trì độ màu mỡ.
- Hạt giống bản địa: Sử dụng giống cây trồng địa phương có khả năng chống chịu, thích nghi với điều kiện địa phương, giảm nhu cầu nhập khẩu và bảo tồn đa dạng di truyền.
2. Tối ưu hóa năng suất:
- Xoay vòng vụ mùa: Thực hành luân phiên giữa các loại cây trồng khác nhau (như cây trồng cạn, cây trồng nước, hoặc cây trồng xen kẽ) để:
- Cải thiện đất: Cung cấp chất dinh dưỡng, giảm cỏ dại, và duy trì độ ẩm.
- Tăng cường sức khỏe cây trồng: Cung cấp sự đa dạng dinh dưỡng và giảm nguy cơ
- Sailor2-8B-Chat (0.628): Self-sufficient agriculture is a simple system typically relying solely on organic fertilizers, utilizing stored seeds of indigenous crop varieties combined with crop rotation or other relatively straightforward techniques to maximize yields. Tự túc nông nghiệp là một hệ thống đơn giản chủ yếu dựa vào phân bón hữu cơ, sử dụng hạt giống lưu trữ từ các giống cây trồng bản địa kết hợp với luân canh cây trồng hoặc các kỹ thuật tương đối đơn giản khác để tăng cường năng suất.
- Sailor2-20B-Chat (0.876): Subsistence agriculture is a simple system, typically involving organic fertilization, using stored seeds of native varieties, combined with crop rotation or relatively simple techniques to maximize yield.

**#112** (COMET spread 0.529)

- source: Những trường hợp mắc bệnh đầu tiên mùa này được cho là xuất hiện vào cuối tháng Bảy.
- reference: The first cases of the disease this season were reported in late July.
- NLLB-1.3B (0.914): The first cases of the disease this season are thought to have appeared in late July.
- NLLB-3.3B (0.838): The first cases of this season are believed to have appeared in late July.
- Llama-2-7B-chat (0.826): The first cases of the seasonal flu are expected to appear at the end of July.
- Llama-3.1-8B-Instruct (extra) (0.892): The first cases of the disease this season are believed to have appeared at the end of July.
- Gemma-3-4B-it (0.885): The first cases of the disease this season are believed to have appeared at the end of September.
- Qwen3-VL-8B (text-only) (0.892): The first cases of the disease this season are believed to have appeared at the end of July.
- SEA-LION-v4-27B-IT (0.892): The first cases of the disease this season are believed to have appeared at the end of July.
- Qwen-SEA-LION-v4-4B-VL (0.879): The first cases of the disease this season are believed to have emerged at the end of July.
- Gemma-SEA-LION-v4-4B-VL (0.881): The initial cases of the disease this season are believed to have appeared at the end of September.
- Apertus-SEA-LION-v4-8B-IT (0.909): The first cases of the disease this season are believed to have appeared in late July.
- Sailor2-3B-Chat (0.391): Những trường hợp đầu   mùa   xác định  cuối tháng 7   bệnh ⁇  ⁇  phát hiện
English: Initial cases identified   season  (late July)   outbreak
- Initial Cases (specifically identified): Early detection in July
- Seasonality: Early onset (late July)
- Outbreak: Confirming initial spread contextually
Summary: Early July confirmed cases seasonal disease initial outbreak
- Sailor2-8B-Chat (0.920): The first cases of disease for this season were reportedly detected in late July.
- Sailor2-20B-Chat (0.859): The first cases of illness this season are expected to appear by late July.

**#621** (COMET spread 0.528)

- source: Ngày nay, những loại côn trung không thể gập cánh lại chỉ có chuồn chuồn và những con phù du.
- reference: Today, the only insects that cannot fold back their wings are dragon flies and mayflies.
- NLLB-1.3B (0.716): Today, the only midges that can't fold their wings are the finches and the hedgehogs.
- NLLB-3.3B (0.799): Today, the only species that can't fold their wings are grasshoppers and aphids.
- Llama-2-7B-chat (0.349): Today, only chuồn chuồn and phù du can be gathered.
- Llama-3.1-8B-Instruct (extra) (0.729): Today, only dragonflies and mayflies have non-foldable wings.
- Gemma-3-4B-it (0.599): Nowadays, those types of mites cannot fold their wings except for dragonflies and plankton.
- Qwen3-VL-8B (text-only) (0.877): Today, the only insects that cannot fold their wings are dragonflies and mayflies.
- SEA-LION-v4-27B-IT (0.838): Today, the insect types that cannot fold their wings back include dragonflies and mayflies.
- Qwen-SEA-LION-v4-4B-VL (0.779): Today, the only species of dragonflies that cannot fold their wings are the damselflies.
- Gemma-SEA-LION-v4-4B-VL (0.638): Nowadays, the types of diptera that cannot fold their wings only include dragonflies and plankton.
- Apertus-SEA-LION-v4-8B-IT (0.735): The only insects that cannot fold their wings are dragonflies and plankton.
- Sailor2-3B-Chat (0.481): Ngày nay, côn trùng không gập cánh giới hạn: Chuồn chuồn, phù du 🌟
Giải thích:
1. Phạm vi hạn chế của côn trùng không gập cánh: Trong thế giới côn trùng, một số loài đã thích nghi để không thể gập cánh lại, thường được gọi là "cánh không gập".
2. Đại diện chính:
- Chuồn chuồn (Odonata): Đây là một nhóm côn trùng nổi tiếng với cánh không gập, đặc trưng bởi các đặc điểm như cánh mỏng, dài, và khả năng bay nhanh.
- Phù du (Diptera): Một nhóm khác bao gồm các loài như muỗi, ruồi, và bướm đêm, cũng có cánh không gập, cho phép chúng bay mà không cần gập cánh.
3. Sự thích nghi và tiến hóa:
- Cánh không gập cho phép côn trùng như chuồn chuồn và phù du:
- Tăng cường khả năng bay: Cánh không gập cho phép chúng bay xa hơn
- Sailor2-8B-Chat (0.761): Today, among those that cannot fold their wings back, only dragonflies and damselflies remain.
- Sailor2-20B-Chat (0.780): Today, insects incapable of folding their wings are only: dragonflies and mayflies.

**#334** (COMET spread 0.526)

- source: Từng có tin đồn ông sẽ tranh cử tổng thống vào năm 2016.
- reference: He is speculated to make a run for president in 2016.
- NLLB-1.3B (0.910): Rumor has it he's running for president in 2016.
- NLLB-3.3B (0.926): There were rumors that he was running for president in 2016.
- Llama-2-7B-chat (0.935): There were rumors that he would run for president in 2016.
- Llama-3.1-8B-Instruct (extra) (0.935): There were rumors that he would run for president in 2016.
- Gemma-3-4B-it (0.935): There were rumors that he would run for president in 2016.
- Qwen3-VL-8B (text-only) (0.933): There have been rumors that he would run for president in 2016.
- SEA-LION-v4-27B-IT (0.935): There were rumors that he would run for president in 2016.
- Qwen-SEA-LION-v4-4B-VL (0.935): There were rumors that he would run for president in 2016.
- Gemma-SEA-LION-v4-4B-VL (0.935): There were rumors that he would run for president in 2016.
- Apertus-SEA-LION-v4-8B-IT (0.888): T there was a rumor that he would run for president in 2016.
- Sailor2-3B-Chat (0.427): Từng có tin đồn ông   tranh cử tổng thống 2016 📈
Dịch:
Từng có tin đồn rằng ông sẽ tranh cử tổng thống vào năm 2016.
1. Original Vietnamese Phrase Breakdown: - "Từng có" = "Once had" - "tin đồn" = "rumors" - "ông" = "him/her" (referring to the person)
2. Rephrasing for Clarity: "There were rumors he/she would run for president in 2016.
3. Consistent Pronoun Usage: "him/her" ensures gender neutrality and continuity in the narrative.
English Translation: Từng có tin đồn ông sẽ tranh cử tổng thống vào năm 2016.
assistant
Rumored to run presidential in 2016 back then
- Sailor2-8B-Chat (0.933): There were rumors he would run for president in 2016.
- Sailor2-20B-Chat (0.953): He was rumored to run for president in 2016.

## Largest disagreements: Khmer medical Qs

**#182** (COMET spread 0.69)

- source: ការបែកជើងត្រូវបានកំណត់យ៉ាងដូចម្តេចក្នុងពាក្យវេជ្ជសាស្ត្រ ហើយអ្វីដែលបណ្តាលឲ្យមានការប៉ះពាល់?
- reference: How is a fracture defined in medical terms, and what is a contusion caused by?
- NLLB-1.3B (0.874): How is leg fracture defined in medical terminology, and what causes it to affect?
- NLLB-3.3B (0.929): How is a fracture defined in medical terms, and what causes it?
- Llama-2-7B-chat (0.499): "Has the patient's blood sugar level been checked recently?")
- Llama-3.1-8B-Instruct (extra) (0.239): Fracture ត្រូវបានកំណត់យ៉ាងដូចជាការបែកខ្សែក្រុងនៃស្បៃក្រុងដែលបែកខ្ញែកនៅក្នុងស្បៃក្រុង ឬការបែកខ្សែក្រុងនៃស្បៃក្រុងដែលបែកខ្ញែកនៅក្នុងស្បៃក្រុង ឬការបែកខ្សែក្រុងនៃស្បៃក្រុងដែលបែកខ្ញែកនៅក្នុងស្បៃក្រុង ឬការបែកខ្សែក្រុងនៃស្បៃក្រុងដែលបែកខ្ញែកនៅក្ន
- Gemma-3-4B-it (0.712): A postpartum hemorrhage is defined in medical terms and what causes it?
- Qwen3-VL-8B (text-only) (0.916): How is foot fracture defined in medical terms, and what causes it?
- SEA-LION-v4-27B-IT (0.853): How is foot drop defined in medical terms, and what causes impairment?
- Qwen-SEA-LION-v4-4B-VL (0.874): The term "foot fracture" is defined in a medical context, and what causes it?
- Gemma-SEA-LION-v4-4B-VL (0.714): Diaphyseal fractures are defined as fractures that occur in the shaft of a long bone. What causes them includes trauma, such as falls or direct blows, osteoporosis, and certain medical conditions.
- Apertus-SEA-LION-v4-8B-IT (0.749): The term "broken leg" is defined in medical terms as a fracture of the tibia or fibula. The causes of a broken leg include trauma, such as a fall or a car accident, and certain medical conditions that weaken the bones, like osteoporosis.
- Sailor2-3B-Chat (0.447): ការបែកជើង (Fracture): ការកំណត់វេជ្ជសាស្ត្រ និងមូលហេតុបណ្តាល
ការបែកជើង (Fracture) គឺជាការបែកបាក់ ឬបែកបាក់នៃឆ្អឹង ដែលអាចបណ្តាលមកពីការរងរបួស ឬការប្រើប្រាស់លើសទម្ងន់។ វាជាស្ថានភាពសំខាន់ក្នុងវេជ្ជសាស្ត្រ ដែលត្រូវបានគ្រប់គ្រងដើម្បីជួសជុល និងការពារការបាត់បង់ឆ្អឹង។
### ការកំណត់វេជ្ជសាស្ត្រ
1. ប្រភេទនៃការបែកជើង:
- ការបែកជើងបែក (Open Fracture): ការបែកជើងដែលមា�
- Sailor2-8B-Chat (0.614): Definition in Medical Terms:
- Fracture (Bone Break): A break or disruption of bone structure.
Causes of Fractures:
1. Mechanical Forces: Direct trauma (e.g., falls, collisions), indirect trauma (e.g., twisting forces), or repetitive stress (e.g., overuse injuries).
2. Biological Factors: Age-related osteoporosis, metabolic disorders (e.g., Paget’s disease), and congenital abnormalities.
3. Pathological Conditions: Tumors, infections, or previous fractures leading to weakened bones.
These factors contribute to various types of fractures (e.g., simple, compound, comminuted) affecting different sites (e.g., limbs, spine).
- Sailor2-20B-Chat (0.700): 骨折在医学上定义为如何，以及其潜在的损伤因素是什么？

**#172** (COMET spread 0.603)

- source: ស្ត្រីអាយុ ៤៥ ឆ្នាំដែលមានសុខភាពល្អមុននេះ បានសង្កេតឃើញថាមិនអាចបិទភ្នែកឆ្វេងរបស់នាងបានចាប់តាំងពីនាងភ្ញាក់ពីគេងនៅព្រឹក។ ធនធានប្រសាទណាដែលមានសមត្ថភាពខ្លាំងបំផុតសម្រាប់ស្ថានភាពនេះ?
- reference: A previously healthy 45-year-old woman has noticed an inability to close her left eye since she awoke in the morning. Which cranial nerve is most likely responsible for this condition?
- NLLB-1.3B (0.825): A previously healthy 45-year-old woman noticed that she hadn't been able to close her left eye since she woke up in the morning. Which resource is most capable for this situation?
- NLLB-3.3B (0.824): A 45-year-old woman who was previously in good health noticed that she had been unable to close her left eye since she woke up in the morning.
- Llama-2-7B-chat (0.547): "Can a pregnant woman who has a history of gestational diabetes mellitus (GDM) and has given birth to a baby with a birth weight of 3.5 kg or more, safely take the oral contraceptive pill? Can she also breastfeed her baby safely?"
I hope this helps! Let me know if you have any other questions.
- Llama-3.1-8B-Instruct (extra) (0.827): A 45-year-old woman who was previously in good health noticed that she could not close her left eye since she woke up. What is the most potent medication for this condition?
- Gemma-3-4B-it (0.813): Woman, age 45, with good health prior to this, noticed that she cannot close her left eye since she woke up from sleep in the morning. What neurological resource has the greatest capacity for this condition?
- Qwen3-VL-8B (text-only) (0.815): A 45-year-old woman with previously good health has noticed that she cannot close her left eye since waking up in the morning. Which of the following resources is most capable for this condition?
- SEA-LION-v4-27B-IT (0.893): A 45-year-old female with previously good health has noted an inability to close her left eye since waking up this morning. Which cranial nerve is most likely involved in this condition?
- Qwen-SEA-LION-v4-4B-VL (0.819): A 45-year-old woman with good health prior to this has noticed that she cannot close her left eye since she woke up. What is the best resource available for this condition?
- Gemma-SEA-LION-v4-4B-VL (0.829): Woman, 45 years old, with good health prior to this, noticed that she cannot close her left eye since she woke up from sleep in the morning. Which nerve resource has the strongest capability for this condition?
- Apertus-SEA-LION-v4-8B-IT (0.809): The patient, a 45-year-old woman who was previously healthy, has noticed that she cannot close her left eye since waking up in the morning. What is the most powerful resource for this condition?
- Sailor2-3B-Chat (0.290): ធនធានប្រសាទដែលមានសមត្ថភាពខ្ពស់ សម្រាប់ ស្ត្រីអាយុ ៤៥ ឆ្នាំ មិនអាចបិទភ្នែកឆ្វេង
ស្ថានភាព: មិនអាចបិទភ្នែកឆ្វេងបាន បន្ទាប់ពីភ្ញាក់ពីគេង
### 1. ការវាយតម្លៃបឋម
- ការស្ទង់មតិ (ការស្ទង់មតិភ្នែក, ការស្ទង់មតិស្មារតី, ការស្ទង់មតិស្មារតី)
- ការស្ទង់មតិស្មារតី (ការស្ទង់មតិស្មារតី, ការស្ទង់មតិស្មារតី, ការស្ទង់មតិស្មារតី)
- ការស្ទង់មតិស្មារតី (ការស
- Sailor2-8B-Chat (0.680): Ophthalmologic evaluation (e.g., neuro-ophthalmology) for the most appropriate resource:
The patient, a previously healthy 45-year-old woman, has reported inability to close her left eye since waking up in the morning. A neuro-ophthalmological assessment is the most suitable initial diagnostic approach for this condition.
- Sailor2-20B-Chat (0.842): A 45-year-old, previously healthy woman noted inability to close her left eye since waking up this morning; most likely neurological source for this condition?

**#156** (COMET spread 0.589)

- source: ស្ត្រីអាយុ ៥៧ ឆ្នាំម្នាក់បានមកបង្ហាញពីការឈឺចាប់ផ្នែកពោះវៀនជាបន្តបន្ទាប់ជាច្រើនឆ្នាំ និងការកើតជំងឺច្របូកច្របល់ ដែលមានលក្ខណៈដោយមានការត្រូវការជាតិអាថ៌កំបាំងកើនឡើង និងអារម្មណ៍ថាបានបញ្ចប់ការបញ្ចេញអាថ៌កំបាំងមិនពេញលេញបន្ទាប់ពីការបញ្ចេញ។ រយៈពេលចុងក្រោយនៃរដូវស្រ្តីរបស់នាងគឺ ៦ ឆ្នាំមុន ហើយនាងបានមានការបញ្ជូនកូនតាមផ្លូវភេទដោយគ្មានបញ្ហា ៣ ដង។ ក្នុងអំឡុងពេលពិនិត្យរាងកាយ គេបានសង្កេតឃើញថាចង្កូតភេទខាងក្រោយមានការបង្ហូរពេលធ្វើចលនាវ៉ាល់សាល់វ៉ា។ រចនាសម្ព័ន្ធអាណាតូមីណាមួយដែលមានឱកាសខ្សោយបំផុត ដែលនាំឲ្យមានរោគសញ្ញានេះគឺអ្វី?
- reference: A 57-year-old woman presents with several years of recurrent pelvic pain and constipation, characterized by increased fecal urgency and a sensation of incomplete evacuation after defecation. Her last menstrual period was 6 years ago, and she has had three uncomplicated vaginal deliveries. During a physical examination, the posterior vaginal wall is observed to bulge during a Valsalva maneuver. Which anatomical structure is most likely weakened, leading to this patient's symptoms?
- NLLB-1.3B (0.713): A 57-year-old woman has come to reveal years of persistent abdominal pain and confusion disorder, characterized by an increased need for secrecy and a feeling of having completed an incomplete post-release secrecy. Her last menstrual period was six years ago, and she has had three uncomplicated miscarriages. During the body examination, it was observed that the rear wheel was leaking during the Wal-Salva movement. What anatomical structure has the least chance of causing this syndrome?
- NLLB-3.3B (0.670): A 57-year-old woman came forward with years of continuous abdominal pain and confusion, characterized by an increased urge to ejaculate and a feeling of having completed an incomplete ejaculate after ejaculation. Her last menstrual period was six years ago, and she had three uncomplicated sexual deliveries.
- Llama-2-7B-chat (0.566): "The patient has been experiencing fever for 3 days, with a temperature of 38.5 degrees Celsius. The patient has been taking paracetamol, but the fever has not subsided. The patient has also been experiencing body aches and fatigue. The patient's medical history includes hypertension, diabetes, and hyperlipidemia. The patient has been smoking for 10 years and drinking alcohol for 5 years. The patient has not been compliant with medication in the past. The patient's family history includes a history of cardiovascular disease. The patient's social history includes a history of stress and anxiety. The patient's review of systems is unremarkable. The patient's physical examination reveals a temperature of 38.5 degrees Celsius, with tachycardia and tachypnea. The patient's laboratory results show an elevated white blood cell count and an elevated C-reactive protein level. The patient's chest X-ray shows a small nodule in the right lung. The patient's electrocardiogram shows a sinus tachycardia. The patient's blood tests show a normal blood sugar level and a normal lipid profile. The patient's urine test shows a normal urinalysis. The patient's abdominal examination shows a normal abdomen. The patient's neurological examination shows a normal neurological examination. The patient's musculoskeletal examination shows a normal musculoskeletal examination. The patient's psychiatric examination
- Llama-3.1-8B-Instruct (extra) (0.255): ស្ត្រីអាយុ ៥៧ ឆ្នាំម្នាក់បានមកបង្ហាញពីការឈឺចាប់ផ្នែកពោះវៀនជាបន្តបន្ទាប់ជាច្រើនឆ្នាំ និងការកើតជំងឺច្របូកច្របល់ ដែលមានលក្ខណៈដោយមានការត្រូវការជាតិអាថ៌កំបាំងកើនឡើង និងអារម្មណ៍ថាបានបញ្ចប់ការបញ្ចេញអាថ៌កំបាំងមិនពេញលេញបន្ទាប់ពីការបញ្ចេញ។ រយៈពេលចុង
- Gemma-3-4B-it (0.844): A 57-year-old woman presented with recurrent abdominal pain for many years and constipation, characterized by an increased need for bowel movements and a feeling of incomplete evacuation after defecation. Her last menstrual period was 6 years prior, and she had 3 successful pregnancies via vaginal delivery. During physical examination, a posterior vaginal bleed was noted during a Valsalva maneuver. What is the most anatomically vulnerable structure that leads to this symptom?
- Qwen3-VL-8B (text-only) (0.843): A 57-year-old woman presented with chronic pelvic pain for many years and symptoms of menopausal disorder, characterized by increased need for fluids and a sensation of incomplete bladder emptying after urination. Her last menstrual period was 6 years ago, and she has had three uncomplicated vaginal deliveries. During physical examination, posterior vaginal wall prolapse was observed during straining. Which anatomical structure is most likely to be the weakest, leading to these symptoms?
- SEA-LION-v4-27B-IT (0.820): A 57-year-old female presented with recurrent pelvic pain for many years and constipation, characterized by increased urgency and a sensation of incomplete evacuation following a bowel movement. Her last menstrual period was 6 years ago, and she has had 3 vaginal deliveries without complications. On physical examination, rectovaginal examination revealed rectocele with prolapse on Valsalva maneuver. What is the least likely anatomical structure contributing to these symptoms?
- Qwen-SEA-LION-v4-4B-VL (0.822): A 57-year-old woman presented with chronic lower abdominal pain for several years and a diagnosis of endometriosis, characterized by increasing pain and a sense of incomplete menstrual bleeding following menses. Her most recent menstrual cycle was 6 years ago, and she has had three uncomplicated vaginal deliveries. During physical examination, it was noted that the posterior vaginal wall showed a prolapse during the Valsalva maneuver. What is the least likely anatomical site for this presentation?
- Gemma-SEA-LION-v4-4B-VL (0.836): A 57-year-old woman presented with persistent abdominal pain for many years and recurrent diverticulitis, characterized by increased urge incontinence and a feeling of incomplete emptying after defecation. Her last menstrual period was 6 years ago, and she had three successful vaginal deliveries. During physical examination, a posterior vaginal prolapse was noted during valsalva maneuvers. What is the anatomical structure with the highest risk of failure that leads to this symptom?
- Apertus-SEA-LION-v4-8B-IT (0.825): A 57-year-old woman has been experiencing recurrent abdominal pain for many years and a feeling of incomplete emptying after defecation. Her last menstrual period was 6 years ago, and she has had three normal vaginal deliveries. During the physical examination, it was noted that the posterior vaginal wall prolapsed during valsalva maneuver. The most likely anatomical structure that is weakest and leads to this symptom is?
- Sailor2-3B-Chat (0.287): រចនាសម្ព័ន្ធ​អាណាតូមីណា ប្រឈម នាំទៅ ការឈឺពោះ និងច្របូកច្របល់ (៥៧yo, រោគសញ្ញា)
ការពន្យល់លម្អិត:
1. ប្រវត្តិរោគសញ្ញា:
- ការឈឺចាប់ផ្នែកពោះវៀនជាបន្តបន្ទាប់ និង ការកើតជំងឺច្របូកច្របល់ ដែលបង្ហាញពីការរំខាននៃការបញ្ចេញអាថ៌កំបាំង។
- ការត្រូវការជាតិអាថ៌កំបាំងកើនឡើង និង អារម្មណ៍ថាបានបញ្ចប់ការបញ្ចេញមិនពេញលេញ បង្ហាញពីការរំខាននៃការ
- Sailor2-8B-Chat (0.637): Most likely pathologic entity: Postmenopausal Urethral Prolapse (Urethrocele) or Cystocele with associated Rectocele (due to pelvic floor weakness)
- Urethrocele: Occurs in postmenopausal women due to decreased estrogen, leading to vaginal atrophy and pelvic organ prolapse, including urethral bulging.
- Cystocele/Rectocele: Concurrent prolapses affecting the bladder (cystocele) and rectum (rectocele), often secondary to weakened pelvic floor muscles after menopause.
These conditions explain the symptoms of increased urgency, incomplete emptying, and perineal fullness during voiding, consistent with her clinical presentation.
- Sailor2-20B-Chat (0.801): A 57-year-old woman presented with recurrent lower abdominal pain and constipation, characterized by increased straining and incomplete sensation of bowel emptying post-defecation. Her last menstrual period was 6 years ago; she had uneventful vaginal deliveries (3 times). On physical exam, rectal prolapse noted with valsalva maneuver. The most likely anatomical structure implicated in these symptoms is: Rectal Prolapse.

**#31** (COMET spread 0.583)

- source: អត្ថបទណាខ្លះក្នុងរដ្ឋធម្មនុញ្ញដែលធានាអត្ថិភាពសិទ្ធិរបស់កុមារ?
- reference: Which articles of the constitution guarantee child rights?
- NLLB-1.3B (0.934): What are some constitutional provisions that guarantee children's rights?
- NLLB-3.3B (0.941): What are some of the articles in the constitution that guarantee the rights of children?
- Llama-2-7B-chat (0.383): What are the side effects of the drug អត្ថបទណា (Atropine) when used for treating ក្នុងរដ្ឋធម្មនុញ្ញ (Parkinson's disease)?
- Llama-3.1-8B-Instruct (extra) (0.925): Some articles in the constitution that guarantee the rights of children.
- Gemma-3-4B-it (0.966): Which articles in the Constitution guarantee the rights of children?
- Qwen3-VL-8B (text-only) (0.939): Which provisions in the Constitution ensure the protection of children's rights?
- SEA-LION-v4-27B-IT (0.939): Which articles in the Constitution guarantee the existence of children's rights?
- Qwen-SEA-LION-v4-4B-VL (0.960): Which article in the Constitution guarantees the rights of children?
- Gemma-SEA-LION-v4-4B-VL (0.966): Which articles in the Constitution guarantee the rights of children?
- Apertus-SEA-LION-v4-8B-IT (0.837): The Constitution of Cambodia guarantees the existence of children's rights.
- Sailor2-3B-Chat (0.552): អត្ថបទសំខាន់ៗ ក្នុងរដ្ឋធម្មនុញ្ញ ធានាសិទ្ធិកុមារ
រដ្ឋធម្មនុញ្ញ បង្កើតជាស្ពានសំខាន់សម្រាប់ការការពារ និងការអនុវត្តសិទ្ធិរបស់កុមារ។ អត្ថបទជាច្រើនក្នុងរដ្ឋធម្មនុញ្ញ ធានានូវអត្ថិភាព និងការអភិវឌ្ឍន៍របស់ពួកគេ។
### ១. សិទ្ធិកុមារ (Article ១៦)
សេចក្តីប្រកាស៖
- សិទ្ធិទទួលបានការអភិវឌ្ឍន៍៖ កុមារមានសិទ្ធិទទួលបានការអប់រំ ការថែទាំសុខភាព និងការអភ
- Sailor2-8B-Chat (0.726): Which articles of the Constitution guarantee children's rights?
These include:
- Article 34: Right to life, health, and well-being.
- Article 28: Protection against exploitation, abuse, and neglect.
- Article 35: Access to education and care.
- Additional provisions ensuring non-discrimination, participation, and special protection for vulnerable children.
- Sailor2-20B-Chat (0.945): Which constitutional provisions ensure the protection of children's rights?

**#63** (COMET spread 0.566)

- source: ក្នុងប្រជាជនមួយដែលការសាកល្បងស្ក្រីនបានកំណត់ឱ្យមានមនុស្ស 90 នាក់ជាសកម្មសម្រាប់ជំងឺទឹកនោមផ្អែមចេញពី 1000 នាក់ ហើយការសាកល្បងវិនិច្ឆ័យស្តង់ដ៍ប្រាក់បានកំណត់ឱ្យមានមនុស្ស 100 នាក់ជាសកម្ម តើអត្រាសេនស៊ីតិវីតីនៃការសាកល្បងស្ក្រីនគឺប៉ុន្មាន?
- reference: In a population where a screening test identified 90 individuals as positive for diabetes out of 1000, and the Gold standard diagnostic test identified 100 individuals as positive, what is the sensitivity of the screening test?
- NLLB-1.3B (0.884): In a population where the screen test identified 90 people as active for diabetes out of 1000, and the silver standard diagnostic test identified 100 people as active, what is the sensitivity ratio of the screen test?
- NLLB-3.3B (0.876): In a population where the screening test identified 90 people as active for diabetes out of 1,000, and the silver standard diagnostic test identified 100 people as active, what is the survival rate of the screening test?
- Llama-2-7B-chat (0.618): "How many people have been infected with COVID-19 in Cambodia as of today, and how many have died from the virus? Also, how many people have been vaccinated with the COVID-19 vaccine in Cambodia as of today, and how many doses have been administered?"
I hope this helps! Let me know if you have any other questions.
- Llama-3.1-8B-Instruct (extra) (0.326): ក្នុងប្រជាជនមួយដែលការសាកល្បងស្ក្រីនបានកំណត់ឱ្យមានមនុស្ស 90 នាក់ជាសកម្មសម្រាប់ជំងឺទឹកនោមផ្អែមចេញពី 1000 នាក់ ហើយការសាកល្បងវិនិច្ឆ័យស្តង់ដ៍ប្រាក់បានកំណត់ឱ្យមានមនុស្ស 100 នាក់ជាសកម្ម តើអត្រាសេនស៊ីតិវីតីនៃការសាកល្បងស្ក្រីនគឺប៉ុន្មាន? អត្រាសេនស៊ីតិវីតីន
- Gemma-3-4B-it (0.876): In a population where screening identified 90 out of 1000 people as active for diabetes, and standard diagnostic testing identified 100 out of 100 people as active, what is the sensitivity rate of the screening test?
- Qwen3-VL-8B (text-only) (0.756): In a population where the trial for drug X was designed to enroll 90 out of 1000 people with diabetes, and the standard trial for drug Y was designed to enroll 100 people, what is the sensitivity rate of the trial for drug X?
- SEA-LION-v4-27B-IT (0.892): In a population where a screening test identified 90 people as active for diabetes out of 1000 people, and a standard gold test identified 100 people as active, what is the sensitivity of the screening test?
- Qwen-SEA-LION-v4-4B-VL (0.801): In a population where the screening for schistosomiasis has identified 90 people as active cases among 1000 people, and the diagnostic testing has identified 100 people as active, what is the sensitivity of the schistosomiasis screening?
- Gemma-SEA-LION-v4-4B-VL (0.890): In a population where screening identified 90 people as active for diabetes out of 1000, and standard diagnostic testing identified 100 people as active, what is the sensitivity of the screening test?
- Apertus-SEA-LION-v4-8B-IT (0.683): The sensitivity rate of the screening test is 90%.
- Sailor2-3B-Chat (0.383): \[ \text{Sensitivity} = \frac{\text{True Positive}}{\text{Total Positive}} \]
- Sailor2-8B-Chat (0.574): Sensitivity of the screening test:
- Population with disease (true positives): 90 out of 1000 = 9%
- Total participants in the study: 1000 individuals
Screening test performance:
- True positives (TP): 90
- False negatives (FN): 1000 - 90 = 910 (not detected but have the disease)
Sensitivity calculation:
\[ \text{Sensitivity} = \frac{\text{True Positives}}{\text{Total Population with Disease}} = \frac{90}{900} = 0.9\% \]
Answer: 9% (or equivalently, 0.9 when expressed as a decimal)
- Sailor2-20B-Chat (0.627): 在人口中，筛查试验检测到90例（1000人中）活动性糖尿病，金标准测试确认100例阳性 - 筛查试验的敏感性百分比是多少？

