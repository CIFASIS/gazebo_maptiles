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

    tif = str(png_path.stem) + '.tif'
    subprocess.run(['gdal', 'raster', 'pipeline',
                    'read', str(png_path), '!',
                    'edit', '--crs', 'EPSG:3857', '!',
                    'edit', '--bbox', bbox_str, '!',
                    'write', tif, '--format=GTiff'
    ], check=True)
    subprocess.run(['gdal', 'raster', 'tile',
                    '--tiling-scheme', 'WorldMercatorWGS84Quad',
                    '--min-zoom', str(min_zoom),
                    '--max-zoom', str(max_zoom),
                    tif, str(tiles_dir)
    ], check=True)

    # Path(tif).unlink(missing_ok=True)

    print("# To serve the tiles, run:")
    print(f"uv run cli serve {tiles_dir}")
    print("# or if you're not using uv:")
    print(f"python3 ./src/gazebo_maptiles/main.py serve {tiles_dir}")
