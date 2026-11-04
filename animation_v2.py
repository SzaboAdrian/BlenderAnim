"""Deterministic, reach-limited gait and acting on a slower 109-second timeline."""
import bpy, math, json
from mathutils import Vector
from geometry_v2 import box,sphere,keys,linear
FPS=24;END=2616
CUTS=[1,193,313,505,649,745,1033,1249,1705,1849,2137]
OLD=[1,145,240,360,470,530,650,745,931,1057,1201,1441]
NEW=CUTS+[2617]
TAPS=[1273,1381,1489,1597,1705,1813]
def ease(t):
    t=max(0,min(1,t));return t*t*t*(10+t*(-15+6*t))
def blend(a,b,t):return Vector(a).lerp(Vector(b),t)
def remap(f):
    for i in range(len(OLD)-1):
        if f<OLD[i+1]:return NEW[i]+(f-OLD[i])*(NEW[i+1]-NEW[i])/(OLD[i+1]-OLD[i])
    return NEW[-1]
def retime(s):
    for action in bpy.data.actions:
        for fc in action.fcurves:
            for p in fc.keyframe_points:
                p.co.x=remap(p.co.x);p.handle_left.x=remap(p.handle_left.x);p.handle_right.x=remap(p.handle_right.x)
    for marker in s.timeline_markers:marker.frame=round(remap(marker.frame))
    s.frame_end=END;s.frame_start=1;s.render.fps=FPS
    if s.sequence_editor:
        for seq in list(s.sequence_editor.sequences):s.sequence_editor.sequences.remove(seq)

def progress(t):
    t=max(0,min(1,t));r=.12
    if t<r:return (.5*t*t/r)/(1-r)
    if t>1-r:return 1-(.5*(1-t)**2/r)/(1-r)
    return (t-r/2)/(1-r)

def ik(a,target,l1,l2,pole):
    a=Vector(a);t=Vector(target);d=t-a;dist=d.length;axis=d.normalized();reach=min(dist,l1+l2-.002)
    # Clamp the endpoint too: rigid limbs never detach or stretch.
    end=a+axis*reach;along=(l1*l1-l2*l2+reach*reach)/(2*reach)
    p=Vector(pole);p=(p-axis*p.dot(axis)).normalized()
    middle=a+axis*along+p*math.sqrt(max(0,l1*l1-along*along))
    return middle,end,dist>l1+l2-.002

def route_point(points,t):
    lengths=[(Vector(b)-Vector(a)).length for a,b in zip(points,points[1:])];total=sum(lengths);distance=max(0,min(1,t))*total
    for a,b,length in zip(points,points[1:],lengths):
        if distance<=length:return Vector(a).lerp(Vector(b),distance/length)
        distance-=length
    return Vector(points[-1])

def walk(f,start,end,points,root,side):
    p=progress((f-start)/(end-start));length=sum((Vector(b)-Vector(a)).length for a,b in zip(points,points[1:]))
    cycles=max(1,round(length/.68));phase=p*cycles+(0 if side<0 else .5);i=math.floor(phase);u=phase-i;offset=0 if side<0 else .5
    def contact(index):
        q=max(0,min(1,(index-offset+.28)/cycles));pt=route_point(points,q)
        tangent=route_point(points,min(1,q+.002))-route_point(points,max(0,q-.002));tangent.z=0;tangent.normalize()
        # Local X right points to (-forward.y, forward.x).
        pt+=Vector((-tangent.y,tangent.x,0))*side*.105
        return pt
    if u<=.62:foot=contact(i)
    else:
        q=(u-.62)/.38;foot=contact(i).lerp(contact(i+1),ease(q));foot.z+=.065*math.sin(math.pi*q)**2
    return foot,phase

def apply(s):
    stats={'leg_reach_clamps':0};record={}
    names=['Narrator seated','Woman seated','Woman standing','Narrator at computer','Narrator on stage']
    for name in names:
        root=s.objects[name];head=next(c for c in root.children if ' head' in c.name);torso=next(c for c in root.children if 'torso' in c.name)
        for child in list(root.children):
            if any(word in child.name for word in [' upper leg',' lower leg',' shoe',' upper arm',' forearm',' hand',' kneecap',' elbow',' pelvis']):bpy.data.objects.remove(child,do_unlink=True)
        # Replace all baked acting, preserving scale visibility only.
        if root.animation_data:
            for fc in list(root.animation_data.action.fcurves):
                if fc.data_path!='scale':root.animation_data.action.fcurves.remove(fc)
        head.animation_data_clear();torso.animation_data_clear()
        iswoman=name.startswith('Woman');shirt=bpy.data.materials['Woman navy suit' if iswoman else 'Portrait black T shirt'];pants=bpy.data.materials['Clothes dark'];skin=bpy.data.materials['Woman warm skin' if iswoman else 'Portrait warm skin']
        pelvis=box(name+' pelvis',(0,0,.77),(.42,.29,.20),pants,root,.045)
        limbs={}
        for side in [-1,1]:
            limbs[side]=[
                box(name+' upper leg',(0,0,0),(.18,.20,.46),pants,root,.035),
                box(name+' lower leg',(0,0,0),(.16,.18,.46),pants,root,.03),
                box(name+' shoe',(0,0,0),(.17,.29,.10),shirt,root,.035),
                box(name+' upper arm',(0,0,0),(.15,.17,.31),shirt,root,.035),
                box(name+' forearm',(0,0,0),(.13,.15,.32),shirt,root,.03),
                box(name+' hand',(0,0,0),(.085,.075,.13),skin,root,.025),
                sphere(name+' kneecap',(0,0,0),(.092,.095,.09),pants,root,n=12,r=8),
                sphere(name+' elbow',(0,0,0),(.075,.078,.073),shirt,root,n=12,r=8)]
        def bone(o,a,b,f):
            o.rotation_mode='QUATERNION'
            q=(Vector(b)-Vector(a)).to_track_quat('Z','Y');q.make_compatible(o.rotation_quaternion)
            keys(o,f,(Vector(a)+Vector(b))/2)
            o.rotation_quaternion=q;o.keyframe_insert('rotation_quaternion',frame=f)
        frames=set(range(1,END+1))|{END,444,445,464,465,504,505,824,825,1020,2064,2065,2136,2137}
        previous_rz=None
        for f in sorted(frames):
            seated=True;walking=False;phase=0;lean=0;gait=None;rz=0;floor=0
            if name=='Narrator seated':
                gait=(313,445,[(5,-.78,.055),(.75,-.78,.055)])
                if f<445:
                    p=progress((f-313)/132);pos=route_point(gait[2],p)+Vector((0,0,.055));rz=-math.pi/2;seated=False;walking=313<=f<445
                elif f<465:
                    pos=Vector((.75,-.78,.11));rz=-math.pi/2*(1-ease((f-445)/20));seated=False
                else:
                    q=ease((f-465)/40);pos=blend((.75,-.78,.11),(.75,-.3,0),q);seated=True;lean=.12*math.sin(q*math.pi)
                if f>=505:lean=.09*(1-ease((f-1175)/25))
            elif name=='Woman seated':
                q=ease((f-785)/40);pos=Vector((-.7,-.3,.11*q));lean=.18*math.sin(q*math.pi)
            elif name=='Woman standing':
                gait=(845,1018,[(-.7,-.3,.055),(-2.65,-.55,.055),(-2.8,.6,.055),(-2.6,1.9,.055),(-1,2.05,.055),(-1,2.7,.555)])
                p=progress((f-845)/173);pos=route_point(gait[2],p)+Vector((0,0,.055));seated=False;walking=845<=f<1018;floor=pos.z-.11
                look=route_point(gait[2],min(1,p+.045))-route_point(gait[2],max(0,p-.045));rz=math.atan2(look.x,-look.y)
                if f<845:rz=-math.pi/2*ease((f-825)/20)
            elif name=='Narrator at computer':pos=Vector((40,-1.05,0));rz=math.pi;lean=.055
            else:
                gait=(1873,2053,[(86,0,.755),(80,0,.755)])
                p=progress((f-1873)/180);pos=route_point(gait[2],p)+Vector((0,0,.055));rz=-math.pi/2-math.pi/2*ease((f-2040)/25);seated=False;walking=1873<=f<2053;floor=.7
            foots={}
            if walking:
                for side in [-1,1]:foots[side],phase=walk(f,*gait,root,side)
                pos.z+=.008*math.cos(phase*math.tau*2)
            if previous_rz is not None:rz=previous_rz+(rz-previous_rz+math.pi)%(math.tau)-math.pi
            previous_rz=rz
            keys(root,f,pos,(0,0,rz))
            def local(world):
                d=world-pos;return Vector((math.cos(rz)*d.x+math.sin(rz)*d.y,-math.sin(rz)*d.x+math.cos(rz)*d.y,d.z))
            def world(local):
                x,y,z=local;return pos+Vector((math.cos(rz)*x-math.sin(rz)*y,math.sin(rz)*x+math.cos(rz)*y,z))
            freeze=name=='Narrator on stage' and 2065<=f<=2136
            idle=0 if freeze else .003*math.sin(f*math.tau/(24*4.5))
            headrot=Vector((lean*.35,0,0))
            if name=='Woman seated':headrot.z=.3*ease((f-205)/55)+.30*ease((f-520)/35)
            if name=='Woman standing':headrot.z=.6*(1-ease((f-825)/25))
            if name=='Narrator seated':
                headrot.x+=.12*ease((f-505)/35)*(1-ease((f-1110)/40))
                if 665<f<726:headrot.z=.16*math.sin((f-665)/61*math.tau*2)*math.sin((f-665)/61*math.pi)
                headrot.x-=.10*ease((f-1145)/30)
            keys(head,f,(0,-.015*lean,1.62+idle),(headrot.x+idle,headrot.y,headrot.z))
            keys(torso,f,(0,0,1.05+idle),(lean,0,.008*math.sin(phase*math.tau) if walking else 0))
            for side in [-1,1]:
                upper,lower,shoe,arm,fore,hand,kneecap,elbowjoint=limbs[side];hip=Vector((side*.105,0,.76))
                foot=local(foots[side]) if walking else Vector((side*.105,-.46 if seated else -.03,floor+.055-pos.z))
                if name=='Narrator seated' and 445<=f<465:
                    finalworld=Vector((.75+side*.105,-.76,.055));previous=walk(444,*gait,root,side)[0];foot=local(previous.lerp(finalworld,ease((f-445)/20)))
                if name=='Narrator seated' and 465<=f<=505:foot=local(Vector((.75+side*.105,-.76,.055)))
                if name=='Woman standing' and f<845:
                    # Match the seated double exactly, then turn on the spot.
                    foot=Vector((side*.105,-.46*(1-ease((f-825)/20)),.055-pos.z))
                if name=='Narrator on stage' and 2053<=f<2065:
                    last=walk(2052,*gait,root,side)[0];foot=local(last.lerp(world((side*.105,-.03,.055-.11)),ease((f-2053)/12)))
                knee,ankle,clamped=ik(hip,foot,.46,.46,(0,-1,0))
                if walking and clamped:stats['leg_reach_clamps']+=1
                bone(upper,hip,knee,f);bone(lower,knee,ankle,f);keys(kneecap,f,knee);keys(shoe,f,ankle+Vector((0,-.065,-.005)),(0,0,0))
                shoulder=Vector((side*.28,-.03,1.30+idle));target=Vector((side*.28,-.10,.80))
                if walking:target.y+=side*.095*math.sin(phase*math.tau);target.z+=.015*math.cos(phase*math.tau)
                elif seated:target=Vector((side*.21,-.32,.84))
                if name=='Narrator seated':
                    cover=ease((f-510)/35)*(1-ease((f-720)/24));target=target.lerp(Vector((side*.085,-.21,1.56)),cover)
                    scratch=ease((f-1060)/35)*(1-ease((f-1155)/30)) if side>0 else 0
                    target=target.lerp(Vector((.15,-.01+.007*math.sin(f*.24),1.81)),scratch)
                if name=='Narrator at computer':
                    tap=max([ease((f-t)/7)*(1-ease((f-t-15)/9)) for t in TAPS]);target=Vector((side*.22,-.53,1.07-(.026*tap if side>0 else .002*math.sin(f*.1))))
                if name=='Woman seated' and 552<f<625 and side>0:target=target.lerp(Vector((.28,-.4,1.08)),.5*math.sin((f-552)/73*math.pi)**2)
                elbow,wrist,_=ik(shoulder,target,.31,.32,(side,-.15,-.5));bone(arm,shoulder,elbow,f);bone(fore,elbow,wrist,f);keys(elbowjoint,f,elbow)
                handrot=(math.pi/2,0,0) if name=='Narrator at computer' else (0,0,side*.08)
                keys(hand,f,wrist,handrot)
            # Reset visibility of both female doubles to the continuous handoff.
        for o in [root,head,torso]+[x for g in limbs.values() for x in g]:linear(o)
    for name,points in [('Woman seated',[(1,1),(824,1),(825,0)]),('Woman standing',[(1,0),(824,0),(825,1),(1020,1),(1021,0)])]:
        o=s.objects[name]
        for fc in list(o.animation_data.action.fcurves):
            if fc.data_path=='scale':o.animation_data.action.fcurves.remove(fc)
        for f,v in points:keys(o,f,scale=(v,v,v))
        for fc in o.animation_data.action.fcurves:
            if fc.data_path=='scale':
                for p in fc.keyframe_points:p.interpolation='CONSTANT'
    s['motion_v2_stats']=json.dumps(stats);s['motion_version']=2;s.frame_set(1)
    print('MOTION_V2',stats,flush=True)
