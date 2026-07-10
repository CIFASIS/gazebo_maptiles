import subprocess
import uvicorn
from fastapi import FastAPI, HTTPException, status
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
    # if zoom not in range(z_min, z_max+1, 1):
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail=f"Zoom={zoom} out of bounds. Valid zoom is only between {z_min} and {z_max}"
    #     )
    # if x < x_min or x > x_max:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail=f"X={x} out of bounds. Only between {x_min} and {x_max}"
    #     )
    # if y < y_min or y > y_max:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail=f"Y={y} out of bounds. Only between {y_min} and {y_max}"
    #     )

    path = Path(TILES_DIR, str(zoom), str(x), str(y) + ".png")
    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tile out of bounds"
        )
    return FileResponse(path, media_type="image/png")


def create_tilemap(args):
    png_path: Path = args.filename
    bbox: str = args.bbox
    min_zoom, max_zoom = args.min_zoom, args.max_zoom
    if not png_path.exists():
        return
    output_dir = Path(TILES_DIR)
    if output_dir.exists():
        print("Remove output_dir before running!")

    subprocess.run(['gdal', 'raster', 'pipeline',
                    'read', str(png_path), '!',
                    'edit', '--bbox', bbox,
                    '--crs', 'EPSG:4326', '!',
                    'write', 'world_georeferenced.tif', '--format=GTiff'])
    subprocess.run(['gdal', 'raster', 'tile',
                    '--min-zoom', min_zoom, '--max-zoom', max_zoom,
                    'world_georeferenced.tif', TILES_DIR])

def serve_tiles(args):
    host: str = args.host
    port: int = args.port
    uvicorn.run(
        "serve_tiles:app",
        host=host,
        port=port,
        ssl_keyfile="./localhost+2-key.pem",
        ssl_certfile="./localhost+2.pem"
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=SCRIPT_DESCRIPTION)
    subparsers = parser.add_subparsers(
        dest="command", required=True, help="Available subcommands")

    parser_create = subparsers.add_parser(
            "create", help="Create a new tilemap")
    parser_create.add_argument(
        'filename', type=Path,
        help='Create a tilemap from path to png.', metavar="PNG_PATH"
    )
    parser_create.add_argument(
        '--bbox', type=str, default='-100,-100,100,100',
        help='Bounding box to pass to gdal raster pipeline'
    )
    parser_create.add_argument(
        '--min_zoom', type=int, default=2,
        help='Minimum zoom for the tilemap'
    )
    parser_create.add_argument(
        '--max_zoom', type=int, default=5,
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

    args = parser.parse_args()
    args.func(args)

