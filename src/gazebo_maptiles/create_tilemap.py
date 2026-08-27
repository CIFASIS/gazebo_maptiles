from pathlib import Path
import subprocess
from sys import exit

def create_tilemap(tiles_dir: Path, png_path: Path, bbox: list[float], min_zoom: int, max_zoom: int) -> None:
    try:
        subprocess.run(['gdal', '--version'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Failed at creating the tilemap!")
        print("gdal does not seem to be installed. Install it before running!")
        exit(1)

    if not png_path.exists():
        print(f"Map image {png_path.resolve()} does not exist!")
        exit(1)
    if tiles_dir.exists():
        print(f"Cannot overwrite {tiles_dir.resolve()}. Remove before running!")
        exit(2)

    bbox_str = ",".join(map(str, bbox))
    tif = str(png_path.stem) + '.tif'
    ptif = Path(tif)
    if ptif.exists():
        print(f"Cannot overwrite {tif}. Remove before running!")

    try:
        subprocess.run(['gdal', 'raster', 'pipeline',
                        'read', str(png_path), '!',
                        'edit', '--crs', 'EPSG:3857', '!',
                        'edit', '--bbox', bbox_str, '!',
                        'write', tif, '--format=GTiff'
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        print("Failed at creating the tilemap!")
        print(f"gdal raster pipeline failed with exit code {e.returncode}")
        print(f"Error: {e.stderr}")
        exit(3)

    try:
        subprocess.run(['gdal', 'raster', 'tile',
                        '--tiling-scheme', 'WorldMercatorWGS84Quad',
                        '--min-zoom', str(min_zoom),
                        '--max-zoom', str(max_zoom),
                        tif, str(tiles_dir)
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        print("Failed at creating the tilemap!")
        print(f"gdal raster tile failed with exit code {e.returncode}")
        print(f"Error: {e.stderr}")
        exit(4)

    # Path(tif).unlink(missing_ok=True)

def create_tilemap_handler(args):
    tiles_dir: Path = args.tiles_dir
    png_path: Path = args.filename
    bbox: list[float] = args.bbox
    min_zoom, max_zoom = args.min_zoom, args.max_zoom

    create_tilemap(tiles_dir, png_path, bbox, min_zoom, max_zoom)

    print("# To serve the tiles, run:")
    print(f"uv run cli serve {tiles_dir}")
    print("# or if you're not using uv:")
    print(f"python3 -m gazebo_maptiles.cli serve {tiles_dir}")
