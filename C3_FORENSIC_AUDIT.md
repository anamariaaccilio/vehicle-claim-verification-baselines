# C3 audit — v2

Comprobación sobre imágenes y máscaras reales con regeneración. Revisión humana de realismo: NOT PERFORMED.
Área alterada <0.5% marcada pequeña; >20% grande. Son alertas de QA, no umbrales de fraude/realismo.
C4: gradiente de borde >2×original es alerta, no prueba de artefacto. C5 comprueba contradicción anotada y manipulación independientemente.

| claim_id | source_image_id | mask_nonempty | dimensions_match | changed_pixels | changed_percent | mask_percent | outside_mask_changed_pixels | reproducible | mask_sha_matches | mean_absolute_rgb_change_in_mask | small_area_flag | large_area_flag | human_realism_review | source_and_destination_in_bounds | valid_source_and_donor | source_copy_matches | original_damage_preserved | patch_size | patch_width_at_360px_display |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| clm_0cf545d2b3c7d43a1f42ba3b | hitl:Car damages 1074 | True | True | 576 | 0.165227618255357 | 0.165227618255357 | 0 | True | True | 165.09664351851853 | True | False | NOT PERFORMED | True | True | True | True | [24, 24] | 12.169014084507042 |
| clm_c42556d19a591760bb29b20d | hitl:Car damages 1172 | True | True | 576 | 0.140565973272942 | 0.140565973272942 | 0 | True | True | 52.67534722222222 | True | False | NOT PERFORMED | True | True | True | True | [24, 24] | 11.723202170963365 |
| clm_65a60289484726b1fe6d99cb | hitl:Car damages 1220 | True | True | 576 | 0.1523809523809524 | 0.1523809523809524 | 0 | True | True | 66.0 | True | False | NOT PERFORMED | True | True | True | True | [24, 24] | 11.428571428571429 |
| clm_f5cac8cffc0da8eba903f862 | hitl:Car damages 159 | True | True | 576 | 0.1872403502954887 | 0.1872403502954887 | 0 | True | True | 35.37384259259259 | True | False | NOT PERFORMED | True | True | True | True | [24, 24] | 13.312788906009246 |
| clm_0e400ebd40a4c70bbaf2bfd7 | hitl:Car damages 163 | True | True | 576 | 0.23081084330107593 | 0.23081084330107593 | 0 | True | True | 33.107638888888886 | True | False | NOT PERFORMED | True | True | True | True | [24, 24] | 13.19083969465649 |
| clm_40103714736b84f2baac3793 | hitl:Car damages 210 | True | True | 576 | 0.12065278182164754 | 0.12065278182164754 | 0 | True | True | 31.477430555555557 | True | False | NOT PERFORMED | True | True | True | True | [24, 24] | 10.840652446675032 |
| clm_5d0919f156eea7b3a7e4ad64 | hitl:Car damages 250 | True | True | 576 | 0.12065278182164754 | 0.12065278182164754 | 0 | True | True | 95.01273148148147 | True | False | NOT PERFORMED | True | True | True | True | [24, 24] | 10.840652446675032 |
| clm_90c06f4dd9482bab1b0cbf23 | hitl:Car damages 256 | True | True | 576 | 0.12797497378290468 | 0.12797497378290468 | 0 | True | True | 124.33680555555553 | True | False | NOT PERFORMED | True | True | True | True | [24, 24] | 9.751693002257337 |
| clm_8c19fe7faad00962ef139c9e | hitl:Car damages 259 | True | True | 576 | 0.12065278182164754 | 0.12065278182164754 | 0 | True | True | 79.24131944444444 | True | False | NOT PERFORMED | True | True | True | True | [24, 24] | 10.840652446675032 |
| clm_f3b0ca23fa6bbfcef8e2afa4 | hitl:Car damages 296 | True | True | 576 | 0.1212090603772632 | 0.1212090603772632 | 0 | True | True | 114.88020833333333 | True | False | NOT PERFORMED | True | True | True | True | [24, 24] | 10.85427135678392 |
| clm_53eb8d7d47944ed99e5de4e4 | hitl:Car damages 463 | True | True | 576 | 0.30007501875468867 | 0.30007501875468867 | 0 | True | True | 30.85706018518518 | True | False | NOT PERFORMED | True | True | True | True | [24, 24] | 17.419354838709676 |
| clm_e1202a5298377e4fb5eb31c4 | hitl:Car damages 482 | True | True | 576 | 0.2867354964606087 | 0.2867354964606087 | 0 | True | True | 87.10416666666667 | True | False | NOT PERFORMED | True | True | True | True | [24, 24] | 17.07509881422925 |
| clm_cc0315b4262ea37b5ead9b75 | hitl:Car damages 495 | True | True | 576 | 0.2647058823529412 | 0.2647058823529412 | 0 | True | True | 61.96585648148149 | True | False | NOT PERFORMED | True | True | True | True | [24, 24] | 16.875 |
| clm_8a20ec87fa1aa28bd71369d9 | hitl:Car damages 498 | True | True | 576 | 0.29767441860465116 | 0.29767441860465116 | 0 | True | True | 41.14699074074073 | True | False | NOT PERFORMED | True | True | True | True | [24, 24] | 16.74418604651163 |
| clm_fbe8949f750725d6b8d85b69 | hitl:Car damages 619 | True | True | 576 | 0.23596789853380365 | 0.23596789853380365 | 0 | True | True | 132.75405092592595 | True | False | NOT PERFORMED | True | True | True | True | [24, 24] | 15.184534270650264 |
| clm_014b06a38241033c03461424 | hitl:Car damages 645 | True | True | 576 | 0.23610427939006395 | 0.23610427939006395 | 0 | True | True | 92.21238425925925 | True | False | NOT PERFORMED | True | True | True | True | [24, 24] | 15.157894736842104 |
| clm_d06b0e323495342cb86e1ebe | hitl:Car damages 698 | True | True | 576 | 0.18996922894260357 | 0.18996922894260357 | 0 | True | True | 103.92881944444444 | True | False | NOT PERFORMED | True | True | True | True | [24, 24] | 13.649289099526067 |
| clm_638971b9cbcd6bf448974b92 | hitl:Car damages 708 | True | True | 576 | 0.23514139100829118 | 0.23514139100829118 | 0 | True | True | 176.50115740740742 | True | False | NOT PERFORMED | True | True | True | True | [24, 24] | 15.131348511383537 |
| clm_91d93107f262a5c1d0937f13 | hitl:Car damages 867 | True | True | 576 | 0.2343206531688207 | 0.2343206531688207 | 0 | True | True | 53.31192129629629 | True | False | NOT PERFORMED | True | True | True | True | [24, 24] | 15.078534031413612 |
| clm_97767ee121b285ddf3c549d2 | hitl:Car damages 899 | True | True | 576 | 0.23500803760128602 | 0.23500803760128602 | 0 | True | True | 46.15856481481482 | True | False | NOT PERFORMED | True | True | True | True | [24, 24] | 15.05226480836237 |
| clm_11e9a1bfd2712bb0a19faf69 | hitl:Car damages 915 | True | True | 576 | 0.23391242903438025 | 0.23391242903438025 | 0 | True | True | 172.19849537037038 | True | False | NOT PERFORMED | True | True | True | True | [24, 24] | 15.05226480836237 |
| clm_d163d2cb8dbbf66d090140b7 | hitl:Car damages 916 | True | True | 576 | 0.23391242903438025 | 0.23391242903438025 | 0 | True | True | 62.298611111111114 | True | False | NOT PERFORMED | True | True | True | True | [24, 24] | 15.05226480836237 |
| clm_78acb7ceda1fad0a1a864a68 | hitl:Car damages 986 | True | True | 576 | 0.23296258847320525 | 0.23296258847320525 | 0 | True | True | 52.185763888888886 | True | False | NOT PERFORMED | True | True | True | True | [24, 24] | 15.02608695652174 |
| clm_21714f9a7c823eba843d2429 | hitl:Car damages 999 | True | True | 576 | 0.23364485981308408 | 0.23364485981308408 | 0 | True | True | 89.13368055555556 | True | False | NOT PERFORMED | True | True | True | True | [24, 24] | 15.0 |

## Ampliación v3

807 casos revisados automáticamente; tabla completa en C3_FORENSIC_AUDIT_V3.md.
