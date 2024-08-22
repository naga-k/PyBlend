import bpy
import os
import numpy as np
import json
import mathutils
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from plotly.io import write_html
from pyblend.render import config_render, render_image
from pyblend.lighting import config_world, create_light
from pyblend.utils import BlenderRemover, ArgumentParserForBlender
from pyblend.object import load_obj, create_plane
from pyblend.transform import look_at, random_loc

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

def get_bounding_box(obj):
    # Get local bounding box coordinates
    local_bbox = np.array([obj.matrix_world @ mathutils.Vector(corner) for corner in obj.bound_box])
    
    # Get min and max coordinates
    min_corner = np.min(local_bbox, axis=0)
    max_corner = np.max(local_bbox, axis=0)
    
    print("Bounding Box Min Corner:", min_corner)
    print("Bounding Box Max Corner:", max_corner)

def normalize_obj(obj):
    """Normalize object to fit within a unit sphere."""
    # Calculate the bounding box in world coordinates
    local_bbox = np.array([obj.matrix_world @ mathutils.Vector(corner) for corner in obj.bound_box])
    
    # Get min and max corners
    min_corner = np.min(local_bbox, axis=0)
    max_corner = np.max(local_bbox, axis=0)
    
    # Compute the size of the bounding box
    size = np.max(max_corner - min_corner)
    
    # Compute scale factor to normalize the object
    scale_factor = 1.0 / size
    
    # Center the object at the origin
    center = (min_corner + max_corner) / 2.0
    obj.location -= mathutils.Vector(center)
    
    # Apply scaling
    obj.scale = (scale_factor, scale_factor, scale_factor)
    
    # Update the object’s transformation matrix
    bpy.context.view_layer.update()

    # Verify bounding box after normalization
    get_bounding_box(obj)

def get_object_vertices(obj):
    """Returns the vertices of the object in world space."""
    vertices = []
    for v in obj.data.vertices:
        world_vertex = obj.matrix_world @ v.co
        vertices.append((world_vertex.x, world_vertex.y, world_vertex.z))
    return vertices

def plot_vertices_and_cameras(vertices, camera_positions, lights, output_path):

    """Plot the vertices of the object, camera positions, and light positions, and save as HTML."""
    x_verts, y_verts, z_verts = zip(*vertices) if vertices else ([], [], [])
    x_cams, y_cams, z_cams = zip(*camera_positions) if camera_positions else ([], [], [])
    x_lights, y_lights, z_lights = zip(*lights) if lights else ([], [], [])
    
    fig = make_subplots(
        rows=1, cols=1,
        specs=[[{'type': 'scatter3d'}]],
        subplot_titles=("Object Vertices, Camera Positions, and Lights")
    )
    
    # Object vertices plot
    fig.add_trace(
        go.Scatter3d(
            x=x_verts, y=y_verts, z=z_verts,
            mode='markers',
            marker=dict(
                size=2,
                color=z_verts,
                colorscale='Viridis',
                opacity=0.8
            ),
            name='Vertices'
        ),
        row=1, col=1
    )
    
    # Camera positions plot
    fig.add_trace(
        go.Scatter3d(
            x=x_cams, y=y_cams, z=z_cams,
            mode='markers',
            marker=dict(
                size=5,
                color='red',
                opacity=0.8
            ),
            name='Cameras'
        ),
        row=1, col=1
    )
    
    # Light positions plot
    fig.add_trace(
        go.Scatter3d(
            x=x_lights, y=y_lights, z=z_lights,
            mode='markers',
            marker=dict(
                size=10,
                color='yellow',
                opacity=0.8,
                symbol='circle'
            ),
            name='Lights'
        ),
        row=1, col=1
    )
    
    fig.update_layout(height=1600, width=1600, title_text="Object Vertices, Camera Positions, and Lights")
    write_html(fig, file=output_path, auto_open=False)

def render_and_save_extrinsics(args):
    config_render(res_x=800, res_y=800, transparent=True)
    remover = BlenderRemover()
    remover.clear_all()
    config_world(0.3)

    # Construct paths to the object and texture files
    obj_path = os.path.join(args.data_dir, args.name, 'meshes', 'model.obj')
    texture_path = os.path.join(args.data_dir, args.name, 'materials', 'textures', 'texture.png')
    
    if not os.path.exists(obj_path):
        raise FileNotFoundError(f"Object file '{obj_path}' not found.")
    
    if not os.path.exists(texture_path):
        raise FileNotFoundError(f"Texture file '{texture_path}' not found.")
    
    texture_material = load_texture(texture_path)
    load_obj(obj_path, "object", center=True)
    bpy.context.view_layer.update()

    obj = bpy.context.selected_objects[0]
    normalize_obj(obj)
    obj.location = (0, 0, 0)

    obj.data.materials.clear()
    obj.data.materials.append(texture_material)

    # Lighting setup
    spot_light = create_light("SPOT", (3, 3, 3), (np.pi / 2, 0, 0), 400, (1, 1, 1), 5, name="light")
    look_at(spot_light, obj.location)

    camera = bpy.data.objects["Camera"]

    if "Track To" not in camera.constraints:
        track_to_constraint = camera.constraints.new(type='TRACK_TO')
        track_to_constraint.track_axis = 'TRACK_NEGATIVE_Z'
        track_to_constraint.up_axis = 'UP_Y'
        track_to_constraint.target = obj

    get_bounding_box(obj)

    extrinsics_list = []
    intrinsics_list = []
    frames_list = []
    camera_positions = []

    # Output directory setup with respect to split
    output_dir = os.path.join(args.output_dir, f"{args.name}_{args.radius}_{args.num}")
    os.makedirs(output_dir, exist_ok=True)

    camera_angle_x = camera.data.angle_x
    camera_angle_y = camera.data.angle_y

    if args.split == 'train':
        # Random camera placement for training
        for i in range(args.num):
            theta = np.random.uniform(0, 2 * np.pi)
            phi = np.random.uniform(0, np.pi)
            x = args.radius * np.sin(phi) * np.cos(theta)
            y = args.radius * np.sin(phi) * np.sin(theta)
            z = args.radius * np.cos(phi)
            camera.location = (x, y, z)
            look_at(camera, obj.location)
            render_image_path = os.path.join(output_dir, f"{args.split}", f"{args.name}_{i:04d}.png")
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
                "transform_matrix": extrinsics['transform_matrix'],
                "focal_length": intrinsics['focal_length'],
                "camera_angle_x": camera_angle_x,
                "camera_angle_y": camera_angle_y
            }
            frames_list.append(frame_info)

            camera_positions.append(camera.location.copy())

    elif args.split == 'test':
        # Spiral camera placement
        num_cameras = args.num
        radius = args.radius
        height_step = 2 * radius / num_cameras  # Adjust height step to spread the spiral along the z-axis

        for i in range(num_cameras):
            angle = np.linspace(0, 2 * np.pi, num_cameras, endpoint=False)[i]
            height = i * height_step - radius  # Spread the spiral along the z-axis

            x = radius * np.cos(angle)
            y = radius * np.sin(angle)
            z = height

            camera.location = (x, y, z)
            look_at(camera, obj.location)
            
            render_image_path = os.path.join(output_dir, f"{args.split}", f"{args.name}_{i:04d}.png")
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
                "transform_matrix": extrinsics['transform_matrix'],
                "focal_length": intrinsics['focal_length'],
                "camera_angle_x": camera_angle_x,
                "camera_angle_y": camera_angle_y
            }
            frames_list.append(frame_info)

            camera_positions.append(camera.location.copy())

    # Save transform JSON
    transform_json_path = os.path.join(output_dir, f"transforms_{args.split}.json")
    with open(transform_json_path, 'w') as outfile:
        json.dump(frames_list, outfile, indent=4)
    
    print(f"Transform JSON saved to {transform_json_path}")

    # Plotting
    vertices = get_object_vertices(obj)
    light_positions = [spot_light.location]
    plot_output_path = os.path.join(output_dir, f"plot_{args.split}.html")
    plot_vertices_and_cameras(vertices, camera_positions, light_positions, plot_output_path)

if __name__ == "__main__":
    parser = ArgumentParserForBlender()
    parser.add_argument('--name', type=str, help='Dataset name', required=True)
    parser.add_argument('--num', type=int, help='Number of images to render', required=True)
    parser.add_argument('--split', type=str, help='Dataset split (train/test)', choices=['train', 'test'], required=True)
    parser.add_argument('--output_dir', type=str, help='Output directory', required=True)
    parser.add_argument('--data_dir', type=str, help='Input data directory', required=True)
    parser.add_argument('--radius', type=float, help='Radius for camera placement', required=True)
    args = parser.parse_args()

    render_and_save_extrinsics(args)
