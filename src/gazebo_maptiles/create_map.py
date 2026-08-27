from watchdog.observers.api import BaseObserver
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from time import sleep
import subprocess

from pathlib import Path
import numpy as np

import pyproj

from lxml.etree import Element, SubElement,\
        _Element, parse, tostring, _ElementTree

recv_trigger: bool = False

class WatchFileCreation(FileSystemEventHandler):
    def __init__(self, watch_dir: str, target_path: Path, observer: BaseObserver):
        self.watch_dir = watch_dir
        self.target_path = target_path
        self.observer = observer

    def on_closed(self, event: FileSystemEvent):
        if event.is_directory:
            return

        source_path = Path(str(event.src_path))
        source_path.replace(self.target_path)
        print(f"Created {self.target_path.name}!")

        self.observer.stop()

    def on_created(self, event: FileSystemEvent):
        if event.is_directory:
            return

        global recv_trigger
        recv_trigger = True

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
        pose = Element('pose')
        pose.text = "%.2f %.2f %.2f %.2f %.2f %.2f" % (self.x, self.y, self.z, self.roll, self.pitch, self.yaw)
        return pose

TMP_IMAGE_PATH: Path = Path("/") / "tmp" /"gazebo_images"

def create_camera_xml(height: float, hfov: float, lat: float, lon: float, res: int = 3840) -> _Element:
    # x,y = latlon_to_meters(lat, lon)
    # TODO: keep it at 0 for now until figuring out how to position
    # the camera in gazebo with the given coordinates.
    x,y = 0,0
    model = Element('model', name='ortho_map_camera')
    # Rotate the camera 90deg east because gazebo is ENU
    model.append(Pose(x,y,height,-1.57,1.57,0).createElement())
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
    SubElement(save, 'path').text = str(TMP_IMAGE_PATH)
    SubElement(camera, 'horizontal_fov').text = str(hfov)
    image = SubElement(camera, 'image')
    SubElement(image, 'width').text = str(res)
    SubElement(image, 'height').text = str(res)
    clip = SubElement(camera, 'clip')
    SubElement(clip, 'near').text = str(1)
    SubElement(clip, 'far').text = str(height+500)

    return model

def create_world_xml(camera, world_path):
    world: _ElementTree = parse(world_path)
    if type(world) is _ElementTree:
        world_element = world.find('world')
        if world_element is not None:
            world_element.append(camera)

            sensors_plugin = world_element.xpath('//plugin[@name="gz::sim::systems::Sensors"]')
            if not sensors_plugin:
                new_plugin = Element(
                    "plugin", {
                        "name": "gz::sim::systems::Sensors",
                        "filename": "gz-sim-sensors-system"
                    }
                )
                SubElement(new_plugin, "render_engine").text = "ogre2"
                world_element.append(new_plugin)
        else:
            print(f"Did not find <world> tag in {world_path}")
            exit(-1)
    else:
        print(f"Gazebo world at {world_path} not found")
        exit(-1)

    world_with_cam = "/tmp/gazebo_world_with_camera.sdf"
    world.write(file=world_with_cam)
    # print("World + camera sdf:")
    # prettyprint(world)

    return world_with_cam

def gazebo_take_photo(height: float, hfov: float, lat: float, lon: float, filepath: Path, world_path: Path, res: int) -> None:
    camera = create_camera_xml(height, hfov, lat, lon, res)
    # print("camera sdf:")
    # prettyprint(camera)

    # Setup world with a camera, and add sensor plugin if missing
    world_with_cam = create_world_xml(camera, world_path)

    # Setup watchdog to wait until the map photo is done 
    TMP_IMAGE_PATH.mkdir(exist_ok=True)
    observer = Observer()
    event_handler = WatchFileCreation(str(TMP_IMAGE_PATH), filepath, observer)
    observer.schedule(event_handler, path=str(TMP_IMAGE_PATH), recursive=False)
    observer.start()

    gz_process = subprocess.Popen(["gz", "sim", "-s", "-r", world_with_cam], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    global recv_trigger
    while not recv_trigger:
        print(".", end='', flush=True)
        trigger_msg = subprocess.Popen([
            'gz', 'topic',
            '-t', '/world_ortho/trigger',
            '-m', 'gz.msgs.Boolean',
            '-p', 'data: true',
            '-n', '1'
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        trigger_msg.wait()
        sleep(1)

    print()

    # TODO: Add a timeout and handle with an error message
    observer.join()
    gz_process.terminate()

def latlon_to_meters(lat: float, lon: float) -> tuple[float, float]:
    transformer = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:3857")

    return transformer.transform(lon, lat)

def meters_to_latlon(x: float, y: float) -> tuple[float, float]:
    transformer = pyproj.Transformer.from_crs("EPSG:3857", "EPSG:4326")

    return transformer.transform(x, y)


def get_bbox(meter_offset: float, lat: float, lon: float) -> tuple[float, float, float, float]:
    x_meters, y_meters = latlon_to_meters(lat, lon)
    return x_meters-meter_offset,\
           y_meters-meter_offset,\
           x_meters+meter_offset,\
           y_meters+meter_offset

def get_image_offset(height: float, hfov: float) -> float:
    # SOHCAHTOA: Tan(angle) = Opposite / Adjacent
    # Opposite = objective, Adjacent = camera height, angle = half the hfov
    return np.tan(hfov/2) * height

def get_image_height(offset: float, hfov: float) -> float:
    return offset / np.tan(hfov/2)

def calculate_ideal_zoom(bbox: tuple[float,float,float,float]) -> tuple[int, int]:
    '''return zooms for:
        1 tile for whole map to 64 tiles for whole map
        that is closest to fit the map size
    '''
    
    # length of a quarter tile in meters
    quarter_x = (bbox[2] - bbox[0]) / 2
    # latitude expressed in meters
    quarter_y = (bbox[3] + bbox[1]) / 2
    _, bbox_longitude = meters_to_latlon(quarter_x, quarter_y)
    zoom_levels = [360.0]
    for zoom in range(1,21):
        zoom_levels.append(zoom_levels[zoom-1] / 2.0)

    diff_to_tile = [abs(width - bbox_longitude) for width in zoom_levels]

    # find the zoom that fits 4 quarter tiles best
    index = 0
    min_zoom_diff = np.inf
    for (i, zoom_diff) in enumerate(diff_to_tile):
        if zoom_diff < min_zoom_diff:
            min_zoom_diff = zoom_diff
            index = i

    if index > 0:
        return (index-1,index+3)
    else:
        return (index, index+3)

def create_map(args) -> tuple[tuple[float,float,float,float], int, int, Path]:
    try:
        subprocess.run(['gz', 'sim', '--versions'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Failed at creating the map image!")
        print("Gazebo does not seem to be installed. Install it before running!")
        exit(1)

    sq_side: float | None = args.square_side
    hfov: float = args.hfov
    if sq_side:
        offset = sq_side/2
        height = get_image_height(offset, hfov)
    else:
        height = args.height
        offset = get_image_offset(height, hfov)
    lat: float = args.latitude
    lon: float = args.longitude
    map_name: Path = args.filename
    world_path: Path = args.world_path
    resolution: int = args.resolution

    if not map_name.suffix:
        map_name = map_name.with_suffix(".png")

    # Generate the camera sdf and instance it in a gazebo world
    gazebo_take_photo(height, hfov, lat, lon, map_name, world_path, resolution)

    bbox = get_bbox(offset, lat, lon)

    min_zoom,max_zoom = calculate_ideal_zoom(bbox)

    return bbox, min_zoom, max_zoom, map_name

def create_map_handler(args):
    bbox, min_zoom, max_zoom, map_name = create_map(args)

    pretty_bbox = " ".join(map(lambda val: "%.7f" % val, bbox))

    print("# To create a tilemap from this image, run:")
    command_text = f"create --bbox {pretty_bbox} --min_zoom {min_zoom} --max_zoom {max_zoom} {map_name} tiles_dir"
    print("uv run cli " + command_text)
    print("# or if you're not using uv:")
    print("python3 -m gazebo_maptiles.cli " + command_text)
