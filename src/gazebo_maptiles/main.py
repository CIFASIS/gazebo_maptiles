from pathlib import Path
import argparse

from gazebo_maptiles.create_map import create_map
from gazebo_maptiles.serve_tiles import serve_tiles
from gazebo_maptiles.create_tilemap import create_tilemap

SCRIPT_DESCRIPTION = \
"""Script to create and serve tilemaps"""

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
        'tiles_dir', type=Path,
        help='Directory to save the tiles in.'
    )
    parser_create.add_argument(
        '--bbox', type=str,
        help='Bounding box to pass to gdal raster pipeline'
    )
    parser_create.add_argument(
        '--min_zoom', type=int,
        help='Minimum zoom for the tilemap'
    )
    parser_create.add_argument(
        '--max_zoom', type=int,
        help='Maximum zoom for the tilemap'
    )
    parser_create.set_defaults(func=create_tilemap)

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
    parser_serve.set_defaults(func=serve_tiles)

    parser_photo = subparsers.add_parser(
        "photo", help="Take a photo inside a gazebo simulation"
    )
    parser_photo.add_argument(
        'filename', type=Path,
        help='Create a map image and save at PATH.', metavar="PATH"
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
