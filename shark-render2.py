import bpy
import os
import numpy as np
import json
from mathutils import Matrix
from pyblend.render import config_render, render_image
from pyblend.lighting import config_world, create_light
from pyblend.utils import BlenderRemover, ArgumentParserForBlender
from pyblend.object import load_obj, create_plane
from pyblend.transform import look_at, normalize_obj, random_loc

def load_texture(texture_path):
    """Load texture image from file."""
    if not os.path.exists(texture_path):
        raise FileNotFoundError(f"Texture image '{texture_path}' not found.")
    
    mat = bpy.data.materials.new(name="TextureMaterial")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes

    for node in nodes:
        nodes.remove(node)

    texture_node = nodes.new(type='ShaderNodeTexImage')
    texture_node.image = bpy.data.images.load(texture_path)

    principled_bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    output_node = nodes.new(type='ShaderNodeOutputMaterial')
    links = mat.node_tree.links
    links.new(texture_node.outputs['Color'], principled_bsdf.inputs['Base Color'])
    links.new(principled_bsdf.outputs['BSDF'], output_node.inputs['Surface'])

    return mat

def get_camera_extrinsics(camera):
    """Returns the camera extrinsics (pose) as a transformation matrix."""
    c2w_matrix = camera.matrix_world
    c2w_list = [list(row) for row in c2w_matrix]
    return {"transform_matrix": c2w_list}

def get_camera_intrinsics(camera):
    """Returns the camera intrinsics (focal length) as a list."""
    focal_length = camera.data.lens
    return {"focal_length": focal_length}

def get_camera_rotation(camera):
    """Returns the camera rotation as a scalar value."""
    return camera.rotation_euler.to_quaternion().angle

def render_and_save_extrinsics(args):
    config_render(res_x=800, res_y=800, transparent=True)
    remover = BlenderRemover()
    remover.clear_all()
    config_world(0.3)

    texture_path = os.path.join(os.getcwd(), args.texture_path)
    texture_material = load_texture(texture_path)

    obj_path = args.input
    load_obj(obj_path, "object", center=True)
    bpy.context.view_layer.update()

    obj = bpy.context.selected_objects[0]
    normalize_obj(obj)
    obj.location = (0, 0, 0)

    obj.data.materials.clear()
    obj.data.materials.append(texture_material)

    spot_light = create_light("SPOT", (3, 3, 10), (np.pi / 2, 0, 0), 400, (1, 1, 1), 5, name="light")
    look_at(spot_light, obj.location)

    camera = bpy.data.objects["Camera"]

    if "Track To" not in camera.constraints:
        track_to_constraint = camera.constraints.new(type='TRACK_TO')
        track_to_constraint.track_axis = 'TRACK_NEGATIVE_Z'
        track_to_constraint.up_axis = 'UP_Y'
        track_to_constraint.target = obj

    extrinsics_list = []
    intrinsics_list = []
    frames_list = []

    os.makedirs(f"tmp/{args.name}/{args.split}", exist_ok=True)

    camera_angle_x = camera.data.angle_x

    for i in range(args.num):
        r = 1.5
        theta = np.random.uniform(0, 2 * np.pi)
        phi = np.random.uniform(0, np.pi)
        x = r * np.sin(phi) * np.cos(theta)
        y = r * np.sin(phi) * np.sin(theta)
        z = r * np.cos(phi)
        camera.location = (x, y, z)
        look_at(camera, obj.location)
        render_image_path = f"tmp/{args.name}/{args.split}/{args.name}_{i:04d}.png"
        render_image(render_image_path)

        extrinsics = get_camera_extrinsics(camera)
        extrinsics['frame'] = f"{args.name}_{i:04d}.png"
        extrinsics_list.append(extrinsics)

        intrinsics = get_camera_intrinsics(camera)
        intrinsics_list.append(intrinsics)

        rotation = get_camera_rotation(camera)
        frame_info = {
            "file_path": f"./{args.split}/{args.name}_{i:04d}.png",
            "rotation": rotation,
            "transform_matrix": extrinsics['transform_matrix']
        }
        frames_list.append(frame_info)

    json_output = {
        "camera_angle_x": camera_angle_x,
        "frames": frames_list
    }

    with open(f"tmp/{args.name}/transforms_{args.split}.json", 'w') as f:
        json.dump(json_output, f, indent=4)

if __name__ == "__main__":
    parser = ArgumentParserForBlender()
    parser.add_argument("-i", "--input", type=str, default="Shark/meshes/model.obj")
    parser.add_argument("-n", "--num", type=int, default=12)
    parser.add_argument("--name", type=str, default="shark_render")
    parser.add_argument("--texture_path", type=str, default="Shark/materials/textures/texture.png")
    parser.add_argument("--split", type=str, choices=["train", "test", "val"], default="train")
    args = parser.parse_args()
    render_and_save_extrinsics(args)
