"""Polish the existing fifth-edition film without rebuilding its scenes.

Blender 4.3.2:
  blender -b output/film_render_v5.blend --python improve_sebareflexia.py
Optional: -- --output /absolute/path/to/release
Requires Pillow for the packed, editable closing artwork. No downloaded assets.
The input project and its soundtrack are never overwritten.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import random
import shutil
import sys

import bpy
from mathutils import Vector, Matrix

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from geometry_v2 import box, sphere, rod, mesh, empty, material
from animation_v2 import ik, ease, walk, route_point, progress

args = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
parser = argparse.ArgumentParser()
parser.add_argument('--output', type=Path, default=HERE/'improved')
OUT = parser.parse_args(args).output.resolve()
for folder in [OUT, OUT/'assets', OUT/'source', OUT/'previews']:
    folder.mkdir(parents=True, exist_ok=True)
S = bpy.context.scene
END = S.frame_end
assert END == 2712 and S.render.fps == 24, 'Expected the existing 113-second film.'
assert not S.get('sebareflexia_improved'), 'Start from the original fifth-edition file.'
SOURCE = Path(bpy.data.filepath).resolve()
assert SOURCE != OUT/'Sebareflexia_Improved.blend'
SOURCE_HASH = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
ORIGINAL_MARKERS = [(m.frame, m.camera.name) for m in S.timeline_markers if m.camera]
DIALOGUE = {o.name: o.data.body for o in S.objects if o.type == 'FONT'}


def audio_snapshot():
    return [dict(name=q.name, type=q.type, start=q.frame_start,
                 end=q.frame_final_end, volume=q.volume, mute=q.mute,
                 sha256=hashlib.sha256(Path(bpy.path.abspath(q.sound.filepath)).read_bytes()).hexdigest())
            for q in S.sequence_editor.sequences if q.type == 'SOUND']


AUDIO = audio_snapshot()


def smooth_keys(owner, paths=None):
    if not owner.animation_data or not owner.animation_data.action:
        return
    for fc in owner.animation_data.action.fcurves:
        if paths and fc.data_path not in paths:
            continue
        if fc.data_path in {'hide_render', 'hide_viewport'}:
            continue
        for k in fc.keyframe_points:
            k.interpolation = 'BEZIER'
            k.handle_left_type = k.handle_right_type = 'AUTO_CLAMPED'


def sector(obj, number):
    obj['render_sector'] = number
    obj['sebareflexia_addition'] = True
    for f, active in [(1,0),(1248,0),(1249,1),(1848,1),(1849,2),(END,2)]:
        obj.hide_render = active != number
        obj.keyframe_insert('hide_render', frame=f)
    for fc in obj.animation_data.action.fcurves:
        if fc.data_path == 'hide_render':
            for k in fc.keyframe_points:
                k.interpolation = 'CONSTANT'
    return obj


def key(obj, f, **values):
    for name, value in values.items():
        setattr(obj, name, value)
        obj.keyframe_insert(name, frame=f)


def pose_bone(obj, a, b, f):
    a, b = Vector(a), Vector(b)
    previous = obj.rotation_quaternion.normalized()
    old_axis = previous @ Vector((0,0,1))
    q = old_axis.rotation_difference((b-a).normalized()) @ previous
    q.make_compatible(previous)
    obj.rotation_mode = 'QUATERNION'
    key(obj, f, location=(a+b)/2, rotation_quaternion=q)


def limb(root, label, side):
    return S.objects[root+' '+label+('.001' if side > 0 else '')]


def arm(root, side, f, target, shoulder=None, rotation=None):
    shoulder = Vector(shoulder or (side*.28,-.03,1.30))
    elbow, wrist, _ = ik(shoulder, target, .31, .32, (side,-.15,-.5))
    pose_bone(limb(root,'upper arm',side), shoulder, elbow, f)
    pose_bone(limb(root,'forearm',side), elbow, wrist, f)
    key(limb(root,'elbow',side),f,location=elbow)
    values={'location':wrist}
    if rotation is not None:
        values['rotation_euler']=rotation
    key(limb(root,'hand',side),f,**values)


def weight(f, start, rise, fall, end):
    return ease((f-start)/(rise-start))*(1-ease((f-fall)/(end-fall)))


def vertices_by_material(obj, name):
    slot = next(i for i,m in enumerate(obj.data.materials) if m.name == name)
    return {v for p in obj.data.polygons if p.material_index == slot for v in p.vertices}


def expression(obj, name, transform):
    if not obj.data.shape_keys:
        obj.shape_key_add(name='Basis')
    shape=obj.shape_key_add(name=name)
    for i,v in enumerate(shape.data):
        v.co=transform(i,v.co.copy())
    return shape


def shape_keys(shape, pairs):
    for f,v in pairs:
        shape.value=v
        shape.keyframe_insert('value',frame=f)


def female_expressions():
    for name in ['Woman seated','Woman standing']:
        obj=S.objects[name+' head unified geometry']
        eyes=vertices_by_material(obj,'Woman eyes')
        lips=vertices_by_material(obj,'Woman lips')
        hair=vertices_by_material(obj,'Woman chestnut hair')
        skin=vertices_by_material(obj,'Woman warm skin')
        brows={i for i in hair if -.18<obj.data.vertices[i].co.y<-.14 and .06<obj.data.vertices[i].co.z<.105 and abs(obj.data.vertices[i].co.x)<.12}
        def smile(i,p):
            if i in lips:
                p.z+=.018*(min(1,abs(p.x)/.05)**1.7)
                p.z=-.1+(p.z+.1)*.78
            if i in skin and p.y<-.1 and -.11<p.z<.01:
                p.z+=.004*math.exp(-((abs(p.x)-.10)/.04)**2)*math.exp(-((p.z+.055)/.04)**2)
            if i in brows:p.z+=.003
            return p
        happy=expression(obj,'SF - warm noticing smile',smile)
        shape_keys(happy,[(1,.05),(205,.05),(256,1),(330,.8),(495,.12),(548,0),(END,0)])
        def concern(i,p):
            if i in brows:p.z+=.011*math.exp(-((abs(p.x)-.035)/.045)**2)
            if i in lips:p.z-=.004*(abs(p.x)/.05)**1.7
            return p
        worried=expression(obj,'SF - concerned inner brows',concern)
        shape_keys(worried,[(1,0),(490,0),(551,1),(682,.8),(778,.35),(840,.1),(END,.1)])
        blink=expression(obj,'SF - relaxed blink',lambda i,p:Vector((p.x,p.y,.035+(p.z-.035)*.06)) if i in eyes else p)
        shape_keys(blink,[(1,0),(END,0)])
        for f in [117,285,471,616,768,908,1005]:
            shape_keys(blink,[(f-3,0),(f,1),(f+4,0)])
        gaze=expression(obj,'SF - eyes notice before head',lambda i,p:p+Vector((.0045,-.001,0)) if i in eyes else p)
        shape_keys(gaze,[(1,.05),(210,0),(225,1),(295,.55),(494,.5),(522,1),(660,.7),(780,0),(END,0)])
        speech=expression(obj,'SF - quiet question articulation',lambda i,p:Vector((p.x,p.y-.001,p.z+(.003 if p.z>-.10 else -.003))) if i in lips else p)
        shape_keys(speech,[(1,0),(END,0)])
        for f,v in [(550,0),(561,.7),(569,.15),(581,.9),(590,.1),(604,.6),(615,.15),(628,.4),(639,0)]:
            shape_keys(speech,[(f,v)])
        smooth_keys(obj.data.shape_keys)


def male_expressions():
    for name in ['Narrator seated','Narrator at computer','Narrator on stage']:
        obj=S.objects[name+' head refined surfaces']
        lips=vertices_by_material(obj,'V4 muted natural lips')
        brows=vertices_by_material(obj,'V4 dark brows')
        def sad(i,p):
            if i in brows:p.z+=.008*math.exp(-((abs(p.x)-.03)/.045)**2)
            if i in lips:p.z-=.004*min(1,abs(p.x)/.048)**1.6
            return p
        sadness=expression(obj,'SF - restrained sadness',sad)
        values=[(1,.2),(350,.6),(508,1),(745,1),(1100,.75),(1200,.45),(END,.45)] if name=='Narrator seated' else [(1,.15),(1249,.55),(1470,.35),(1740,.2),(1849,.05),(END,.05)]
        shape_keys(sadness,values)
        if name=='Narrator seated':
            response=expression(obj,'SF - hesitant reply',lambda i,p:Vector((p.x*.97,p.y-.001,p.z+(.002 if p.z>-.153 else -.0025))) if i in lips else p)
            shape_keys(response,[(1,0),(649,0),(671,.75),(685,.2),(699,.6),(716,.15),(732,0),(END,0)])
        smooth_keys(obj.data.shape_keys)
        # Move just the iris material vertices inside each existing almond eye.
        for pivot in [c for c in S.objects[name+' head'].children if 'eye pivot' in c.name]:
            eye=next(c for c in pivot.children if c.type=='MESH')
            iris=set()
            for matname in ['V4 brown iris','V4 pupils','V4 iris outer ring','V4 small eye highlights']:
                iris|=vertices_by_material(eye,matname)
            gaze=expression(eye,'SF - tiny gaze shifts',lambda i,p:p+Vector((.0028,-.0003,-.0005)) if i in iris else p)
            # Nonperiodic attention shifts; movement stays inside the eyelid rim.
            for f,v in [(1,.2),(380,.2),(386,.8),(508,.4),(650,.15),(660,.6),(728,.35),(1090,.2),(1100,.65),(1273,.6),(1455,.6),(1463,1),(1570,.5),(1730,.5),(1740,.12),(1830,.35),(END,.35)]:
                shape_keys(gaze,[(f,v)])
            smooth_keys(eye.data.shape_keys)


def body_acting():
    # Add measured secondary acting to existing animation, keeping established gait.
    for name,start,end in [('Narrator seated',313,1248),('Woman seated',1,784),('Narrator at computer',1249,1848),('Narrator on stage',1849,END)]:
        head=S.objects[name+' head']
        torso=next(o for o in S.objects[name].children if 'torso' in o.name)
        for f in range(start,end+1):
            S.frame_set(f)
            breath=math.sin(f*math.tau/(24*4.8)+.6)
            head.rotation_euler.y+=.008*math.sin(f*.021+.4)
            head.rotation_euler.z+=.007*math.sin(f*.013)
            head.location.z+=.0015*breath
            if name=='Narrator seated':
                sadness=weight(f,480,540,1090,1200)
                head.rotation_euler.x+=.055*sadness
                torso.rotation_euler.x+=.025*sadness
                if 649<=f<=744:
                    t=(f-649)/95
                    head.rotation_euler.z=.115*math.sin(math.tau*t)*math.sin(math.pi*t)
                    head.rotation_euler.x=.16+.035*math.sin(math.pi*t)
            elif name=='Woman seated':
                head.rotation_euler.x+=.025*weight(f,502,552,674,754)
                head.rotation_euler.y+=.045*weight(f,502,552,674,754)
                if 193<=f<=312:
                    head.rotation_euler.z=.34*ease((f-222)/58)
            elif name=='Narrator at computer':
                head.rotation_euler.x+=.024+.014*math.sin((f-1273)*math.tau/48)*ease((f-1273)/48)
                head.rotation_euler.z+=.10*weight(f,1433,1477,1513,1585)
                torso.rotation_euler.x+=.008*breath
            else:
                head.rotation_euler.z+=.025*weight(f,2065,2110,2170,2220)
            key(head,f,location=head.location,rotation_euler=head.rotation_euler)
            key(torso,f,rotation_euler=torso.rotation_euler)
        smooth_keys(head,{'location','rotation_euler'})
        smooth_keys(torso,{'rotation_euler'})
    # Hands lower ahead of the boy's reply so the emotional response is visible.
    for f in range(505,1033):
        S.frame_set(f)
        breath=.003*math.sin(f*math.tau/(24*4.5))
        cover=weight(f,510,548,613,661)
        for side in [-1,1]:
            target=Vector((side*.21,-.32,.84)).lerp(Vector((side*.085,-.21,1.56)),cover)
            target.y-=.02*weight(f,661,685,745,815)
            arm('Narrator seated',side,f,target,(side*.28,-.03,1.30+breath))


def stand_and_board():
    # Keep the same two character doubles; match their full pose at the handoff.
    points=[Vector(p) for p in [(-.7,-.72,.055),(-2.95,-.72,.055),(-3.20,.65,.055),(-2.70,1.92,.055),(-2.70,2.20,.205),(-2.70,2.56,.405),(-2.70,2.96,.505)]]
    route=[points[0]]
    for before,p,after in zip(points,points[1:],points[2:]):
        radius=min(.27,(p-before).length*.32,(after-p).length*.32)
        a=p+(before-p).normalized()*radius;b=p+(after-p).normalized()*radius
        for j in range(9):
            t=j/8;route.append((1-t)**2*a+2*t*(1-t)*p+t*t*b)
    route.append(points[-1])
    start,end=849,1018
    previous_rz=0.0
    for f in range(765,1021):
        S.frame_set(f)
        q=ease((f-785)/40)
        pos=Vector((-.7,-.3-.42*q,.11*q))
        lean=.24*math.sin(q*math.pi)+.055*weight(f,767,784,790,817)
        rz=-math.pi/2*ease((f-827)/22)
        moving=f>=start
        phase=0
        if moving:
            p=progress((f-start)/(end-start))
            pos=route_point(route,p)+Vector((0,0,.055))
            tangent=route_point(route,min(1,p+.012))-route_point(route,max(0,p-.012))
            rz=math.atan2(tangent.x,-tangent.y)
        rz=previous_rz+(rz-previous_rz+math.pi)%math.tau-math.pi
        previous_rz=rz
        # Both doubles receive exactly the same root and limb pose.
        for name in ['Woman seated','Woman standing']:
            root=S.objects[name]
            key(root,f,location=pos,rotation_euler=(0,0,rz))
            def local(world):
                d=Vector(world)-pos
                return Vector((math.cos(rz)*d.x+math.sin(rz)*d.y,-math.sin(rz)*d.x+math.cos(rz)*d.y,d.z))
            for side in [-1,1]:
                if moving:
                    foot,phase=walk(f,start,end,route,root,side)
                    foot=local(foot)
                else:
                    foot=local((-.7+side*.105,-.76,.055))
                    final=Vector((side*.105,-.03,.055-pos.z))
                    foot=foot.lerp(final,ease((f-829)/20))
                hip=Vector((side*.105,0,.76))
                knee,ankle,_=ik(hip,foot,.46,.46,(0,-1,0))
                pose_bone(limb(name,'upper leg',side),hip,knee,f)
                pose_bone(limb(name,'lower leg',side),knee,ankle,f)
                key(limb(name,'kneecap',side),f,location=knee)
                key(limb(name,'shoe',side),f,location=ankle+Vector((0,-.065,-.005)),rotation_euler=(0,0,0))
                target=Vector((side*.21,-.32,.84)).lerp(Vector((side*.28,-.1,.80)),q)
                if moving:target.y+=side*.07*math.sin(phase*math.tau)
                arm(name,side,f,target)
            idle=.0025*math.sin(f*.055)
            key(S.objects[name+' head'],f,location=(0,-.015*lean,1.62+idle),rotation_euler=(lean*.35+.018,0,.6*(1-ease((f-780)/65))))
            torso=next(c for c in root.children if 'torso' in c.name)
            key(torso,f,location=(0,0,1.05+idle),rotation_euler=(lean,0,.005*math.sin(phase*math.tau)))
    S['boarding_route']=[list(p) for p in route]
    S['boarding_frames']=[849,1018]


def improve_bus():
    bus=S.objects['Arriving bus']
    # Retain the animated root and original wheels; replace the solid body with
    # a panelled shell that has a real opening at the boarding door.
    for obj in list(bus.children):
        if obj.name in ['Bus body','Bus dark doorway','Bus boarding step'] or obj.name.startswith('Bus window'):
            bpy.data.objects.remove(obj,do_unlink=True)
    paint=material('SF bus muted midnight blue',(.055,.11,.15),rough=.42,metal=.22)
    trim=material('SF bus rubber trim',(.012,.017,.022),rough=.85)
    glass=material('SF bus dark reflective glass',(.022,.055,.075),rough=.25,metal=.30)
    inside=material('SF bus quiet warm interior',(.22,.18,.12),emission=.35,rough=.7)
    headlamp=material('SF bus warm headlights',(1,.78,.46),emission=2.5)
    tail=material('SF bus rear lamps',(.60,.035,.018),emission=1.5)
    chrome=material('SF bus satin wheel hubs',(.25,.30,.32),rough=.35,metal=.65)
    def part(name,loc,dims,mat,parent=bus,bevel=.02):
        return sector(box('SF Bus '+name,loc,dims,mat,parent,bevel),0)
    part('floor',(0,0,.47),(7,2.3,.14),trim)
    part('roof',(0,0,2.75),(7.05,2.4,.19),paint,bevel=.07)
    # Door opening: x -3.24..-2.16; shell is split to avoid a painted-on doorway.
    part('near body',( .67,-1.13,1.05),(5.66,.10,1.10),paint)
    part('front pillar',(-3.38,-1.13,1.54),(.24,.10,2.24),paint)
    part('far body',(0,1.13,1.05),(7,.10,1.10),paint)
    part('front fascia',(-3.48,0,.98),(.13,2.3,.98),paint)
    part('rear panel',(3.48,0,1.48),(.13,2.3,2.25),paint)
    for y in [-1.15,1.15]:
        for x in [-1.60,-.5,.6,1.7,2.8]:
            part('window surround',(x,y,2.09),(1.0,.06,1.0),trim)
            part('side window',(x,y+(-.035 if y<0 else .035),2.09),(.91,.028,.88),glass)
        part('waist stripe',(.68,y+(-.01 if y<0 else .01),1.50),(5.64,.06,.10),chrome)
    part('front windshield',(-3.558,0,2.08),(.035,2.08,1.12),glass)
    part('windscreen divider',(-3.582,0,2.08),(.027,.045,1.13),trim)
    for y in [-.78,.78]:
        part('headlight',(-3.58,y,.94),(.035,.36,.19),headlamp)
        part('tail light',(3.56,y,1.03),(.035,.22,.27),tail)
        sector(rod('SF Bus windshield wiper',(-3.59,y*.8,1.62),(-3.59,y*.5,2.16),.015,trim,bus),0)
    part('front bumper',(-3.58,0,.58),(.16,2.3,.17),chrome)
    for y in [-1.32,1.32]:
        part('mirror',(-3.12,y,2.24),(.17,.10,.30),trim)
    for x in [-2.2,2.2]:
        for side in [-1,1]:
            y=side*1.14
            if side>0:sector(sphere('SF Bus far wheel',(x,y,.45),(.50,.20,.50),trim,bus,n=20,r=12),0)
            hub=sector(rod('SF Bus hub',(x,y+side*.16,.45),(x,y+side*.20,.45),.23,chrome,bus,n=16),0)
            for angle in range(0,360,60):
                a=math.radians(angle)
                sector(sphere('SF Bus hub stud',(x+.15*math.cos(a),y+side*.205,.45+.15*math.sin(a)),(.025,.012,.025),trim,bus,n=8,r=4),0)
    part('interior floor',(-2.7,0,.53),(1.02,2.1,.10),inside)
    for y,z in [(-1.38,.15),(-1.10,.30),(-.80,.45)]:
        part('entry step',(-2.7,y,z),(1.0,.34,.12),chrome)
    part('door warm ceiling',(-2.7,-.55,2.61),(.80,1.0,.04),inside)
    for side in [-1,1]:
        panel=empty('SF Bus sliding door '+str(side),(-2.7+side*.265,-1.205,1.55),bus)
        part('door panel',(0,0,0),(.52,.045,2.0),glass,panel)
        part('door edge',(side*.24,-.03,0),(.025,.035,2.0),chrome,panel)
        part('door lower',(0,-.01,-.68),(.50,.035,.62),paint,panel)
        for f,openness in [(1,0),(831,0),(851,1),(1019,1),(1043,0),(END,0)]:
            key(panel,f,location=(-2.7+side*(.265+.51*openness),-1.205-.055*openness,1.55))
        smooth_keys(panel)
    bus.animation_data_clear()
    for f in range(1,1250):
        if f<713:x=17
        elif f<827:x=17*(1-ease((f-713)/114))
        elif f<1045:x=0
        else:x=-19*ease((f-1045)/159)
        key(bus,f,location=(x,3.5,0))
    smooth_keys(bus)


def camera_path(camera, frames, lens=None, focus=None, aperture=5.6):
    camera.animation_data_clear()
    if lens:camera.data.lens=lens
    for f,loc,target in frames:
        key(camera,f,location=loc,rotation_euler=(Vector(target)-Vector(loc)).to_track_quat('-Z','Y').to_euler())
    smooth_keys(camera)
    if focus:
        camera.data.dof.use_dof=True
        camera.data.dof.focus_object=focus
        camera.data.dof.aperture_fstop=aperture
        camera.data.dof.aperture_blades=6


def new_camera(name, start, end, a, b, target, lens=50):
    data=bpy.data.cameras.new(name)
    obj=bpy.data.objects.new(name,data);S.collection.objects.link(obj)
    focus=empty(name+' focus',target)
    camera_path(obj,[(start,a,target),(end,b,target)],lens,focus,7.1)
    marker=S.timeline_markers.new(name,frame=start);marker.camera=obj
    return obj


def studio():
    graphite=material('SF rotary controller graphite',(.025,.03,.045),rough=.65)
    silver=material('SF controller satin knob',(.32,.34,.40),rough=.4,metal=.45)
    cyan=material('SF DAW soft mint',(.22,.64,.61),emission=1.1,rough=.6)
    amber=material('SF DAW soft amber',(.78,.39,.14),emission=.8,rough=.6)
    sector(box('SF small audio controller',(40.38,-.48,1.055),(.18,.17,.07),graphite,bevel=.012),1)
    knob=empty('SF audio volume knob',(40.38,-.48,1.105))
    sector(rod('SF rotary cap',(0,0,0),(0,0,.036),.037,silver,knob,n=20),1)
    sector(box('SF knob indicator',(0,-.021,.037),(.006,.022,.003),cyan,knob),1)
    for f,angle in [(1,-.35),(1465,-.35),(1513,.40),(END,.40)]:
        key(knob,f,rotation_euler=(0,0,angle))
    smooth_keys(knob)
    for f in range(1433,1586):
        S.frame_set(f)
        t=weight(f,1433,1477,1513,1585)
        rest=Vector((-.22,-.53,1.07+.002*math.sin(f*.1)))
        target=rest.lerp(Vector((-.38,-.57,1.185)),t)
        idle=.003*math.sin(f*math.tau/(24*4.5))
        arm('Narrator at computer',-1,f,target,(-.28,-.03,1.30+idle),(math.pi/2,0,.22*t*math.sin((f-1465)*.035)))
    playhead=sector(box('SF DAW playback cursor',(39.50,.289,1.60),(.008,.003,.52),cyan),1)
    playhead.driver_add('location',0).driver.expression='39.50 + (max(0,frame-1280)%192)/192 * 0.96'
    for side in [-1,1]:
        for row in range(10):
            bar=sector(box('SF stereo meter',(40.48+side*.018,.288,1.34+row*.049),(.024,.003,.035),cyan if row<8 else amber),1)
            bar.driver_add('scale',0).driver.expression=f'0.25 + 0.75*(frame>=1280)*(0.5+0.5*sin((frame-1280)*0.13+{row*.6+side*.4}))'
    new_camera('08A One keyboard press',1261,1320,(40.95,-1.45,1.93),(40.84,-1.30,1.80),(40,-.43,1.065),55)
    marker=S.timeline_markers.new('08 Side listening',frame=1321);marker.camera=S.objects['08 Studio side typing']
    new_camera('08B Shaping the sound',1465,1536,(41.08,.00,1.90),(40.99,-.05,1.80),(40.38,-.48,1.12),60)
    marker=S.timeline_markers.new('08 Side listening return',frame=1537);marker.camera=S.objects['08 Studio side typing']
    camera_path(S.objects['08 Studio side typing'],[(1249,(43.45,-2.65,2.40),(40,-.28,1.28)),(1704,(42.60,-2.15,2.13),(40,-.22,1.34))],48)


def area(name, loc, target, color, energy, size, where):
    data=bpy.data.lights.new(name,'AREA');data.color=color;data.energy=energy;data.shape='DISK';data.size=size
    obj=bpy.data.objects.new(name,data);S.collection.objects.link(obj)
    obj.location=loc;obj.rotation_euler=(Vector(target)-Vector(loc)).to_track_quat('-Z','Y').to_euler()
    sector(obj,where)
    return obj


def cameras_and_lighting():
    for obj in S.objects:
        if obj.type=='CAMERA':smooth_keys(obj)
    # The original 65 mm close-up cropped its camera-parented reply subtitle.
    # Keep the dialogue wording and visibility keyframes; move it into safe area.
    for obj in S.objects:
        if obj.type=='FONT' and obj.data.body=="No, I'm not...":
            obj.location=(0,-.06125,-.5)
            obj.data.size=.01225
            ink=material('SF readable reply subtitle',(.8,.8,.87),emission=1,rough=1)
            obj.data.materials.clear();obj.data.materials.append(ink)
    # Same narrative shots, with slightly kinder portrait framing.
    camera_path(S.objects['02 She notices you'],[(193,(-.22,-2.20,1.81),(-.70,-.30,1.63)),(312,(-.29,-2.01,1.79),(-.70,-.30,1.64))],65,S.objects['Woman seated head'],5.6)
    camera_path(S.objects['06 Bus and goodbye'],[(745,(-7.8,-7.8,3.9),(-.9,.9,1.25)),(900,(-7.5,-6.4,3.3),(-1.2,1.0,1.25)),(1032,(-7.2,-5.6,3.1),(-1.3,1.05,1.26))],39)
    cam=S.objects['09 Studio face push'];cam.data.dof.use_dof=True;cam.data.dof.focus_object=S.objects['Narrator at computer head'];cam.data.dof.aperture_fstop=6.3
    camera_path(S.objects['10 Stage arrival and greeting'],[(1849,(80.25,-7.6,3.05),(80,9,1.5)),(2232,(79.75,-7.1,2.85),(80,10,1.5))],32)
    camera_path(S.objects['11 Drone pull away'],[(2233,(79.75,-9,6.4),(80,10,1.0)),(2365,(80,-14,12),(80,12,0)),(2550,(80,-39,32),(80,19,0)),(2712,(80,-51,43),(80,23,0))],28)
    area('SF stop lavender rim',(-2.4,1.7,3.4),(-.1,-.3,1.3),(.49,.38,1),110,3,0)
    area('SF stop warm face bounce',(1.5,-3.0,2.3),(.1,-.3,1.5),(1,.69,.47),36,3.0,0)
    area('SF studio desk glow',(40,.05,2.15),(40,-.9,1.3),(.38,.58,1),22,1.5,1)
    area('SF studio lavender rim',(38.8,-1.8,2.6),(40,-1,1.5),(.58,.24,1),75,2.0,1)
    area('SF performer warm edge',(83,-2,4.5),(80,0,1.6),(1,.65,.36),160,3,2)
    # Avoid broad clipping from the existing strongest emitters.
    S.node_tree.nodes['Glare'].threshold=1.8
    S.node_tree.nodes['Glare'].mix=-.89


def concert():
    # Existing crowd is retained. Low-detail distant rows use a single mesh.
    rng=random.Random(661)
    verts=[];faces=[];matids=[]
    palette=[material('SF distant audience '+str(i),c,rough=.9) for i,c in enumerate([(.045,.065,.10),(.09,.07,.12),(.06,.10,.12),(.16,.12,.13)])]
    def block(center,dims,mi,rotation=0):
        index=len(verts);cx,cy,cz=center;dx,dy,dz=dims
        for x,y,z in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]:
            xx=x*dx/2;zz=z*dz/2
            verts.append((cx+xx*math.cos(rotation)+zz*math.sin(rotation),cy+y*dy/2,cz-xx*math.sin(rotation)+zz*math.cos(rotation)))
        for indices in [(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)]:
            faces.append(tuple(index+i for i in indices));matids.append(mi)
    people=0
    for row in range(22):
        for col in range(48):
            x=57.5+col*.94+rng.uniform(-.14,.14);y=35.8+row*.87+rng.uniform(-.13,.13)
            if abs(x-80)<2.0 and y>40:continue # preserve the central entry path
            h=rng.uniform(.89,1.08);mi=rng.randrange(4)
            block((x,y,.91*h),(.32,.25,.87*h),mi)
            block((x,y,1.52*h),(.25,.25,.28*h),mi)
            for side in [-1,1]:
                block((x+side*.10,y,.32*h),(.12,.15,.64*h),mi)
                a=side*rng.uniform(.25,.85)
                block((x+side*.29,y,1.43*h),(.10,.12,.70*h),mi,a)
            people+=1
    obj=mesh('SF distant audience rows',verts,faces,None)
    for mat in palette:obj.data.materials.append(mat)
    for poly,mi in zip(obj.data.polygons,matids):poly.material_index=mi
    sector(obj,2)
    obj.shape_key_add(name='Basis')
    sway=obj.shape_key_add(name='Soft distant movement')
    for v,base in zip(sway.data,obj.data.vertices):
        v.co.x+=.032*math.sin(base.co.y*.9+base.co.x*.6)*max(0,base.co.z-.45)
    for f in range(1849,END+1,24):
        shape_keys(sway,[(f,.5+.5*math.sin((f-1849)*.024))])
    smooth_keys(obj.data.shape_keys)
    S['additional_distant_spectators']=people
    # A static volume is evaluated only in the concert sector: no particle or fluid sim.
    haze=bpy.data.materials.new('SF thin concert haze');haze.use_nodes=True
    nodes=haze.node_tree.nodes;nodes.clear()
    vol=nodes.new('ShaderNodeVolumeScatter');vol.inputs['Density'].default_value=.0032;vol.inputs['Anisotropy'].default_value=.25;vol.inputs['Color'].default_value=(.54,.59,.78,1)
    out=nodes.new('ShaderNodeOutputMaterial');haze.node_tree.links.new(vol.outputs[0],out.inputs['Volume'])
    sector(box('SF concert atmosphere',(80,23,4),(57,65,10),haze),2)
    for i,obj in enumerate(sorted([o for o in S.objects if o.type=='LIGHT' and o.name.startswith('Festival spotlight')],key=lambda o:o.name)):
        for f in range(1849,END+1,18):
            target=Vector((80+(i-5)*2+3*math.sin(f*.009+i),12+5*math.sin(f*.007+i*.6),.4))
            key(obj,f,rotation_euler=(target-obj.location).to_track_quat('-Z','Y').to_euler())
            obj.data.energy=420+100*math.sin(f*.016+i)
            obj.data.keyframe_insert('energy',frame=f)
        smooth_keys(obj);smooth_keys(obj.data)
    if hasattr(S.eevee,'volumetric_samples'):S.eevee.volumetric_samples=32
    if hasattr(S.eevee,'volumetric_tile_size'):S.eevee.volumetric_tile_size='16'


def closing_and_fades():
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    quote="Maybe in another life, I'll be more than just a dreamer."
    asset=OUT/'assets'
    original_assets=SOURCE.parent/'assets_v3'
    font=original_assets/'DejaVuSerif-Italic.ttf'
    if not font.exists():font=HERE/'DejaVuSerif-Italic.ttf'
    assert font.exists(),font
    shutil.copy2(font,asset/font.name)
    license=original_assets/'FONT_LICENSE.txt'
    if license.exists():shutil.copy2(license,asset/license.name)
    image=Image.new('RGBA',(1920,1080));letters=Image.new('RGBA',image.size)
    draw=ImageDraw.Draw(letters);face=ImageFont.truetype(str(font),56)
    for text,y in [('Maybe in another life,',792),("I'll be more than just a dreamer.",868)]:
        draw.text((960,y),text,font=face,anchor='mm',fill=(232,229,241,255))
    shadow=Image.new('RGBA',image.size,(5,7,16,0))
    shadow.putalpha(letters.getchannel('A').filter(ImageFilter.GaussianBlur(6)).point(lambda v:min(255,int(v*1.3))))
    Image.alpha_composite(shadow,letters).save(asset/'closing_title.png')
    (asset/'closing_words.txt').write_text(quote+'\n')
    packed=bpy.data.images.load(str(asset/'closing_title.png'),check_existing=False)
    packed.name='Sebareflexia | closing words (packed)';packed.colorspace_settings.name='Non-Color';packed.alpha_mode='STRAIGHT';packed.pack()
    packed.filepath='//assets/closing_title.png'
    S.node_tree.nodes['Closing words'].image=packed
    S['closing_quote']=quote
    tree=S.node_tree
    # Explicit handles keep long black holds flat and both sides of each cut black.
    for fc in list(tree.animation_data.action.fcurves):
        if 'Editorial fades' in fc.data_path or 'Closing words opacity' in fc.data_path:
            tree.animation_data.action.fcurves.remove(fc)
    fade=tree.nodes['Editorial fades'].inputs[2]
    for f,v in [(1,0),(37,1),(1198,1),(1248,0),(1249,0),(1273,1),(1800,1),(1848,0),(1849,0),(1897,1),(2640,1),(END,0)]:
        fade.default_value=(v,v,v,1);fade.keyframe_insert('default_value',frame=f)
    title=tree.nodes['Closing words opacity'].outputs[0]
    for f,v in [(1,0),(2365,0),(2437,1),(2640,1),(END,0)]:
        title.default_value=v;title.keyframe_insert('default_value',frame=f)
    smooth_keys(tree)


for operation in [female_expressions,male_expressions,body_acting,stand_and_board,
                  improve_bus,studio,cameras_and_lighting,concert,closing_and_fades]:
    operation()
    print('SF_UPDATED',operation.__name__,flush=True)

# Preserve every original audio strip, its content, volume, timing and mute state.
assert audio_snapshot()==AUDIO
for sound in bpy.data.sounds:
    source=Path(bpy.path.abspath(sound.filepath))
    if sound.users and source.exists():
        shutil.copy2(source,OUT/source.name)
        sound.filepath='//'+source.name
assert all(S.objects[name].data.body==body for name,body in DIALOGUE.items())
assert [(m.frame,m.camera.name) for m in S.timeline_markers if m.camera and m.frame in dict(ORIGINAL_MARKERS)]==ORIGINAL_MARKERS
assert SOURCE_HASH==hashlib.sha256(SOURCE.read_bytes()).hexdigest()
S['sebareflexia_improved']=True
S['source_sha256']=SOURCE_HASH
S['keyboard_press_count']=1
S['film_version']='Sebareflexia Improved — emotional acting, boarding, studio inserts, dream concert'
S.render.engine='BLENDER_EEVEE_NEXT'
S.eevee.taa_render_samples=32
S.render.resolution_x=1280;S.render.resolution_y=720;S.render.resolution_percentage=100
S.render.fps=24;S.render.fps_base=1.0
S.render.image_settings.file_format='FFMPEG';S.render.ffmpeg.format='MPEG4';S.render.ffmpeg.codec='H264';S.render.ffmpeg.audio_codec='AAC'
S.render.filepath='//Sebareflexia_Improved.mp4'
S.frame_set(1)
note=bpy.data.texts.new('READ ME - Sebareflexia Improved')
note.write('113 seconds / 2712 frames / 24 fps. Original project and sound preserved.\nOne keyboard press, two studio inserts, subtle emotions, real bus doorway and boarding.\nRender Animation writes beside this file. Keep final_mix_v5.wav beside the blend.\nThe closing title is packed; its editable text is assets/closing_words.txt.\n'+S['closing_quote'])
report={'source':SOURCE.name,'source_sha256':SOURCE_HASH,'source_unchanged':True,'audio_preserved':AUDIO,'original_markers':ORIGINAL_MARKERS,'all_markers':[(m.frame,m.name) for m in sorted(S.timeline_markers,key=lambda m:m.frame)],'frame_end':END,'fps':24,'seconds':END/24,'additional_distant_spectators':S['additional_distant_spectators'],'closing_quote':S['closing_quote'],'blender_version':bpy.app.version_string}
(OUT/'source/build_report.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Sebareflexia_Improved.blend'))
print('SEBAREFLEXIA_IMPROVED_SAVED',json.dumps(report),flush=True)
