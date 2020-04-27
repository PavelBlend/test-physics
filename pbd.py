bl_info = {
    'name': 'Position Based Dynamics',
    'blender': (2, 82, 0),
    'category': 'Physics'
}


import bpy
import bmesh
import mathutils
import random


# particles
pars = []
PARS_OBJ_NAME = 'PBD'
PAR_OBJ_NAME = 'Particle'
par_radius = 0.0


class Particle:
    def __init__(self):
        # particle position
        self.x = mathutils.Vector()
        # particle preview position
        self.p = mathutils.Vector()
        # particle acceleration
        self.a = mathutils.Vector()
        # particle radius
        self.r = 0.0
        # static
        self.st = False

    def move(self, dt):
        if not self.st:
            # delta position
            d = self.x - self.p
            self.x = self.p
            # gravity
            self.a[2] -= 1.0
            self.x += d + self.a * dt * dt


def seed_pars():
    global pars
    global par_radius
    pars.clear()
    size = 10
    par_size = 0.1
    par_radius = par_size / 2
    off = size * par_size / 2
    for x in range(size):
        for y in range(size):
            for z in range(size):
                par = Particle()
                # position
                par.x[0] = x * par_size - off
                par.x[1] = y * par_size - off
                par.x[2] = z * par_size
                # preview position
                par.p[0] = x * par_size
                par.p[1] = y * par_size
                par.p[2] = z * par_size
                # radius
                par.r = par_radius
                par.a[2] = -9.81
                pars.append(par)
    sz_x = 20
    sz_y = 20
    sz_z = 1
    off_x = sz_x * par_size / 2
    off_y = sz_y * par_size / 2
    for x in range(sz_x):
        for y in range(sz_y):
            for z in range(sz_z):
                par = Particle()
                # position
                par.x[0] = x * par_size - off_x
                par.x[1] = y * par_size - off_y
                par.x[2] = -0.5 + z * par_size
                par.r = par_radius
                par.st = True
                pars.append(par)


def step(dt):
    global pars
    par_cnt = len(pars)
    for i in range(0, par_cnt - 1):
        for j in range(i + 1, par_cnt):
            p1 = pars[i]
            p2 = pars[j]
            if (p1.x - p2.x).length < p1.r + p2.r:
                # penetration direction
                direct = (p2.x - p1.x).normalized()
                # penetration depth
                depth = p1.r + p2.r - (p2.x - p1.x).length
                if not p1.st:
                    p1.x += -direct * depth * 0.5
                if not p2.st:
                    p2.x += direct * depth * 0.5
    for p in pars:
        p.move(dt)


def pbd_solve(fps):
    steps = 16
    dt = 1 / fps / steps
    for s in range(steps):
        print(s)
        step(dt)


def get_par_obj(pars_obj):
    par_obj = bpy.data.objects.get(PAR_OBJ_NAME)
    if not par_obj:
        par_obj = create_obj(PAR_OBJ_NAME)
        bm = bmesh.new()
        global par_radius
        bmesh.ops.create_icosphere(
            bm, subdivisions=2, diameter=par_radius, calc_uvs=False
        )
        for face in bm.faces:
            face.smooth = True
        bm.to_mesh(par_obj.data)
    return par_obj


def create_obj(name):
    me = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, me)
    scn = bpy.context.scene
    scn.collection.objects.link(obj)
    return obj


def set_par(pars_obj):
    pars_obj.instance_type = 'VERTS'
    par_obj = get_par_obj(pars_obj)
    par_obj.parent = pars_obj


def create_pars():
    global pars
    verts = []
    for p in pars:
        verts.append(p.x)
    pars_obj = bpy.data.objects.get(PARS_OBJ_NAME)
    if not pars_obj:
        pars_obj = create_obj(PARS_OBJ_NAME)
        set_par(pars_obj)
    old_me = pars_obj.data
    old_me.name = 'TEMP'
    new_me = bpy.data.meshes.new(PARS_OBJ_NAME)
    new_me.from_pydata(verts, (), ())
    pars_obj.data = new_me
    bpy.data.meshes.remove(old_me)


@bpy.app.handlers.persistent
def pbd_update(scene):
    if scene.frame_current == 0:
        seed_pars()
    fps = scene.render.fps
    pbd_solve(fps)
    create_pars()


def register():
    bpy.app.handlers.frame_change_post.append(pbd_update)


def unregister():
    bpy.app.handlers.frame_change_post.remove(pbd_update)
