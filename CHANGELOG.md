# Sebareflexia — Improved

Upravená je existujúca piata verzia projektu, nie novo vytvorený film.
Zdroj má **1:53 / 2 712 snímok / 24 fps**; toto časovanie zostáva zachované.
Pôvodný projekt, `BlenderAnim.zip` a `BlenderAnim_final.mp4` zostávajú dostupné.

| Zábery | Zmeny |
| --- | --- |
| Zastávka a rozhovor, 0:00–0:31 | Animovaný úsmev dievčaťa, prechod k obavám, žmurkanie, malé pohyby očí a hlavy. Chlapec skláňa hlavu, jemne pohybuje ramenami a spustí ruky pred odpoveďou. Pomalšie odmietavé gesto hlavy. Titulok „No, I'm not...“ je presunutý dovnútra obrazu; jeho znenie a časovanie sú zachované. |
| Autobus, 0:31–0:43 | Čelné sklo, stierače, zrkadlá, okná, svetlomety, zadné svetlá a viditeľné náboje kolies. Otvárateľné posuvné dvere a skutočný otvor v karosérii. Plynulé brzdenie a rozjazd, státie počas nastupovania. Vstávanie s predklonom, zhodné pózy oboch kópií dievčaťa pri prechode, zaoblená cesta okolo prístrešku a výstup po schodíkoch. Kamera vidí vstup. |
| Štúdio, 0:52–1:17 | Zachované **jediné stlačenie medzerníka**. Dva detaily vložené do existujúcej dĺžky: klávesnica a otočný ovládač. Ľavá ruka pomaly nastaví ovládač, pravá už znovu nestláča klávesnicu. Pohyblivý kurzor a stereo indikátory na monitore, jemné prikyvovanie pri počúvaní, plynulý posun kamery a mäkké doplnkové svetlo. |
| Koncert, 1:17–1:53 | Zachovaný príchod, pomalé zamávanie a spustenie ruky pred odletom kamery. Pomalý pohyb reflektorov, riedka statická hmla bez simulácie, teplé obrysové svetlo. Pridaných 976 jednoduchých vzdialených divákov v jednom objekte; centrálna prístupová cesta ostáva voľná. Dvadsaťsekundový odlet odhalí väčšiu hĺbku areálu. |
| Obraz a záver | Zachovaná modrofialová farebnosť, dážď, tmavé vlasy a čisté tričko. Jemná hĺbka ostrosti vo vybraných detailoch, tlmenejšia žiara, plynulé prechody cez čiernu. Nová čitateľná záverečná veta v kurzíve. |

> Maybe in another life, I'll be more than just a dreamer.

Zvukové stopy sa nemažú ani neposúvajú. WAV, hlasitosť, začiatok, koniec a stav
stlmenia zostávajú identické. Pôvodné repliky sú naďalej titulky; nový dabing
sa nevytváral. Jeden rytmický podklad hrá v štúdiu tak ako v piatej verzii.

## Súbory a reprodukcia

- `Sebareflexia_Improved.blend`: samostatný upravený projekt, EEVEE, 1280 × 720,
  24 fps, 32 vzoriek. Zvuk `final_mix_v5.wav` je vedľa neho; titulok je zabalený v projekte.
- `source/improve_sebareflexia.py`: zmeny existujúceho projektu. Spusti ho cez
  Blender 4.3.2 na pôvodnej piatej verzii. Potrebuje priložené `geometry_v2.py`,
  `animation_v2.py` a Pillow v Python prostredí Blenderu. Na bežné otvorenie
  alebo render hotového `.blend` Pillow ani žiadny doplnok netreba.
- `source/validate_sebareflexia.py`: kontrola uloženého projektu v novom procese.
- `source/render_sebareflexia.py` a `source/assemble_sebareflexia.py`: render
  reprezentatívnych snímok a kompletného ľahkého náhľadu; zostavenie MP4 používa FFmpeg/FFprobe.
- `assets/closing_words.txt`, `closing_title.png` a font s licenciou: podklady záverečnej vety.

Príklad reprodukcie po rozbalení oboch balíkov do rovnakého priečinka:

```sh
blender -b BlenderAnim/output/bus_stop_to_stage.blend --python Sebareflexia_Improved/source/improve_sebareflexia.py -- --output Sebareflexia_Rebuilt
blender -b Sebareflexia_Rebuilt/Sebareflexia_Improved.blend --python Sebareflexia_Improved/source/validate_sebareflexia.py
```

## Overenie a rozsah výstupu

Generátor aj samostatné otvorenie projektu boli spustené v Blenderi 4.3.2.
Kontroly overujú spojenie končatín, kontinuitu natočenia pri chôdzi, dosiahnutie
vnútra autobusu, státie autobusu pri nastupovaní, jedno stlačenie klávesnice,
pôvodné strihy, dĺžku filmu, dostupnosť súborov, obsah zvuku a čierne prechody.
Podrobné záznamy sú v `source/*report.json`.

Reprezentatívne PNG sú v `previews/`. Kompletné video je **náhľad 480 × 270 v nižšom rozlíšení**;
finálny render 1280 × 720 s 32 vzorkami treba spustiť v Blenderi cez
**Render → Render Animation**. Náhľad používa natívne snímky s frekvenciou
12 fps a optické dopočítanie na 24 fps osobitne v každom zábere. Pohyby v
samotnom projekte sú animované v plných 24 fps. Mimika používa jednoduché
deformácie a transformácie existujúcich modelov, bez foneticky presného lip-syncu.
