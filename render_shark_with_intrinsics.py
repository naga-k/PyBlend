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
    # Check if texture image exists
    if not os.path.exists(texture_path):
        raise FileNotFoundError(f"Texture image '{texture_path}' not found.")
    
    # Create material
    mat = bpy.data.materials.new(name="TextureMaterial")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes

    # Clear default nodes
    for node in nodes:
        nodes.remove(node)

    # Create image texture node
    texture_node = nodes.new(type='ShaderNodeTexImage')
    texture_node.image = bpy.data.images.load(texture_path)

    # Connect nodes
    principled_bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    output_node = nodes.new(type='ShaderNodeOutputMaterial')
    links = mat.node_tree.links
    links.new(texture_node.outputs['Color'], principled_bsdf.inputs['Base Color'])
    links.new(principled_bsdf.outputs['BSDF'], output_node.inputs['Surface'])

    return mat

def get_camera_extrinsics(camera):
    """Returns the camera extrinsics (pose) as a transformation matrix."""
    # Get camera-to-world matrix (4x4)
    c2w_matrix = camera.matrix_world

    # Convert to list for JSON serialization
    c2w_list = [list(row) for row in c2w_matrix]
    
    return {
        "transform_matrix": c2w_list
    }

def get_camera_intrinsics(camera):
    """Returns the camera intrinsics (focal length) as a list."""
    # Assuming fixed focal length for simplicity
    focal_length = 35  # Adjust this value based on your camera settings
    return {
        "focal_length": focal_length
    }

def render_and_save_extrinsics(args):
    # ======== Config ========
    config_render(res_x=800, res_y=800, transparent=True)  # Changed resolution and transparent background
    remover = BlenderRemover()
    remover.clear_all()
    config_world(0.3)

    # ======== Load Texture ========
    texture_path = os.path.join(os.getcwd(), args.texture_path)
    texture_material = load_texture(texture_path)

    # Load OBJ with associated MTL and apply texture
    obj_path = args.input
    load_obj(obj_path, "object", center=True)
    bpy.context.view_layer.update()

    obj = bpy.context.selected_objects[0]
    normalize_obj(obj)
    obj.location = (0, 0, 0)  # Ensure object is centered at origin

    # Assign loaded texture to the object's material
    obj.data.materials.clear()
    obj.data.materials.append(texture_material)

    # Setup lighting
    spot_light = create_light("SPOT", (3, 3, 10), (np.pi / 2, 0, 0), 400, (1, 1, 1), 5, name="light")
    look_at(spot_light, obj.location)

    camera = bpy.data.objects["Camera"]

    # Ensure camera tracking constraint
    if "Track To" not in camera.constraints:
        track_to_constraint = camera.constraints.new(type='TRACK_TO')
        track_to_constraint.track_axis = 'TRACK_NEGATIVE_Z'
        track_to_constraint.up_axis = 'UP_Y'
        track_to_constraint.target = obj

    # ======== Render and Save Extrinsics and Intrinsics ========
    extrinsics_list = []
    intrinsics_list = []
    
    for i in range(args.num):
        # Move camera to a random position around the object using spherical coordinates
        r = 1.5  # Decreased radius
        theta = np.random.uniform(0, 2 * np.pi)
        phi = np.random.uniform(0, np.pi)
        x = r * np.sin(phi) * np.cos(theta)
        y = r * np.sin(phi) * np.sin(theta)
        z = r * np.cos(phi)
        camera.location = (x, y, z)
        look_at(camera, obj.location)  # Ensure the camera looks at the object after moving
        render_image_path = f"tmp/multiview/{args.name}_{i:04d}.png"
        render_image(render_image_path)

        # Save camera extrinsics
        extrinsics = get_camera_extrinsics(camera)
        extrinsics['frame'] = f"{args.name}_{i:04d}.png"
        extrinsics_list.append(extrinsics)

        # Save camera intrinsics (focal length)
        intrinsics = get_camera_intrinsics(camera)
        intrinsics_list.append(intrinsics)

    # Save extrinsics to a JSON file
    os.makedirs("tmp/multiview", exist_ok=True)
    with open(f"tmp/multiview/{args.name}_extrinsics.json", 'w') as f:
        json.dump(extrinsics_list, f, indent=4)

    # Save intrinsics to a JSON file
    with open(f"tmp/multiview/{args.name}_intrinsics.json", 'w') as f:
        json.dump(intrinsics_list, f, indent=4)

if __name__ == "__main__":
    parser = ArgumentParserForBlender()
    parser.add_argument("-i", "--input", type=str, default="Shark/meshes/model.obj")
    parser.add_argument("-n", "--num", type=int, default=12)
    parser.add_argument("--name", type=str, default="shark_render")
    parser.add_argument("--texture_path", type=str, default="Shark/materials/textures/texture.png")
    args = parser.parse_args()
    render_and_save_extrinsics(args)
