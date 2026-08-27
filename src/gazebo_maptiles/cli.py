from pathlib import Path
import argparse

from gazebo_maptiles.create_map import create_map_handler, create_map
from gazebo_maptiles.serve_tiles import serve_tiles_handler, serve_tiles
from gazebo_maptiles.create_tilemap import create_tilemap_handler, create_tilemap

SCRIPT_DESCRIPTION = \
"""Script to create and serve tilemaps"""

def pipeline(args):
    # Create the map
    print("Creating map...")
    bbox, min_zoom, max_zoom, map_name = create_map(args)

    # Create the tilemap
    tiles_dir = Path("output_tiles_dir")
    print(f"Creating tilemap at {tiles_dir}...")
    create_tilemap(tiles_dir, map_name, list(bbox), min_zoom, max_zoom)

    # Start the server
    host: str = args.host
    port: int = args.port
    print(f"Hosting XYZ tile server at {host}:{port}...")
    serve_tiles(host, port, str(tiles_dir.resolve()))

def main():
    parser = argparse.ArgumentParser(description=SCRIPT_DESCRIPTION)
    subparsers = parser.add_subparsers(
        dest="command", required=True, help="Available subcommands")

    # PHOTO subcommand: Take a picture inside gazebo to use as a map
    parser_photo = subparsers.add_parser(
        "photo", help="Take a photo inside a gazebo simulation"
    )
    parser_photo.add_argument(
        'filename', type=Path,
        help='Create a map image and save at IMG_PATH.', metavar="IMG_PATH"
    )
    parser_photo.add_argument(
        'world_path', type=Path, metavar="WORLD_PATH",
        help='Path to the gazebo world in which to take the photo.',
    )
    photo_length_group = parser_photo.add_mutually_exclusive_group(required=True)
    photo_length_group.add_argument(
        '-s', '--square_side', type=float,
        help='Length of the side of the map in meters.'
    )
    photo_length_group.add_argument(
        '--height', type=float,
        help='Height of the camera inside gazebo in meters.'
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
    parser_photo.add_argument(
        '--resolution', type=int, default=3840,
        help='Resolution for the square image taken inside gazebo.'
    )
    parser_photo.set_defaults(func=create_map_handler)

    # CREATE subcommand: Using the gazebo photo, create a tilemap
    parser_create = subparsers.add_parser(
        "create", help="Create a new tilemap"
    )
    parser_create.add_argument(
        'filename', type=Path,
        help='Create a tilemap from path to png.', metavar="PNG_PATH"
    )
    parser_create.add_argument(
        'tiles_dir', type=Path,
        help='Directory to save the tiles in.'
    )
    parser_create.add_argument(
        '--bbox', type=float, nargs=4, required=True,
        help='Bounding box to pass to gdal raster pipeline'
    )
    parser_create.add_argument(
        '--min_zoom', type=int, required=True,
        help='Minimum zoom for the tilemap'
    )
    parser_create.add_argument(
        '--max_zoom', type=int, required=True,
        help='Maximum zoom for the tilemap'
    )
    parser_create.set_defaults(func=create_tilemap_handler)

    # SERVE subcommand: With the tilemap ready, serve requests for it with a fastapi server
    parser_serve = subparsers.add_parser(
            "serve", help="Start a tilemap server")
    parser_serve.add_argument(
        'tiles_dir', type=Path,
        help='Directory where we find the tiles to serve.'
    )
    parser_serve.add_argument(
        '--host', type=str, default='127.0.0.1',
        help='IP to listen to. Default is loopback'
    )
    parser_serve.add_argument(
        '--port', type=int, default=8000,
        help='Port for connection.'
    )
    parser_serve.set_defaults(func=serve_tiles_handler)

    # PIPELINE subcommand: do all steps by itself
    parser_pipeline = subparsers.add_parser(
        "pipeline", help="Take a photo inside gazebo, create a tilemap, then serve it"
    )
    parser_pipeline.add_argument(
        '--filename', type=Path, default=Path("world_map"),
        help='Create a map image and save at IMG_PATH.', metavar="IMG_PATH"
    )
    parser_pipeline.add_argument(
        'world_path', type=Path, metavar="WORLD_PATH",
        help='Path to the gazebo world in which to take the photo.',
    )
    photo_length_group = parser_pipeline.add_mutually_exclusive_group(required=True)
    photo_length_group.add_argument(
        '-s', '--square_side', type=float,
        help='Length of the side of the map in meters.'
    )
    photo_length_group.add_argument(
        '--height', type=float,
        help='Height of the camera inside gazebo in meters.'
    )
    parser_pipeline.add_argument(
        '--hfov', type=float, default=0.101,
        help='Horizontal field of view of the camera. Default is low enough to appear ortographic.'
    )
    parser_pipeline.add_argument(
        '--latitude', type=float, default=0,
        help='Latitude in degrees of the origin of the gazebo simulation.'
    )
    parser_pipeline.add_argument(
        '--longitude', type=float, default=0,
        help='Longitude in degrees of the origin of the gazebo simulation.'
    )
    parser_pipeline.add_argument(
        '--resolution', type=int, default=3840,
        help='Resolution for the square image taken inside gazebo.'
    )
    parser_pipeline.add_argument(
        '--host', type=str, default='127.0.0.1',
        help='IP to listen to. Default is loopback'
    )
    parser_pipeline.add_argument(
        '--port', type=int, default=8000,
        help='Port for connection.'
    )
    parser_pipeline.set_defaults(func=pipeline)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
