# Gazebo maptiles

Utility to create and serve tilemaps for gazebo simulations

## Requirements

### External

- 'Gazebo' to take the map photo (https://gazebosim.org/home)
- 'Gdal' to transform the png into a tilemap (https://gdal.org/en/stable/index.html)
- 'Mapviz' to display the tiles

### Using uv

You only need to run the package through uv and it will setup a virtual environment.

### Using pip

0) (__Recommended__) Create a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```
1) Install the requirements with pip
```bash
pip install -r requirements.txt
# use the program...

# If using a virtual environment
deactivate # turns it off
```

## Running

```bash
usage: cli [-h] {create,serve,photo} ...

Script to create and serve tilemaps

positional arguments:
  {create,serve,photo}  Available subcommands
    create              Create a new tilemap
    serve               Start a tilemap server
    photo               Take a photo inside a gazebo simulation

options:
  -h, --help            show this help message and exit
```

### Using uv

```bash
uv run cli [-h] {create,serve,photo} ...
```

### Using pip

```bash
python3 src/gazebo_maptiles/main.py [-h] {create,serve,photo} ...
```

## Example

We're going to get a map from a gazebo simulation setup by PX4 using worlds from OpenRobotics (https://github.com/PX4/PX4-gazebo-models/blob/main/worlds/baylands.sdf)



## Contributing