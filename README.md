# BlenderAnim — celý film

[Stiahnuť celý film (MP4)](BlenderAnim_final.mp4?raw=true) · [Stiahnuť Blender projekt a film (ZIP)](BlenderAnim.zip?raw=true)

Na stránke súboru môžeš použiť aj **Download raw file**. ZIP rozbaľ a v Blenderi otvor `BlenderAnim/output/bus_stop_to_stage.blend`.


Celý film má 109 sekúnd. V balíku otvor `output/bus_stop_to_stage.blend` v Blenderi 4.3 alebo novšom. `BlenderAnim_final.mp4` je celé výsledné video, nie výber záberov.

Zmeny: odstránený nápis BUS / 24, pomalšie kamery a chôdza, kratšie kroky s užším postojom, spojené kolená a lakte, spojité quaternionové rotácie končatín uložené v každej snímke, jemnejšie sadanie a vstávanie, šesť stlačení klávesnice s intervalom 4,5 sekundy, rozsvietená žiarovka pri nápade, stmavenie a rozsvietenie pred koncertom, 20-sekundový odlet kamery a festivalový areál s prírodou, stánkami a svetlami.

Video je štylizovaná 3D animácia. Hovorené repliky sú zachované ako titulky. Hudba, beaty, atmosféra a zvukové efekty sú vlastné syntetické zvuky bez prevzatých nahrávok. Nejde o fotorealistický film alebo motion capture.

Video: 960 × 540, 24 fps, H.264/AAC. Kompletné 3D zábery sú renderované v EEVEE s priestorovým vzorkovaním a 12 časovými snímkami za sekundu; medzisnímky do 24 fps sa dopočítavajú optickým pohybom osobitne v každom zábere, bez miešania cez strihy. Blender projekt obsahuje animáciu v plných 24 fps a je pripravený aj na vlastný render 1280 × 720 / 32 vzoriek.

Zvukový súbor `final_mix.wav` nechaj vedľa súboru `.blend`. Všetky cesty v projekte sú relatívne. Odporúčaný postup: File → Open, vybrať projekt; Num0 zobrazí kameru a medzerník spustí prehrávanie. Render → Render Animation vytvorí celý film podľa výkonu tvojho počítača.

Zdrojové skripty v `source/` dokumentujú úpravy. Renderovací projekt spája statické objekty a dav, aby prehrávanie bolo menej náročné. Film nevyžaduje žiadne sťahované modely, externé textúry ani doplnky.

Prechody do čiernej a žiara sa aplikujú v kompozitore pri renderovaní. Bežný náhľad v 3D okne ich nemusí zobrazovať; hotové MP4 obsahuje všetky efekty.
