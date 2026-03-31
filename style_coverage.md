# Style Coverage

This report is generated from the local `Examples of carousels` folder and the current style-engine mappings in `tools/carousel_system/example_style_audit.py`.

## Summary
- Total grouped example families: 113
- Covered groups: 11
- Duplicate/alias groups: 16
- Missing or unmapped groups: 86

## Covered
- `01 – Long Title` (9 files)
  Canonical: `creator_mono_minimal`
  Style families: reference_creator_mono_minimal
  Recipes: creator_mono_minimal_v1
  Samples: 01 – Long Title-1.png, 01 – Long Title-2.png, 01 – Long Title-3.png
  Notes: Monochrome hook-export family now mapped into the minimal creator text recipe.
- `02 – Title` (14 files)
  Canonical: `creator_mono_minimal`
  Style families: reference_creator_mono_minimal
  Recipes: creator_mono_minimal_v1
  Samples: 02 – Title-1.png, 02 – Title-10.png, 02 – Title-11.png
  Notes: Title-only exports now map to the same minimal creator family as the long-title and CTA slides.
- `03 – Copy` (4 files)
  Canonical: `creator_mono_minimal`
  Style families: reference_creator_mono_minimal
  Recipes: creator_mono_minimal_v1
  Samples: 03 – Copy-1.png, 03 – Copy-2.png, 03 – Copy-3.png
  Notes: Soft rose copy exports are now absorbed by the minimal creator family.
- `05 – Call to Action` (9 files)
  Canonical: `creator_mono_minimal`
  Style families: reference_creator_mono_minimal
  Recipes: creator_mono_minimal_v1
  Samples: 05 – Call to Action-1.png, 05 – Call to Action-2.png, 05 – Call to Action-3.png
  Notes: CTA exports now map to the same minimal creator family.
- `Alder_1` (12 files)
  Canonical: `Alder_1`
  Style families: reference_mix_alder_portrait, reference_alder_split_media, reference_alder_text_only
  Recipes: alder_portrait_editorial_mix_v1, alder_portrait_editorial_dense_v1, alder_split_media_right_v1, alder_split_media_left_v1, alder_text_only_air_v1
  Samples: Alder_1-1.png, Alder_1-10.png, Alder_1-11.png
  Notes: Primary upper-file family already harvested into multiple Alder-driven recipes.
- `CP_3` (6 files)
  Canonical: `CP_3`
  Style families: reference_cp_minimal_split, reference_cp_longform_split, reference_cp_gallery_wall
  Recipes: cp_split_minimal_statement_v1, cp_split_longform_v1, cp_gallery_wall_v1
  Samples: CP_3-1.png, CP_3-2.png, CP_3-3.png
  Notes: Minimal split, longform split, and gallery variants are already implemented.
- `Light_1` (20 files)
  Canonical: `light_grain_glow`
  Style families: reference_light_grain_glow
  Recipes: light_grain_glow_v1
  Samples: Light_1-1.jpg, Light_1-10.jpg, Light_1-11.jpg
  Notes: Primary light-grain hero set is now mapped into the light glow family.
- `Title (01)` (15 files)
  Canonical: `retro_swipe_creator`
  Style families: reference_retro_swipe_creator
  Recipes: retro_swipe_creator_v1
  Samples: Title (01)-1.jpg, Title (01)-10.jpg, Title (01)-11.jpg
  Notes: Textured retro creator CTA set is now mapped into the swipe-button family.
- `Twitter Post - Default` (1 files)
  Canonical: `twitter_card_soft`
  Style families: reference_twitter_card_soft
  Recipes: twitter_card_soft_v1
  Samples: Twitter Post - Default.png
  Notes: Flat tweet screenshot layout is now covered by the soft tweet-card renderer.
- `typography slide 1` (10 files)
  Canonical: `typography slide 1`
  Style families: reference_typography_signal, reference_typography_editorial_light
  Recipes: typography_signal_glow_v1, typography_editorial_light_v1
  Samples: typography slide 1-1.png, typography slide 1-2.png, typography slide 1-3.png
  Notes: Dark centered-signal and light editorial directions are both mapped from this family.
- `typography slide 2` (1 files)
  Canonical: `typography slide 2`
  Style families: reference_typography_signal
  Recipes: typography_signal_glow_v1
  Samples: typography slide 2.png
  Notes: Used as the current CTA/end-card reference family.

## Duplicate Or Alias
- `1971245110` (1 files)
  Canonical: `reference_sadekov_black_profile_cover_export`
  Style families: reference_sadekov_black_profile
  Recipes: sadekov_black_profile_minimal_v1
  Samples: 1971245110.png
  Notes: Exported black-profile cover slide already mapped to node 1:9052.
- `1971245111` (1 files)
  Canonical: `reference_sadekov_black_profile_body_export`
  Style families: reference_sadekov_black_profile
  Recipes: sadekov_black_profile_minimal_v1
  Samples: 1971245111.png
  Notes: Exported black-profile body slide already mapped to node 1:9076.
- `1971245118` (1 files)
  Canonical: `reference_sadekov_black_profile_cta_export`
  Style families: reference_sadekov_black_profile
  Recipes: sadekov_black_profile_minimal_v1
  Samples: 1971245118.png
  Notes: Exported black-profile CTA slide already mapped to node 1:9176.
- `1971245119` (1 files)
  Canonical: `reference_sadekov_white_profile_cover_export`
  Style families: reference_sadekov_white_profile
  Recipes: sadekov_white_profile_minimal_v1
  Samples: 1971245119.png
  Notes: Exported white-profile cover slide already mapped to node 1:9064.
- `1971245120` (1 files)
  Canonical: `reference_sadekov_white_profile_body_export`
  Style families: reference_sadekov_white_profile
  Recipes: sadekov_white_profile_minimal_v1
  Samples: 1971245120.png
  Notes: Exported white-profile body slide already mapped to node 1:9086.
- `1971245125` (1 files)
  Canonical: `reference_sadekov_white_profile_cta_export`
  Style families: reference_sadekov_white_profile
  Recipes: sadekov_white_profile_minimal_v1
  Samples: 1971245125.png
  Notes: Exported white-profile CTA slide already mapped to node 1:9187.
- `1971245499` (1 files)
  Canonical: `portrait_reference_1971245499`
  Style families: reference_mix_alder_portrait, reference_alder_split_media, reference_alder_text_only, reference_typography_signal, reference_cp_minimal_split, reference_cp_longform_split, reference_cp_gallery_wall
  Recipes: None
  Samples: 1971245499.png
  Notes: Single exported portrait layout reference already used as a shared sizing/layout anchor.
- `Light_2` (4 files)
  Canonical: `light_grain_glow`
  Style families: reference_light_grain_glow
  Recipes: light_grain_glow_v1
  Samples: Light_2-1.jpg, Light_2-2.jpg, Light_2-3.jpg
  Notes: Numbered light exports are treated as close aliases of the same grain-glow system.
- `Light_3` (4 files)
  Canonical: `light_grain_glow`
  Style families: reference_light_grain_glow
  Recipes: light_grain_glow_v1
  Samples: Light_3-1.jpg, Light_3-2.jpg, Light_3-3.jpg
  Notes: Grouped into the same light glow family as `Light_1` pending more granular harvest work.
- `Light_4` (4 files)
  Canonical: `light_grain_glow`
  Style families: reference_light_grain_glow
  Recipes: light_grain_glow_v1
  Samples: Light_4-1.jpg, Light_4-2.jpg, Light_4-3.jpg
  Notes: Grouped into the same light glow family as `Light_1` pending more granular harvest work.
- `Light_6` (4 files)
  Canonical: `light_grain_glow`
  Style families: reference_light_grain_glow
  Recipes: light_grain_glow_v1
  Samples: Light_6-1.jpg, Light_6-2.jpg, Light_6-3.jpg
  Notes: Profile-heavy light export treated as a high-confidence alias of the light glow family.
- `Tweet` (3 files)
  Canonical: `twitter_card_soft`
  Style families: reference_twitter_card_soft
  Recipes: twitter_card_soft_v1
  Samples: Tweet-1.png, Tweet-2.png, Tweet.png
  Notes: Tweet exports are treated as aliases of the tweet-card family.
- `Twitter Post - Dim` (1 files)
  Canonical: `twitter_card_soft`
  Style families: reference_twitter_card_soft
  Recipes: twitter_card_soft_v1
  Samples: Twitter Post - Dim.png
  Notes: Theme variation of the same tweet-card structure.
- `Twitter Post - Lights Out` (1 files)
  Canonical: `twitter_card_soft`
  Style families: reference_twitter_card_soft
  Recipes: twitter_card_soft_v1
  Samples: Twitter Post - Lights Out.png
  Notes: Theme variation of the same tweet-card structure.
- `TwitterPost_02` (7 files)
  Canonical: `twitter_card_soft`
  Style families: reference_twitter_card_soft
  Recipes: twitter_card_soft_v1
  Samples: TwitterPost_02-1.png, TwitterPost_02-2.png, TwitterPost_02-3.png
  Notes: Soft-gradient tweet card export treated as a high-confidence alias of the covered tweet-card family.
- `TwitterPost_08` (28 files)
  Canonical: `twitter_card_soft`
  Style families: reference_twitter_card_soft
  Recipes: twitter_card_soft_v1
  Samples: TwitterPost_08-1.png, TwitterPost_08-10.png, TwitterPost_08-11.png
  Notes: Repeated soft-card tweet exports grouped into the same tweet-card family for now.

## Missing Or Unmapped
- `1` (5 files)
  Canonical: `1`
  Style families: None
  Recipes: None
  Samples: 1-1.jpg, 1-2.jpg, 1-3.jpg
  Notes: Present in local examples folder but not mapped into the current style engine.
- `104` (1 files)
  Canonical: `104`
  Style families: None
  Recipes: None
  Samples: 104.jpg
  Notes: Present in local examples folder but not mapped into the current style engine.
- `105` (1 files)
  Canonical: `105`
  Style families: None
  Recipes: None
  Samples: 105.jpg
  Notes: Present in local examples folder but not mapped into the current style engine.
- `106` (4 files)
  Canonical: `106`
  Style families: None
  Recipes: None
  Samples: 106-1.jpg, 106-2.jpg, 106-3.jpg
  Notes: Present in local examples folder but not mapped into the current style engine.
- `108` (1 files)
  Canonical: `108`
  Style families: None
  Recipes: None
  Samples: 108.jpg
  Notes: Present in local examples folder but not mapped into the current style engine.
- `109` (1 files)
  Canonical: `109`
  Style families: None
  Recipes: None
  Samples: 109.jpg
  Notes: Present in local examples folder but not mapped into the current style engine.
- `11 3` (15 files)
  Canonical: `11 3`
  Style families: None
  Recipes: None
  Samples: 11 3-1.png, 11 3-10.png, 11 3-11.png
  Notes: Present in local examples folder but not mapped into the current style engine.
- `112` (1 files)
  Canonical: `112`
  Style families: None
  Recipes: None
  Samples: 112.jpg
  Notes: Present in local examples folder but not mapped into the current style engine.
- `113` (1 files)
  Canonical: `113`
  Style families: None
  Recipes: None
  Samples: 113.jpg
  Notes: Present in local examples folder but not mapped into the current style engine.
- `116` (1 files)
  Canonical: `116`
  Style families: None
  Recipes: None
  Samples: 116.jpg
  Notes: Present in local examples folder but not mapped into the current style engine.
- `117` (1 files)
  Canonical: `117`
  Style families: None
  Recipes: None
  Samples: 117.jpg
  Notes: Present in local examples folder but not mapped into the current style engine.
- `120` (1 files)
  Canonical: `120`
  Style families: None
  Recipes: None
  Samples: 120.jpg
  Notes: Present in local examples folder but not mapped into the current style engine.
- `121` (1 files)
  Canonical: `121`
  Style families: None
  Recipes: None
  Samples: 121.jpg
  Notes: Present in local examples folder but not mapped into the current style engine.
- `123` (1 files)
  Canonical: `123`
  Style families: None
  Recipes: None
  Samples: 123.jpg
  Notes: Present in local examples folder but not mapped into the current style engine.
- `124` (1 files)
  Canonical: `124`
  Style families: None
  Recipes: None
  Samples: 124.jpg
  Notes: Present in local examples folder but not mapped into the current style engine.
- `127` (1 files)
  Canonical: `127`
  Style families: None
  Recipes: None
  Samples: 127.jpg
  Notes: Present in local examples folder but not mapped into the current style engine.
- `128` (1 files)
  Canonical: `128`
  Style families: None
  Recipes: None
  Samples: 128.jpg
  Notes: Present in local examples folder but not mapped into the current style engine.
- `131` (1 files)
  Canonical: `131`
  Style families: None
  Recipes: None
  Samples: 131.jpg
  Notes: Present in local examples folder but not mapped into the current style engine.
- `132` (1 files)
  Canonical: `132`
  Style families: None
  Recipes: None
  Samples: 132.jpg
  Notes: Present in local examples folder but not mapped into the current style engine.
- `135` (1 files)
  Canonical: `135`
  Style families: None
  Recipes: None
  Samples: 135.jpg
  Notes: Present in local examples folder but not mapped into the current style engine.
- `136` (1 files)
  Canonical: `136`
  Style families: None
  Recipes: None
  Samples: 136.jpg
  Notes: Present in local examples folder but not mapped into the current style engine.
- `139` (1 files)
  Canonical: `139`
  Style families: None
  Recipes: None
  Samples: 139.jpg
  Notes: Present in local examples folder but not mapped into the current style engine.
- `140` (1 files)
  Canonical: `140`
  Style families: None
  Recipes: None
  Samples: 140.jpg
  Notes: Present in local examples folder but not mapped into the current style engine.
- `142` (1 files)
  Canonical: `142`
  Style families: None
  Recipes: None
  Samples: 142.jpg
  Notes: Present in local examples folder but not mapped into the current style engine.
- `143` (1 files)
  Canonical: `143`
  Style families: None
  Recipes: None
  Samples: 143.jpg
  Notes: Present in local examples folder but not mapped into the current style engine.
- `146` (1 files)
  Canonical: `146`
  Style families: None
  Recipes: None
  Samples: 146.jpg
  Notes: Present in local examples folder but not mapped into the current style engine.
- `147` (1 files)
  Canonical: `147`
  Style families: None
  Recipes: None
  Samples: 147.jpg
  Notes: Present in local examples folder but not mapped into the current style engine.
- `148` (4 files)
  Canonical: `148`
  Style families: None
  Recipes: None
  Samples: 148-1.jpg, 148-2.jpg, 148-3.jpg
  Notes: Present in local examples folder but not mapped into the current style engine.
- `149` (4 files)
  Canonical: `149`
  Style families: None
  Recipes: None
  Samples: 149-1.jpg, 149-2.jpg, 149-3.jpg
  Notes: Present in local examples folder but not mapped into the current style engine.
- `150` (5 files)
  Canonical: `150`
  Style families: None
  Recipes: None
  Samples: 150-1.jpg, 150-2.jpg, 150-3.jpg
  Notes: Present in local examples folder but not mapped into the current style engine.
- `151` (5 files)
  Canonical: `151`
  Style families: None
  Recipes: None
  Samples: 151-1.jpg, 151-2.jpg, 151-3.jpg
  Notes: Present in local examples folder but not mapped into the current style engine.
- `154` (1 files)
  Canonical: `154`
  Style families: None
  Recipes: None
  Samples: 154.jpg
  Notes: Present in local examples folder but not mapped into the current style engine.
- `155` (1 files)
  Canonical: `155`
  Style families: None
  Recipes: None
  Samples: 155.jpg
  Notes: Present in local examples folder but not mapped into the current style engine.
- `158` (1 files)
  Canonical: `158`
  Style families: None
  Recipes: None
  Samples: 158.jpg
  Notes: Present in local examples folder but not mapped into the current style engine.
- `159` (1 files)
  Canonical: `159`
  Style families: None
  Recipes: None
  Samples: 159.jpg
  Notes: Present in local examples folder but not mapped into the current style engine.
- `1971245112` (1 files)
  Canonical: `1971245112`
  Style families: None
  Recipes: None
  Samples: 1971245112.png
  Notes: Present in local examples folder but not mapped into the current style engine.
- `1971245113` (1 files)
  Canonical: `1971245113`
  Style families: None
  Recipes: None
  Samples: 1971245113.png
  Notes: Present in local examples folder but not mapped into the current style engine.
- `1971245114` (1 files)
  Canonical: `1971245114`
  Style families: None
  Recipes: None
  Samples: 1971245114.png
  Notes: Present in local examples folder but not mapped into the current style engine.
- `1971245115` (1 files)
  Canonical: `1971245115`
  Style families: None
  Recipes: None
  Samples: 1971245115.png
  Notes: Present in local examples folder but not mapped into the current style engine.
- `1971245121` (1 files)
  Canonical: `1971245121`
  Style families: None
  Recipes: None
  Samples: 1971245121.png
  Notes: Present in local examples folder but not mapped into the current style engine.
- `1971245122` (1 files)
  Canonical: `1971245122`
  Style families: None
  Recipes: None
  Samples: 1971245122.png
  Notes: Present in local examples folder but not mapped into the current style engine.
- `1971245123` (1 files)
  Canonical: `1971245123`
  Style families: None
  Recipes: None
  Samples: 1971245123.png
  Notes: Present in local examples folder but not mapped into the current style engine.
- `1971245124` (1 files)
  Canonical: `1971245124`
  Style families: None
  Recipes: None
  Samples: 1971245124.png
  Notes: Present in local examples folder but not mapped into the current style engine.
- `2` (5 files)
  Canonical: `2`
  Style families: None
  Recipes: None
  Samples: 2-1.jpg, 2-2.jpg, 2-3.jpg
  Notes: Present in local examples folder but not mapped into the current style engine.
- `28` (1 files)
  Canonical: `28`
  Style families: None
  Recipes: None
  Samples: 28.jpg
  Notes: Present in local examples folder but not mapped into the current style engine.
- `29` (1 files)
  Canonical: `29`
  Style families: None
  Recipes: None
  Samples: 29.jpg
  Notes: Present in local examples folder but not mapped into the current style engine.
- `32` (1 files)
  Canonical: `32`
  Style families: None
  Recipes: None
  Samples: 32.jpg
  Notes: Present in local examples folder but not mapped into the current style engine.
- `33` (1 files)
  Canonical: `33`
  Style families: None
  Recipes: None
  Samples: 33.jpg
  Notes: Present in local examples folder but not mapped into the current style engine.
- `36` (1 files)
  Canonical: `36`
  Style families: None
  Recipes: None
  Samples: 36.jpg
  Notes: Present in local examples folder but not mapped into the current style engine.
- `37` (1 files)
  Canonical: `37`
  Style families: None
  Recipes: None
  Samples: 37.jpg
  Notes: Present in local examples folder but not mapped into the current style engine.
- `40` (1 files)
  Canonical: `40`
  Style families: None
  Recipes: None
  Samples: 40.jpg
  Notes: Present in local examples folder but not mapped into the current style engine.
- `41` (1 files)
  Canonical: `41`
  Style families: None
  Recipes: None
  Samples: 41.jpg
  Notes: Present in local examples folder but not mapped into the current style engine.
- `44` (1 files)
  Canonical: `44`
  Style families: None
  Recipes: None
  Samples: 44.jpg
  Notes: Present in local examples folder but not mapped into the current style engine.
- `45` (1 files)
  Canonical: `45`
  Style families: None
  Recipes: None
  Samples: 45.jpg
  Notes: Present in local examples folder but not mapped into the current style engine.
- `5` (5 files)
  Canonical: `5`
  Style families: None
  Recipes: None
  Samples: 5-1.jpg, 5-2.jpg, 5-3.jpg
  Notes: Present in local examples folder but not mapped into the current style engine.
- `Carousel4` (7 files)
  Canonical: `Carousel4`
  Style families: None
  Recipes: None
  Samples: Carousel4-1.png, Carousel4-2.png, Carousel4-3.png
  Notes: Present in local examples folder but not mapped into the current style engine.
- `Carousel5` (7 files)
  Canonical: `Carousel5`
  Style families: None
  Recipes: None
  Samples: Carousel5-1.png, Carousel5-2.png, Carousel5-3.png
  Notes: Present in local examples folder but not mapped into the current style engine.
- `Carousel6` (16 files)
  Canonical: `Carousel6`
  Style families: None
  Recipes: None
  Samples: Carousel6-1-1.png, Carousel6-1.png, Carousel6-2-1.png
  Notes: Present in local examples folder but not mapped into the current style engine.
- `Carousel8` (7 files)
  Canonical: `Carousel8`
  Style families: None
  Recipes: None
  Samples: Carousel8-1.png, Carousel8-11.png, Carousel8-9-1.png
  Notes: Present in local examples folder but not mapped into the current style engine.
- `Carousel8-9bis` (1 files)
  Canonical: `Carousel8-9bis`
  Style families: None
  Recipes: None
  Samples: Carousel8-9bis.png
  Notes: Present in local examples folder but not mapped into the current style engine.
- `Figma vs Sketch_ ` (1 files)
  Canonical: `Figma vs Sketch_ `
  Style families: None
  Recipes: None
  Samples: Figma vs Sketch_ .png
  Notes: Present in local examples folder but not mapped into the current style engine.
- `Frame 1` (8 files)
  Canonical: `Frame 1`
  Style families: None
  Recipes: None
  Samples: Frame 1-1.png, Frame 1-2.png, Frame 1-3.png
  Notes: Present in local examples folder but not mapped into the current style engine.
- `Frame 15` (8 files)
  Canonical: `Frame 15`
  Style families: None
  Recipes: None
  Samples: Frame 15-1.png, Frame 15-2.png, Frame 15-3.png
  Notes: Present in local examples folder but not mapped into the current style engine.
- `Frame 16` (5 files)
  Canonical: `Frame 16`
  Style families: None
  Recipes: None
  Samples: Frame 16-1.png, Frame 16-2.png, Frame 16-3.png
  Notes: Present in local examples folder but not mapped into the current style engine.
- `Frame 17` (5 files)
  Canonical: `Frame 17`
  Style families: None
  Recipes: None
  Samples: Frame 17-1.png, Frame 17-2.png, Frame 17-3.png
  Notes: Present in local examples folder but not mapped into the current style engine.
- `Frame 18` (5 files)
  Canonical: `Frame 18`
  Style families: None
  Recipes: None
  Samples: Frame 18-1.png, Frame 18-2.png, Frame 18-3.png
  Notes: Present in local examples folder but not mapped into the current style engine.
- `Frame 19` (5 files)
  Canonical: `Frame 19`
  Style families: None
  Recipes: None
  Samples: Frame 19-1.png, Frame 19-2.png, Frame 19-3.png
  Notes: Present in local examples folder but not mapped into the current style engine.
- `Frame 20` (5 files)
  Canonical: `Frame 20`
  Style families: None
  Recipes: None
  Samples: Frame 20-1.png, Frame 20-2.png, Frame 20-3.png
  Notes: Present in local examples folder but not mapped into the current style engine.
- `Frame 21` (5 files)
  Canonical: `Frame 21`
  Style families: None
  Recipes: None
  Samples: Frame 21-1.png, Frame 21-2.png, Frame 21-3.png
  Notes: Present in local examples folder but not mapped into the current style engine.
- `Frame 34034` (3 files)
  Canonical: `Frame 34034`
  Style families: None
  Recipes: None
  Samples: Frame 34034-1.png, Frame 34034-2.png, Frame 34034.png
  Notes: Present in local examples folder but not mapped into the current style engine.
- `Frame 34303` (11 files)
  Canonical: `Frame 34303`
  Style families: None
  Recipes: None
  Samples: Frame 34303-1.png, Frame 34303-10.png, Frame 34303-2.png
  Notes: Present in local examples folder but not mapped into the current style engine.
- `Frame 34304` (4 files)
  Canonical: `Frame 34304`
  Style families: None
  Recipes: None
  Samples: Frame 34304-1.png, Frame 34304-2.png, Frame 34304-3.png
  Notes: Present in local examples folder but not mapped into the current style engine.
- `Frame 34305` (7 files)
  Canonical: `Frame 34305`
  Style families: None
  Recipes: None
  Samples: Frame 34305-1.png, Frame 34305-2.png, Frame 34305-3.png
  Notes: Present in local examples folder but not mapped into the current style engine.
- `Frame 34306` (8 files)
  Canonical: `Frame 34306`
  Style families: None
  Recipes: None
  Samples: Frame 34306-1.png, Frame 34306-2.png, Frame 34306-3.png
  Notes: Present in local examples folder but not mapped into the current style engine.
- `Frame 34307` (1 files)
  Canonical: `Frame 34307`
  Style families: None
  Recipes: None
  Samples: Frame 34307.png
  Notes: Present in local examples folder but not mapped into the current style engine.
- `Frame 34308` (1 files)
  Canonical: `Frame 34308`
  Style families: None
  Recipes: None
  Samples: Frame 34308.png
  Notes: Present in local examples folder but not mapped into the current style engine.
- `Frame 34309` (1 files)
  Canonical: `Frame 34309`
  Style families: None
  Recipes: None
  Samples: Frame 34309.png
  Notes: Present in local examples folder but not mapped into the current style engine.
- `Frame 6` (30 files)
  Canonical: `Frame 6`
  Style families: None
  Recipes: None
  Samples: Frame 6-1.png, Frame 6-10.png, Frame 6-11.png
  Notes: Present in local examples folder but not mapped into the current style engine.
- `Profile Picture` (5 files)
  Canonical: `Profile Picture`
  Style families: None
  Recipes: None
  Samples: Profile Picture-1.png, Profile Picture-2.png, Profile Picture-3.png
  Notes: Present in local examples folder but not mapped into the current style engine.
- `TwitterPost_01` (1 files)
  Canonical: `TwitterPost_01`
  Style families: None
  Recipes: None
  Samples: TwitterPost_01.png
  Notes: Present in local examples folder but not mapped into the current style engine.
- `TwitterPost_03` (1 files)
  Canonical: `TwitterPost_03`
  Style families: None
  Recipes: None
  Samples: TwitterPost_03.png
  Notes: Present in local examples folder but not mapped into the current style engine.
- `TwitterPost_04` (1 files)
  Canonical: `TwitterPost_04`
  Style families: None
  Recipes: None
  Samples: TwitterPost_04.png
  Notes: Present in local examples folder but not mapped into the current style engine.
- `TwitterPost_05` (1 files)
  Canonical: `TwitterPost_05`
  Style families: None
  Recipes: None
  Samples: TwitterPost_05.png
  Notes: Present in local examples folder but not mapped into the current style engine.
- `TwitterPost_06` (1 files)
  Canonical: `TwitterPost_06`
  Style families: None
  Recipes: None
  Samples: TwitterPost_06.png
  Notes: Present in local examples folder but not mapped into the current style engine.
- `TwitterPost_07` (1 files)
  Canonical: `TwitterPost_07`
  Style families: None
  Recipes: None
  Samples: TwitterPost_07.png
  Notes: Present in local examples folder but not mapped into the current style engine.
- `TwitterPost_09` (1 files)
  Canonical: `TwitterPost_09`
  Style families: None
  Recipes: None
  Samples: TwitterPost_09.png
  Notes: Present in local examples folder but not mapped into the current style engine.
