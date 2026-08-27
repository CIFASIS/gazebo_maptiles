import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pathlib import Path

app = FastAPI()

TILES_DIR: str
@app.get("/{zoom}/{x}/{y}.png")
async def get_tile(zoom: int, x: int, y: int) -> FileResponse:
    global TILES_DIR
    path = Path(TILES_DIR, str(zoom), str(x), str(y) + ".png")
    if not path.exists():
        return FileResponse('./tile_not_found.png', media_type="image/png")
    return FileResponse(path, media_type="image/png")

def serve_tiles(host: str, port: int, tiles_dir: str):
    global TILES_DIR
    TILES_DIR = tiles_dir

    uvicorn.run(
        "gazebo_maptiles.serve_tiles:app",
        host=host,
        port=port,
    )

def serve_tiles_handler(args):
    serve_tiles(args.host, args.port, args.tiles_dir)
