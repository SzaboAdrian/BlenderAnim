"""Native EEVEE representative stills or complete lightweight preview frames.

Run against Sebareflexia_Improved.blend. -- --proof 265 573 ... renders 960x540
stills at 24 samples. Otherwise renders all odd frames at 480x270/6 samples.
Two independent workers may safely share the full-preview directory.
"""
from pathlib import Path
import os
import sys
import time
import bpy

s=bpy.context.scene
root=Path(bpy.data.filepath).resolve().parent
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
proof=bool(args and args[0]=='--proof')
frames=[int(f) for f in args[1:]] if proof or (args and args[0]=='--frames') else range(1,s.frame_end+1,2)
folder=root/('previews' if proof else 'preview_frames')
folder.mkdir(exist_ok=True);pending=folder/'.pending';pending.mkdir(exist_ok=True)
s.render.engine='BLENDER_EEVEE_NEXT'
s.render.resolution_x=960 if proof else 480
s.render.resolution_y=540 if proof else 270
s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.render.image_settings.compression=15
s.render.use_border=False;s.render.use_crop_to_border=False
s.eevee.taa_render_samples=24 if proof else 6
for f in frames:
    final=folder/f'{f:05d}.png'
    if final.exists():continue
    lock=pending/f'{f:05d}.lock'
    try:
        fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.write(fd,str(os.getpid()).encode());os.close(fd)
    except FileExistsError:continue
    try:
        s.frame_set(f)
        temporary=pending/f'{f:05d}-{os.getpid()}.png'
        s.render.filepath=str(temporary)
        begin=time.time();bpy.ops.render.render(write_still=True)
        temporary.replace(final)
        print('SF_FRAME',f,round(time.time()-begin,3),flush=True)
    finally:lock.unlink(missing_ok=True)
print('SF_RENDER_COMPLETE',flush=True)
