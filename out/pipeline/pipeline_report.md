# Pipeline report

## Stages

| # | stage | folder | status | finished | host | time (s) |
|---|---|---|---|---|---|---|
| 1 | translate | stage1_translate/ | done | 2026-11-26 12:09:52 | pipeline-translate-0-0 | 57.1 |
| 2 | extract | stage2_extract/ | done | 2026-11-26 13:10:39 | haas034.ds-a3-r02.cct.rcp.epfl.ch | 33.6 |
| 3 | verify | stage3_verify/ | done | 2026-11-26 13:10:49 | haas034.ds-a3-r02.cct.rcp.epfl.ch | 10.0 |
| 4 | chunk | stage4_chunk/ | done | 2026-11-27 02:51:11 | haas034.ds-a3-r02.cct.rcp.epfl.ch | 20.9 |
| 5 | validate | stage5_validate/ | done | 2026-11-27 02:51:47 | haas034.ds-a3-r02.cct.rcp.epfl.ch | 35.2 |

## Stage 1: translation

Model facebook/nllb-200-1.3B. Non-English text was found on PDF pages **1, 4, 5, 6, 266** (44 unique segments). Segments per page: p1: 8 khm/pdf_text; p4: 13 khm/chandra; p5: 9 khm/chandra; p6: 2 khm/chandra; p266: 12 khm/pdf_text.

Translation counters: {'number_retry': 1, 'segments_khm': 44, 'sentences_khm': 45}.
Segments that lost a number in translation: [['seg_0015', 4, ['1']]]. Segments whose source text is itself repetitive (Chandra loops): 1. Vietnamese-looking lines rejected (fewer than 3 Vietnamese words): 0.

Translated blocks (content replaced by the English text; original in `metadata.original_text`):

| block | page | type | lang | was | flags | original | English |
|---|---|---|---|---|---|---|---|
| chunk_00000 | 1 | text | khm | pdf_text | withheld_unreliable | ## ព្រះរាជាណាចព្ររម្ពុជា ជាតិ សាសនា ព្រះម្ហារសព្ត ## 3 ភាគ ១… | ## The Kingdom of Cambodia The nation, the religion, the temple ## 3 [Khmer text, machine … |
| chunk_00004 | 4 | text | khm | chandra | withheld_unreliable | ព្រះរាជាណាចក្រភាពជា ជាតិ សាធារណៈ ព្រះរាជាណាចក្រភាព ព្រះមហាក្… | The Kingdom of God is the Kingdom of the heavens and the earth. [Khmer text, machine trans… |
| chunk_00005 | 4 | text | khm | chandra | numbers_lost, withheld_unreliable | ### ផ្អែកទី១ លទ្ធផល និង ការវាយតម្លៃ - ប្រព័ន្ធប្រមូលទិន្នន័យ… | ### [Khmer text, machine translation withheld (unreliable); numbers in it: 1] - The data c… |
| chunk_00006 | 4 | text | khm | chandra |  | ទីតាំង: ផ្នែកទី១ នៃ ការណាត្រប្រមូលទិន្នន័យ និង ការវាយតម្លៃ ន… | Location: Part 1 of data collection and evaluation and data collection Location: Part 1 of… |
| chunk_00007 | 4 | text | khm | chandra |  | ទីតាំង: ផ្នែកទី១ នៃ ការណាត្រប្រមូលទិន្នន័យ និង ការវាយតម្លៃ ន… | Location: Part 1 of data collection and evaluation and data collection Location: Part 1 of… |
| chunk_00008 | 4 | text | khm | chandra |  | ទីតាំង: ផ្នែកទី១ នៃ ការណាត្រប្រមូលទិន្នន័យ និង ការវាយតម្លៃ ន… | Location: Part 1 of data collection and evaluation and data collection Location: Part 1 of… |
| chunk_00009 | 4 | text | khm | chandra |  | ទីតាំង: ផ្នែកទី១ នៃ ការណាត្រប្រមូលទិន្នន័យ និង ការវាយតម្លៃ ន… | Location: Part 1 of data collection and evaluation and data collection Location: Part 1 of… |
| chunk_00010 | 4 | algorithm | khm | chandra | numbers_lost, withheld_unreliable | ព្រះរាជាណាចក្រភាពជា ជាតិ សាធារណៈ ព្រះរាជាណាចក្រភាព ព្រះមហាក្… | The Kingdom of God is the Kingdom of the heavens and the earth. [Khmer text, machine trans… |
| chunk_00011 | 5 | text | khm | chandra | withheld_unreliable | ស្រាវជ្រាវ រូបភាព 1. ក្រុមហ៊ុនផលិតថ្នាំ ដែលបានបង្កើតឡើងដើម្ប… | [Khmer text, machine translation withheld (unreliable)] The picture 1. [Khmer text, machin… |
| chunk_00012 | 6 | text | khm | chandra | source_repetitive, withheld_unreliable | ## សាលារាជធានីភ្នែក វាយបញ្ចូលព័ត៌មានដែលអាចប្រើប្រាស់បានដើម្ប… | ## [Khmer text, machine translation withheld (unreliable)] [Khmer text, machine translatio… |
| chunk_00706 | 266 | table | khm | mmore_table+pdf_text | withheld_unreliable | \| Latin name \| English name \| Cambodian name \| \|---\|---\|---\|… | \| Latin name \| English name \| Cambodian name \| \|---\|---\|---\| \| Ophiophagus hannah \| King c… |

Quality gate (stage 2): a translation is used only if the chrF of its back-translation against the source is >= 60 and no number was lost; otherwise `placeholder`. Used: 18, withheld: 26.

| seg | page | original | NLLB output | back-translation | chrF | used |
|---|---|---|---|---|---|---|
| seg_0000 | 1 | ព្រះរាជាណាចព្ររម្ពុជា | The Kingdom of Cambodia | ព្រះរាជាណាចក្រ កម្ពុជា | 66.1 | yes |
| seg_0001 | 1 | ជាតិ សាសនា ព្រះម្ហារសព្ត | The nation, the religion, the temple | ជាតិ សាសនា ព្រះវិហារ | 60.7 | yes |
| seg_0002 | 1 | ភាគ ១ | Part 1 | ផ្នែកទី 1 | 5.2 | no |
| seg_0003 | 1 | នាយរដ្ឋានសសវាសុខភារ | The head of the National Security Council | ប្រធាន ក្រុមប្រឹក្សា សន្តិសុខ … | 14.3 | no |
| seg_0004 | 1 | ធ្នូ ២០២៥ | December 2025 | ខែធ្នូ ឆ្នាំ ២០២៥ | 20.2 | no |
| seg_0005 | 1 | ម្គគុសទេសរ៍រាបាលគលីនិរ | In the first century C.E., the Greek city of Magdala was the capital o… | [រូបភាព នៅ ទំព័រ ១៦] | 4.8 | no |
| seg_0006 | 1 | សេជ្ជសាស្រសតទូសៅ | In the meantime, I'm trying to find a way to make it work. | ទន្ទឹម នឹង នេះ ខ្ញុំ កំពុង ព្យ… | 4.1 | no |
| seg_0007 | 1 | ផ្ននរ | The tomb | ផ្នូរ | 32.7 | no |
| seg_0008 | 4 | ព្រះរាជាណាចក្រភាពជា | The Kingdom of God is the Kingdom of the heavens and the earth. | ព្រះ រាជាណាចក្រ នៃ ព្រះ ជាម្ចា… | 66.6 | yes |
| seg_0009 | 4 | ជាតិ សាធារណៈ ព្រះរាជាណាចក្រភាព | The nation, the people, the kingdom | ប្រទេសជាតិ ប្រជាជន ព្រះរាជាណាច… | 51.6 | no |
| seg_0010 | 4 | ព្រះមហាក្សត្របារាំង | The King of France | ព្រះមហាក្សត្រ នៃ ប្រទេស បារាំង | 76.3 | yes |
| seg_0011 | 4 | ថ្ងែ 04 ខែ ឧសភា \| ឆ្នាំ | May 4th. | ថ្ងៃទី៤ ខែឧសភា | 29.2 | no |
| seg_0012 | 4 | ព្រះរាជា | The Kingdom | ព្រះរាជាណាចក្រ | 81.4 | yes |
| seg_0013 | 4 | គ្រូ | Teacher | គ្រូបង្រៀន | 66.2 | yes |
| seg_0014 | 4 | សាមគ្គីរដ្ឋបាលសុខាភិបាល និងអង្គការសុខាភិ… | Health authorities and health organizations | អាជ្ញាធរ សុខាភិបាល និង អង្គការ… | 68.1 | yes |
| seg_0015 | 4 | ផ្អែកទី១ លទ្ធផល និង ការវាយតម្លៃ | Based on results and evaluation | ផ្អែកលើលទ្ធផល និងការវាយតម្លៃ | 78.5 | no |
| seg_0016 | 4 | ប្រព័ន្ធប្រមូលទិន្នន័យ: ការណាត្រប្រមូលទិ… | The data collection system: the data collection interface | ប្រព័ន្ធប្រមូលទិន្នន័យ: ប្រព័ន… | 76.5 | yes |
| seg_0017 | 4 | ប្រព័ន្ធប្រមូលទិន្នន័យ: ការណាត្រប្រមូលទិ… | Data collection systems: data collection and evaluation and data colle… | ប្រព័ន្ធ ប្រមូល ទិន្នន័យ: ប្រម… | 69.3 | yes |
| seg_0018 | 4 | អាការៈ ផ្នែកទី១ នៃ ការណាត្រប្រមូលទិន្នន័… | A sense of the 1 part of data collection and evaluation and data colle… | ការយល់ដឹងអំពីផ្នែកទី 1 នៃការប្… | 76.1 | yes |
| seg_0019 | 4 | ទីតាំង: ផ្នែកទី១ នៃ ការណាត្រប្រមូលទិន្នន… | Location: Part 1 of data collection and evaluation and data collection | ទីតាំង: ផ្នែកទី 1 នៃការប្រមូលទ… | 84.5 | yes |
| seg_0020 | 4 | ទីតាំង: ផ្នែកទី១ នៃ ការណាត្រប្រមូលទិន្នន… | Location: Part 1 of the data collection and evaluation | ទីតាំង: ផ្នែកទី 1 នៃការប្រមូលទ… | 88.4 | yes |
| seg_0021 | 5 | ស្រាវជ្រាវ | How can we do this? | តើ យើង អាច ធ្វើ បែប នេះ បាន យ៉… | 5.6 | no |
| seg_0022 | 5 | រូបភាព | The picture | រូបភាព | 100.0 | yes |
| seg_0023 | 5 | ក្រុមហ៊ុនផលិតថ្នាំ ដែលបានបង្កើតឡើងដើម្បី… | Pharmaceutical companies that were created to help patients | ក្រុមហ៊ុន ផលិត ឱសថ ដែល ត្រូវ ប… | 59.6 | no |
| seg_0024 | 5 | ដែលជាមូលដ្ឋានសម្រាប់ការស្រាវជ្រាវ | It's the foundation for research. | វា ជា មូលដ្ឋាន សម្រាប់ ការស្រា… | 90.1 | yes |
| seg_0025 | 5 | ការស្រាវជ្រាវ: មានការស្រាវជ្រាវដែលបានបង្… | Research: There is research that is designed to help patients, that is… | ការស្រាវជ្រាវ: មាន ការស្រាវជ្រ… | 56.6 | no |
| seg_0026 | 5 | ប្រព័ន្ធផ្សព្វផ្សាយ: ប្រព័ន្ធផ្សព្វផ្សាយ… | Media: media created to provide assistance to patients | ប្រព័ន្ធផ្សព្វផ្សាយ: ប្រព័ន្ធផ… | 94.7 | yes |
| seg_0027 | 5 | អ្នកស្រាវជ្រាវ: អ្នកស្រាវជ្រាវដែលបានបង្ក… | Researchers: Researchers created to help patients created to help pati… | អ្នកស្រាវជ្រាវ: អ្នកស្រាវជ្រាវ… | 65.6 | yes |
| seg_0028 | 5 | អ្នកស្រាវជ្រាវ: អ្នកស្រាវជ្រាវដែលបានបង្ក… | Researchers: Researchers created to help patients | អ្នកស្រាវជ្រាវ: អ្នកស្រាវជ្រាវ… | 72.3 | yes |
| seg_0029 | 5 | អ្នកស្រាវជ្រ | A researcher | អ្នកស្រាវជ្រាវ | 95.9 | yes |
| seg_0030 | 6 | សាលារាជធានីភ្នែក | The capital's eyes | ភ្នែក របស់ រដ្ឋធានី | 30.0 | no |
| seg_0031 | 6 | វាយបញ្ចូលព័ត៌មានដែលអាចប្រើប្រាស់បានដើម្ប… | It provides usable information to create a daily account and usable in… | វា ផ្តល់ ព័ត៌មាន ដែល អាច ប្រើប… | 48.6 | no |
| seg_0032 | 266 | ពស់វែករន ៀម | How do we know that Jehovah's Witnesses are genuinely interested in us… | [រូបភាព នៅ ទំព័រ ១៦] | 4.4 | no |
| seg_0033 | 266 | ពស់វែកប្ររី | The snake is known for its fearsome appearance. | សត្វ ពស់ នេះ ត្រូវ បាន គេ ស្គា… | 10.7 | no |
| seg_0034 | 266 | ពស់វែកដំរូក | The snake is known as the sea snake, or sea snake. | ពស់ នេះ ត្រូវបាន គេ ស្គាល់ ថា … | 9.8 | no |
| seg_0035 | 266 | ពស់ប្ាយកាលប្កហម | The snake, however, was not a snake. | [រូបភាព នៅ ទំព័រ ១៦] | 3.2 | no |
| seg_0036 | 266 | ពស់ប្ាយរង្កង្់លលឿង្លមៅ | The snake is known for its large size, which makes it difficult to see… | ពស់ នេះ ល្បី ពី ទំហំ ធំ របស់ វ… | 11.9 | no |
| seg_0037 | 266 | ពស់ប្ាយរង្កង្់សលមៅ | The snake is known for its large size, which makes it difficult to see… | ពស់ នេះ ល្បី ពី ទំហំ ធំ របស់ វ… | 12.8 | no |
| seg_0038 | 266 | ពស់សមុប្រ | The Sea Serpent | ពស់ សមុទ្រ | 56.0 | no |
| seg_0039 | 266 | ពស់ហនុមាន | What is the origin of the name? | តើ ឈ្មោះ នេះ មាន ប្រភព មក ពី ណ… | 11.5 | no |
| seg_0040 | 266 | ពស់ល ៀែវនែកធំ | It is also known as the great horned viper, or big horned viper. | [រូបភាព នៅ ទំព័រ ១៦] | 3.8 | no |
| seg_0041 | 266 | ពស់ល ឿែ | How do we know that Jehovah's Witnesses are genuine? | [រូបភាព នៅ ទំព័រ ១២] | 2.0 | no |
| seg_0042 | 266 | ពស់ប្សាចាស់ | The ancient serpent | ពស់ បុរាណ | 19.6 | no |
| seg_0043 | 266 | ពស់ពញ្លាក់ | The snake fell. | ពស់ នោះ បាន ធ្លាក់ ចុះ។ | 33.3 | no |

## Stage 3: completeness check

Numbers by value **6362/6362**, symbols **245/245** (expected 6362/6362 and 245/245). Word coverage 100.00%, exact number form 99.98%. Figures {'described': 165, 'DECORATIVE': 10, 'skipped-small': 9}, unaccounted 0. 439 pages checked; image-only pages not checked: 35.

## Sections (from the PDF's table of contents)

The printed TOC (PDF pages [9, 10]) lists **51 numbered sections** in 2 chapters: Chapter I Emergency (from PDF p16): 27 sections, Chapter II Cardiology (from PDF p284): 24 sections. The work plan's figure of 28 sections does not match the TOC.

- Every section's title line was looked up in the text layer at TOC page + 13: not found: none; found on a different page: none.
- Sections 45 and 46 have the same title in the TOC and in the body ("Infectious Endocarditis", PDF p407 and p417); they stay two sections.
- Title spelling taken from the body heading where the TOC has a typo: §11: Pisoning → Poisoning; §24: Empiric Al → Empirical; §25: Respiratonry → Respiratory.
- Sections without a detectable reference-list heading: none.

**How the stage-2 section labels map onto the TOC.** Stage 2 labels blocks with 54 values: 51 numbered sections plus Front matter, Chapter I introduction, Chapter II introduction. Each numbered label maps to the TOC section with the same number; labels where any block lands in a different TOC section: none. The unnumbered labels map to front matter (excluded) and the chapter title pages (excluded).

Docling found 1303 section headers (all levels). 58 of them resemble a TOC title (49 on the section's start page; the rest are sub-headings such as "Pulmonary embolism (19.6%)" inside other sections). TOC sections with no Docling header at all: [4, 7, 46]. Docling headers are not used for sectioning.

<details><summary>Section table</summary>

| § | ch | title | TOC page | PDF start | heading line in text layer |
|---|---|---|---|---|---|
| 1 | I | Assessment the Patients in Emergency Room | 4 | 17 | ASSESSMENT THE PATIENTS IN EMERGENCY ROOM |
| 2 | I | Oxygen Therapy and Respiratory Supports | 17 | 30 | OXYGEN THERAPY AND RESPIRATORY SUPPORTS |
| 3 | I | Early Warning Score in Hospital | 29 | 42 | EARLY WARNING SCORE IN HOSPITAL |
| 4 | I | Shock | 36 | 49 | SHOCK |
| 5 | I | Hemorrhagic Shock | 50 | 63 | HEMORRHAGIC SHOCK |
| 6 | I | Stroke Syndrome in Emergency | 63 | 76 | STROKE SYNDROME IN EMERGENCY |
| 7 | I | Coma | 76 | 89 | COMA |
| 8 | I | Allergic Reaction | 86 | 99 | ALLERGIC REACTION |
| 9 | I | General Management of Poisoning | 95 | 108 | GENERAL MANAGEMENT OF POISONING |
| 10 | I | Paracetamol Poisoning | 107 | 120 | PARACETAMOL POISONING |
| 11 | I | Methamphetamines Poisoning | 116 | 129 | METHAMPHETAMINES POISONING |
| 12 | I | Organophosphate and Carbamate Insecticides Poisoning | 123 | 136 | ORGANOPHOSPHATE AND CARBAMATE INSECTICIDES |
| 13 | I | Methanol And Ethylene Glycol Intoxication | 132 | 145 | METHANOL AND ETHYLENE GLYCOL INTOXICATION |
| 14 | I | Cardiopulmonary Arrest Basic and Advance Cardiac Life Support | 141 | 154 | CARDIOPULMONARY ARREST |
| 15 | I | Acute Metabolic Complication of Diabetes Mellitus, Hyperosmolar Hyperglycemia State | 159 | 172 | ACUTE METABOLIC COMPLICATION OF DIABETES |
| 16 | I | Traumatism In Adult | 167 | 180 | TRAUMATISM IN ADULT |
| 17 | I | Initial Management of Head Trauma | 177 | 190 | INITIAL MANAGEMENT OF HEAD TRAUMA |
| 18 | I | Initial Management of chest Trauma | 184 | 197 | INITIAL MANAGEMENT OF CHEST TRAUMA |
| 19 | I | Acute Abdominal Syndrome | 193 | 206 | ACUTE ABDOMINAL SYNDROME |
| 20 | I | Hyperkalemia | 202 | 215 | HYPERKALEMIA |
| 21 | I | Hypokalemia | 210 | 223 | HYPOKALEMIA |
| 22 | I | Hypernatremia | 219 | 232 | HYPERNATREMIA |
| 23 | I | Hyponatremia | 228 | 241 | HYPONATREMIA |
| 24 | I | Sepsis and Septic Shock, Empirical Antibiotherapy | 236 | 249 | SEPSIS AND SEPTIC SHOCK, EMPIRICAL ANTIBIOTHERAPY |
| 25 | I | Severe Acute Respiratory infection (SARI) And Influenza | 244 | 257 | SEVERE ACUTE RESPIRATORY INFECTION (SARI) AND |
| 26 | I | Snake Bites | 253 | 266 | SNAKE BITES |
| 27 | I | Massive blood Transfusion | 263 | 276 | MASSIVE BLOOD TRANSFUSION |
| 28 | II | Acute Coronary Syndrome St-elevation Myocardial Infarction (STEMI) | 272 | 285 | ACUTE CORONARY SYNDROME |
| 29 | II | Acute Coronary Syndrome (ACS)NON-ST Elevation Myocardial Infarction (NSTEMI) | 280 | 293 | ACUTE CORONARY SYNDROME (ACS) |
| 30 | II | Chronic Coronary Syndrome | 289 | 302 | CHRONIC CORONARY SYNDROME |
| 31 | II | Emergency Tachy-Arrhythmia | 293 | 306 | EMERGENCY TACHY-ARRHYTHMIA |
| 32 | II | Emergency Bradycardia | 302 | 315 | EMERGENCY BRADYCARDIA |
| 33 | II | Pulmonary Embolism | 306 | 319 | PULMONARY EMBOLISM |
| 34 | II | Acute Pulmonary Edema | 313 | 326 | ACUTE PULMONARY EDEMA |
| 35 | II | Hypertension | 320 | 333 | HYPERTENSION |
| 36 | II | Chronic Heart failure | 332 | 345 | CHRONIC HEART FAILURE |
| 37 | II | Aortic regurgitation (AR) | 346 | 359 | AORTIC REGURGITATION (AR) |
| 38 | II | Aortic Stenosis (AS) | 353 | 366 | AORTIC STENOSIS (AS) |
| 39 | II | Management of Aortic Aneurysm | 359 | 372 | MANAGEMENT OF AORTIC ANEURYSM |
| 40 | II | Mitral Regurgitation (MR) | 364 | 377 | MITRAL REGURGITATION (MR) |
| 41 | II | Mitral Stenosis (MS) | 371 | 384 | MITRAL STENOSIS (MS) |
| 42 | II | Management And Surveillance of Prosthetic Valves | 379 | 392 | MANAGEMENT AND SURVEILLANCE OF PROSTHETIC |
| 43 | II | Deep Venous Thrombosis | 384 | 397 | DEEP VENOUS THROMBOSIS |
| 44 | II | Prevention Of Deep Venous Thrombosis | 390 | 403 | PREVENTION OF DEEP VENOUS THROMBOSIS |
| 45 | II | Infectious Endocarditis | 394 | 407 | INFECTIOUS ENDOCARDITIS |
| 46 | II | Infectious Endocarditis | 404 | 417 | INFECTIOUS ENDOCARDITIS |
| 47 | II | Pericarditis | 415 | 428 | PERICARDITIS |
| 48 | II | Constrictive Pericarditis | 419 | 432 | CONSTRICTIVE PERICARDITIS |
| 49 | II | Management of Cardiovascular Diseases During Pregnancy | 428 | 441 | MANAGEMENT OF CARDIOVASCULAR DISEASES DURING |
| 50 | II | Cardiovascular Drugs and Pregnancy | 451 | 464 | CARDIOVASCULAR DRUGS AND PREGNANCY |
| 51 | II | Cardiac Evaluation before NON-Cardiac Surgery (NCS) | 456 | 469 | CARDIAC EVALUATION BEFORE NON-CARDIAC |

</details>

## Stage 4: chunks

Excluded from the index (`excluded.jsonl`, 129 records): {'front_matter': 33, 'reference_list': 95, 'chapter_title_page': 1}.

| variant | chunks | body_text | table | flowchart | figure | tokens min / median / max | over max | text chunks with overlap | mean overlap |
|---|---|---|---|---|---|---|---|---|---|
| 256 (max 384) | 1626 | 940 | 287 | 55 | 344 | 33 / 222.0 / 934 | 24 {'flowchart': 21, 'table': 3} | 500/940 | 19% |
| 512 (max 768) | 905 | 503 | 185 | 55 | 162 | 48 / 376 / 934 | 2 {'flowchart': 2} | 183/503 | 20% |

Tokens per source_type (min / median / max):

| variant | body_text | table | flowchart | figure |
|---|---|---|---|---|
| 256 | 33 / 227.0 / 278 | 58 / 219 / 446 | 73 / 301 / 934 | 40 / 207.0 / 381 |
| 512 | 48 / 390 / 512 | 58 / 250 / 738 | 73 / 301 / 934 | 48 / 439.5 / 758 |

Flowcharts: 53 Chandra algorithm blocks were matched to the Qwen3 description of the same figure (Chandra text kept, Qwen3 in `metadata.alt_description`); the other Qwen3 descriptions are figure chunks with `numbers_verified: false`. Sentences joined across a line break: 644, across a block/page break: 52. Sentences longer than max that had to be cut: 0.

Over-max chunks are flowcharts kept whole (rule 4 outranks the size limit) and single table rows longer than the limit (a row is never split).

## Stage 5: validation

| check | 256 | 512 |
|---|---|---|
| 1 numbers (chunks + excluded, all pages) | 6362/6362 ✓ | 6362/6362 ✓ |
| 1 symbols (chunks + excluded, all pages) | 245/245 | 245/245 |
| 1 numbers / symbols, index only (p17+, reference lists removed from the reference) | 4430/4430 / 240/240 | 4430/4430 / 240/240 |
| 2 orphan blocks / lost sentences | 0 / 0 ✓ | 0 / 0 ✓ |
| 3 chunks crossing a section / table parts without header | 0 / 0 ✓ | 0 / 0 ✓ |
| 4 citations not matching | 0 ✓ | 0 ✓ |
| 5 chunks under 40 tokens | 1 {'body_text': 1} | 0 {} |
| 5 numbers_verified (type:value) | {'body_text:True': 930, 'table:False': 125, 'flowchart:False': 55, 'figure:False': 329, 'table:True': 162, 'body_text:False': 10, 'figure:True': 15} | {'body_text:True': 499, 'table:False': 60, 'flowchart:False': 55, 'figure:False': 147, 'table:True': 125, 'body_text:False': 4, 'figure:True': 15} |

Overall: **all checks passed**.

Token histogram, variant 256:

| type | 0-39 | 40-63 | 64-127 | 128-191 | 192-255 | 256-383 | 384-511 | 512-767 | 768-1023 | 1024- |
|---|---|---|---|---|---|---|---|---|---|---|
| body_text | 1 | 14 | 98 | 199 | 601 | 27 | 0 | 0 | 0 | 0 |
| figure | 0 | 18 | 37 | 84 | 174 | 31 | 0 | 0 | 0 | 0 |
| flowchart | 0 | 0 | 7 | 8 | 7 | 12 | 11 | 8 | 2 | 0 |
| table | 0 | 1 | 35 | 65 | 148 | 35 | 3 | 0 | 0 | 0 |

<details><summary>Chunks under 40 tokens (256)</summary>

- s31_emergency_tachy_arrhythmia_0046 (body_text, 33 tok): ## IX. OMPLICATIONS The common complications include sudden cardiac de…

</details>

Token histogram, variant 512:

| type | 0-39 | 40-63 | 64-127 | 128-191 | 192-255 | 256-383 | 384-511 | 512-767 | 768-1023 | 1024- |
|---|---|---|---|---|---|---|---|---|---|---|
| body_text | 0 | 4 | 22 | 28 | 74 | 119 | 246 | 10 | 0 | 0 |
| figure | 0 | 2 | 8 | 7 | 9 | 34 | 63 | 39 | 0 | 0 |
| flowchart | 0 | 0 | 7 | 8 | 7 | 12 | 11 | 8 | 2 | 0 |
| table | 0 | 1 | 28 | 42 | 23 | 33 | 44 | 14 | 0 | 0 |

Preview: `out/pipeline/stage5_validate/chunks_preview.html`

