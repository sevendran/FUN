# Christmas ASCII

A Python/pygame animation in which an ASCII snowball strikes the ground, forms a snowy stage, and grows into a decorated Christmas scene.

![Completed scene](preview.jpg)

## Run on Windows

Install Python 3.10 or newer, then double-click `run.bat`. The launcher checks the project environment and compatible environments one or two parent folders above it. If needed, it runs `setup.bat` to create a local `.venv` and install dependencies. Initial setup requires internet access.

You can also run `setup.bat` directly, or install manually from this folder:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe tree.py
```

Setup prefers `python` and falls back to `py -3`. Dependencies are NumPy and pygame-ce.

## Display and controls

The default output rotates the entire scene **90 degrees counterclockwise** for a physically upright monitor. Keep the Windows display setting in landscape orientation. This rotation includes the greeting, snow, and all effects.

| Key | Action |
|---|---|
| 1 | Landscape output without rotation |
| 2 | Rotate output 90 degrees counterclockwise |
| F11 | Toggle fullscreen/windowed mode |
| Space | Pause/resume |
| R | Restart from the snowball drop |
| S | Save the current output in `captures` |
| Esc | Quit |

```powershell
# Start in a window
.\.venv\Scripts\python.exe tree.py --windowed
# Start in landscape orientation
.\.venv\Scripts\python.exe tree.py --orientation landscape
# Export the actual output at 50 seconds without opening a window
.\.venv\Scripts\python.exe tree.py --export preview.png --time 50
```

Fullscreen is enabled by default. OS keyboard shortcuts remain available; this project does not include an OS kiosk lock or a packaged executable.

## Animation

- A shaded ASCII snowball falls, flashes on impact, and sends circular shockwaves and individual character particles outward. The particles return to form a snowy disc.
- The stage, rocks, grass, twigs, tree, and attached decorations rotate together clockwise. Falling snow moves independently.
- Green branches grow upward in layers with a bright white growth front and twinkling white lights.
- A gold spiral climbs the tree, followed by red and gold baubles, a glowing star, individually falling gifts, and a second bright yellow spiral.
- Continuous multicolored ASCII fireworks begin behind the tree when the second yellow spiral starts. Random heights and positions between the greeting and tree star feature circles, hearts, stockings, cookies, snowmen, snowflakes, bells, and gingerbread figures.
- An ASCII Santa sleigh led by Rudolph crosses the sky when the tree finishes growing, revealing Merry Christmas behind it. Frost decorations and occasional warm or icy highlights keep it lively.

Installed fonts such as Gabriola or Segoe Script provide the greeting's shape mask; its visible letters and surrounding decorations are rendered as ASCII characters. Fallback fonts are supported. Reference photographs are not needed at runtime.

## Source layout

| File | Responsibility |
|---|---|
| `tree.py` | Application loop, controls, export, and final output rotation |
| `winter_scene.py` | Camera, terrain, snow, and composition |
| `ascii_surface.py` | Surface sampling and ASCII rendering |
| `ground_details.py` | Rocks, grass, twigs, and pinecones |
| `stage_motion.py` | Shared stage rotation |
| `rotating_stage.py` | Reprojection, depth, ground shading, and warm light |
| `impact_intro.py` | Snowball, impact, shockwaves, and particles |
| `growing_tree.py` | Branch growth and white lights |
| `tree_decorations.py` | Gold spiral and baubles |
| `christmas_finale.py` | Star, gifts, warm lighting, and yellow spiral |
| `santa_flyby.py` | Santa and reindeer flyby synchronized with the greeting |
| `christmas_fireworks.py` | Repeating ASCII circle and heart fireworks |
| `christmas_greeting.py` | ASCII greeting, frost decorations, and highlights |

See [Implementation notes](docs/IMPLEMENTATION.md) for rendering details and the animation timeline.
