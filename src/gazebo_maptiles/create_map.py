from pathlib import Path
import numpy as np

from lxml.etree import Element, SubElement,\
        _Element, XMLParser, parse, tostring, _ElementTree

def prettyprint(element, **kwargs):
    xml = tostring(element, pretty_print=True, **kwargs)
    print(xml.decode())

class Pose:
    def __init__(self, x, y, z, roll, pitch, yaw):
        self.x = x
        self.y = y
        self.z = z
        self.roll = roll
        self.pitch = pitch
        self.yaw = yaw

    def createElement(self):
        pose = Element('pose', frame='')
        pose.text = "%.2f %.2f %.2f %.2f %.2f %.2f" % (self.x, self.y, self.z, self.roll, self.pitch, self.yaw)
        return pose

TMP_IMAGE_PATH = "/tmp/gazebo_images"

def create_camera_xml(height: float, hfov: float, res: int = 3840) -> _Element:
    model = Element('model', name='ortho_map_camera')
    # Rotate the camera 90deg east because gazebo is ENU
    model.append(Pose(0,0,height,-1.57,1.57,0).createElement())
    SubElement(model, 'static').text = 'true'
    link = SubElement(model, 'link', name='camera_link')
    sensor = SubElement(link, 'sensor', name='map_sensor', type='camera')
    SubElement(sensor, 'topic').text = '/world_ortho/image_raw'
    SubElement(sensor, 'always_on').text = 'true'
    SubElement(sensor, 'update_rate').text = '30'
    camera = SubElement(sensor, 'camera')
    SubElement(camera, 'triggered').text = 'true'
    SubElement(camera, 'trigger_topic').text = '/world_ortho/trigger'
    save = SubElement(camera, 'save', enabled='true')
    SubElement(save, 'path').text = TMP_IMAGE_PATH
    SubElement(camera, 'horizontal_fov').text = str(hfov)
    image = SubElement(camera, 'image')
    SubElement(image, 'width').text = str(res)
    SubElement(image, 'height').text = str(res)
    clip = SubElement(camera, 'clip')
    SubElement(clip, 'near').text = str(1)
    SubElement(clip, 'far').text = str(height+500)

    return model

def gazebo_take_photo(height: float, hfov: float, filepath: Path, world_path: Path, res: int = 3840) -> None:
    camera = create_camera_xml(height, hfov, res)
    print("camera sdf:")
    prettyprint(camera)

    # Take the image starting the gazebo world with the added camera
    world = parse(world_path)
    if world is not _ElementTree:
        print(f"Gazebo world at {world_path} not found")
        exit(-1)
    else:
        world.append(camera)

    # Move it from /tmp/gazebo_images/
    files = list(Path(TMP_IMAGE_PATH).glob("*.png"))
    if files:
        latest = max(files, key=lambda f: f.stat().st_mtime)
        latest.rename(filepath)
    else:
        print("Failed to generate image")
        exit(-1)

    print(f"Generated map to {filepath}")

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
        if height is None:
            print("ERROR: square_side and height are not set! Need one of them")
            exit(-1)
    lat: float = args.latitude
    lon: float = args.longitude
    map_name: Path = args.filename
    world_path: Path = args.world_path

    # Generate the camera sdf and instance it in a gazebo world
    gazebo_take_photo(height, hfov, map_name, world_path)

    offset = get_image_offset(height, hfov)
    bbox = get_bbox(offset, lat, lon)

    min_zoom,max_zoom = calculate_ideal_zoom(bbox)

    pretty_bbox = ",".join(map(lambda val: "%.7f" % val, bbox))

    print("To create a tilemap from this image, run:")
    print(f"uv run cli create {map_name}.png --bbox '{pretty_bbox}' --min_zoom {min_zoom} --max_zoom {max_zoom}")
    print("or")
    print(f"python3 ./src/gazebo_maptiles/main.py create {map_name}.png --bbox '{pretty_bbox}' --min_zoom {min_zoom} --max_zoom {max_zoom}")
