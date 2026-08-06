from pathlib import Path
import subprocess
from sys import exit

def create_tilemap(args):
    tiles_dir: Path = args.tiles_dir
    png_path: Path = args.filename
    bbox: list[float] = args.bbox
    bbox_str = ",".join(map(str, bbox))
    min_zoom, max_zoom = args.min_zoom, args.max_zoom
    if not png_path.exists():
        return
    if tiles_dir.exists():
        print(f"Cannot overwrite {tiles_dir}. Remove before running!")
        exit(1)

    subprocess.run(['gdal', 'raster', 'pipeline',
                    'read', str(png_path), '!',
                    'edit', '--bbox', bbox_str,
                    '--crs', 'EPSG:4326', '!',
                    'write', str(png_path.stem) + '.tif', '--format=GTiff'])
    subprocess.run(['gdal', 'raster', 'tile',
                    '--min-zoom', str(min_zoom),
                    '--max-zoom', str(max_zoom),
                    str(png_path.stem) + '.tif', str(tiles_dir)])

    print("# To serve the tiles, run:")
    print(f"uv run cli serve {tiles_dir}")
    print("# or if you're not using uv:")
    print(f"python3 ./src/gazebo_maptiles/main.py serve {tiles_dir}")
