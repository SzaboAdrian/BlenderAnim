"""Small direct-mesh helpers used by the finished-film generator."""
import bpy, math
from mathutils import Vector

def material(name,color,emission=0,rough=.6,metal=0):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*color,1)
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
    p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=emission
    return m

def mesh(name,v,f,m,parent=None):
    d=bpy.data.meshes.new(name);d.from_pydata(v,[],f);d.update();o=bpy.data.objects.new(name,d);bpy.context.scene.collection.objects.link(o);o.parent=parent
    if m:d.materials.append(m)
    return o

def empty(name,loc=(0,0,0),parent=None):
    o=bpy.data.objects.new(name,None);bpy.context.scene.collection.objects.link(o);o.location=loc;o.parent=parent;return o

def box(name,loc,dim,m,parent=None,bevel=0):
    v=[(x*dim[0]/2,y*dim[1]/2,z*dim[2]/2) for x,y,z in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]]
    o=mesh(name,v,[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)],m,parent);o.location=loc
    if bevel:
        mod=o.modifiers.new('Soft edges','BEVEL');mod.width=bevel;mod.segments=2
    return o

def sphere(name,loc,scale,m,parent=None,n=16,r=10):
    v=[];f=[]
    for j in range(r+1):
        t=math.pi*j/r
        for i in range(n):
            a=math.tau*i/n;v.append((scale[0]*math.sin(t)*math.cos(a),scale[1]*math.sin(t)*math.sin(a),scale[2]*math.cos(t)))
    for j in range(r):
        for i in range(n):a=j*n+i;b=j*n+(i+1)%n;f.append((a,b,b+n,a+n))
    o=mesh(name,v,f,m,parent);o.location=loc
    for p in o.data.polygons:p.use_smooth=True
    return o

def rod(name,a,b,r,m,parent=None,n=8):
    a=Vector(a);b=Vector(b);length=(b-a).length;v=[];f=[]
    for z in [0,length]:
        for i in range(n):t=math.tau*i/n;v.append((r*math.cos(t),r*math.sin(t),z))
    for i in range(n):j=(i+1)%n;f.append((i,j,j+n,i+n))
    f.extend([tuple(reversed(range(n))),tuple(range(n,n*2))]);o=mesh(name,v,f,m,parent);o.location=a;o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o

def keys(o,frame,location=None,rotation=None,scale=None):
    for prop,value in [('location',location),('rotation_euler',rotation),('scale',scale)]:
        if value is not None:setattr(o,prop,value);o.keyframe_insert(prop,frame=frame)

def linear(o):
    if o.animation_data and o.animation_data.action:
        for fc in o.animation_data.action.fcurves:
            for p in fc.keyframe_points:p.interpolation='LINEAR'
