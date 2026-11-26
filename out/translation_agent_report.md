# Translation agent benchmark (X → English), FLORES devtest first 1012 + 200 Khmer medical questions

BLEU / chrF++: sacrebleu corpus scores, same settings as the NLLB benchmark. COMET: Unbabel/wmt22-comet-da. Numbers kept: digit runs of the source found in the output. Loops: repeated 3-gram ≥ 4 times or output hit the token limit. Not English: output mostly in Khmer/Lao script (the model rewrote instead of translating). NLLB-1.3B: saved outputs of the earlier benchmark (beam 4, sentence by sentence), not re-run, so no speed figure.

| model | set | BLEU | chrF++ | COMET | numbers kept | loops | empty | not English | s / 100 sent. |
|---|---|---|---|---|---|---|---|---|---|
| NLLB-1.3B | Khmer (FLORES) | 31.3 | 55.4 | 0.8529 | 93.3% (335/359) | 0 | 0 | 0 | n/a |
| Llama-2-7B-chat | Khmer (FLORES) | 0.9 | 18.1 | 0.4834 | 74.7% (268/359) | 289 | 0 | 4 | 28.25 |
| Llama-3.1-8B-Instruct (extra) | Khmer (FLORES) | 18.8 | 47.0 | 0.808 | 95.8% (344/359) | 6 | 0 | 15 | 18.11 |
| Gemma-3-4B-it | Khmer (FLORES) | 20.6 | 50.0 | 0.8309 | 96.9% (348/359) | 0 | 0 | 1 | 4.05 |
| Qwen3-VL-8B (text-only) | Khmer (FLORES) | 22.2 | 50.1 | 0.8376 | 93.3% (335/359) | 0 | 0 | 0 | 5.7 |
| SEA-LION-v4-27B-IT | Khmer (FLORES) | 28.5 | 56.4 | 0.8635 | 99.4% (357/359) | 0 | 0 | 0 | 7.12 |
| NLLB-1.3B | Lao (FLORES) | 34.2 | 58.1 | 0.8607 | 95.9% (348/363) | 0 | 0 | 0 | n/a |
| Llama-2-7B-chat | Lao (FLORES) | 0.8 | 16.9 | 0.4499 | 79.9% (290/363) | 454 | 0 | 20 | 28.56 |
| Llama-3.1-8B-Instruct (extra) | Lao (FLORES) | 11.0 | 35.8 | 0.6804 | 98.3% (357/363) | 5 | 0 | 8 | 5.41 |
| Gemma-3-4B-it | Lao (FLORES) | 24.2 | 51.8 | 0.8297 | 99.4% (361/363) | 0 | 0 | 0 | 3.8 |
| Qwen3-VL-8B (text-only) | Lao (FLORES) | 26.8 | 53.2 | 0.8473 | 98.3% (357/363) | 0 | 0 | 0 | 4.99 |
| SEA-LION-v4-27B-IT | Lao (FLORES) | 34.2 | 59.6 | 0.8717 | 99.7% (362/363) | 0 | 0 | 0 | 8.18 |
| NLLB-1.3B | Vietnamese (FLORES) | 36.6 | 59.7 | 0.867 | 89.9% (340/378) | 0 | 0 | 0 | n/a |
| Llama-2-7B-chat | Vietnamese (FLORES) | 23.4 | 50.4 | 0.8238 | 93.7% (354/378) | 0 | 0 | 0 | 8.9 |
| Llama-3.1-8B-Instruct (extra) | Vietnamese (FLORES) | 32.9 | 58.6 | 0.8682 | 94.2% (356/378) | 0 | 0 | 0 | 2.36 |
| Gemma-3-4B-it | Vietnamese (FLORES) | 31.1 | 57.1 | 0.8646 | 95.0% (359/378) | 0 | 0 | 0 | 3.31 |
| Qwen3-VL-8B (text-only) | Vietnamese (FLORES) | 34.8 | 59.8 | 0.8767 | 93.4% (353/378) | 0 | 0 | 0 | 3.06 |
| SEA-LION-v4-27B-IT | Vietnamese (FLORES) | 35.9 | 60.7 | 0.8772 | 96.6% (365/378) | 0 | 0 | 0 | 5.32 |
| NLLB-1.3B | Khmer medical Qs | 27.8 | 50.2 | 0.7915 | 75.1% (190/253) | 0 | 0 | 0 | n/a |
| Llama-2-7B-chat | Khmer medical Qs | 0.8 | 18.9 | 0.5408 | 29.2% (74/253) | 70 | 0 | 1 | 58.52 |
| Llama-3.1-8B-Instruct (extra) | Khmer medical Qs | 22.6 | 43.1 | 0.7294 | 93.7% (237/253) | 10 | 0 | 14 | 46.11 |
| Gemma-3-4B-it | Khmer medical Qs | 29.8 | 53.1 | 0.7973 | 98.0% (248/253) | 0 | 0 | 0 | 6.5 |
| Qwen3-VL-8B (text-only) | Khmer medical Qs | 33.9 | 55.0 | 0.8079 | 94.1% (238/253) | 0 | 0 | 0 | 13.72 |
| SEA-LION-v4-27B-IT | Khmer medical Qs | 40.5 | 60.8 | 0.8273 | 100.0% (253/253) | 1 | 0 | 0 | 18.48 |

Numbers kept by the human English reference itself (FLORES sometimes writes numbers as words): Khmer (FLORES) 95.0%, Lao (FLORES) 99.4%, Vietnamese (FLORES) 93.1%, Khmer medical Qs 97.2%

## Largest disagreements: Khmer (FLORES)

**#760** (COMET spread 0.616)

- source: តំបន់ម៉ុនតេវីដេអូ (Montevideo) ស្ថិត​នៅ​កៀក​នឹង​តំបន់​ត្រូពិក។ ក្នុង​អំឡុងខែរដូវក្តៅ តាមធម្មតាសីតុណ្ហភាពឡើងលើសពី 30 អង្សាសេ។
- reference: Montevideo is in the subtropics; in the summer months, temperatures above +30°C are common.
- NLLB-1.3B (0.895): Montevideo is on the edge of the tropics, where temperatures typically exceed 30 degrees Celsius during the summer months.
- Llama-2-7B-chat (0.286): Montevideo 30 mg
- Llama-3.1-8B-Instruct (extra) (0.822): The Montevideo region is located adjacent to the Trópico region. In the midst of the hot season, the average temperature usually exceeds 30°C.
- Gemma-3-4B-it (0.867): The area of Montevideo is near the tropical region. During the summer months, the temperature usually rises and falls above 30 degrees Celsius.
- Qwen3-VL-8B (text-only) (0.804): The Montevideo region is located adjacent to the Trópico region. During the hot season, the temperature typically rises above 30°C.
- SEA-LION-v4-27B-IT (0.902): The Montevideo area is located near the tropics. During the summer months, the temperature usually rises above 30 °C.

**#364** (COMET spread 0.61)

- source: ជាទូទៅ ស្ដ្រីមាន​ទំនាក់​ទំនង​ស្និត​ស្នាល​ជាមួយ​គ្នា​ ក្លាយជា​ក្រុម​គ្រួសារ​ដ៏ធំដែលមានបងប្អូនស្រីនិង​កូនស្រី។​
- reference: The females are usually closely related to each other, being a large family of sisters and daughters.
- NLLB-1.3B (0.886): Women generally work closely together, forming a large family of sisters and daughters.
- Llama-2-7B-chat (0.302): The patient has a history of hypertension, diabetes, and hyperlipidemia. The patient's blood pressure is 160/100 mmHg, blood sugar is 200 mg/dL, and total cholesterol is 300 mg/dL. The patient has a history of smoking and excessive alcohol consumption. The patient's ECG shows ST segment elevation in leads II, III, and aVf, and the troponin level is elevated at 0.4 ng/mL. The patient has a history of myocardial infarction and coronary artery disease. The patient's echocardiogram shows left ventricular hypertrophy and decreased ejection fraction. The patient has a history of atrial fibrillation and is currently in sinus rhythm. The patient's creatinine level is 1.5 mg/dL and the estimated glomerular filtration rate is 30 mL/min/1.73 m2.
- Llama-3.1-8B-Instruct (extra) (0.904): Generally, women have close relationships with each other, becoming a large family group consisting of sisters and daughters.
- Gemma-3-4B-it (0.913): Generally, women who are closely related to each other form a large family with sisters and daughters.
- Qwen3-VL-8B (text-only) (0.901): Generally, women have close relationships with each other, forming large families that include sisters and daughters.
- SEA-LION-v4-27B-IT (0.807): Generally, women who have sexual relations with each other form large families with sisters and daughters.

**#498** (COMET spread 0.603)

- source: តាមប្រវត្តិសាស្រ្ត កសិករភាគច្រើនបានចូលរួមក្នុងកសិកម្មចិញ្ចឹមជីវិត ហើយនេះនៅតែជាករណីបន្តកើតមាននៅតាមបណ្ដាប្រទេសកំពុងអភិវឌ្ឍជាច្រើន។
- reference: Historically most farmers were engaged in subsistence agriculture and this is still the case in many developing nations.
- NLLB-1.3B (0.944): Historically, most farmers have engaged in subsistence agriculture, and this is still the case in many developing countries.
- Llama-2-7B-chat (0.341): The patient's blood pressure was measured at 140/90 mmHg during the examination. The blood pressure was recorded at 140/90 mmHg.
- Llama-3.1-8B-Instruct (extra) (0.901): According to historical records, most farmers have participated in subsistence farming to sustain life, and this is still a continuing case in many developing countries.
- Gemma-3-4B-it (0.848): Historically, most farmers have participated in animal husbandry, and this remains a continuing case occurring in many developing countries.
- Qwen3-VL-8B (text-only) (0.935): Historically, most farmers have been involved in subsistence farming, and this remains a prevalent case in many developing countries.
- SEA-LION-v4-27B-IT (0.920): According to history, most farmers have engaged in subsistence agriculture, and this remains a continuing case in many developing countries.

**#419** (COMET spread 0.599)

- source: កីឡាពេញនិយម រួមមានបាល់ទាត់ បាល់បោះ បាល់ទះ បាល់ទះលើទឹក កីឡាប្រកួតដាវ កីឡាបាល់ឱប ជិះកង់ វាយកូនបាល់លើទឹកកក វាយកូនគោលលើទឹកកក និងប្រណាំងរថយន្ត F1។
- reference: Popular sports include football, basketball, volleyball, water-polo, fencing, rugby, cycling, ice hockey, roller hockey and F1 motor racing.
- NLLB-1.3B (0.859): Popular sports include soccer, volleyball, volleyball, water polo, fencing, figure skating, cycling, ice hockey, ice hockey, and F1 racing.
- Llama-2-7B-chat (0.329): "The patient has a history of hypertension, hyperlipidemia, and diabetes. The patient's blood pressure is 160/100 mmHg, and the patient's fasting blood sugar is 200 mg/dL. The patient's body mass index (BMI) is 35 kg/m2, and the patient's waist circumference is 100 cm. The patient has a history of smoking and alcohol consumption. The patient's electrocardiogram (ECG) shows ST segment elevation in leads II, III, and aVL. The patient's echocardiogram shows left ventricular hypertrophy and left atrial enlargement. The patient's chest X-ray shows cardiomegaly. The patient's laboratory results show a high level of creatinine kinase (CK) and a low level of troponin I. The patient's urine output is 30 mL/hour. The patient's fluid balance is maintained with 500 m
- Llama-3.1-8B-Instruct (extra) (0.904): Popular sports include football, basketball, volleyball, water polo, fencing, badminton, horse riding, water skiing, and Formula 1 racing.
- Gemma-3-4B-it (0.802): Popular sports include football, volleyball, table tennis, water polo, knife fighting, hugging ball, cycling, water ball hitting, hitting targets on water, and Formula 1 racing.
- Qwen3-VL-8B (text-only) (0.896): Popular sports include football, basketball, volleyball, water polo, track and field, baseball, cycling, water skiing, wakeboarding, and Formula 1 racing.
- SEA-LION-v4-27B-IT (0.928): Popular sports include football, basketball, volleyball, water polo, fencing, handball, cycling, ice hockey, ice golf and F1 racing.

**#786** (COMET spread 0.598)

- source: ត្រីឆ្លាមពិតជាមានមែន ទោះជាយ៉ាងណាពួកវាកម្រមកខាំមនុស្សណាស់។ ត្រីឆ្លាមភាគច្រើនខ្លាចមនុស្សខ្លាំងណាស់ ហើយវាហែលចេញទៅឆ្ងាយពីមនុស្ស។
- reference: Sharks do exist, however they rarely attack humans. Most sharks are scared of humans and would swim away.
- NLLB-1.3B (0.855): There are whales, but they rarely catch people. Most whales are afraid of people, and they run away from people.
- Llama-2-7B-chat (0.319): "The patient has a history of hypertension and hyperlipidemia. The patient's blood pressure is 160/100 mmHg, and the patient's total cholesterol level is 300 mg/dL. The patient's triglyceride level is 200 mg/dL, and the patient's HDL cholesterol level is 40 mg/dL. The patient's LDL cholesterol level is 160 mg/dL, and the patient's VLDL cholesterol level is 100 mg/dL. The patient's fasting blood sugar level is 120 mg/dL, and the patient's HbA1c level is 7.5%. The patient's creatinine level is 1.5 mg/dL, and the patient's eGFR is 60 mL/min/1.73m2. The patient's urine output is 400 m
- Llama-3.1-8B-Instruct (extra) (0.843): Fish are indeed carnivores, regardless of the fact that they often attack humans. Most fish are very afraid of humans and swim away from them.
- Gemma-3-4B-it (0.844): Plaice are indeed real, though they rarely bite humans at all. Most plaice are very afraid of humans, and they tend to swim away from people.
- Qwen3-VL-8B (text-only) (0.831): The sea bass is indeed real, but they are very shy. Most sea bass are extremely afraid of humans, and they swim away from people.
- SEA-LION-v4-27B-IT (0.917): Sharks are indeed real, however they rarely bite humans. Most sharks are very afraid of humans and swim away from people.

## Largest disagreements: Lao (FLORES)

**#697** (COMET spread 0.655)

- source: ບັນດາຫມູ່ເກາະອາຟຼິກກາຕາເວັນອອກ ແມ່ນຢູ່ໃນມະຫາສະໝຸດອິນເດຍ ນອກຝັ່ງທະເລທາງຕາເວັນອອກຂອງອາຟຼິກກາ.
- reference: The East African Islands are in the Indian Ocean off the eastern coast of Africa.
- NLLB-1.3B (0.966): The East African Islands are in the Indian Ocean off the eastern coast of Africa.
- Llama-2-7B-chat (0.311): The patient has a history of hypertension, hyperlipidemia, and diabetes mellitus. The patient's blood pressure is 180/100 mmHg, and the patient's fasting blood glucose level is 300 mg/dL. The patient's total cholesterol level is 300 mg/dL, and the patient's triglyceride level is 200 mg/dL. The patient has a history of smoking and excessive alcohol consumption. The patient's body mass index (BMI) is 35 kg/m2, and the patient's waist circumference is 120 cm. The patient has a history of cardiovascular disease and has been prescribed medications for hypertension, hyperlipidemia, and diabetes mellitus.
- Llama-3.1-8B-Instruct (extra) (0.612): Several species of aquatic animals, such as fish, are found in the Indian Ocean outside the western coast of Africa.
- Gemma-3-4B-it (0.902): The African islands of the East are in the Indian Ocean, off the western coast of Africa.
- Qwen3-VL-8B (text-only) (0.901): The African island nations are located in the Indian Ocean, off the southeastern coast of Africa.
- SEA-LION-v4-27B-IT (0.891): The Comoros Islands are in the Indian Ocean, off the east coast of Africa.

**#357** (COMET spread 0.632)

- source: ກົງລໍ້ໄດ້ປ່ຽນແປງໂລກດ້ວຍວິທີທີ່ໜ້າເຫຼືອເຊື່ອ. ສິ່ງທີ່ຍິ່ງໃຫຍ່ທີ່ສຸດທີ່ກົງລໍ້ໄດ້ຊ່ວຍເຮົາກໍຄືເຮັດໃຫ້ການຄົມມະນາຄົມຂົນສົ່ງນັ້ນງ່າຍ ແລະ ໄວຂຶ້ນຫຼາຍ.
- reference: The wheel has changed the world in incredible ways. The biggest thing that the wheel has done for us is given us much easier and faster transportation.
- NLLB-1.3B (0.888): The wheels have changed the world in incredible ways, and the greatest thing that they've helped us with is that they've made transportation easier and faster.
- Llama-2-7B-chat (0.352): The patient has a history of hypertension, hyperlipidemia, and diabetes mellitus. The patient's blood pressure is 180/100 mmHg, and the patient's fasting blood sugar is 300 mg/dL. The patient's body mass index (BMI) is 35 kg/m2, and the patient's waist circumference is 120 cm. The patient has a history of smoking and excessive alcohol consumption. The patient's electrocardiogram (ECG) shows ST segment elevation in leads II, III, and aVf, and the patient's echocardiogram shows left ventricular hypertrophy. The patient's chest X-ray shows cardiomegaly, and the patient's laboratory tests show elevated levels of troponin I and creatine kinase MB.
- Llama-3.1-8B-Instruct (extra) (0.726): The climate has changed the world with a sense of uncertainty. The biggest thing that climate change helps us is to make the transportation system faster and more convenient.
- Gemma-3-4B-it (0.256): Kongloe dai biian plian pong lok duai wi thi thi na leua cheua. Sing thi ying lai thi kongloe dai chuai hao krao het kan khom mana nak khon song nan ngai lae wai khun lai.
- Qwen3-VL-8B (text-only) (0.769): Gong Lao has changed the world in a remarkable way. The greatest thing Gong Lao has helped us with is making the transportation of goods much easier and faster.
- SEA-LION-v4-27B-IT (0.881): Wheels have changed the world in an unbelievable way. The greatest thing wheels have helped us with is making communication and transportation easier and much faster.

**#760** (COMET spread 0.627)

- source: Montevideo ແມ່ນຢູ່ໃນເຂດຮ້ອນຊຸ່ມ; ໃນເດືອນທີ່ເປັນລະດູຮ້ອນອຸນຫະພູມສູງກວ່າ + 30 ອົງສາ ແມ່ນເປັນເລື່ອງທົ່ວໄປ.
- reference: Montevideo is in the subtropics; in the summer months, temperatures above +30°C are common.
- NLLB-1.3B (0.933): Montevideo is in the humid tropics; in the summer months temperatures above +30 degrees are common.
- Llama-2-7B-chat (0.306): Montevideo 100mg/mL; 30ml/mL.
- Llama-3.1-8B-Instruct (extra) (0.681): Montevideo is located in the Maldonado Department; in the month that is the southernmost high tide is more than +30 degrees.
- Gemma-3-4B-it (0.873): Montevideo is in a humid zone; during the hot months, the temperature is higher than +30 degrees is common.
- Qwen3-VL-8B (text-only) (0.911): Montevideo is located in a humid tropical zone; in the months of the hot season, temperatures above +30 degrees Celsius are common.
- SEA-LION-v4-27B-IT (0.899): Montevideo is in a tropical climate; in the months that are summer, temperatures higher than +30 degrees are common.

**#194** (COMET spread 0.625)

- source: ທ່ານ ນາງ ແບັກມານ (Bachmann) ຜູ້ທີ່ໄດ້ຮັບໄຊຊະນະຈາກຄະແນນຜົນສຳຫຼວດ Ames Straw ໃນເດືອນ ສິງຫາ ໄດ້ຕັດສິນໃຈຢຸດຕິຂະບວນການຫາສຽງຂອງລາວ.
- reference: Bachmann, who won the Ames Straw Poll in August, decided to end her campaign.
- NLLB-1.3B (0.898): Bachmann, who won the Ames Straw poll in August, decided to suspend his campaign.
- Llama-2-7B-chat (0.311): Bachmann (Ames Straw) test for detecting antibodies in the blood, including:
* ທ່ານ (Glomerular filtration rate)
* ນາງ (Serum creatinine)
* ແບັກມານ (Blood urea nitrogen)
* ຜູ້ທີ່ໄດ້ (Proteinuria)
* ໄດ້ຕັດ (Renal function)
- Llama-3.1-8B-Instruct (extra) (0.823): Ms. Bachmann, the winner of the Ames Straw Poll in August, has been criticized for her stance on the issue.
- Gemma-3-4B-it (0.819): Ms. Bachmann, who won by the poll score of Ames Straw in August, has decided to halt her campaign.
- Qwen3-VL-8B (text-only) (0.839): Ms. Bachmann, who won the Ames Straw Poll vote in August, has decided to suspend her campaign for votes.
- SEA-LION-v4-27B-IT (0.936): Ms. Bachmann, who won the Ames Straw Poll in August, has decided to end her campaign.

**#769** (COMET spread 0.622)

- source: Apia ແມ່ນຖືກສ້າງຕັ້ງຂຶ້ນໃນຊຸມປີ 1850 ແລະ ເປັນນະຄອນຫຼວງຢ່າງເປັນທາງການຂອງປະເທດຊາມົວຕັ້ງແຕ່ປີ 1959.
- reference: Apia was founded in the 1850s and has been the official capital of Samoa since 1959.
- NLLB-1.3B (0.973): Apia was founded in the 1850s and has been the official capital of Samoa since 1959.
- Llama-2-7B-chat (0.351): Apia 1850 mg oral tablet taken once daily for 1959 days.
- Llama-3.1-8B-Instruct (extra) (0.922): Apiam was established in the year 1850 and has been the capital of the country of Samoa since 1959.
- Gemma-3-4B-it (0.907): Apia was established in the 1850s and has been the official capital of the country of Savamahtung since 1959.
- Qwen3-VL-8B (text-only) (0.956): Apia was established in the 1850s and has been the official capital of Samoa since 1959.
- SEA-LION-v4-27B-IT (0.956): Apia was established in the 1850s and has been the official capital of Samoa since 1959.

## Largest disagreements: Vietnamese (FLORES)

**#621** (COMET spread 0.528)

- source: Ngày nay, những loại côn trung không thể gập cánh lại chỉ có chuồn chuồn và những con phù du.
- reference: Today, the only insects that cannot fold back their wings are dragon flies and mayflies.
- NLLB-1.3B (0.716): Today, the only midges that can't fold their wings are the finches and the hedgehogs.
- Llama-2-7B-chat (0.349): Today, only chuồn chuồn and phù du can be gathered.
- Llama-3.1-8B-Instruct (extra) (0.729): Today, only dragonflies and mayflies have non-foldable wings.
- Gemma-3-4B-it (0.599): Nowadays, those types of mites cannot fold their wings except for dragonflies and plankton.
- Qwen3-VL-8B (text-only) (0.877): Today, the only insects that cannot fold their wings are dragonflies and mayflies.
- SEA-LION-v4-27B-IT (0.838): Today, the insect types that cannot fold their wings back include dragonflies and mayflies.

**#58** (COMET spread 0.399)

- source: Các chỉ trích tự do của nỗ lực tái thiết tập trung vào việc trao các hợp đồng tái thiết cho những người có thông tin nội bộ của Washington.
- reference: Liberal criticism of the reconstruction effort has focused on the awarding of reconstruction contracts to perceived Washington insiders.
- NLLB-1.3B (0.880): Liberal criticism of the reconstruction effort focused on awarding reconstruction contracts to people with inside information of Washington.
- Llama-2-7B-chat (0.481): The user's text in Vietnamese:
Các chỉ trích tự do của nỗ lực tái thiết tập trung vào việc trao các hợp đồng tái thiết cho những người có thông tin nội bộ của Washington.
English translation:
The free criticism of the concentration of efforts on providing contracts for those with internal information of Washington.
- Llama-3.1-8B-Instruct (extra) (0.869): Critics of the reconstruction effort have focused on awarding reconstruction contracts to those with Washington insiders.
- Gemma-3-4B-it (0.825): Criticisms of the free effort of reconstruction focused on awarding reconstruction contracts to those with inside information from Washington.
- Qwen3-VL-8B (text-only) (0.870): Critics of the reconstruction efforts focus on the awarding of reconstruction contracts to individuals with inside information from Washington.
- SEA-LION-v4-27B-IT (0.827): The free criticisms of the reconstruction effort focus on awarding reconstruction contracts to those with Washington insider information.

**#413** (COMET spread 0.374)

- source: Văn hóa thiểu số thường biến mất mà không để lại bằng chứng lịch sử xác đáng và không được công nhận là nền văn minh riêng.
- reference: Minor cultures often vanish without leaving relevant historic evidence and fail to be recognized as proper civilizations.
- NLLB-1.3B (0.906): Minority cultures often disappear without leaving valid historical evidence and without being recognized as a distinct civilization.
- Llama-2-7B-chat (0.541): The user's text in Vietnamese: "Văn hóa thiểu số thường biến mất mà không để lại bằng chứng lịch sử xác đáng và không được công nhận là nền văn minh riêng."
English translation: "Cultural heritage often disappears without leaving any historical evidence and is not recognized as a distinct cultural heritage."
- Llama-3.1-8B-Instruct (extra) (0.856): Minority cultures often disappear without leaving a historically significant and recognized evidence of a separate civilization.
- Gemma-3-4B-it (0.914): Minority cultures often disappear without leaving credible historical evidence and are not recognized as distinct civilizations.
- Qwen3-VL-8B (text-only) (0.911): Minority cultures often disappear without leaving adequate historical evidence and are not recognized as distinct civilizations.
- SEA-LION-v4-27B-IT (0.901): Minority cultures often disappear without leaving verifiable historical evidence and are not recognized as a separate civilization.

**#6** (COMET spread 0.365)

- source: Ông đã lắp môt chuông cửa WiFi, ông cho biết.
- reference: He built a WiFi door bell, he said.
- NLLB-1.3B (0.845): You installed a Wi-Fi doorbell, you said.
- Llama-2-7B-chat (0.570): The user's text in Vietnamese is: "Ông đã lắp môt chuông cửa WiFi, ông cho biết."
The English translation is: "He has installed the WiFi door lock, he informed."
- Llama-3.1-8B-Instruct (extra) (0.918): He has installed a WiFi doorbell, he said.
- Gemma-3-4B-it (0.935): He installed a WiFi doorbell, he said.
- Qwen3-VL-8B (text-only) (0.918): He has installed a WiFi doorbell, he said.
- SEA-LION-v4-27B-IT (0.935): He installed a WiFi doorbell, he said.

**#845** (COMET spread 0.363)

- source: Đầu tiên, hầu hết người cưỡi ngựa mang ủng có gót cao và đế trơn, khá hẹp.
- reference: First, most riders wear riding boots with a heel and a smooth, quite narrow, sole.
- NLLB-1.3B (0.792): First, most riders wear boots with high heels and smooth, rather narrow heels.
- Llama-2-7B-chat (0.479): First, most people who ride horses have a high and wide forehead, quite broad.
- Llama-3.1-8B-Instruct (extra) (0.775): Firstly, most horse riders wear boots with high heels and slippery soles, quite narrow.
- Gemma-3-4B-it (0.819): First, most horse riders wear high-heeled boots with a smooth sole and quite narrow.
- Qwen3-VL-8B (text-only) (0.842): First, most horse riders wear boots with high heels and smooth soles, which are relatively narrow.
- SEA-LION-v4-27B-IT (0.817): First, most horseback riders wear boots with high heels and smooth soles, quite narrow.

## Largest disagreements: Khmer medical Qs

**#182** (COMET spread 0.677)

- source: ការបែកជើងត្រូវបានកំណត់យ៉ាងដូចម្តេចក្នុងពាក្យវេជ្ជសាស្ត្រ ហើយអ្វីដែលបណ្តាលឲ្យមានការប៉ះពាល់?
- reference: How is a fracture defined in medical terms, and what is a contusion caused by?
- NLLB-1.3B (0.874): How is leg fracture defined in medical terminology, and what causes it to affect?
- Llama-2-7B-chat (0.499): "Has the patient's blood sugar level been checked recently?")
- Llama-3.1-8B-Instruct (extra) (0.239): Fracture ត្រូវបានកំណត់យ៉ាងដូចជាការបែកខ្សែក្រុងនៃស្បៃក្រុងដែលបែកខ្ញែកនៅក្នុងស្បៃក្រុង ឬការបែកខ្សែក្រុងនៃស្បៃក្រុងដែលបែកខ្ញែកនៅក្នុងស្បៃក្រុង ឬការបែកខ្សែក្រុងនៃស្បៃក្រុងដែលបែកខ្ញែកនៅក្នុងស្បៃក្រុង ឬការបែកខ្សែក្រុងនៃស្បៃក្រុងដែលបែកខ្ញែកនៅក្ន
- Gemma-3-4B-it (0.712): A postpartum hemorrhage is defined in medical terms and what causes it?
- Qwen3-VL-8B (text-only) (0.916): How is foot fracture defined in medical terms, and what causes it?
- SEA-LION-v4-27B-IT (0.853): How is foot drop defined in medical terms, and what causes impairment?

**#156** (COMET spread 0.589)

- source: ស្ត្រីអាយុ ៥៧ ឆ្នាំម្នាក់បានមកបង្ហាញពីការឈឺចាប់ផ្នែកពោះវៀនជាបន្តបន្ទាប់ជាច្រើនឆ្នាំ និងការកើតជំងឺច្របូកច្របល់ ដែលមានលក្ខណៈដោយមានការត្រូវការជាតិអាថ៌កំបាំងកើនឡើង និងអារម្មណ៍ថាបានបញ្ចប់ការបញ្ចេញអាថ៌កំបាំងមិនពេញលេញបន្ទាប់ពីការបញ្ចេញ។ រយៈពេលចុងក្រោយនៃរដូវស្រ្តីរបស់នាងគឺ ៦ ឆ្នាំមុន ហើយនាងបានមានការបញ្ជូនកូនតាមផ្លូវភេទដោយគ្មានបញ្ហា ៣ ដង។ ក្នុងអំឡុងពេលពិនិត្យរាងកាយ គេបានសង្កេតឃើញថាចង្កូតភេទខាងក្រោយមានការបង្ហូរពេលធ្វើចលនាវ៉ាល់សាល់វ៉ា។ រចនាសម្ព័ន្ធអាណាតូមីណាមួយដែលមានឱកាសខ្សោយបំផុត ដែលនាំឲ្យមានរោគសញ្ញានេះគឺអ្វី?
- reference: A 57-year-old woman presents with several years of recurrent pelvic pain and constipation, characterized by increased fecal urgency and a sensation of incomplete evacuation after defecation. Her last menstrual period was 6 years ago, and she has had three uncomplicated vaginal deliveries. During a physical examination, the posterior vaginal wall is observed to bulge during a Valsalva maneuver. Which anatomical structure is most likely weakened, leading to this patient's symptoms?
- NLLB-1.3B (0.713): A 57-year-old woman has come to reveal years of persistent abdominal pain and confusion disorder, characterized by an increased need for secrecy and a feeling of having completed an incomplete post-release secrecy. Her last menstrual period was six years ago, and she has had three uncomplicated miscarriages. During the body examination, it was observed that the rear wheel was leaking during the Wal-Salva movement. What anatomical structure has the least chance of causing this syndrome?
- Llama-2-7B-chat (0.566): "The patient has been experiencing fever for 3 days, with a temperature of 38.5 degrees Celsius. The patient has been taking paracetamol, but the fever has not subsided. The patient has also been experiencing body aches and fatigue. The patient's medical history includes hypertension, diabetes, and hyperlipidemia. The patient has been smoking for 10 years and drinking alcohol for 5 years. The patient has not been compliant with medication in the past. The patient's family history includes a history of cardiovascular disease. The patient's social history includes a history of stress and anxiety. The patient's review of systems is unremarkable. The patient's physical examination reveals a temperature of 38.5 degrees Celsius, with tachycardia and tachypnea. The patient's laboratory results show an elevated white blood cell count and an elevated C-reactive protein level. The patient's chest X-ray shows a small nodule in the right lung. The patient's electrocardiogram shows a sinus tachycardia. The patient's blood tests show a normal blood sugar level and a normal lipid profile. The patient's urine test shows a normal urinalysis. The patient's abdominal examination shows a normal abdomen. The patient's neurological examination shows a normal neurological examination. The patient's musculoskeletal examination shows a normal musculoskeletal examination. The patient's psychiatric examination
- Llama-3.1-8B-Instruct (extra) (0.255): ស្ត្រីអាយុ ៥៧ ឆ្នាំម្នាក់បានមកបង្ហាញពីការឈឺចាប់ផ្នែកពោះវៀនជាបន្តបន្ទាប់ជាច្រើនឆ្នាំ និងការកើតជំងឺច្របូកច្របល់ ដែលមានលក្ខណៈដោយមានការត្រូវការជាតិអាថ៌កំបាំងកើនឡើង និងអារម្មណ៍ថាបានបញ្ចប់ការបញ្ចេញអាថ៌កំបាំងមិនពេញលេញបន្ទាប់ពីការបញ្ចេញ។ រយៈពេលចុង
- Gemma-3-4B-it (0.844): A 57-year-old woman presented with recurrent abdominal pain for many years and constipation, characterized by an increased need for bowel movements and a feeling of incomplete evacuation after defecation. Her last menstrual period was 6 years prior, and she had 3 successful pregnancies via vaginal delivery. During physical examination, a posterior vaginal bleed was noted during a Valsalva maneuver. What is the most anatomically vulnerable structure that leads to this symptom?
- Qwen3-VL-8B (text-only) (0.843): A 57-year-old woman presented with chronic pelvic pain for many years and symptoms of menopausal disorder, characterized by increased need for fluids and a sensation of incomplete bladder emptying after urination. Her last menstrual period was 6 years ago, and she has had three uncomplicated vaginal deliveries. During physical examination, posterior vaginal wall prolapse was observed during straining. Which anatomical structure is most likely to be the weakest, leading to these symptoms?
- SEA-LION-v4-27B-IT (0.820): A 57-year-old female presented with recurrent pelvic pain for many years and constipation, characterized by increased urgency and a sensation of incomplete evacuation following a bowel movement. Her last menstrual period was 6 years ago, and she has had 3 vaginal deliveries without complications. On physical examination, rectovaginal examination revealed rectocele with prolapse on Valsalva maneuver. What is the least likely anatomical structure contributing to these symptoms?

**#31** (COMET spread 0.583)

- source: អត្ថបទណាខ្លះក្នុងរដ្ឋធម្មនុញ្ញដែលធានាអត្ថិភាពសិទ្ធិរបស់កុមារ?
- reference: Which articles of the constitution guarantee child rights?
- NLLB-1.3B (0.934): What are some constitutional provisions that guarantee children's rights?
- Llama-2-7B-chat (0.383): What are the side effects of the drug អត្ថបទណា (Atropine) when used for treating ក្នុងរដ្ឋធម្មនុញ្ញ (Parkinson's disease)?
- Llama-3.1-8B-Instruct (extra) (0.925): Some articles in the constitution that guarantee the rights of children.
- Gemma-3-4B-it (0.966): Which articles in the Constitution guarantee the rights of children?
- Qwen3-VL-8B (text-only) (0.939): Which provisions in the Constitution ensure the protection of children's rights?
- SEA-LION-v4-27B-IT (0.939): Which articles in the Constitution guarantee the existence of children's rights?

**#63** (COMET spread 0.566)

- source: ក្នុងប្រជាជនមួយដែលការសាកល្បងស្ក្រីនបានកំណត់ឱ្យមានមនុស្ស 90 នាក់ជាសកម្មសម្រាប់ជំងឺទឹកនោមផ្អែមចេញពី 1000 នាក់ ហើយការសាកល្បងវិនិច្ឆ័យស្តង់ដ៍ប្រាក់បានកំណត់ឱ្យមានមនុស្ស 100 នាក់ជាសកម្ម តើអត្រាសេនស៊ីតិវីតីនៃការសាកល្បងស្ក្រីនគឺប៉ុន្មាន?
- reference: In a population where a screening test identified 90 individuals as positive for diabetes out of 1000, and the Gold standard diagnostic test identified 100 individuals as positive, what is the sensitivity of the screening test?
- NLLB-1.3B (0.884): In a population where the screen test identified 90 people as active for diabetes out of 1000, and the silver standard diagnostic test identified 100 people as active, what is the sensitivity ratio of the screen test?
- Llama-2-7B-chat (0.618): "How many people have been infected with COVID-19 in Cambodia as of today, and how many have died from the virus? Also, how many people have been vaccinated with the COVID-19 vaccine in Cambodia as of today, and how many doses have been administered?"
I hope this helps! Let me know if you have any other questions.
- Llama-3.1-8B-Instruct (extra) (0.326): ក្នុងប្រជាជនមួយដែលការសាកល្បងស្ក្រីនបានកំណត់ឱ្យមានមនុស្ស 90 នាក់ជាសកម្មសម្រាប់ជំងឺទឹកនោមផ្អែមចេញពី 1000 នាក់ ហើយការសាកល្បងវិនិច្ឆ័យស្តង់ដ៍ប្រាក់បានកំណត់ឱ្យមានមនុស្ស 100 នាក់ជាសកម្ម តើអត្រាសេនស៊ីតិវីតីនៃការសាកល្បងស្ក្រីនគឺប៉ុន្មាន? អត្រាសេនស៊ីតិវីតីន
- Gemma-3-4B-it (0.876): In a population where screening identified 90 out of 1000 people as active for diabetes, and standard diagnostic testing identified 100 out of 100 people as active, what is the sensitivity rate of the screening test?
- Qwen3-VL-8B (text-only) (0.756): In a population where the trial for drug X was designed to enroll 90 out of 1000 people with diabetes, and the standard trial for drug Y was designed to enroll 100 people, what is the sensitivity rate of the trial for drug X?
- SEA-LION-v4-27B-IT (0.892): In a population where a screening test identified 90 people as active for diabetes out of 1000 people, and a standard gold test identified 100 people as active, what is the sensitivity of the screening test?

**#91** (COMET spread 0.541)

- source: អ្វីខ្លះជាគុណសម្បត្តិសំខាន់ពីរនៃអូទីសមកុមារ ដែលពាក់ព័ន្ធនឹងការអភិវឌ្ឍន៍ប្រព័ន្ធប្រសាទនិងឥទ្ធិពលសង្គម-សេដ្ឋកិច្ចក្រៅ?
- reference: What are two key characteristics of infantile autism related to neurobehavioural development and external socio-economic influences?
- NLLB-1.3B (0.911): What are the two main characteristics of childhood autism, related to neural development and external socio-economic influences?
- Llama-2-7B-chat (0.474): Can you tell me the side effects of the drug 'Ciprofloxacin'?
- Llama-3.1-8B-Instruct (extra) (0.369): គុណសម្បត្តិសំខាន់ពីរនៃអូទីសមកុមារ ដែលពាក់ព័ន្ធនឹងការអភិវឌ្ឍន៍ប្រព័ន្ធប្រសាទនិងឥទ្ធិពលសង្គម-សេដ្ឋកិច្ចក្រៅ គឺជា ការរីករាយនិងការសម្រេចចិត្តរបស់កុមារ និង ការរីករាយនិងការសម្រេចចិត្តរបស់កុមារក្នុងសង្គម-សេដ្ឋកិច្ចក្រៅ។
- Gemma-3-4B-it (0.659): What are the two main benefits of Otesom Kamay that relate to nervous system development and extra-social-economic impact?
- Qwen3-VL-8B (text-only) (0.755): What are two key advantages of the OIOS for children, related to the development of the nervous system and external socio-economic impacts?
- SEA-LION-v4-27B-IT (0.806): What are the two key benefits of childhood obesity related to neurological development and external socio-economic impacts?

