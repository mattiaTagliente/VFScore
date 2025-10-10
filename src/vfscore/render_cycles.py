"""Blender Cycles rendering for candidate 3D objects."""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict

from rich.console import Console
from rich.progress import track

from vfscore.config import Config

console = Console()

def generate_blender_script(
    glb_path: Path,
    output_path: Path,
    hdri_path: Path,
    config: Config,
) -> str:
    """Generate Blender Python script for rendering."""
    
    render_cfg = config.render
    camera_cfg = render_cfg.camera
    
    # Correct the denoiser name
    if render_cfg.denoiser == "OIDN":
        denoiser = "OPENIMAGEDENOISE"
    else:
        denoiser = render_cfg.denoiser

    script = f'''
import bpy
import math
import sys
from pathlib import Path
from mathutils import Vector

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Import GLB
glb_path = r"{glb_path}"
bpy.ops.import_scene.gltf(filepath=glb_path)

# Get imported objects
imported_objects = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']

if not imported_objects:
    print("ERROR: No mesh objects imported from GLB")
    sys.exit(1)

# Join all meshes
if len(imported_objects) > 1:
    bpy.context.view_layer.objects.active = imported_objects[0]
    bpy.ops.object.select_all(action='DESELECT')
    for obj in imported_objects:
        obj.select_set(True)
    bpy.ops.object.join()

obj = bpy.context.active_object

# Center at origin
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
obj.location = (0, 0, 0)

# Normalize scale (fit to unit cube)
max_dim = max(obj.dimensions)
if max_dim > 0:
    scale_factor = 1.0 / max_dim
    obj.scale = (scale_factor, scale_factor, scale_factor)

# Apply transforms
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# Rotate object for presentation
obj.rotation_euler[2] = math.radians({render_cfg.object_prez_rot_z_deg})
bpy.ops.object.transform_apply(rotation=True)

# Setup camera
cam_data = bpy.data.cameras.new(name='Camera')
cam_data.lens_unit = 'FOV'
cam_data.angle = math.radians({render_cfg.fov_deg})

cam_obj = bpy.data.objects.new('Camera', cam_data)
bpy.context.scene.collection.objects.link(cam_obj)

# Position camera (spherical coordinates)
radius = {camera_cfg.radius}
azimuth = math.radians({camera_cfg.azimuth_deg})
elevation = math.radians({camera_cfg.elevation_deg})

cam_x = radius * math.cos(elevation) * math.cos(azimuth)
cam_y = radius * math.cos(elevation) * math.sin(azimuth)
cam_z = radius * math.sin(elevation)

cam_obj.location = (cam_x, cam_y, cam_z)

# Point camera at origin
direction = Vector((-cam_x, -cam_y, -cam_z))
rot_quat = direction.to_track_quat('-Z', 'Y')
cam_obj.rotation_euler = rot_quat.to_euler()

bpy.context.scene.camera = cam_obj

# Setup HDRI lighting
world = bpy.context.scene.world
world.use_nodes = True
nodes = world.node_tree.nodes
links = world.node_tree.links

nodes.clear()

node_env = nodes.new('ShaderNodeTexEnvironment')
node_env.image = bpy.data.images.load(r"{hdri_path}")

node_bg = nodes.new('ShaderNodeBackground')
node_bg.inputs['Strength'].default_value = 1.0

node_output = nodes.new('ShaderNodeOutputWorld')

links.new(node_env.outputs['Color'], node_bg.inputs['Color'])
links.new(node_bg.outputs['Background'], node_output.inputs['Surface'])

# Setup render settings
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'GPU'  # Use GPU if available
scene.cycles.samples = {render_cfg.samples}
scene.cycles.use_denoising = True
scene.cycles.denoiser = '{denoiser}'

# Film settings
scene.render.film_transparent = {str(render_cfg.film_transparent)}

# Color management
scene.view_settings.view_transform = 'Filmic' if {str(render_cfg.filmic)} else 'Standard'
scene.view_settings.look = 'None'
scene.view_settings.exposure = 0
scene.view_settings.gamma = 1

# Output settings
scene.render.resolution_x = {render_cfg.resolution}
scene.render.resolution_y = {render_cfg.resolution}
scene.render.resolution_percentage = 100

scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.render.image_settings.color_depth = '8'
scene.render.image_settings.compression = 15

output_path = r"{output_path}"
scene.render.filepath = output_path

# Render
print(f"Rendering to: {{output_path}}")
bpy.ops.render.render(write_still=True)

print("Render complete")
'''
    
    return script


def render_glb(
    glb_path: Path,
    output_path: Path,
    hdri_path: Path,
    blender_exe: Path,
    config: Config,
) -> bool:
    """Render a single GLB file using Blender."""

    # Generate Blender script
    script = generate_blender_script(glb_path, output_path, hdri_path, config)

    # Write script to temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(script)
        script_path = Path(f.name)

    try:
        # Run Blender in background
        cmd = [str(blender_exe), "--background", "--python", str(script_path)]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=300,  # 5 minute timeout
        )

        # Always print Blender's output for debugging
        if result.stdout:
            console.print("[bold]Blender stdout:[/bold]")
            console.print(result.stdout)
        if result.stderr:
            console.print("[bold]Blender stderr:[/bold]")
            console.print(result.stderr)

        if result.returncode != 0:
            console.print(
                f"[red]Blender exited with error code: {result.returncode}[/red]"
            )
            return False

        # Check if output was created
        if not output_path.exists():
            console.print(f"[red]Output file not created: {output_path}[/red]")
            return False

        return True

    except subprocess.TimeoutExpired:
        console.print(f"[red]Blender render timeout for {glb_path}[/red]")
        return False
    except Exception as e:
        console.print(f"[red]Error rendering {glb_path}: {e}[/red]")
        return False
    finally:
        # Clean up temp script
        script_path.unlink(missing_ok=True)


def load_manifest(manifest_path: Path) -> list:
    """Load manifest from JSONL file."""
    records = []
    with open(manifest_path, "r", encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))
    return records


def run_render_candidates(config: Config) -> None:
    """Render all candidate objects."""
    # Load manifest
    manifest_path = config.paths.out_dir / "manifest.jsonl"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    
    manifest = load_manifest(manifest_path)
    
    # Check Blender executable
    if not config.paths.blender_exe.exists():
        raise FileNotFoundError(f"Blender not found: {config.paths.blender_exe}")
    
    # Check HDRI
    if not config.paths.hdri.exists():
        raise FileNotFoundError(f"HDRI not found: {config.paths.hdri}")
    
    console.print(f"\n[bold]Rendering {len(manifest)} objects with Blender Cycles...[/bold]")
    console.print(f"Samples: {config.render.samples}")
    console.print(f"Resolution: {config.render.resolution}x{config.render.resolution}")
    
    success_count = 0
    
    for record in track(manifest, description="Rendering candidates"):
        item_id = record["item_id"]
        glb_path = Path(record["glb_path"])
        
        output_path = config.paths.out_dir / "preprocess" / "cand" / item_id / "candidate.png"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            success = render_glb(
                glb_path,
                output_path,
                config.paths.hdri,
                config.paths.blender_exe,
                config
            )
            if success:
                success_count += 1
        except Exception as e:
            console.print(f"[red]Failed to render {item_id}: {e}[/red]")
    
    console.print(f"[green]Successfully rendered {success_count}/{len(manifest)} objects[/green]")


if __name__ == "__main__":
    from vfscore.config import get_config
    
    config = get_config()
    run_render_candidates(config)
