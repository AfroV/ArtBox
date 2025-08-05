# pip install pillow trimesh numpy
# python dual_lithophane_generator.py path/to/your/image.jpg --width 144 --output_dir output_folder
# Optional flags:
# --width → total print width in mm (default: 100 mm)
# --max_thickness → for darkest parts (default: 2.5 mm)
# --min_thickness → for lightest parts (default: 0.8 mm)
# --backplate_thickness → black backing plate (default: 0.6 mm)
#



import argparse
from pathlib import Path
from PIL import Image
import numpy as np
import trimesh

def generate_lithophane_mesh(image_path, width_mm=100, max_thickness_mm=2.5, min_thickness_mm=0.8, backplate_thickness_mm=0.6):
    img = Image.open(image_path).convert("L")
    img = img.transpose(Image.FLIP_TOP_BOTTOM)
    img_np = np.array(img)

    height_px, width_px = img_np.shape
    aspect_ratio = width_px / height_px
    height_mm = width_mm / aspect_ratio

    norm_img = img_np / 255.0
    thickness_map = min_thickness_mm + (1 - norm_img) * (max_thickness_mm - min_thickness_mm)

    x = np.linspace(0, width_mm, width_px)
    y = np.linspace(0, height_mm, height_px)
    xx, yy = np.meshgrid(x, y)

    vertices = np.column_stack((xx.ravel(), yy.ravel(), thickness_map.ravel()))
    faces = []

    for i in range(height_px - 1):
        for j in range(width_px - 1):
            idx = i * width_px + j
            faces.append([idx, idx + 1, idx + width_px])
            faces.append([idx + 1, idx + width_px + 1, idx + width_px])

    litho_mesh = trimesh.Trimesh(vertices=vertices, faces=faces)

    backplate_vertices = np.column_stack((xx.ravel(), yy.ravel(), np.zeros_like(xx).ravel() - backplate_thickness_mm))
    backplate_faces = []

    for i in range(height_px - 1):
        for j in range(width_px - 1):
            idx = i * width_px + j
            backplate_faces.append([idx, idx + width_px, idx + 1])
            backplate_faces.append([idx + 1, idx + width_px, idx + width_px + 1])

    backplate_mesh = trimesh.Trimesh(vertices=backplate_vertices, faces=backplate_faces)

    return litho_mesh, backplate_mesh

def main():
    parser = argparse.ArgumentParser(description="Generate dual-layer lithophane STL files.")
    parser.add_argument("image", type=str, help="Path to the input image (grayscale recommended).")
    parser.add_argument("--width", type=float, default=100.0, help="Width of the lithophane in mm.")
    parser.add_argument("--max_thickness", type=float, default=2.5, help="Maximum thickness (darkest areas).")
    parser.add_argument("--min_thickness", type=float, default=0.8, help="Minimum thickness (lightest areas).")
    parser.add_argument("--backplate_thickness", type=float, default=0.6, help="Thickness of the backplate in mm.")
    parser.add_argument("--output_dir", type=str, default="output", help="Directory to save STL files.")

    args = parser.parse_args()

    image_path = Path(args.image)
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    litho_mesh, back_mesh = generate_lithophane_mesh(
        image_path,
        width_mm=args.width,
        max_thickness_mm=args.max_thickness,
        min_thickness_mm=args.min_thickness,
        backplate_thickness_mm=args.backplate_thickness
    )

    litho_mesh.export(output_path / "lithophane_white_part.stl")
    back_mesh.export(output_path / "lithophane_black_backplate.stl")

    print(f"Saved: {output_path / 'lithophane_white_part.stl'}")
    print(f"Saved: {output_path / 'lithophane_black_backplate.stl'}")

if __name__ == "__main__":
    main()
