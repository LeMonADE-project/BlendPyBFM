"""
----------------------------------------------------------------------------------
 _______________
|   /       \   | L   attice-based  | BlendPyBFM:
|  /   ooo   \  | e   xtensible     | ----------------
| /  o\.|./o  \ | Mon te-Carlo      | An Blender binding in Python to convert
|/  o\.\|/./o  \| A   lgorithm and  | BFM files generated by LeMonADE-software.
|  BlendPyBFM   | D   evelopment    | See: https://github.com/LeMonADE-project/LeMonADE
|\  o/./|\.\o  /| E   nvironment    |
| \  o/.|.\o  / | -                 |
|  \   ooo   /  | BlendPyBFM        | Copyright (C) 2020 by
|___\_______/___|                   | BlendPyBFM Principal Developers (see AUTHORS)
----------------------------------------------------------------------------------
This file is part of BlendPyBFM.
BlendPyBFM is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
BlendPyBFM is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with BlendPyBFM.  If not, see <http://www.gnu.org/licenses/>.
-----------------------------------------------------------------------------------
"""

import bpy

from bpy.utils import register_class, unregister_class

from bpy.props import (StringProperty,
                       PointerProperty,
                       EnumProperty,
                       )

from bpy.types import (Panel,
                       Operator,
                       AddonPreferences,
                       PropertyGroup,
                       )

import numpy as np
import os
from mathutils import Vector;
import math


class PyBFMLoader():
    
    # default constructor 
    def __init__(self, fname): 
        self.filename = fname
        self.boxX = 128
        self.boxY = 128
        self.boxZ = 128
        self.set_of_bondvectors = {} # holds dictionary of all bond vectors ASCII->[x,y,z]
        self.line2MCS = [] # mapping the frame with linenumber to MCStime
        self.polymer_last_config = np.empty((0, 3),dtype=int) # last configuration of polymeric system
        self.polymer_bonds={} # holds dictionary of all bonds due to !bonds and !mcs
    
        self.read_box() # read !box_x, !box_y, box_z
        self.load_bondvector() # read !set_of_bondvectors
        self.read_bonds() # read !bonds
        self.scan_file()
        self.read_configuration(0) # read first frame
        print("CAUTION: all indecies start at Zero!")
    
    def load_bondvector(self):
        print("read in set of bond vectors")
        vector = {} 
        fobj = open(self.filename)
        
        while True:
            # read line
            line = fobj.readline()
            
            # check if line is not empty-> EOF
            if not line:
                break
            
            if line.startswith('!set_of_bondvectors'):
                print(line)
                while True:
                    line = fobj.readline()
                    # print(line)
                    # check if line is not empty
                    if not line or line[0] =="\n":
                        break
                    aline=line.split(":")
                    i=int(aline[1])
                    aline=aline[0].split(' ')
                    vector[i]= [int(aline[0]),int(aline[1]),int(aline[2])]
                    
            # found first frame    
            if line.startswith('!mcs'):
                print("found mcs")
                print(line)
                break
            
            
                
        fobj.close()
        
        self.set_of_bondvectors = vector
       
        return vector
    
    def read_box(self):
        print("read in of !box command")
        
        fobj = open(self.filename)
        
        while True:
            # read line
            line = fobj.readline()
            
            # check if line is not empty-> EOF
            if not line:
                break
            
            if line.startswith('!box_x'):
                aline=line.split("=")
                self.boxX = int(aline[1])
                
            if line.startswith('!box_y'):
                aline=line.split("=")
                self.boxY = int(aline[1])
                
            if line.startswith('!box_z'):
                aline=line.split("=")
                self.boxZ = int(aline[1])        
                    
                    
            # found first frame    
            if line.startswith('!mcs'):
                print("found mcs")
                print(line)
                break
            
            
                
        fobj.close()
        
        return True
    
    def read_bonds(self):
        print("read in of !bonds command")
        additional_bonds = {} 
        fobj = open(self.filename)
        
        while True:
            # read line
            line = fobj.readline()
            
            # check if line is not empty-> EOF
            if not line:
                break
            
            if line.startswith('!bonds'):
                print(line)
                while True:
                    line = fobj.readline()
                    #print(line)
                    # check if line is not empty
                    if not line or line[0] =="\n":
                        break
                    aline=line.split(" ")
                    # indecies start at 0
                    mono1=int(aline[0])-1
                    mono2=int(aline[1])-1
                                           
                    if mono1 in self.polymer_bonds:
                        self.polymer_bonds[mono1].add(mono2)
                    else:
                        self.polymer_bonds[mono1] = set([mono2])
                        
                    if mono2 in self.polymer_bonds:
                        self.polymer_bonds[mono2].add(mono1)
                    else:
                        self.polymer_bonds[mono2] = set([mono1])
                        
                    
            # found first frame    
            if line.startswith('!mcs'):
                print("found mcs")
                print(line)
                break
            
            
                
        fobj.close()
        
        return additional_bonds
    
    def read_configuration(self, frame):
        fobj = open(self.filename)
        
        polymer = np.empty((0, 3),dtype=int) # np.array([[]], dtype=int, ndmin=2) # [] #np.zeros(3,dtype=int)
        
        if frame < 0 or frame >= len(self.line2MCS):
            print("frame out of bounds")
            return polymer
        
        frame_linenumber = self.line2MCS[frame][0]
        
        # skip all lines until the reach the desired line
        # should be improved for huge files
        for _ in range(1, frame_linenumber):
            fobj.readline()
        
        while True:
            # read line
            line = fobj.readline()
            #print(line)
            # check if line is not empty-> EOF
            if not line:
                break
                
            # found first frame    
            if line.startswith('!mcs'):
                print("found mcs")
                print(line)
                
                xyz = [] #np.zeros((0,3),dtype=int)
                
                idx_count=0 # counter of index position
                
                while True:
                    line = fobj.readline()
                    # print(line)
                    # check if line is not empty
                    if not line or line[0] =="\n":
                        break
                        
                    aline=line.split(" ")
                    xyz = [int(aline[0]),int(aline[1]),int(aline[2])]
                    print("start")
                    print(np.asarray(xyz, dtype=int))
                    
                    polymer = np.vstack([polymer, np.asarray(xyz, dtype=int)])
                    
                    offset = len(aline[0])+len(aline[1])+len(aline[2])+3
                    
                    idx_count += 1
                    
                    for i in line[offset:-1].encode('ascii'):
                        
                        idx_count += 1
                        
                        bond = np.asarray(self.set_of_bondvectors[i], dtype=int)
                        # print(str(j) + " " + chr(i) + " " + str(bond[0]) + " " + str(bond[1]) + " " + str(bond[2]))
                        
                        #if bond[0]!=0 or bond[1]!=0 or bond[2]!=0:
                        
                        xyz=polymer[len(polymer)-1]+bond
                        polymer = np.vstack([polymer, [np.asarray(xyz, dtype=int)]])
                        
                        # build the graph if neccessary
                        mono1=idx_count-1 # recent monomer
                        mono2=idx_count-2 # previous monomer
                        
                        if mono1 in self.polymer_bonds:
                            self.polymer_bonds[mono1].add(mono2)
                        else:
                            self.polymer_bonds[mono1] = set([mono2])
                        
                        if mono2 in self.polymer_bonds:
                            self.polymer_bonds[mono2].add(mono1)
                        else:
                            self.polymer_bonds[mono2] = set([mono1])
                break
            
        print("readin done")
        fobj.close()
        
        self.polymer_last_config=polymer
        return polymer  
     
    
    def scan_file(self):
        fp = open(self.filename)
        
        linenumbermcs = []
        
        for i, line in enumerate(fp):
            if line.startswith('!mcs'):
                linenumbermcs.append([i, (int)(line.split("=")[1])])
        
        fp.close()
        
        self.line2MCS = linenumbermcs
        
        print("Found " + str(len(linenumbermcs)) + " !mcs commands")
        
        return linenumbermcs


class MyProperties(PropertyGroup):
    path : StringProperty(
        name="",
        description="Path to Directory",
        default="",
        maxlen=1024,
        subtype='FILE_PATH')




class PT_BlendPyBFM(bpy.types.Panel):
    bl_label = "BFM Tools"
    bl_idname = "PT_BlendPyBFM"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'BlendPyBFM'
   
    def draw(self, context):
        layout = self.layout
       
        row = layout.row()
        row.label(text= "Add an object", icon= 'OBJECT_ORIGIN')
        row = layout.row()
        row.operator("mesh.primitive_cube_add", icon= 'CUBE')
       
        row.operator("mesh.primitive_uv_sphere_add", icon= 'SPHERE')
        row = layout.row()
        
        scn = context.scene
        col = layout.column(align=True)
        col.prop(scn.my_tool, "path", text="")

        # print the path to the console
        print (scn.my_tool.path)
        
        #scn = bpy.context.scene
        #row = layout.row()
        #row.operator("scn.my_tool", text="Select file dialog *bfm", icon='FILE')
        #row.prop("macbook_controller.identifier_file_selector.path", "screen_path")  # <-- just for display purposes
        
        #row.operator('test.test_op', text='Select file dialog').action = 'SELECT_FILE'
        row = layout.row()
        
        row.operator('test.test_op', text='Clear scene').action = 'CLEAR'
        row = layout.row()
        row.operator('test.test_op', text='Add simulation cube').action = 'ADD_CUBE'
        row = layout.row()
        row.operator('test.test_op', text='Add sphere first frame').action = 'ADD_SPHERE'
        row = layout.row()
        row.operator('test.test_op', text='Add sphere movie').action = 'ADD_SPHERE_MOVIE'
        
class TEST_OT_test_op(Operator):
    bl_idname = 'test.test_op'
    bl_label = 'BlendPyBFM HelperFunctions'
    bl_description = 'BlendPyBFM HelperFunctions'
    bl_options = {'REGISTER', 'UNDO'}
 
    action: EnumProperty(
        items=[
            ('CLEAR', 'clear scene', 'clear scene'),
            ('ADD_CUBE', 'add simulation cube', 'add simulation cube'),
            ('ADD_SPHERE', 'add sphere first frame', 'add sphere first frame'),
            ('ADD_SPHERE_MOVIE', 'add sphere movie', 'add sphere movie'),
            ('SELECT_FILE', 'select file dialog', 'select file dialog')
        ]
    )
    
    def cylinder_between(self, x1, y1, z1, x2, y2, z2, r):
        dx = x2 - x1
        dy = y2 - y1
        dz = z2 - z1    
        dist = math.sqrt(dx**2 + dy**2 + dz**2)

        bpy.ops.mesh.primitive_cylinder_add(
              radius = r, 
              depth = dist,
              location = (dx/2 + x1, dy/2 + y1, dz/2 + z1)   
          ) 

        phi = math.atan2(dy, dx) 
        theta = math.acos(dz/dist) 

        bpy.context.object.rotation_euler[1] = theta 
        bpy.context.object.rotation_euler[2] = phi 
            
    def execute(self, context):
        if self.action == 'SELECT_FILE':
            self.selectFileDialog(context=context)
        elif self.action == 'CLEAR':
            self.clear_scene(context=context)
        elif self.action == 'ADD_CUBE':
            self.filename = context.scene.my_tool.path
            self.loader=PyBFMLoader(self.filename)
            bpy.ops.object.select_all(action='DESELECT')
        
            self.cylinder_between(0,0,0, self.loader.boxX,0,0,1)
            self.cylinder_between(0,0,0, 0,self.loader.boxY,0,1)
            self.cylinder_between(0,0,0, 0,0,self.loader.boxZ,1)
            
            self.cylinder_between(self.loader.boxX,0,0, self.loader.boxX,self.loader.boxY,0,1)
            self.cylinder_between(self.loader.boxX,0,0, self.loader.boxX,0,self.loader.boxZ,1)
            
            self.cylinder_between(0,0,self.loader.boxZ, self.loader.boxX,0,self.loader.boxZ,1)
            self.cylinder_between(0,0,self.loader.boxZ, 0,self.loader.boxY,self.loader.boxZ,1)
            
            self.cylinder_between(0,self.loader.boxY,0, self.loader.boxX,self.loader.boxY,0,1)
            self.cylinder_between(0,self.loader.boxY,0, 0,self.loader.boxY,self.loader.boxZ,1)
            
            self.cylinder_between(self.loader.boxX,0,self.loader.boxZ, self.loader.boxX,self.loader.boxY,self.loader.boxZ,1)
            self.cylinder_between(self.loader.boxX,self.loader.boxY,0, self.loader.boxX,self.loader.boxY,self.loader.boxZ,1)
            self.cylinder_between(0,self.loader.boxY,self.loader.boxZ, self.loader.boxX,self.loader.boxY,self.loader.boxZ,1)
            
#            coll = bpy.data.collections.new("SimulationBox")
#            bpy.context.scene.collection.children.link(coll)
#        
#            bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius = 0.4, depth = 2.7,location = (0, 0, 0)) 
#        cylinder = bpy.context.object
#        #coll.objects.link(cylinder)
#        bpy.context.collection.objects.unlink(cylinder)
#        
#        for key in sorted(bonds.keys()):
#            for item in sorted(bonds[key]):
#                if key < item:
#                    dx = polymer[key][0] - polymer[item][0]
#                    dy = polymer[key][1] - polymer[item][1]
#                    dz = polymer[key][2] - polymer[item][2]  
#                    dist = math.sqrt(dx**2 + dy**2 + dz**2)
#                    
#                    #bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius = 0.4, depth = dist,location = (dx/2 + polymer[item][0], dy/2 + polymer[item][1], dz/2 + polymer[item][2])) 
#                    ob = cylinder.copy()
#                    ob.data = cylinder.data.copy()
#                    ob.location = Vector((dx/2 + polymer[item][0], dy/2 + polymer[item][1], dz/2 + polymer[item][2]));
#                    #bpy.context.collection.objects.link(ob)
#                    #coll.objects.link(ob)
#                    
#                    phi = math.atan2(dy, dx) 
#                    theta = math.acos(dz/dist)
#                    #cylinder = bpy.context.object
#                    ob.rotation_euler[1] = theta 
#                    ob.rotation_euler[2] = phi
#                    #print(cylinder.rotation_euler[1])
#                    #print(cylinder.rotation_euler[2])
#                    coll.objects.link(ob)
#                    #bpy.context.collection.objects.unlink(cylinder)
#        
#            
#            self.add_cube(context=context)
        elif self.action == 'ADD_SPHERE':
            # self.add_cube(context=context)
            self.filename = context.scene.my_tool.path
            self.loader=PyBFMLoader(self.filename)
            polymer = self.loader.polymer_last_config
            print("File loaded")
            self.add_sphere(context=context, polymer=polymer)
            self.add_bonds(context=context, bonds=self.loader.polymer_bonds, polymer=polymer)
        elif self.action == 'ADD_SPHERE_MOVIE':
            # self.add_cube(context=context)
            self.filename = context.scene.my_tool.path
            self.loader=PyBFMLoader(self.filename)
            polymer = self.loader.polymer_last_config
            
            # create initial config
            self.add_sphere(context=context, polymer=self.loader.polymer_last_config)
            self.add_bonds(context=context, bonds=self.loader.polymer_bonds, polymer=self.loader.polymer_last_config)
            
            # useful shortcut
            scene = bpy.context.scene
            
            #bpy.ops.graph.select_all_toggle(invert=False)
            
            for i, frames in enumerate(self.loader.line2MCS):
                # if i < 40:
                    # now we will describe frame with number $number_of_frame
                    scene.frame_set(i*10)
                    
                    polymer = self.loader.read_configuration(i)
                    print("read next frame")
                    self.adjust_location(context=context, bonds=self.loader.polymer_bonds, polymer=self.loader.polymer_last_config)
                    
                    for i, obj in enumerate(bpy.data.objects):
                        obj.keyframe_insert(data_path="location", index=-1)
                        obj.keyframe_insert(data_path="rotation_euler", index=-1)
                        
                        # comment this if you want interpolation between frames
                        for fcurve in obj.animation_data.action.fcurves:
                            kf = fcurve.keyframe_points[-1]
                            kf.interpolation = 'CONSTANT'
                    
                    
                
            #self.add_sphere_movie(context=context, polymer=polymer)
        return {'FINISHED'}
 
    @staticmethod
    def selectFileDialog(context):
        #filedialogBFM = bpy.ops.test.open_filebrowser_for_bfm('INVOKE_DEFAULT')
        #print(filedialogBFM)
        print(context.scene.my_path.path)
        #print(filedialogBFM.getFilename())
            
    @staticmethod
    def clear_scene(context):
        
        # remove mesh Cube
        if "Cube" in bpy.data.meshes:
            mesh = bpy.data.meshes["Cube"]
            print("removing mesh", mesh)
            bpy.data.meshes.remove(mesh)
        
        bpy.ops.object.select_by_type(type='MESH')
        bpy.ops.object.delete()
        
        scene = bpy.context.scene
        scene.animation_data_clear()
        for o in scene.objects:
            o.animation_data_clear()
        #bpy.ops.object.select_by_type(type='CAMERA')
        #bpy.context.active_object.animation_data_clear()
        #for obj in bpy.data.objects:
        #    bpy.data.objects.remove(obj)
        
        # delete collection
        name = "PolymerSystem"
        remove_collection_objects = True

        coll = bpy.data.collections.get(name)

        if coll:
            if remove_collection_objects:
                obs = [o for o in coll.objects]
                while obs:
                    bpy.data.objects.remove(obs.pop())

            bpy.data.collections.remove(coll)
            
        coll = bpy.data.collections.get("Bonds")
        if coll:
            if remove_collection_objects:
                obs = [o for o in coll.objects]
                while obs:
                    bpy.data.objects.remove(obs.pop())

            bpy.data.collections.remove(coll)
 
    @staticmethod
    def add_cube(context):
        bpy.ops.mesh.primitive_cube_add()
 
    @staticmethod
    def add_sphere(context, polymer):
        
        #frame_num=0
        #bpy.context.scene.frame_set(frame_num)
        
        #for vec in polymer:
        #    print(vec)
        #    bpy.ops.mesh.primitive_uv_sphere_add(segments=9, ring_count=6, location=(vec[0],vec[1],vec[2]))
       
        bpy.ops.object.select_all(action='DESELECT')
        # default segments=32, ring_count=16
        bpy.ops.mesh.primitive_uv_sphere_add(segments=9, ring_count=6)
        vec = polymer[0]
        sphere = bpy.context.object
        sphere.location = Vector((vec[0],vec[1],vec[2]));
        bpy.ops.object.shade_smooth()
        coll = bpy.data.collections.new("PolymerSystem")
        # link the newCol to the scene
        bpy.context.scene.collection.children.link(coll)
        #bpy.context.collection.objects.link(sphere)
        coll.objects.link(sphere)
        bpy.context.collection.objects.unlink(sphere)

        # link the object to collection
        #newCol.objects.link(obj)
        # ... or link through bpy.data
        #bpy.data.collections['Yammy'].objects.link(obj)

        #for i in range(1000):
        
        for vec in polymer[1:]:
            ob = sphere.copy()
            ob.data = sphere.data.copy()
            ob.location = Vector((vec[0],vec[1],vec[2]));
            #bpy.context.collection.objects.link(ob)
            coll.objects.link(ob)
            #bpy.context.scene.collection.objects.unlink(ob)
        
        #bpy.context.scene.update()
        
        
        #.select.select_by_type(type=’MESH’)
        for i, obj in enumerate(bpy.data.objects):
            if obj.type == 'MESH':
                mat = bpy.data.materials.new("mat_" + str(obj.name))
                mat.diffuse_color = (1.0-i/len(bpy.data.objects), 0, i/len(bpy.data.objects), 1)
                obj.data.materials.append(mat)
            
    @staticmethod
    def add_bonds(context, bonds, polymer):
        bpy.ops.object.select_all(action='DESELECT')
        
        coll = bpy.data.collections.new("Bonds")
        bpy.context.scene.collection.children.link(coll)
        
        bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius = 0.4, depth = 2.7,location = (0, 0, 0)) 
        cylinder = bpy.context.object
        #coll.objects.link(cylinder)
        bpy.context.collection.objects.unlink(cylinder)
        
        for key in sorted(bonds.keys()):
            for item in sorted(bonds[key]):
                if key < item:
                    dx = polymer[key][0] - polymer[item][0]
                    dy = polymer[key][1] - polymer[item][1]
                    dz = polymer[key][2] - polymer[item][2]  
                    dist = math.sqrt(dx**2 + dy**2 + dz**2)
                    
                    #bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius = 0.4, depth = dist,location = (dx/2 + polymer[item][0], dy/2 + polymer[item][1], dz/2 + polymer[item][2])) 
                    ob = cylinder.copy()
                    ob.data = cylinder.data.copy()
                    ob.location = Vector((dx/2 + polymer[item][0], dy/2 + polymer[item][1], dz/2 + polymer[item][2]));
                    #bpy.context.collection.objects.link(ob)
                    #coll.objects.link(ob)
                    
                    phi = math.atan2(dy, dx) 
                    theta = math.acos(dz/dist)
                    #cylinder = bpy.context.object
                    ob.rotation_euler[1] = theta 
                    ob.rotation_euler[2] = phi
                    #print(cylinder.rotation_euler[1])
                    #print(cylinder.rotation_euler[2])
                    coll.objects.link(ob)
                    #bpy.context.collection.objects.unlink(cylinder)
        
        #breakpoint()
        
#        print("%s: %s" % (key, item))
#        # default segments=32, ring_count=16
#        bpy.ops.mesh.primitive_uv_sphere_add(segments=9, ring_count=6)
#        vec = polymer[0]
#        sphere = bpy.context.object
#        sphere.location = Vector((vec[0],vec[1],vec[2]));
#        
#        coll = bpy.data.collections.new("Bonds")
#        # link the newCol to the scene
#        bpy.context.scene.collection.children.link(coll)
#        #bpy.context.collection.objects.link(sphere)
#        coll.objects.link(sphere)
#        bpy.context.collection.objects.unlink(sphere)

#        # link the object to collection
#        #newCol.objects.link(obj)
#        # ... or link through bpy.data
#        #bpy.data.collections['Yammy'].objects.link(obj)

#        #for i in range(1000):
#        
#        for vec in polymer[1:]:
#            ob = sphere.copy()
#            ob.data = sphere.data.copy()
#            ob.location = Vector((vec[0],vec[1],vec[2]));
#            #bpy.context.collection.objects.link(ob)
#            coll.objects.link(ob)
#            #bpy.context.scene.collection.objects.unlink(ob)
#        
#        #bpy.context.scene.update()
#        
        
 
    @staticmethod
    def add_sphere_movie(context, polymer, frame):
        
        #frame_num=0
        #bpy.context.scene.frame_set(frame_num)
       
        
        bpy.ops.object.select_all(action='DESELECT')
        # default segments=32, ring_count=16
        bpy.ops.mesh.primitive_uv_sphere_add(segments=9, ring_count=6)
        sphere = bpy.context.object

        #for i in range(1000):
        from mathutils import Vector;
        
        for vec in polymer:
            ob = sphere.copy()
            ob.data = sphere.data.copy()
            ob.location = Vector((vec[0],vec[1],vec[2]));
            bpy.context.collection.objects.link(ob)
        
            
        for i, obj in enumerate(bpy.data.objects):
            mat = bpy.data.materials.new("mat_" + str(obj.name))
            mat.diffuse_color = (1.0-i/len(bpy.data.objects), 0, i/len(bpy.data.objects), 1)
            obj.data.materials.append(mat)
            
        
    
    @staticmethod  
    def adjust_location(context, bonds, polymer):
        
        bpy.ops.object.select_all(action='DESELECT')
        name = "PolymerSystem"
        
        coll = bpy.data.collections.get(name)

        if coll:
            for i, obj in enumerate(coll.objects):
            #obs = [o for o in coll.objects]
            #while obs:
                obj.location=polymer[i]
                #bpy.data.objects.remove(obs.pop())

        bpy.ops.object.select_all(action='DESELECT')
        
        coll = bpy.data.collections.get("Bonds")
        
        if coll:
            idx=0     
            for key in sorted(bonds.keys()):
                for item in sorted(bonds[key]):
                    if key < item:
                        dx = polymer[key][0] - polymer[item][0]
                        dy = polymer[key][1] - polymer[item][1]
                        dz = polymer[key][2] - polymer[item][2]  
                        dist = math.sqrt(dx**2 + dy**2 + dz**2)
                        
                        #bpy.ops.mesh.primitive_cylinder_add(radius = 0.4, depth = dist,location = (dx/2 + polymer[item][0], dy/2 + polymer[item][1], dz/2 + polymer[item][2])) 
                        phi = math.atan2(dy, dx) 
                        theta = math.acos(dz/dist)
                        cylinder = coll.objects[idx]
                        print(cylinder.rotation_euler[1])
                        print(cylinder.rotation_euler[2])
                        cylinder.location = (dx/2 + polymer[item][0], dy/2 + polymer[item][1], dz/2 + polymer[item][2])
                        #cylinder.depth = dist
                        cylinder.rotation_euler[1] = theta 
                        cylinder.rotation_euler[2] = phi
                        idx += 1
                        #coll.objects.link(cylinder)
                        #bpy.context.collection.objects.unlink(cylinder)   
            
        #idx=0
        #for i, obj in enumerate(bpy.data.objects):
        #   if obj.type == 'MESH':
        #       obj.location=polymer[idx]
        #        idx += 1
     
# ------------------------------------------------------------------------
#    Registration
# ------------------------------------------------------------------------

classes = (
    MyProperties,
    TEST_OT_test_op,
    PT_BlendPyBFM
)

def register():
    
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.my_tool = PointerProperty(type=MyProperties)

def unregister():
    
    for cls in reversed(classes):
        unregister_class(cls)
    del bpy.types.Scene.my_tool


if __name__ == "__main__":
    register()
 
       
