# C4 audit — v2

Comprobación sobre imágenes y máscaras reales con regeneración. Revisión humana de realismo: NOT PERFORMED.
Área alterada <0.5% marcada pequeña; >20% grande. Son alertas de QA, no umbrales de fraude/realismo.
C4: gradiente de borde >2×original es alerta, no prueba de artefacto. C5 comprueba contradicción anotada y manipulación independientemente.

| claim_id | source_image_id | mask_nonempty | dimensions_match | changed_pixels | changed_percent | mask_percent | outside_mask_changed_pixels | reproducible | mask_sha_matches | mean_absolute_rgb_change_in_mask | small_area_flag | large_area_flag | human_realism_review | mask_matches_annotation | boundary_gradient_before | boundary_gradient_after | possible_boundary_artifact_flag | damage_removal_verified |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| clm_d58a5ff66fd7b90a36be7670 | hitl:Car damages 1074 | True | True | 2324 | 0.666647543099739 | 0.6735320271937122 | 0 | True | True | 25.512067007382168 | False | False | NOT PERFORMED | True | 94.66238066435461 | 51.27556377496435 | False | False |
| clm_1dd140e544f1b55dfec676c5 | hitl:Car damages 1172 | True | True | 123 | 0.030016692209326158 | 0.030016692209326158 | 0 | True | True | 19.566395663956637 | True | False | NOT PERFORMED | True | 114.80134789407755 | 72.66645244364325 | False | False |
| clm_55c84206047cbe66f75a5bf6 | hitl:Car damages 1220 | True | True | 2305 | 0.6097883597883598 | 0.6103174603174604 | 0 | True | True | 58.450946395029625 | False | False | NOT PERFORMED | True | 123.16170636031801 | 60.935678805927225 | False | False |
| clm_0c388c5b7aa7ad945eabbe56 | hitl:Car damages 159 | True | True | 252 | 0.0819176532542763 | 0.0819176532542763 | 0 | True | True | 18.021164021164022 | True | False | NOT PERFORMED | True | 73.78699773933661 | 52.71763109353394 | False | False |
| clm_678d55c0c5472fe0899e62c9 | hitl:Car damages 163 | True | True | 173 | 0.06932339564424676 | 0.07132696199234638 | 0 | True | True | 19.90074906367041 | True | False | NOT PERFORMED | True | 53.258104984448174 | 26.889624844655525 | False | False |
| clm_3e2a1bba638d2c26162af26e | hitl:Car damages 210 | True | True | 573 | 0.12002438191632644 | 0.12023384855143347 | 0 | True | True | 12.586527293844368 | True | False | NOT PERFORMED | True | 33.88627694131868 | 19.658342422153805 | False | False |
| clm_e11c2c30d261a17659c3f62a | hitl:Car damages 250 | True | True | 309 | 0.06472519024807134 | 0.06472519024807134 | 0 | True | True | 18.22653721682848 | True | False | NOT PERFORMED | True | 75.09451802021894 | 34.647538547570264 | False | False |
| clm_4565850a7954c1d5f83af25c | hitl:Car damages 256 | True | True | 23 | 0.005110111800359041 | 0.005110111800359041 | 0 | True | True | 19.985507246376812 | True | False | NOT PERFORMED | True | 79.62343168863364 | 17.6889851821304 | False | False |
| clm_4ac6cc9b88ae6a3aa262e540 | hitl:Car damages 259 | True | True | 24 | 0.005027199242568648 | 0.005027199242568648 | 0 | True | True | 20.569444444444443 | True | False | NOT PERFORMED | True | 115.19736250753117 | 65.48987396779377 | False | False |
| clm_b338b045fcc1ffb87762ab01 | hitl:Car damages 296 | True | True | 902 | 0.18981002163245037 | 0.1914934808043568 | 0 | True | True | 22.802930402930404 | True | False | NOT PERFORMED | True | 47.392303890378386 | 19.941315825132673 | False | False |
| clm_de7fb58fed0148d466e1afbe | hitl:Car damages 463 | True | True | 27 | 0.01406601650412603 | 0.01406601650412603 | 0 | True | True | 8.160493827160494 | True | False | NOT PERFORMED | True | 68.13061224773766 | 50.33796796723963 | False | False |
| clm_eb3c38d144c012b75595cff1 | hitl:Car damages 482 | True | True | 787 | 0.3917722842265609 | 0.3917722842265609 | 0 | True | True | 30.143583227445998 | True | False | NOT PERFORMED | True | 81.66495296247363 | 40.46677310214788 | False | False |
| clm_4e7562e21c4b22ec8b0efe32 | hitl:Car damages 495 | True | True | 30 | 0.013786764705882353 | 0.013786764705882353 | 0 | True | True | 23.11111111111111 | True | False | NOT PERFORMED | True | 123.82222091813878 | 76.03715659051666 | False | False |
| clm_b10d457443c695e896ff5f6a | hitl:Car damages 498 | True | True | 25 | 0.012919896640826873 | 0.012919896640826873 | 0 | True | True | 10.866666666666667 | True | False | NOT PERFORMED | True | 53.82193060629092 | 28.60126778879917 | False | False |
| clm_441fe0789adc5c60cfb465af | hitl:Car damages 619 | True | True | 46 | 0.018844658563463484 | 0.018844658563463484 | 0 | True | True | 14.07246376811594 | True | False | NOT PERFORMED | True | 65.34048689590537 | 51.800655469479935 | False | False |
| clm_c273d6b418af4f422cee461c | hitl:Car damages 645 | True | True | 345 | 0.1414166256763404 | 0.14182652893917036 | 0 | True | True | 15.34489402697495 | True | False | NOT PERFORMED | True | 76.05084110734751 | 46.15014736524996 | False | False |
| clm_8f75a62a4e84f4282b2aa18c | hitl:Car damages 698 | True | True | 64 | 0.02110769210473373 | 0.02110769210473373 | 0 | True | True | 10.984375 | True | False | NOT PERFORMED | True | 42.281897632248 | 31.01833036223669 | False | False |
| clm_07b2309a77391be7dc012e95 | hitl:Car damages 708 | True | True | 469 | 0.19146061177584822 | 0.19146061177584822 | 0 | True | True | 13.57000710732054 | True | False | NOT PERFORMED | True | 78.80627490048127 | 52.19549617528885 | False | False |
| clm_825ecd004709bdc2cb352db0 | hitl:Car damages 867 | True | True | 1178 | 0.47921828026540064 | 0.47921828026540064 | 0 | True | True | 18.778155065082057 | True | False | NOT PERFORMED | True | 75.48798936141402 | 40.74993179471722 | False | False |
| clm_8be3440ae000c13d10f1f7ce | hitl:Car damages 899 | True | True | 228 | 0.09302401488384238 | 0.09302401488384238 | 0 | True | True | 30.410818713450297 | True | False | NOT PERFORMED | True | 178.849299379709 | 117.31376491015095 | False | False |
| clm_167bcc49a4ec7a95fbdb89cf | hitl:Car damages 915 | True | True | 9 | 0.0036548817036621915 | 0.004467077637809345 | 0 | True | True | 11.272727272727273 | True | False | NOT PERFORMED | True | 48.02739444062313 | 4.9293346367775195 | False | False |
| clm_2f78d987c595817ef72234d0 | hitl:Car damages 916 | True | True | 37 | 0.015025624781722343 | 0.015025624781722343 | 0 | True | True | 7.396396396396399 | True | False | NOT PERFORMED | True | 31.392107442122047 | 14.87682277453918 | False | False |
| clm_1e346ae93b3aaa0b34973548 | hitl:Car damages 986 | True | True | 7 | 0.0028311425682507585 | 0.0028311425682507585 | 0 | True | True | 7.047619047619048 | True | False | NOT PERFORMED | True | 77.38814394841654 | 80.04447308311546 | False | False |
| clm_118e616ec6b25d8bb6eb9eb9 | hitl:Car damages 999 | True | True | 24 | 0.009735202492211837 | 0.009735202492211837 | 0 | True | True | 10.694444444444445 | True | False | NOT PERFORMED | True | 59.31186982775909 | 32.57595670825073 | False | False |

## Ampliación v3

807 casos revisados automáticamente; tabla completa en C4_INPAINT_AUDIT_V3.md.
