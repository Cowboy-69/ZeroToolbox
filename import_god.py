import os
import mmap
import struct
from dataclasses import dataclass
from bpy_extras.image_utils import load_image

import bpy
import bmesh

@dataclass
class Vector:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

@dataclass
class Color:
    r: int = 0
    g: int = 0
    b: int = 0
    a: int = 0

@dataclass
class ColorFloat:
    r: float = 0.0
    g: float = 0.0
    b: float = 0.0
    a: float = 0.0

@dataclass
class FaceObj:
    vtx: list = 0
    verts: list = 0
    norms: list = 0
    uvs: list = 0
    index: list = 0 # face
    buckyIndex: list = 0 # material group

@dataclass
class BucketDesc:
    flags0: list = 0
    vertCount: list = 0 # max possible
    indexCount: list = 0 # max possible
    materialName: list = 0
    diffuse: list = 0
    specular: list = 0
    specularPower: list = 0
    emissive: list = 0
    ambient: list = 0
    textureName: list = 0


class Importer:
    MAX_GAMEIDENT = 64 # The maximum size of a standard game identifier string

    FLOAT_SIZE = 4
    INT_SIZE = 4

    MAX_VERTS = 22000
    MAX_TRIS = 22000
    MAX_BUCKYS = 16
    MAX_MESHPERGROUP = 64

    godVersion = 13

    streambuffer = ""

    mapPointer = ""
    memPtr = ""
    initPtr = ""

    streamsize = 6361 # TEMPORARY
    dataPos = 52 # TEMPORARY

    ##########################
    ### Info from file

    objectName = ""

    # Bounds
    width = 0.0
    height = 0.0
    breadth = 0.0
    radius = 0.0
    offset = [0.0, 0.0, 0.0]

    scale = 0.0

    quickLight = 0
    shadowPlane = 0

    envMap = 0
    texTimer = 0

    hasTread = 0
    hasControl = 0

    unknown1 = 0.0 # version > 12

    shadowInfo_radxRender = 0.0
    shadowInfo_radyRender = 0.0
    shadowInfo_p1 = [0.0, 0.0, 0.0]
    shadowInfo_p2 = [0.0, 0.0, 0.0]

    shadowType = 0
    shadowRadius = 0.0

    treadPerMeter = 0.0

    vertices = []
    normals = []
    uvs = [] # u, v
    colors = [] # b, g, r, a
    faces = FaceObj([], [], [], [], [], [])
    buckys = BucketDesc([], [], [], [], [], [], [], [], [], [])
    vertToState = [0.0, 0.0, 0.0]
    planes = [0.0, 0.0, 0.0]

    stateMats = [0.0, 0.0, 0.0]

    ### End of info from file
    ##########################

def load(size):
    data = Importer.memPtr.read(size)
    return data

def loadStr():
    length = load(2)
    length = int.from_bytes(length, "little")
    length = min(Importer.MAX_GAMEIDENT, length-1)
    string = load(length)
    string = string.decode()
    return string

def loadFloat():
    return struct.unpack('f', load(Importer.FLOAT_SIZE))[0]

def loadInt():
    return struct.unpack('i', load(Importer.INT_SIZE))[0]

def loadBounds():
    if (Importer.godVersion > 1):
        v0, v1, v2 = [0.0, 0.0, 0.0]
        v0 = loadFloat()
        Importer.radius = v0

        v0 = loadFloat()
        v1 = loadFloat()
        v2 = loadFloat()
        Importer.width = v0
        Importer.height = v1
        Importer.breadth = v2

        Importer.offset[0] = loadFloat()
        Importer.offset[1] = loadFloat()
        Importer.offset[2] = loadFloat()
    else:
        Importer.radius = loadFloat()
        Importer.memPtr.read(64) # Matrix
        Importer.width = loadFloat()
        Importer.height = loadFloat()
        Importer.breadth = loadFloat()

def loadArray4_Vertices():
    count = loadInt()

    # 12 - sizeof( DATA)
    # size = count * 12

    for _ in range (0, count):
        x = loadFloat()
        y = loadFloat()
        z = loadFloat()
        Importer.vertices.append((x, y, z))

def loadArray4_Normals():
    count = loadInt()

    # 12 - sizeof( DATA)
    # size = count * 12

    for _ in range (0, count):
        x = loadFloat()
        y = loadFloat()
        z = loadFloat()
        Importer.normals.append((x, y, z))

def loadArray4_UVs():
    count = loadInt()

    # 12 - sizeof( DATA)
    # size = count * 12

    for _ in range (0, count):
        u = loadFloat()
        v = loadFloat()
        Importer.uvs.append((u, v))

def loadArray4_Colors():
    count = loadInt()

    # 12 - sizeof( DATA)
    # size = count * 12

    for _ in range (0, count):
        b = loadInt()
        g = loadInt()
        r = loadInt()
        a = loadInt()
        Importer.colors.append((b, g, r, a))

def loadArray4_Faces():
    count = loadInt()

    # 12 - sizeof( DATA)
    # size = count * 12

    for _ in range (0, count):
        verts = [0.0, 0.0, 0.0]
        norms = [0.0, 0.0, 0.0]
        uvs = [0.0, 0.0, 0.0]

        bi = int.from_bytes(Importer.memPtr.read(2), "little")
        buckyIndex = bi

        verts[0] = int.from_bytes(Importer.memPtr.read(2), "little")
        verts[1] = int.from_bytes(Importer.memPtr.read(2), "little")
        verts[2] = int.from_bytes(Importer.memPtr.read(2), "little")
        norms[0] = int.from_bytes(Importer.memPtr.read(2), "little")
        norms[1] = int.from_bytes(Importer.memPtr.read(2), "little")
        norms[2] = int.from_bytes(Importer.memPtr.read(2), "little")
        uvs[0] = int.from_bytes(Importer.memPtr.read(2), "little")
        uvs[1] = int.from_bytes(Importer.memPtr.read(2), "little")
        uvs[2] = int.from_bytes(Importer.memPtr.read(2), "little")

        Importer.faces.verts.append(verts)
        Importer.faces.norms.append(norms)
        Importer.faces.uvs.append(uvs)
        Importer.faces.buckyIndex.append(buckyIndex)

def loadArray4_Buckys():
    count = loadInt()

    # 12 - sizeof( DATA)
    # size = count * 12

    for i in range (0, count):
        diffuse = [0.0, 0.0, 0.0, 0.0]
        specular = [0.0, 0.0, 0.0, 0.0]
        emissive = [0.0, 0.0, 0.0, 0.0]
        ambient = [0.0, 0.0, 0.0, 0.0]

        flags0 = loadInt()
        vertCount = loadInt()
        indexCount = loadInt()

        Importer.buckys.flags0.append(flags0)
        Importer.buckys.vertCount.append(vertCount)
        Importer.buckys.indexCount.append(indexCount)
        
        # 0x9709513E - "Material"
        if (loadInt() == -1760997058):
            ### load material

            materialName = loadStr()
            Importer.memPtr.read(1)

            diffuse[0] = loadFloat()
            diffuse[1] = loadFloat()
            diffuse[2] = loadFloat()
            diffuse[3] = loadFloat()
            specular[0] = loadFloat()
            specular[1] = loadFloat()
            specular[2] = loadFloat()
            specular[3] = loadFloat()
            specularPower = loadFloat()
            emissive[0] = loadFloat()
            emissive[1] = loadFloat()
            emissive[2] = loadFloat()
            emissive[3] = loadFloat()
            ambient[0] = loadFloat()
            ambient[1] = loadFloat()
            ambient[2] = loadFloat()
            ambient[3] = loadFloat()

            if (Importer.godVersion > 1 and Importer.godVersion < 10):
                Importer.memPtr.read(4)
                Importer.memPtr.read(4)
                Importer.memPtr.read(4)
            
            textureName = ""
            if (Importer.godVersion > 1):

                # 0xF644CB33 - "Texture0"
                memPtrPos = Importer.memPtr.tell()
                if (loadInt() == -163263693):
                    textureName = loadStr()
                    Importer.memPtr.read(1)
                    type = loadInt()
                    mipMapCount = loadInt()
                else:
                    Importer.memPtr.seek(memPtrPos)

                # 0xF285D684 - "Texture1"
                memPtrPos = Importer.memPtr.tell()
                if (loadInt() == -226109820):
                    textureName = loadStr()
                    Importer.memPtr.read(1)
                    type = loadInt()
                    mipMapCount = loadInt()
                else:
                    Importer.memPtr.seek(memPtrPos)
                
                teamColor = loadInt()
                envMap = loadInt()
                overlay = loadInt()
            else:
                # 0x7951FC0B - "Texture"
                memPtrPos = Importer.memPtr.tell()
                if (loadInt() == 2035416075):
                    textureName = loadStr()
                    Importer.memPtr.read(1)
                    type = loadInt()
                    mipMapCount = loadInt()
                else:
                    Importer.memPtr.seek(memPtrPos)

                teamColor = 0
                envMap = 0
                overlay = 0

            Importer.buckys.textureName.append(textureName)
            Importer.buckys.materialName.append(materialName)
            Importer.buckys.diffuse.append(diffuse)
            Importer.buckys.specular.append(specular)
            Importer.buckys.specularPower.append(specularPower)
            Importer.buckys.emissive.append(emissive)
            Importer.buckys.ambient.append(ambient)

def Cleanup():
    Importer.godVersion = 13

    Importer.streambuffer = ""

    Importer.mapPointer = ""
    Importer.memPtr = ""
    Importer.initPtr = ""

    Importer.streamsize = 6361 # TEMPORARY
    Importer.dataPos = 52 # TEMPORARY

    # Bounds
    Importer.width = 0.0
    Importer.height = 0.0
    Importer.breadth = 0.0
    Importer.radius = 0.0
    Importer.offset = [0.0, 0.0, 0.0]

    Importer.scale = 0.0

    Importer.quickLight = 0
    Importer.shadowPlane = 0

    Importer.envMap = 0
    Importer.texTimer = 0

    Importer.hasTread = 0
    Importer.hasControl = 0

    Importer.unknown1 = 0.0

    Importer.shadowInfo_radxRender = 0.0
    Importer.shadowInfo_radyRender = 0.0
    Importer.shadowInfo_p1 = [0.0, 0.0, 0.0]
    Importer.shadowInfo_p2 = [0.0, 0.0, 0.0]

    Importer.shadowType = 0
    Importer.shadowRadius = 0.0

    Importer.treadPerMeter = 0.0
    
    Importer.vertices = []
    Importer.normals = []
    Importer.uvs = []
    Importer.colors = []
    Importer.faces = FaceObj([], [], [], [], [], [])
    Importer.buckys = BucketDesc([], [], [], [], [], [], [], [], [], [])
    Importer.vertToState = [0.0, 0.0, 0.0]
    Importer.planes = [0.0, 0.0, 0.0]

    stateMats = [0.0, 0.0, 0.0]

def start_import(options):
    Cleanup()

    Importer.filePath = options['filePath']

    meshRootBlock = options['meshRoot']
    if (meshRootBlock == "MeshRootBlock13"):
        Importer.godVersion = 13
    elif (meshRootBlock == "MeshRootBlock12"):
        Importer.godVersion = 12
    elif (meshRootBlock == "MeshRootBlock11"):
        Importer.godVersion = 11
    elif (meshRootBlock == "MeshRootBlock10"):
        Importer.godVersion = 10
    elif (meshRootBlock == "MeshRootBlock9"):
        Importer.godVersion = 9
    elif (meshRootBlock == "MeshRootBlock8"):
        Importer.godVersion = 8
    elif (meshRootBlock == "MeshRootBlock7"):
        Importer.godVersion = 7
    elif (meshRootBlock == "MeshRootBlock6"):
        Importer.godVersion = 6
    elif (meshRootBlock == "MeshRootBlock5"):
        Importer.godVersion = 5
    elif (meshRootBlock == "MeshRootBlock3"):
        Importer.godVersion = 3
    elif (meshRootBlock == "MeshRootBlock2"):
        Importer.godVersion = 2
    else:
        Importer.godVersion = 1

    ###################### File reading section ######################

    bFile = open(Importer.filePath, mode='rb')

    Importer.streambuffer = bFile.read()
    Importer.streambuffer = bytearray(Importer.streambuffer)
    #streamsize = os.path.getsize(filePath)
    Importer.mapPointer = mmap.mmap(bFile.fileno(), 0, access=mmap.ACCESS_READ)
    Importer.mapPointer.read(Importer.dataPos)
    Importer.memPtr = Importer.mapPointer
    Importer.initPtr = Importer.mapPointer

    Importer.objectName = loadStr()

    Importer.memPtr.read(1)

    loadBounds()

    Importer.scale = loadFloat()
    Importer.quickLight = loadInt()
    Importer.shadowPlane = loadInt()

    if (Importer.godVersion > 1):
        Importer.envMap = loadInt()
        Importer.texTimer = loadInt()
        Importer.texTimer = float(Importer.texTimer) * 0.001

    if (Importer.godVersion > 11):
        Importer.shadowInfo_radxRender = loadFloat()
        Importer.shadowInfo_radyRender = loadFloat()
        Importer.shadowInfo_p2[0] = loadFloat()
        Importer.shadowInfo_p2[1] = loadFloat()
        Importer.shadowInfo_p2[2] = loadFloat()
        Importer.shadowInfo_p1 = Importer.shadowInfo_p2

    if (Importer.godVersion > 12):
        Importer.unknown1 = loadFloat()

    if (Importer.godVersion > 5):
        Importer.hasTread = loadInt()
        Importer.hasControl = loadInt()

    if (Importer.godVersion > 10):
        Importer.shadowType = loadInt()
    elif (Importer.godVersion > 8):
        if (loadInt() == True):
            Importer.shadowType = 2 # shadowSEMILIVE
        else:
            Importer.shadowType = 0 # shadowOVAL

    Importer.shadowRadius = loadFloat()

    if (Importer.godVersion > 7):
        Importer.treadPerMeter = loadFloat()

    loadArray4_Vertices()
    loadArray4_Normals()
    loadArray4_UVs()
    loadArray4_Colors()

    loadArray4_Faces()
    loadArray4_Buckys()

    bFile.close()

    ###################### Blender section ######################

    # Mesh
    newMesh = bpy.data.meshes.new(Importer.objectName)
    blenderMesh = bmesh.new()

    # Vertices
    for vert in Importer.vertices:
        blenderMesh.verts.new(vert)
    blenderMesh.verts.ensure_lookup_table()
    blenderMesh.verts.index_update()

    uv_layers = []
    uv_layers.append([])
    for j in range(0, len(Importer.uvs)):
        uv_layers[0].append(Importer.uvs[j])

    bl_uv_layers = []
    for layer in uv_layers:
        bl_uv_layers.append(blenderMesh.loops.layers.uv.new())

    # Faces
    for i in range(0, len(Importer.faces.verts)):
        try:
            face = blenderMesh.faces.new([blenderMesh.verts[v] for v in Importer.faces.verts[i]])

            face.material_index = Importer.faces.buckyIndex[i]

            count = 0
            for loop in face.loops:

                u = Importer.uvs[Importer.faces.uvs[i][count]][0]
                v = Importer.uvs[Importer.faces.uvs[i][count]][1]
                loop[bl_uv_layers[0]].uv = (u, 1 - v)

                count += 1
        except:
            pass

    # The resulting mesh is mirrored, so return it to the correct position
    for v in blenderMesh.verts:
        v.co.x *= -1

    # Materials
    for i in range(0, len(Importer.buckys.materialName)):
        material = bpy.data.materials.new(Importer.buckys.materialName[i])
        material.blend_method = 'CLIP'
        material.diffuse_color = Importer.buckys.diffuse[i]
        material.specular_color = Importer.buckys.specular[i][:3]
        material.specular_intensity = Importer.buckys.specularPower[i]
        material.use_nodes = True

        newMesh.materials.append(material)

    # Textures
    for i in range(0, len(Importer.buckys.textureName)):
        if (Importer.buckys.textureName[i] == ""):
            continue

        texturePath = os.path.dirname(Importer.filePath)
        textureImage = load_image(Importer.buckys.textureName[i], texturePath, False, True, True)

        if (textureImage == None):
            continue

        material = newMesh.materials[i]

        tex_node = material.node_tree.nodes.new('ShaderNodeTexImage')
        tex_node.image = textureImage

        principled_BSDF = material.node_tree.nodes.get('Principled BSDF')

        material.node_tree.links.new(tex_node.outputs[0], principled_BSDF.inputs[0])

    # Collection
    blenderCollection = bpy.data.collections.new(Importer.objectName)
    bpy.context.scene.collection.children.link(blenderCollection)

    # Object
    blenderObject = bpy.data.objects.new(Importer.objectName, newMesh)
    blenderCollection.objects.link(blenderObject)
    blenderObject.rotation_euler.x += 1.5708 # Rotate the object 90 degrees

    blenderMesh.to_mesh(newMesh)

    newMesh.update()

    blenderMesh.free()

### testing
#file = "filepath.god"
#start_import({'filePath' : file, 'meshRoot' : "MeshRootBlock13"})
