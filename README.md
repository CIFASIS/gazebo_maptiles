# Gazebo maptiles

Utility to create and serve tilemaps for gazebo simulations

## Requirements

### External

- 'Gazebo' to take the map photo (https://gazebosim.org/home)
- 'Gdal' to transform the png into a tilemap (https://gdal.org/en/stable/index.html)
- 'Mapviz' to display the tiles (https://swri-robotics.github.io/mapviz/)

### Using uv

You only need to run the package through uv and it will setup a virtual environment automatically.

### Using pip

0) (__Recommended__) Create a virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
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
usage: cli [-h] {photo,create,serve} ...

Script to create and serve tilemaps

positional arguments:
  {photo,create,serve}  Available subcommands
    photo               Take a photo inside a gazebo simulation
    create              Create a new tilemap
    serve               Start a tilemap server

options:
  -h, --help            show this help message and exit
```

### Using uv

```bash
uv run cli [-h] {photo,create,serve} ...
```

### Using pip

```bash
python3 src/gazebo_maptiles/main.py [-h] {photo,create,serve} ...
```

To see an example of the project, check out the [baylands example](./docs/example.md)

## Contributing