import numpy as np

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
        height = get_image_height(sq_side/2, hfov)
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
