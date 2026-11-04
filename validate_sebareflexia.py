"""Validate the saved improved project in a fresh Blender process."""
from pathlib import Path
import hashlib
import json
import math
import wave
import bpy
from mathutils import Vector

s=bpy.context.scene
root=Path(bpy.data.filepath).resolve().parent
build=json.loads((root/'source/build_report.json').read_text())
assert s.get('sebareflexia_improved') and s.frame_start==1 and s.frame_end==2712
assert s.render.fps==24 and s.render.engine=='BLENDER_EEVEE_NEXT'
assert s.render.filepath=='//Sebareflexia_Improved.mp4'
assert not any(o.get('shirt_print') for o in s.objects)
sounds=[]
for q in s.sequence_editor.sequences:
    if q.type=='SOUND':
        path=Path(bpy.path.abspath(q.sound.filepath))
        assert path.exists() and q.sound.filepath.startswith('//')
        sounds.append(dict(name=q.name,type=q.type,start=q.frame_start,end=q.frame_final_end,
                           volume=q.volume,mute=q.mute,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        with wave.open(str(path)) as audio:assert audio.getnframes()/audio.getframerate()==113
assert sounds==build['audio_preserved']
assert s['closing_quote']=="Maybe in another life, I'll be more than just a dreamer."
assert s.node_tree.nodes['Closing words'].image.packed_file
for image in bpy.data.images:
    if image.source=='FILE' and image.users:assert image.packed_file or Path(bpy.path.abspath(image.filepath)).exists(),image.name
cuts=sorted(m.frame for m in s.timeline_markers if m.camera)
assert cuts==[1,193,313,505,649,745,1033,1249,1261,1321,1465,1537,1705,1849,2233]
for f,name in build['original_markers']:
    assert any(m.frame==f and m.camera and m.camera.name==name for m in s.timeline_markers)
assert s.objects['Woman seated head unified geometry'].data.shape_keys.key_blocks.get('SF - warm noticing smile')
assert s.objects['Woman seated head unified geometry'].data.shape_keys.key_blocks.get('SF - relaxed blink')
presses=[];in_press=False;max_gap=0;max_root_step=0;max_root_yaw=0;lastpos=None;lastrz=None
for frame in range(1,2713):
    # Evaluate dense acting intervals; sample environmental sections sparsely.
    if not (765<=frame<=1020 or 1249<=frame<=1848 or frame%24==1 or frame in cuts):continue
    s.frame_set(frame)
    camera=s.camera
    assert camera is not None
    assert all(math.isfinite(v) for row in camera.matrix_world for v in row)
    if 1249<=frame<=1848:
        hand=s.objects['Narrator at computer hand.001'];space=s.objects['Spacebar']
        press=hand.location.z<1.065
        if press and not in_press:presses.append(frame)
        in_press=press
        if frame>=1297:
            assert abs(hand.location.z-1.07)<1e-6 and abs(space.location.z-1.014)<1e-6
    if 765<=frame<=1020:
        actor=s.objects['Woman standing']
        if lastpos is not None:
            max_root_step=max(max_root_step,(actor.location-lastpos).length)
            max_root_yaw=max(max_root_yaw,abs(actor.rotation_euler.z-lastrz))
        lastpos=actor.location.copy();lastrz=actor.rotation_euler.z
        # Both copies share the exact transform and pose through the handoff.
        a=s.objects['Woman seated'];b=s.objects['Woman standing']
        assert (a.location-b.location).length<1e-6
    for name in (['Woman seated' if frame<825 else 'Woman standing'] if 765<=frame<=1020 else ['Narrator at computer'] if 1249<=frame<=1848 else []):
        for suffix in ['', '.001']:
            upper=s.objects[name+' upper arm'+suffix];lower=s.objects[name+' forearm'+suffix];hand=s.objects[name+' hand'+suffix]
            a=upper.matrix_basis@Vector((0,0,.155));b=lower.matrix_basis@Vector((0,0,-.16));c=lower.matrix_basis@Vector((0,0,.16))
            max_gap=max(max_gap,(a-b).length,(c-hand.location).length)
            if name.startswith('Woman'):
                upper=s.objects[name+' upper leg'+suffix];lower=s.objects[name+' lower leg'+suffix]
                max_gap=max(max_gap,((upper.matrix_basis@Vector((0,0,.23)))-(lower.matrix_basis@Vector((0,0,-.23)))).length)
assert presses==[1276],presses
assert max_gap<.0001,max_gap
assert max_root_step<.12,max_root_step
assert max_root_yaw<.55,max_root_yaw
bus=s.objects['Arriving bus']
for f in [827,851,950,1018,1044]:
    s.frame_set(f);assert abs(bus.location.x)<1e-6
for f in [1248,1249,1848,1849,2712]:
    s.frame_set(f)
    assert max(s.node_tree.nodes['Editorial fades'].inputs[2].default_value[:3])<1e-6
s.frame_set(1018)
girl=s.objects['Woman standing']
assert abs(girl.location.x+2.70)<.02 and girl.location.y>2.90 and girl.location.z>.5
report={'file_opens':True,'seconds':113,'frames':2712,'fps':24,'original_audio_strips_and_pcm_identical':True,
        'all_original_cuts_preserved':True,'additional_insert_cuts':[1261,1321,1465,1537],
        'one_keyboard_press_episode':presses,'max_limb_joint_gap_m':max_gap,
        'max_boarding_root_step_m':max_root_step,'max_boarding_yaw_step_radians':max_root_yaw,
        'girl_reaches_bus_interior':True,'bus_stationary_during_boarding':True,
        'transition_midpoints_black':True,'packed_title':True,'relative_audio_resolves':True}
(root/'source/validation_report.json').write_text(json.dumps(report,indent=2))
print('SEBAREFLEXIA_VALIDATED',json.dumps(report),flush=True)
