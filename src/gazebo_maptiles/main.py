import numpy as np
from sys import exit
import subprocess
import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pathlib import Path
from os import getenv
import argparse

SCRIPT_DESCRIPTION = \
"""Script to create and serve tilemaps"""

TILES_DIR = getenv("TILES_DIR", "output_tiles_dir")

app = FastAPI()

# x_min, x_max, y_min, y_max = -50, 50, -50, 50
# z_min, z_max = 2, 5

@app.get("/{zoom}/{x}/{y}")
async def get_tile(zoom: int, x: int, y: int) -> FileResponse:
    path = Path(TILES_DIR, str(zoom), str(x), str(y) + ".png")
    if not path.exists():
        return FileResponse('./tile_not_found.png', media_type="image/png")
    return FileResponse(path, media_type="image/png")

def serve_tiles(args):
    host: str = args.host
    port: int = args.port
    uvicorn.run(
        "gazebo_maptiles.main:app",
        host=host,
        port=port,
        # ssl_keyfile="./localhost+2-key.pem",
        # ssl_certfile="./localhost+2.pem"
    )

def create_tilemap(args):
    png_path: Path = args.filename
    bbox: str = args.bbox
    min_zoom, max_zoom = args.min_zoom, args.max_zoom
    if not png_path.exists():
        return
    output_dir = Path(TILES_DIR)
    if output_dir.exists():
        print(f"Cannot overwrite {output_dir}. Remove before running!")
        exit(1)

    subprocess.run(['gdal', 'raster', 'pipeline',
                    'read', str(png_path), '!',
                    'edit', '--bbox', bbox,
                    '--crs', 'EPSG:4326', '!',
                    'write', str(png_path.stem) + '.tif', '--format=GTiff'])
    subprocess.run(['gdal', 'raster', 'tile',
                    '--min-zoom', str(min_zoom),
                    '--max-zoom', str(max_zoom),
                    str(png_path.stem) + '.tif', TILES_DIR])

def gazebo_take_photo(height: float, hfov: float, filename: str) -> None:
    #TODO
    print(f"Generated map to {filename}.png")

def get_bbox(meter_offset: float, lat: float, lon: float) -> tuple[float, float, float, float]:
    EARTH_EQUATOR_RADIUS = 6378
    km_per_rad = (np.pi/180) * EARTH_EQUATOR_RADIUS * np.cos(lat * np.pi/180)
    dcoord = meter_offset / 1000 / km_per_rad
    new_lat = lat + dcoord
    new_lon = lon + dcoord / np.cos(lat * np.pi/180)
    return (-new_lon,-new_lat,new_lon,new_lat)

def get_image_offset(height: float, hfov: float) -> float:
    # SOHCAHTOA: Tan(angle) = Opposite / Adjacent
    # Opposite = objective, Adjacent = camera height, angle = half the hfov
    return np.tan(hfov/2) * height

def get_image_height(offset: float, hfov: float) -> float:
    return offset / np.tan(hfov/2)

def calculate_ideal_zoom(bbox: tuple[float,float,float,float]) -> tuple[int, int]:
    # TODO
    return (16,19)

def create_map(args):
    sq_side: float | None = args.square_side
    hfov: float = args.hfov
    if sq_side is not None:
        height = get_image_height(sq_side, hfov)
    else:
        height = args.height
    lat: float = args.lat
    lon: float = args.lon
    map_name: str = args.filename

    # Generate the camera sdf and instance it in a gazebo world
    gazebo_take_photo(height, hfov, map_name)

    offset = get_image_offset(height, hfov)
    bbox = get_bbox(offset, lat, lon)

    min_zoom,max_zoom = calculate_ideal_zoom(bbox)

    pretty_bbox = ",".join(map(str, bbox))

    print("To create a tilemap from this image, run:")
    print(f"python3 serve_tiles.py create {map_name}.png --bbox '{pretty_bbox}' --min_zoom {min_zoom} --max_zoom {max_zoom}")

def main():
    parser = argparse.ArgumentParser(description=SCRIPT_DESCRIPTION)
    subparsers = parser.add_subparsers(
        dest="command", required=True, help="Available subcommands")

    parser_create = subparsers.add_parser(
        "create", help="Create a new tilemap"
    )
    parser_create.add_argument(
        'filename', type=Path,
        help='Create a tilemap from path to png.', metavar="PNG_PATH"
    )
    parser_create.add_argument(
        '--bbox', type=str, default='-0.0023,-0.0023,0.0023,0.0023',
        help='Bounding box to pass to gdal raster pipeline'
    )
    parser_create.add_argument(
        '--min_zoom', type=int, default=16,
        help='Minimum zoom for the tilemap'
    )
    parser_create.add_argument(
        '--max_zoom', type=int, default=19,
        help='Maximum zoom for the tilemap'
    )
    parser_create.set_defaults(func=create_tilemap)

    parser_serve = subparsers.add_parser(
            "serve", help="Start a tilemap server")
    parser_serve.add_argument(
        '--host', type=str, default='127.0.0.1',
        help='IP to listen to. Default is loopback'
    )
    parser_serve.add_argument(
        '--port', type=int, default=8000,
        help='Port for connection.'
    )
    parser_serve.set_defaults(func=serve_tiles)

    parser_photo = subparsers.add_parser(
        "photo", help="Take a photo inside a gazebo simulation"
    )
    parser_photo.add_argument(
        'filename', type=str,
        help='Create a map image and save at NAME.png.', metavar="NAME"
    )
    parser_photo.add_argument(
        '--square_side', type=float,
        help='Length of the side of the map.'
    )
    parser_photo.add_argument(
        '--height', type=float,
        help='Height of the camera inside gazebo.'
    )
    parser_photo.add_argument(
        '--hfov', type=float, default=0.101,
        help='Horizontal field of view of the camera. Default is low enough to appear ortographic.'
    )
    parser_photo.add_argument(
        '--latitude', type=float, default=0,
        help='Latitude in degrees of the origin of the gazebo simulation.'
    )
    parser_photo.add_argument(
        '--longitude', type=float, default=0,
        help='Longitude in degrees of the origin of the gazebo simulation.'
    )
    parser_photo.set_defaults(func=create_map)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
