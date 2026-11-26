# Translation agent benchmark (X → English), FLORES devtest first 200 + 200 Khmer medical questions

BLEU / chrF++: sacrebleu corpus scores, same settings as the NLLB benchmark. COMET: Unbabel/wmt22-comet-da. Numbers kept: digit runs of the source found in the output. Loops: repeated 3-gram ≥ 4 times or output hit the token limit. NLLB-1.3B: saved outputs of the earlier benchmark (beam 4, sentence by sentence), not re-run, so no speed figure.

| model | set | BLEU | chrF++ | COMET | numbers kept | loops | empty | s / 100 sent. |
|---|---|---|---|---|---|---|---|---|
| NLLB-1.3B | Khmer (FLORES) | 34.0 | 57.7 | 0.8656 | 93.8% (105/112) | 0 | 0 | n/a |
| Llama-2-7B-chat | Khmer (FLORES) | 1.5 | 20.2 | 0.53 | 76.8% (86/112) | 31 | 0 | 28.25 |
| Llama-3.1-8B-Instruct (extra) | Khmer (FLORES) | 21.1 | 49.1 | 0.8152 | 96.4% (108/112) | 1 | 0 | 18.11 |
| Gemma-3-4B-it | Khmer (FLORES) | 21.0 | 50.8 | 0.8308 | 97.3% (109/112) | 0 | 0 | 4.05 |
| Qwen3-VL-8B (text-only) | Khmer (FLORES) | 24.6 | 52.3 | 0.8402 | 95.5% (107/112) | 0 | 0 | 5.7 |
| NLLB-1.3B | Lao (FLORES) | 35.2 | 59.1 | 0.8671 | 97.4% (113/116) | 0 | 0 | n/a |
| Llama-2-7B-chat | Lao (FLORES) | 1.4 | 18.2 | 0.4871 | 76.7% (89/116) | 65 | 0 | 28.56 |
| Llama-3.1-8B-Instruct (extra) | Lao (FLORES) | 12.1 | 36.2 | 0.6837 | 99.1% (115/116) | 1 | 0 | 5.41 |
| Gemma-3-4B-it | Lao (FLORES) | 23.6 | 51.7 | 0.8347 | 100.0% (116/116) | 0 | 0 | 3.8 |
| Qwen3-VL-8B (text-only) | Lao (FLORES) | 26.9 | 54.2 | 0.8499 | 100.0% (116/116) | 0 | 0 | 4.99 |
| NLLB-1.3B | Vietnamese (FLORES) | 37.5 | 61.3 | 0.8747 | 90.8% (108/119) | 0 | 0 | n/a |
| Llama-2-7B-chat | Vietnamese (FLORES) | 24.1 | 47.6 | 0.7957 | 92.4% (110/119) | 0 | 0 | 8.9 |
| Llama-3.1-8B-Instruct (extra) | Vietnamese (FLORES) | 34.4 | 60.2 | 0.874 | 95.0% (113/119) | 0 | 0 | 2.36 |
| Gemma-3-4B-it | Vietnamese (FLORES) | 30.3 | 57.5 | 0.8677 | 97.5% (116/119) | 0 | 0 | 3.31 |
| Qwen3-VL-8B (text-only) | Vietnamese (FLORES) | 35.2 | 61.2 | 0.8828 | 94.1% (112/119) | 0 | 0 | 3.06 |
| NLLB-1.3B | Khmer medical Qs | 27.8 | 50.2 | 0.7915 | 75.1% (190/253) | 0 | 0 | n/a |
| Llama-2-7B-chat | Khmer medical Qs | 0.7 | 13.8 | 0.4692 | 14.6% (37/253) | 56 | 0 | 58.52 |
| Llama-3.1-8B-Instruct (extra) | Khmer medical Qs | 22.7 | 42.8 | 0.7272 | 93.7% (237/253) | 9 | 0 | 46.11 |
| Gemma-3-4B-it | Khmer medical Qs | 29.9 | 53.0 | 0.7954 | 98.0% (248/253) | 0 | 1 | 6.5 |
| Qwen3-VL-8B (text-only) | Khmer medical Qs | 33.9 | 55.0 | 0.8079 | 94.1% (238/253) | 0 | 0 | 13.72 |

Numbers kept by the human English reference itself (FLORES sometimes writes numbers as words): Khmer (FLORES) 94.6%, Lao (FLORES) 100.0%, Vietnamese (FLORES) 93.3%, Khmer medical Qs 97.2%

## Largest disagreements: Khmer (FLORES)

**#181** (COMET spread 0.557)

- source: ការរញ្ជួយដីកម្រិតមធ្យមបានធ្វើឱ្យកក្រើក​ភាគខាងលិច​ Montana ​នៅម៉ោង 10 និង 08 នាទីយប់កាលពីថ្ងៃចន្ទ។
- reference: A moderate earthquake shook western Montana at 10:08 p.m. on Monday.
- NLLB-1.3B (0.960): A moderate earthquake rocked western Montana at 10:08 p.m. on Monday.
- Llama-2-7B-chat (0.402): The patient has been taking Montana 10 mg every 8 hours for the past 10 days.
- Llama-3.1-8B-Instruct (extra) (0.621): The land subsidence has caused the west fork of the Big Hole River in Montana at 10:08 PM on Wednesday night.
- Gemma-3-4B-it (0.893): Moderate ground shaking occurred in western Montana at 10:08 PM on Monday.
- Qwen3-VL-8B (text-only) (0.808): Moderate soil erosion caused the landslide in western Montana at 10:08 PM last Monday.

**#78** (COMET spread 0.548)

- source: ប្រធានាធិបតី​សហរដ្ឋអាមេរិក​ ចក ដាប់ប៊ែលយ៊ូ ប៊ូស​ បាន​ស្វាគមន៍​ចំពោះ​ការ​ប្រកាស​នោះ​។​
- reference: U.S. President George W. Bush welcomed the announcement.
- NLLB-1.3B (0.900): US President Barack Obama has welcomed the announcement.
- Llama-2-7B-chat (0.356): The patient has been diagnosed with chronic kidney disease stage 5, with a creatinine level of 5.5 mg/dL and a glomerular filtration rate (GFR) of 15 mL/min/1.73m2. The patient has been advised to follow a renal diet and to take medications as prescribed by their doctor to manage their condition.
- Llama-3.1-8B-Instruct (extra) (0.847): President of the United States Joe Biden expressed welcome to that announcement.
- Gemma-3-4B-it (0.705): The President of the United States, Chuck Daubelyeu Boo, welcomed the announcement.
- Qwen3-VL-8B (text-only) (0.903): U.S. President Joe Biden welcomed that announcement.

**#138** (COMET spread 0.544)

- source: ដីល្បាប់នេះគឺចាំបាច់សម្រាប់បង្កើតផ្នូកខ្សាច់ និងឆ្នេរទាំងឡាយ ដែលដើរតួនាទីជាដែនជម្រករបស់សត្វព្រៃ។
- reference: This sediment was necessary for creating sandbars and beaches, which served as wildlife habitats.
- NLLB-1.3B (0.903): This land is necessary for the creation of sand dunes and beaches that serve as wildlife refuges.
- Llama-2-7B-chat (0.359): The patient has a history of hypertension, diabetes, and hyperlipidemia. The patient's blood pressure is 160/100 mmHg, and the patient's fasting blood sugar is 200 mg/dL. The patient's total cholesterol is 300 mg/dL, and the patient's triglycerides are 200 mg/dL. The patient has a history of smoking and excessive alcohol consumption.
- Llama-3.1-8B-Instruct (extra) (0.846): This land is necessary for creating many reefs and shores, which play the role as a habitat of wild animals.
- Gemma-3-4B-it (0.884): This document is essential for creating sandbars and beaches, which serve as habitats for wildlife.
- Qwen3-VL-8B (text-only) (0.764): This law is essential for establishing buffer zones and riparian areas that serve as protective buffers for wildlife.

**#61** (COMET spread 0.534)

- source: ផ្ទាំង​​អេក្រង់ទូរទស្សន៍ធំៗជាច្រើន ​ត្រូវបានដំឡើងនៅទីកន្លែងផ្សេងៗគ្នា​ជា​ច្រើន​នៅ​ក្នុងទីក្រុងរ៉ូម ដើម្បីឱ្យប្រជាជន​ទស្សនាពិធីនេះ។
- reference: Several large television screens were installed in various places in Rome to let the people watch the ceremony.
- NLLB-1.3B (0.892): Large television screens were installed at various locations in Rome for the public to watch.
- Llama-2-7B-chat (0.376): "The patient has been diagnosed with chronic kidney disease stage 5, which is severe and requires close monitoring and management to prevent complications. The patient's creatinine level is 5.5 mg/dL, which is above the normal range of 0.5-1.0 mg/dL. The patient's estimated glomerular filtration rate (eGFR) is 15 mL/min/1.73m2, which is below the normal range of 90-120 mL/min/1.73m2. The patient's urine output is 1200 mL/day, which is within the normal range of 1000-1500 mL/day. The patient's blood urea nitrogen (BUN) level is 25 mg/dL, which is above the normal range of 7-20 mg/dL. The patient's serum albumin level is 3.5 g/dL, which is below the normal range of
- Llama-3.1-8B-Instruct (extra) (0.902): Large TV screens were installed at various locations throughout the city of Rome in order for the public to watch this event.
- Gemma-3-4B-it (0.911): Large television screens were installed in many different places throughout the city of Rome so that the public could watch the event.
- Qwen3-VL-8B (text-only) (0.903): Many large television screens have been installed at various locations throughout the city of Rome to allow the public to watch the event.

**#164** (COMET spread 0.533)

- source: ច្បាប់បោះឆ្នោតបារាំងមានការកំណត់និតិវិធីយ៉ាង​តឹងរឹង។
- reference: French electoral law rather strictly codifies the proceedings.
- NLLB-1.3B (0.916): French electoral law has strict rules.
- Llama-2-7B-chat (0.382): The patient has a history of hypertension, diabetes, and hyperlipidemia. The patient's blood pressure is 140/90 mmHg, and the patient's fasting blood sugar is 200 mg/dL. The patient's total cholesterol is 300 mg/dL, and the patient's triglycerides are 200 mg/dL. The patient has a history of smoking and excessive alcohol consumption.
- Llama-3.1-8B-Instruct (extra) (0.894): The French electoral law has strict electoral procedures.
- Gemma-3-4B-it (0.875): French voting laws have very strict regulations.
- Qwen3-VL-8B (text-only) (0.907): French electoral law has stringent procedural regulations.

## Largest disagreements: Lao (FLORES)

**#9** (COMET spread 0.591)

- source: ຣີງ (Ring) ຍັງໄດ້ຕັດສິນຄະດີຄວາມກັບບໍລິສັດຄວາມປອດໄພທີ່ເປັນຄູ່ແຂ່ງ, ຊຶ່ງແມ່ນບໍລິສັດ ADT Corporation.
- reference: Ring also settled a lawsuit with competing security company, the ADT Corporation.
- NLLB-1.3B (0.937): Ring also settled a lawsuit against a competing security firm, ADT Corporation.
- Llama-2-7B-chat (0.346): Ring (ADT Corporation) 100mg/5ml Injection
- Llama-3.1-8B-Instruct (extra) (0.696): Ring has been removed from the ADT Corporation's business license, which is a security company.
- Gemma-3-4B-it (0.810): Ring still ruled on the lawsuit against the security company that was a competitor, which is ADT Corporation.
- Qwen3-VL-8B (text-only) (0.878): Ring also decided to sue a competing security company, which is ADT Corporation.

**#183** (COMET spread 0.586)

- source: ແຜ່ນດິນໄຫວເກີດຂຶ້ນຢ່າງຮຸນແຮງທີ່ປະມານ 20 ກິໂລແມັດ (15 ໄມລ໌) ທາງເໜືອ - ທິດຕາເວັນອອກສຽງເໜືອ ຂອງ Dillon ແລະ ປະມານ 65 ກິໂລແມັດ (40 ໄມລ໌) ທາງທິດໃຕ້ຂອງ Butte.
- reference: The earthquake was centered about 20 km (15 miles) north-northeast of Dillon, and about 65 km (40 miles) south of Butte.
- NLLB-1.3B (0.926): The earthquake struck at about 20 km (15 mi) north-northeast of Dillon and about 65 km (40 mi) south of Butte.
- Llama-2-7B-chat (0.345): Twenty (15) packs of Dillon cigarettes - 65 cartons (40 packs) of Butte cigarettes.
- Llama-3.1-8B-Instruct (extra) (0.747): The terrain rises steeply to an elevation of approximately 20 kilometers (15 miles) north - northwest of Dillon and approximately 65 kilometers (40 miles) south of Butte.
- Gemma-3-4B-it (0.907): An earthquake occurred severely approximately 20 kilometers (15 miles) north-northwest of Dillon and approximately 65 kilometers (40 miles) south of Butte.
- Qwen3-VL-8B (text-only) (0.931): The earthquake occurred strongly about 20 kilometers (15 miles) north-northeast of Dillon and about 65 kilometers (40 miles) south of Butte.

**#21** (COMET spread 0.581)

- source: Gosling ແລະ Stone ໄດ້ຮັບການນໍາສະເໜີຊື່ເຂົ້າຊິງສໍາລັບນັກສະແດງຊາຍ ແລະ ນັກສະແດງຍິງດີເດັ່ນຕາມລຳດັບ.
- reference: Gosling and Stone received nominations for Best Actor and Actress respectively.
- NLLB-1.3B (0.957): Gosling and Stone were nominated for Best Actor and Best Actress respectively.
- Llama-2-7B-chat (0.385): "Gosling Stone's medical report shows that the patient's blood pressure is 140/90 mmHg, which is slightly elevated. The patient also has a history of hypertension and hyperlipidemia. The laboratory test results show that the patient's creatinine level is 1.5 mg/dL, which is within the normal range. The patient's urine output is 400 mL/day, which is slightly below the normal range. The patient's electrolyte levels are within the normal range. The patient's liver function tests are normal. The patient's thyroid function tests are also normal. The patient's chest X-ray shows no evidence of cardiomegaly or pulmonary disease. The patient's electrocardiogram (ECG) shows no evidence of ischemia or arrhythmia. The patient's echocardiogram shows no evidence of left ventricular hypertrophy or valvular disease. The patient's stress test shows no evidence of ischemia or arrhythmia
- Llama-3.1-8B-Instruct (extra) (0.850): Gosling and Stone have received Golden Globe nominations for Best Actor in a Leading Role and Best Actress in a Leading Role.
- Gemma-3-4B-it (0.956): Gosling and Stone were nominated for Best Actor and Best Actress, respectively.
- Qwen3-VL-8B (text-only) (0.966): Gosling and Stone received nominations for Best Actor and Best Actress respectively.

**#59** (COMET spread 0.576)

- source: ຄົນຫຼາຍກວ່າສີ່ລ້ານຄົນໄປທີ່ Rome ເພື່ອເຂົ້າຮ່ວມງານສົບ.
- reference: Over four million people went to Rome to attend the funeral.
- NLLB-1.3B (0.894): More than four million people come to Rome for funerals.
- Llama-2-7B-chat (0.332): The patient has a history of taking Rome 300 mg once daily for 3 months, and the current dose is 200 mg once daily. The patient has been taking this medication for 6 months.
- Llama-3.1-8B-Instruct (extra) (0.881): More than nine million people went to Rome to join the festival.
- Gemma-3-4B-it (0.824): More than four million people went to Rome to attend the Sob festival.
- Qwen3-VL-8B (text-only) (0.907): More than four million people went to Rome to attend the event.

**#130** (COMET spread 0.573)

- source: ຟຼຸກຄ໌ (Fluke) ໄດ້ຂຽນວ່າ ຄວາມພະຍາຍາມຂອງບາງຄົນ ທີ່ຈະກະຕຸ້ນແມ່ຍິງໃຫ້ເວົ້າຢ່າງເປີດໃຈອອກມາໃຫ້ໝົດ ກ່ຽວກັບສຸຂະພາບຂອງແມ່ຍິງ ແມ່ນບໍ່ປະສົບຜົນສຳເລັດ.
- reference: Fluke wrote that the efforts by some to drown out women from speaking out about women’s health were unsuccessful.
- NLLB-1.3B (0.897): Fluke writes that attempts by some to encourage women to speak openly about women's health have been unsuccessful.
- Llama-2-7B-chat (0.324): Fluke (Fluke) 100g x 10 packs x 10 boxes = 1000g
- Llama-3.1-8B-Instruct (extra) (0.633): Fluke stated that the degree of maternal-fetal attachment in some people who can induce labor by talking openly about the mother's health is not effective.
- Gemma-3-4B-it (0.890): Fluke wrote that the efforts of some people to encourage women to speak openly and completely about their health are not successful.
- Qwen3-VL-8B (text-only) (0.896): Fluke wrote that the attempts by some people to encourage women to openly speak about their health have not been successful.

## Largest disagreements: Vietnamese (FLORES)

**#146** (COMET spread 0.553)

- source: Đảng cầm quyền, Tổ chức Nhân dân Tây Nam Phi (SWAPO), cũng giữ được thế đa số trong các cuộc bầu cử nghị viện.
- reference: The ruling party, South West Africa People's Organisation (SWAPO), also retained a majority in the parliamentary elections.
- NLLB-1.3B (0.941): The ruling party, the South West Africa People's Organisation (SWAPO), also retained its majority in the parliamentary elections.
- Llama-2-7B-chat (0.389): The English translation of the user's text is:
- Llama-3.1-8B-Instruct (extra) (0.939): The ruling party, the South West Africa People's Organization (SWAPO), also maintained a majority in the parliamentary elections.
- Gemma-3-4B-it (0.928): The ruling party, the Southwest African People’s Organization (SWAPO), also maintained a majority in the parliamentary elections.
- Qwen3-VL-8B (text-only) (0.928): The ruling party, the South West Africa People's Organization (SWAPO), also maintained a majority in parliamentary elections.

**#195** (COMET spread 0.537)

- source: Nhiếp ảnh gia này sau đó được chuyển đến Trung tâm y tế Ronald Reagan UCLA và qua đời tại đây.
- reference: The photographer was transported to Ronald Reagan UCLA Medical Center, where he subsequently died.
- NLLB-1.3B (0.931): The photographer was later transferred to the Ronald Reagan UCLA Medical Center, where he died.
- Llama-2-7B-chat (0.394): The medical translator translates the Vietnamese text as follows:
- Llama-3.1-8B-Instruct (extra) (0.907): This photographer was then transferred to the Ronald Reagan UCLA Medical Center and died there.
- Gemma-3-4B-it (0.910): This photographer was subsequently transferred to the Ronald Reagan UCLA Medical Center and passed away there.
- Qwen3-VL-8B (text-only) (0.907): This photographer was then transferred to the Ronald Reagan UCLA Medical Center and died there.

**#129** (COMET spread 0.529)

- source: Số tiền này có thể dùng để xây nhà chống lũ, quản lý nguồn nước tốt hơn và đa dạng hóa mùa vụ.
- reference: The money could go toward flood-proof houses, better water management, and crop diversification.
- NLLB-1.3B (0.910): This money could be used to build flood defences, improve water management, and diversify crops.
- Llama-2-7B-chat (0.381): The English translation of the user's text is:
- Llama-3.1-8B-Instruct (extra) (0.888): This amount of money can be used to build flood-resistant houses, manage water resources better, and diversify the crop season.
- Gemma-3-4B-it (0.895): This money can be used to build flood-resistant houses, manage water resources better, and diversify the crop season.
- Qwen3-VL-8B (text-only) (0.888): This amount of money can be used to build flood-resistant houses, manage water resources better, and diversify crop seasons.

**#186** (COMET spread 0.524)

- source: Những ca nghi nhiễm H5N1 tại Croatia và Đan Mạch vẫn chưa được xác nhận.
- reference: Suspected cases of H5N1 in Croatia and Denmark remain unconfirmed.
- NLLB-1.3B (0.942): Suspected cases of H5N1 in Croatia and Denmark have not yet been confirmed.
- Llama-2-7B-chat (0.419): The text in English is:
- Llama-3.1-8B-Instruct (extra) (0.931): Cases of suspected H5N1 in Croatia and Denmark have not been confirmed yet.
- Gemma-3-4B-it (0.923): The suspected H5N1 infections in Croatia and Denmark have not yet been confirmed.
- Qwen3-VL-8B (text-only) (0.918): The H5N1 suspected cases in Croatia and Denmark have not been confirmed.

**#36** (COMET spread 0.524)

- source: Họ phát hiện ra rằng Mặt Trời hoạt động theo những nguyên tắc căn bản giống như các ngôi sao khác: Hoạt động của tất cả những ngôi sao trong hệ thống này được kết luận vận hành vì sự tự phát sáng, tự quay quanh trục và không có gì khác.
- reference: They found the Sun operated on the same basic principles as other stars: The activity of all stars in the system was found to be driven by their luminosity, their rotation, and nothing else.
- NLLB-1.3B (0.834): They discovered that the Sun operates according to the same basic principles as other stars: The activity of all the stars in this system is concluded to operate by self-illumination, self-rotation, and nothing else.
- Llama-2-7B-chat (0.310): The user's text in Vietnamese:
- Llama-3.1-8B-Instruct (extra) (0.824): They discovered that the Sun operates according to basic principles similar to other stars: The activity of all stars in this system is concluded to operate due to self-emission, self-rotation around the axis, and nothing else.
- Gemma-3-4B-it (0.808): They discovered that the Sun operates according to basic principles similar to other stars: The activity of all stars in this system is concluded to operate due to self-illumination, self-rotation around its axis, and nothing else.
- Qwen3-VL-8B (text-only) (0.823): They discovered that the Sun operates according to fundamental principles similar to other stars: The activity of all stars in this system is concluded to operate due to self-luminosity, self-rotation around their axes, and nothing else.

## Largest disagreements: Khmer medical Qs

**#182** (COMET spread 0.677)

- source: ការបែកជើងត្រូវបានកំណត់យ៉ាងដូចម្តេចក្នុងពាក្យវេជ្ជសាស្ត្រ ហើយអ្វីដែលបណ្តាលឲ្យមានការប៉ះពាល់?
- reference: How is a fracture defined in medical terms, and what is a contusion caused by?
- NLLB-1.3B (0.874): How is leg fracture defined in medical terminology, and what causes it to affect?
- Llama-2-7B-chat (0.499): "Has the patient's blood sugar level been checked recently?")
- Llama-3.1-8B-Instruct (extra) (0.239): Fracture ត្រូវបានកំណត់យ៉ាងដូចជាការបែកខ្សែក្រុងនៃស្បៃក្រុងដែលបែកខ្ញែកនៅក្នុងស្បៃក្រុង ឬការបែកខ្សែក្រុងនៃស្បៃក្រុងដែលបែកខ្ញែកនៅក្នុងស្បៃក្រុង ឬការបែកខ្សែក្រុងនៃស្បៃក្រុងដែលបែកខ្ញែកនៅក្នុងស្បៃក្រុង ឬការបែកខ្សែក្រុងនៃស្បៃក្រុងដែលបែកខ្ញែកនៅក្ន
- Gemma-3-4B-it (0.712): A postpartum hemorrhage is defined in medical terms and what causes it?
- Qwen3-VL-8B (text-only) (0.916): How is foot fracture defined in medical terms, and what causes it?

**#156** (COMET spread 0.589)

- source: ស្ត្រីអាយុ ៥៧ ឆ្នាំម្នាក់បានមកបង្ហាញពីការឈឺចាប់ផ្នែកពោះវៀនជាបន្តបន្ទាប់ជាច្រើនឆ្នាំ និងការកើតជំងឺច្របូកច្របល់ ដែលមានលក្ខណៈដោយមានការត្រូវការជាតិអាថ៌កំបាំងកើនឡើង និងអារម្មណ៍ថាបានបញ្ចប់ការបញ្ចេញអាថ៌កំបាំងមិនពេញលេញបន្ទាប់ពីការបញ្ចេញ។ រយៈពេលចុងក្រោយនៃរដូវស្រ្តីរបស់នាងគឺ ៦ ឆ្នាំមុន ហើយនាងបានមានការបញ្ជូនកូនតាមផ្លូវភេទដោយគ្មានបញ្ហា ៣ ដង។ ក្នុងអំឡុងពេលពិនិត្យរាងកាយ គេបានសង្កេតឃើញថាចង្កូតភេទខាងក្រោយមានការបង្ហូរពេលធ្វើចលនាវ៉ាល់សាល់វ៉ា។ រចនាសម្ព័ន្ធអាណាតូមីណាមួយដែលមានឱកាសខ្សោយបំផុត ដែលនាំឲ្យមានរោគសញ្ញានេះគឺអ្វី?
- reference: A 57-year-old woman presents with several years of recurrent pelvic pain and constipation, characterized by increased fecal urgency and a sensation of incomplete evacuation after defecation. Her last menstrual period was 6 years ago, and she has had three uncomplicated vaginal deliveries. During a physical examination, the posterior vaginal wall is observed to bulge during a Valsalva maneuver. Which anatomical structure is most likely weakened, leading to this patient's symptoms?
- NLLB-1.3B (0.713): A 57-year-old woman has come to reveal years of persistent abdominal pain and confusion disorder, characterized by an increased need for secrecy and a feeling of having completed an incomplete post-release secrecy. Her last menstrual period was six years ago, and she has had three uncomplicated miscarriages. During the body examination, it was observed that the rear wheel was leaking during the Wal-Salva movement. What anatomical structure has the least chance of causing this syndrome?
- Llama-2-7B-chat (0.566): "The patient has been experiencing fever for 3 days, with a temperature of 38.5 degrees Celsius. The patient has been taking paracetamol, but the fever has not subsided. The patient has also been experiencing body aches and fatigue. The patient's medical history includes hypertension, diabetes, and hyperlipidemia. The patient has been smoking for 10 years and drinking alcohol for 5 years. The patient has not been compliant with medication in the past. The patient's family history includes a history of cardiovascular disease. The patient's social history includes a history of stress and anxiety. The patient's review of systems is unremarkable. The patient's physical examination reveals a temperature of 38.5 degrees Celsius, with tachycardia and tachypnea. The patient's laboratory results show an elevated white blood cell count and an elevated C-reactive protein level. The patient's chest X-ray shows a small nodule in the right lung. The patient's electrocardiogram shows a sinus tachycardia. The patient's blood tests show a normal blood sugar level and a normal lipid profile. The patient's urine test shows a normal urinalysis. The patient's abdominal examination shows a normal abdomen. The patient's neurological examination shows a normal neurological examination. The patient's musculoskeletal examination shows a normal musculoskeletal examination. The patient's psychiatric examination
- Llama-3.1-8B-Instruct (extra) (0.255): ស្ត្រីអាយុ ៥៧ ឆ្នាំម្នាក់បានមកបង្ហាញពីការឈឺចាប់ផ្នែកពោះវៀនជាបន្តបន្ទាប់ជាច្រើនឆ្នាំ និងការកើតជំងឺច្របូកច្របល់ ដែលមានលក្ខណៈដោយមានការត្រូវការជាតិអាថ៌កំបាំងកើនឡើង និងអារម្មណ៍ថាបានបញ្ចប់ការបញ្ចេញអាថ៌កំបាំងមិនពេញលេញបន្ទាប់ពីការបញ្ចេញ។ រយៈពេលចុង
- Gemma-3-4B-it (0.844): A 57-year-old woman presented with recurrent abdominal pain for many years and constipation, characterized by an increased need for bowel movements and a feeling of incomplete evacuation after defecation. Her last menstrual period was 6 years prior, and she had 3 successful pregnancies via vaginal delivery. During physical examination, a posterior vaginal bleed was noted during a Valsalva maneuver. What is the most anatomically vulnerable structure that leads to this symptom?
- Qwen3-VL-8B (text-only) (0.843): A 57-year-old woman presented with chronic pelvic pain for many years and symptoms of menopausal disorder, characterized by increased need for fluids and a sensation of incomplete bladder emptying after urination. Her last menstrual period was 6 years ago, and she has had three uncomplicated vaginal deliveries. During physical examination, posterior vaginal wall prolapse was observed during straining. Which anatomical structure is most likely to be the weakest, leading to these symptoms?

**#31** (COMET spread 0.583)

- source: អត្ថបទណាខ្លះក្នុងរដ្ឋធម្មនុញ្ញដែលធានាអត្ថិភាពសិទ្ធិរបស់កុមារ?
- reference: Which articles of the constitution guarantee child rights?
- NLLB-1.3B (0.934): What are some constitutional provisions that guarantee children's rights?
- Llama-2-7B-chat (0.383): What are the side effects of the drug អត្ថបទណា (Atropine) when used for treating ក្នុងរដ្ឋធម្មនុញ្ញ (Parkinson's disease)?
- Llama-3.1-8B-Instruct (extra) (0.925): Some articles in the constitution that guarantee the rights of children.
- Gemma-3-4B-it (0.966): Which articles in the Constitution guarantee the rights of children?
- Qwen3-VL-8B (text-only) (0.939): Which provisions in the Constitution ensure the protection of children's rights?

**#63** (COMET spread 0.558)

- source: ក្នុងប្រជាជនមួយដែលការសាកល្បងស្ក្រីនបានកំណត់ឱ្យមានមនុស្ស 90 នាក់ជាសកម្មសម្រាប់ជំងឺទឹកនោមផ្អែមចេញពី 1000 នាក់ ហើយការសាកល្បងវិនិច្ឆ័យស្តង់ដ៍ប្រាក់បានកំណត់ឱ្យមានមនុស្ស 100 នាក់ជាសកម្ម តើអត្រាសេនស៊ីតិវីតីនៃការសាកល្បងស្ក្រីនគឺប៉ុន្មាន?
- reference: In a population where a screening test identified 90 individuals as positive for diabetes out of 1000, and the Gold standard diagnostic test identified 100 individuals as positive, what is the sensitivity of the screening test?
- NLLB-1.3B (0.884): In a population where the screen test identified 90 people as active for diabetes out of 1000, and the silver standard diagnostic test identified 100 people as active, what is the sensitivity ratio of the screen test?
- Llama-2-7B-chat (0.470): Sure, I'd be happy to help! Here is the English translation of the user's text:
- Llama-3.1-8B-Instruct (extra) (0.326): ក្នុងប្រជាជនមួយដែលការសាកល្បងស្ក្រីនបានកំណត់ឱ្យមានមនុស្ស 90 នាក់ជាសកម្មសម្រាប់ជំងឺទឹកនោមផ្អែមចេញពី 1000 នាក់ ហើយការសាកល្បងវិនិច្ឆ័យស្តង់ដ៍ប្រាក់បានកំណត់ឱ្យមានមនុស្ស 100 នាក់ជាសកម្ម តើអត្រាសេនស៊ីតិវីតីនៃការសាកល្បងស្ក្រីនគឺប៉ុន្មាន? អត្រាសេនស៊ីតិវីតីន
- Gemma-3-4B-it (0.876): In a population where screening identified 90 out of 1000 people as active for diabetes, and standard diagnostic testing identified 100 out of 100 people as active, what is the sensitivity rate of the screening test?
- Qwen3-VL-8B (text-only) (0.756): In a population where the trial for drug X was designed to enroll 90 out of 1000 people with diabetes, and the standard trial for drug Y was designed to enroll 100 people, what is the sensitivity rate of the trial for drug X?

**#91** (COMET spread 0.541)

- source: អ្វីខ្លះជាគុណសម្បត្តិសំខាន់ពីរនៃអូទីសមកុមារ ដែលពាក់ព័ន្ធនឹងការអភិវឌ្ឍន៍ប្រព័ន្ធប្រសាទនិងឥទ្ធិពលសង្គម-សេដ្ឋកិច្ចក្រៅ?
- reference: What are two key characteristics of infantile autism related to neurobehavioural development and external socio-economic influences?
- NLLB-1.3B (0.911): What are the two main characteristics of childhood autism, related to neural development and external socio-economic influences?
- Llama-2-7B-chat (0.474): Can you tell me the side effects of the drug 'Ciprofloxacin'?
- Llama-3.1-8B-Instruct (extra) (0.369): គុណសម្បត្តិសំខាន់ពីរនៃអូទីសមកុមារ ដែលពាក់ព័ន្ធនឹងការអភិវឌ្ឍន៍ប្រព័ន្ធប្រសាទនិងឥទ្ធិពលសង្គម-សេដ្ឋកិច្ចក្រៅ គឺជា ការរីករាយនិងការសម្រេចចិត្តរបស់កុមារ និង ការរីករាយនិងការសម្រេចចិត្តរបស់កុមារក្នុងសង្គម-សេដ្ឋកិច្ចក្រៅ។
- Gemma-3-4B-it (0.659): What are the two main benefits of Otesom Kamay that relate to nervous system development and extra-social-economic impact?
- Qwen3-VL-8B (text-only) (0.755): What are two key advantages of the OIOS for children, related to the development of the nervous system and external socio-economic impacts?

