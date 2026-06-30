from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from pathlib import Path

app = FastAPI()

x_min, x_max, y_min, y_max = 0, 8140, 0, 8140
z_min, z_max = 15, 20

@app.get("/{zoom}/{x}/{y}")
async def get_tile(zoom: int, x: int, y: int) -> FileResponse:
    if zoom not in range(z_min, z_max+1, 1):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Zoom={zoom} out of bounds. Valid zoom is only between {z_min} and {z_max}"
        )
    if x < x_min or x > x_max:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"X={x} out of bounds. Only between {x_min} and {x_max}"
        )
    if y < y_min or y > y_max:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Y={y} out of bounds. Only between {y_min} and {y_max}"
        )

    path = Path("output_tiles_dir", str(zoom), str(x), str(y))
    return FileResponse(path, media_type="image/png")

