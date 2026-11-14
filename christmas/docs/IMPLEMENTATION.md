# Christmas ASCII implementation

## Rendering model

The scene uses procedural 3D geometry projected through a shared camera into a character grid. Geometry determines position, lighting, and visibility; ASCII glyphs supply the visible surface texture. Subtle glow reinforces bright characters.

`winter_scene.py` defines the camera, terrain, snow, and composition. The overview camera uses a horizontal distance of 26, an eye height of 12, a downward pitch of about 20 degrees, and a yaw of about 16 degrees. This view exposes the stage surface and layered branches.

`ascii_surface.py` samples surfaces into roughly 6 by 9 pixel character cells. Material-specific glyph pools, shading, and time-dependent character changes keep surfaces animated while preserving their silhouettes. The greeting uses a finer 4 by 6 pixel grid.

`rotating_stage.py` reprojects cached terrain and prop samples from their 3D coordinates each frame and resolves depth. The ground is an elliptical disc with approximate radii of 8.6 and 5.2 world units, shallow surface variation, and a side wall about 0.36 units thick. Its center is brighter than its edge.

## Shared motion and depth

`stage_motion.py` supplies a common rotation beginning at the impact, approximately 1.08 seconds after startup. The stage turns clockwise when viewed from above at 0.095 radians per second, completing a revolution in about 66 seconds.

Terrain, props, the tree, attached ornaments, the star, and settled presents share this transform. Snow is independent. Coordinates are rotated and projected again each frame; depth testing hides rear branches, lights, ornaments, and presents behind foreground geometry.

The tree has an additional width scale of 1.23. Its height scale is 1.12 in rotated portrait output and approximately 1.005 in landscape output. Branches, attached ornaments, and the star share that tree scale; the floor and presents retain their own dimensions.

## Animation timeline

Times are approximate seconds after restart.

| Time | Event |
|---|---|
| 0-1.08 | A shaded ASCII snowball accelerates toward the ground |
| 1.08 | Impact flash, shockwaves, camera recoil, and particle expansion; stage rotation starts |
| 1.08-6.2 | Individual particles spread, arc, return, and settle into a snowy disc |
| 6.65 | The trunk begins growing |
| 7.5-18.11 | Fourteen branch tiers grow from bottom to top |
| 18.11 | Tree growth finishes; the greeting and first gold spiral begin |
| 25.66-30.96 | Red and gold baubles appear from lower branches upward |
| 31.21 | The top star appears with a single bright flash |
| 32.26-40.26 | Sixteen gift boxes fall and settle around the tree |
| 40.51-47.01 | A second bright yellow spiral grows upward |
| After 47.01 | The completed scene continues rotating, twinkling, and glowing |

## Impact and snowy stage

`impact_intro.py` constructs a solid snowball using sphere normals and shaded characters. Impact adds a brief compression, a flash, two expanding shock fronts, and camera recoil.

Character particles have individual directions, velocities, heights, and target positions. They travel outward, lose energy, then return inward to settle on the final ground disc. The effect changes particle positions rather than shrinking a completed image.

`ground_details.py` adds six snow-capped rocks, sixteen grass tufts, four twigs, and four pinecones. Their world-space placement, shading, and occlusion connect them to the terrain.

## Tree growth

`growing_tree.py` represents branches as layered 3D samples. Each sample has a growth time. A short trunk appears first, followed by fourteen tiers at roughly 0.72-second intervals. Branches extend radially from the center while the growth front climbs upward.

New growth shines white before settling into green. Branch normals, directional lighting, darker inner foliage, and brighter rims reveal the depth between layers. Completed foliage keeps changing its internal characters and green shading.

Seven white lights per tier produce 98 lights in total. They appear as their branches grow and subsequently twinkle with independent phases. These lights are separate from the moving white growth front and respect depth occlusion.

## Decorations, star, and gifts

`tree_decorations.py` draws a gold spiral around the tree over about 7.2 seconds. Its leading tip advances upward through 4.6 turns and leaves a persistent illuminated ribbon. Forty-eight red and gold baubles then appear from bottom to top.

`christmas_finale.py` creates an extruded, faceted five-point star. Its first appearance triggers a brief broad flash and thin rays. Afterward, gentle periodic light warms nearby snow, props, and branches according to world-space proximity while retaining their ASCII texture.

Sixteen presents fall individually at 0.46-second intervals. Each fall lasts about 0.82 seconds, followed by landing squash and a short bounce. Boxes, ribbons, and bows move together as rigid objects. Their settled positions form a ring around the tree and rotate with the stage.

After the final landing, a second spiral climbs for about 6.5 seconds. It is brighter yellow and offset by half a turn from the first gold ribbon. Both ribbons remain visible afterward.

## Greeting and snow

`christmas_greeting.py` uses an installed decorative font only to derive a shape mask. It converts the text and surrounding frost ornaments into ASCII glyphs, then discards the source mask. The visible greeting contains no conventional text-image overlay.

The greeting appears at tree completion and is revealed from left to right during a seven-second Santa flyby. Rotated portrait composition uses two lines; landscape uses one. Merry uses warm red and gold, while Christmas uses icy blue and white. Snowflakes, hanging crystals, evergreen details, and berries extend the decoration.

After appearing, the greeting stays bright. Selected letter regions or a whole word occasionally shine for about 0.8-1.55 seconds, using colors appropriate to their palette. Seeded time-based scheduling keeps these variations consistent across pause, restart, and frame-rate changes.

The scene contains approximately 1,800 world-space snowflakes. A small subset, about 1.8 percent, can produce brief asynchronous icy glints.

## Output orientation and composition

`tree.py` renders the logical scene before applying the final output rotation. Default portrait output swaps the logical dimensions and rotates the finished frame 90 degrees counterclockwise. For example, a logical 1080 by 1920 frame becomes a 1920 by 1080 output for a physically rotated monitor.

The portrait composition places the stage lower and uses a larger tree while preserving space for the greeting. Landscape has its own framing. Keys 1 and 2 switch orientation without restarting animation time. Screenshots and headless exports use the same final rotation as the visible output.

## Setup and verification

`run.bat` checks a local `.venv` first. It can also use a compatible environment one or two folders above the project after checking that both pygame and NumPy import successfully. Otherwise, it calls `setup.bat --quiet` to create and populate a local environment.

`setup.bat` prefers a working `python` command with Python 3.10 or newer and falls back to `py -3`. It installs `requirements.txt`, checks imports, and returns an error code if setup fails.

A reproducible rendering check from the project folder is:

```powershell
.\run.bat --export "$env:TEMP\christmas-check.png" --time 50
```

The repository includes a small `preview.jpg`. Virtual environments, generated captures, development GIFs, and reference photographs are excluded from version control.


## Background fireworks

`christmas_fireworks.py` begins at `ChristmasFinale.yellow_start`. Launches repeat every 1.5 seconds with independently randomized flight durations, origins, and angles. Event seeds are stable across restart, pause, and exports; only active events remain cached.

Burst centers span the full horizontal sky, including the center behind the tree. The vertical range is derived from the greeting and the projected top star rather than a fixed horizontal band. Random sizes, eight color palettes, and eight procedural silhouettes provide variation: circles, hearts, stockings, cookies, snowmen, snowflakes, bells, and gingerbread figures.

ASCII particles expand into a recognizable outline, briefly retain it, then scatter, drift, twinkle, and fade. Tree and terrain depth produce filled foreground silhouette masks, so even sparks aligned with spaces between foreground characters remain hidden. Snow and the greeting render afterward.

## Santa flyby and distant fireworks

`santa_flyby.py` draws Santa, a gift-filled sleigh, reins, two reindeer, and Rudolph's red nose as colored ASCII samples. Two leg poses, a gentle flight arc, and a golden trail animate a single seven-second crossing when the tree completes. A shared time-based horizontal reveal front writes the greeting behind the leading reindeer. The sleigh exits completely and the greeting remains illuminated.

Firework centers occupy the upper sky near the greeting. Their smaller apparent size suggests distance; horizontal centers and heights vary independently. A filled silhouette mask derived from tree and terrain depth prevents sparks from appearing through gaps between foreground ASCII glyphs. The greeting is drawn afterward to preserve readability.
