# BlenderAnim — dážď, upravená postava a pozdrav publiku

[Stiahnuť celý film (MP4)](BlenderAnim_final.mp4?raw=true) · [Stiahnuť Blender projekt a film (ZIP)](BlenderAnim.zip?raw=true)

Na stránke súboru klikni na **Download raw file**. ZIP rozbaľ a v Blenderi 4.3 alebo novšom otvor **BlenderAnim → output → bus_stop_to_stage.blend**. Celé výsledné video je v súbore `BlenderAnim_final.mp4`.

Film má **1 minútu 53 sekúnd**. Postava má čisté čierne tričko bez nápisu, prepracovanú tvár s jemnejším nosom a perami, zapustenými očami a veľmi tmavými hnedými vlasmi. Na zastávke prší; scénu dopĺňajú mláky, chladnejšie svetlo a jemný zvuk dažďa.

Po príchode do stredu pódia postava pomaly zdvihne ruku, zamáva publiku a ruku spustí. Po krátkej pauze sa začne dvadsaťsekundový odlet kamery. Počas neho sa v jemnej kurzíve postupne objaví záverečná veta a na konci zmizne do čiernej:

> Maybe in another life, there will be an opportunity, to be more than a dreamer, Adrian

Film má melancholický modrofialový grading, pomalšiu chôdzu a kamery, dlhšie pauzy pri klávesnici, žiarovku pri nápade, stmavenie pred koncertom a festivalový areál so svetlami a prírodou. Štúdiový detail ukazuje tvár z miernejšieho uhla.

Medzerník v Blenderi spustí prehrávanie, Num0 zobrazí kameru. **Render → Render Animation** vyrenderuje celý projekt. Farebný grading, záverečná veta, žiara a stmavenia sú v kompozitore; bežné 3D okno ich nemusí zobrazovať. Hotové MP4 obsahuje všetky efekty.

Video má 960 × 540, 24 fps, obraz H.264 a zvuk AAC. Ide o štylizovanú 3D animáciu; repliky sú zobrazené titulkami. Hudba, beaty a zvukové efekty sú vlastné syntetické nahrávky. Blender projekt je pripravený na render 1280 × 720 s 32 vzorkami a animáciou v plných 24 fps. Dodané video používa 12 vyrenderovaných časových snímok za sekundu a optické dopočítanie na 24 fps, osobitne v každom zábere.

Grafika záverečného textu je zabalená priamo v `.blend`. Zvuk `final_mix_v4.wav` nechaj vedľa projektu. Grafický podklad, font s licenciou a presné znenie vety sú aj v `output/assets_v3/`. Na otvorenie a render projektu netreba doplnky ani sťahovať modely. Zdrojové skripty a technické poznámky sú v `source/`.
