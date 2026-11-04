"""Encode the complete preview, interpolating only within each camera shot.

python3 assemble_sebareflexia.py --root improved --follow
Source frames are native EEVEE 480x270 at 12 fps; delivered preview is 24 fps.
The editable .blend remains a full 24 fps, 1280x720/32-sample project.
"""
from pathlib import Path
import argparse
import json
import subprocess
import time

parser=argparse.ArgumentParser()
parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parent/'improved')
parser.add_argument('--follow',action='store_true')
args=parser.parse_args();root=args.root.resolve()
report=json.loads((root/'source/build_report.json').read_text())
cuts=sorted(f for f,_ in report['all_markers'])+[report['frame_end']+1]
frames=root/'preview_frames';encoded=root/'encoded_preview';encoded.mkdir(exist_ok=True)
for i,(start,end) in enumerate(zip(cuts,cuts[1:]),1):
    destination=encoded/f'{i:02d}.mp4';count=end-start
    if destination.exists():
        duration=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(destination)]))
        if abs(duration-count/24)<.01:continue
    temporary=encoded/f'{i:02d}.partial.mp4'
    filters=f'tpad=start_mode=clone:start_duration=0.166667:stop_mode=clone:stop_duration=0.25,minterpolate=fps=24:mi_mode=mci:mc_mode=aobmc:vsbmc=1:scd=none,trim=start_frame=4:end_frame={count+4},setpts=PTS-STARTPTS'
    command=['ffmpeg','-y','-loglevel','warning','-threads','1','-filter_threads','1',
             '-f','image2pipe','-vcodec','png','-framerate','12','-i','pipe:0',
             '-vf',filters,'-frames:v',str(count),'-c:v','libx264','-preset','medium',
             '-crf','18','-pix_fmt','yuv420p','-r','24','-movflags','+faststart',str(temporary)]
    with subprocess.Popen(command,stdin=subprocess.PIPE) as p:
        for frame in range(start,end,2):
            file=frames/f'{frame:05d}.png'
            while not file.exists():
                if not args.follow:raise RuntimeError(f'Missing native frame {frame}')
                if p.poll() is not None:raise RuntimeError('Encoder stopped')
                time.sleep(.25)
            p.stdin.write(file.read_bytes())
        p.stdin.close()
        assert p.wait()==0
    temporary.replace(destination)
    print('SF_SHOT_ENCODED',i,start,end-1,flush=True)
listing=encoded/'concat.txt'
listing.write_text(''.join("file '"+str(encoded/f'{i:02d}.mp4')+"'\n" for i in range(1,len(cuts))))
output=root/'Sebareflexia_Improved_Preview.mp4'
subprocess.run(['ffmpeg','-y','-loglevel','warning','-f','concat','-safe','0','-i',str(listing),'-i',str(root/'final_mix_v5.wav'),
                '-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-t','113','-movflags','+faststart',str(output)],check=True)
info=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_entries','stream=codec_name,codec_type,width,height,r_frame_rate,nb_read_frames:format=duration','-of','json',str(output)]))
video=next(s for s in info['streams'] if s['codec_type']=='video')
assert video['nb_read_frames']=='2712' and video['r_frame_rate']=='24/1'
assert abs(float(info['format']['duration'])-113)<.01
subprocess.run(['ffmpeg','-v','error','-i',str(output),'-f','null','-'],check=True)
info['native_source_fps']=12;info['interpolation']='motion compensated, within individual shots only';info['complete_file_decoded']=True
(root/'source/video_validation.json').write_text(json.dumps(info,indent=2))
print('SF_COMPLETE_PREVIEW_VALIDATED',json.dumps(info),flush=True)
