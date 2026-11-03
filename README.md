# BlenderAnim — melancholická verzia

[Stiahnuť celý film (MP4)](BlenderAnim_final.mp4?raw=true) · [Stiahnuť Blender projekt a film (ZIP)](BlenderAnim.zip?raw=true)

Na stránke súboru klikni na **Download raw file**. ZIP rozbaľ a v Blenderi 4.3 alebo novšom otvor **BlenderAnim → output → bus_stop_to_stage.blend**. Celé výsledné video je v súbore `BlenderAnim_final.mp4`.

Film má **1 minútu 49 sekúnd**. Táto verzia pridáva tlmený modrofialový color grading, jemnejší kontrast, nápis **Adrian** na prednej aj zadnej strane trička a záverečný text v jemnej kurzíve. Veta sa postupne objavuje počas posledného odletu kamery a na konci mizne do čiernej:

> Maybe in another life, there will be an opportunity, to be more than a dreamer, Adrian

Upravená je aj kamera štúdiového detailu, aby monitor nezakrýval tvár. Zachované sú pomalšia chôdza a kamery, spojené kĺby, dlhšie pauzy pri klávesnici, žiarovka pri nápade, stmavenie pred koncertom, zmrazenie na pódiu a festivalový areál so svetlami a prírodou.

Medzerník v Blenderi spustí prehrávanie, Num0 zobrazí kameru. **Render → Render Animation** vyrenderuje celý projekt. Farebný grading, záverečná veta, žiara a stmavenia sú v kompozitore; bežné 3D okno ich nemusí zobrazovať. Hotové MP4 obsahuje všetky efekty.

Video má 960 × 540, 24 fps, obraz H.264 a zvuk AAC. Ide o štylizovanú 3D animáciu; repliky sú zobrazené titulkami. Hudba, beaty a zvukové efekty sú vlastné syntetické nahrávky. Blender projekt je pripravený na render 1280 × 720 s 32 vzorkami a animáciou v plných 24 fps. Dodané video používa 12 vyrenderovaných časových snímok za sekundu a optické dopočítanie na 24 fps, osobitne v každom zábere.

Grafika trička a záverečného textu je zabalená priamo v `.blend`. Zvuk `final_mix.wav` nechaj vedľa projektu. Editovateľné grafické podklady, fonty s licenciou a presné znenie vety sú aj v `output/assets_v3/`. Na otvorenie a render projektu netreba doplnky ani sťahovať modely. Zdrojové skripty a technické poznámky sú v `source/`.
