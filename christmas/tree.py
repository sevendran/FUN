"""Snowball impact, snow stage and a growing undecorated ASCII fir."""

import argparse
from pathlib import Path

import pygame


HERE = Path(__file__).resolve().parent
from winter_scene import Winter


def canvas_size(display_size,orientation):
    """The monitor signal stays landscape; rotated output uses a swapped canvas."""
    base=(1080,1920) if orientation=='portrait' else (1920,1080)
    available=display_size[::-1] if orientation=='portrait' else display_size
    scale=min(available[0]/base[0],available[1]/base[1],1.)
    return max(1,round(base[0]*scale)),max(1,round(base[1]*scale))


def output_frame(art,orientation):
    """Positive pygame rotation is counterclockwise: a real left 90-degree turn."""
    return pygame.transform.rotate(art,90) if orientation=='portrait' else art


def present(screen,art,orientation):
    art=output_frame(art,orientation)
    screen.fill((0,0,0))
    ratio=min(screen.get_width()/art.get_width(),screen.get_height()/art.get_height())
    size=(max(1,round(art.get_width()*ratio)),max(1,round(art.get_height()*ratio)))
    fitted=art if size==art.get_size() else pygame.transform.smoothscale(art,size)
    screen.blit(fitted,fitted.get_rect(center=screen.get_rect().center))


def main():
    parser=argparse.ArgumentParser(description="Snowball impact and growing ASCII fir")
    parser.add_argument('--windowed',action='store_true')
    parser.add_argument('--export',type=Path)
    parser.add_argument('--time',type=float,default=50.0)
    parser.add_argument('--orientation',choices=('portrait','landscape'),default='portrait')
    args=parser.parse_args()
    pygame.font.init()
    if args.export:
        args.export.parent.mkdir(parents=True,exist_ok=True)
        size=(1080,1920) if args.orientation=='portrait' else (1920,1080)
        pygame.image.save(output_frame(Winter(size).render(args.time),args.orientation),str(args.export))
        pygame.quit()
        return
    pygame.display.init()
    fullscreen=not args.windowed
    orientation=args.orientation
    scenes={}
    def display():
        desktop_w,desktop_h=pygame.display.get_desktop_sizes()[0]
        desired=(1280,720)
        scale=min(1.,desktop_w*.92/desired[0],desktop_h*.88/desired[1])
        window_size=(round(desired[0]*scale),round(desired[1]*scale))
        win=pygame.display.set_mode((0,0) if fullscreen else window_size,pygame.FULLSCREEN if fullscreen else pygame.RESIZABLE)
        pygame.mouse.set_visible(not fullscreen)
        return win,get_scene(win.get_size())
    def get_scene(size):
        render_size=canvas_size(size,orientation)
        key=(orientation,render_size)
        if key not in scenes:
            # Keep at most the two orientations at their current viewport sizes.
            for old in list(scenes):
                if old[0]==orientation:del scenes[old]
            scenes[key]=Winter(render_size)
        return scenes[key]
    screen,winter=display()
    pygame.display.set_caption('Christmas — Winter ASCII')
    clock=pygame.time.Clock()
    t=0.;paused=False;running=True
    try:
        while running:
            dt=clock.tick(30)/1000
            for e in pygame.event.get():
                if e.type==pygame.QUIT:running=False
                elif e.type==pygame.VIDEORESIZE:winter=get_scene(screen.get_size())
                elif e.type==pygame.KEYDOWN:
                    if e.key==pygame.K_ESCAPE:running=False
                    elif e.key==pygame.K_SPACE:paused=not paused
                    elif e.key==pygame.K_r:t=0
                    elif e.key in (pygame.K_1,pygame.K_KP1,pygame.K_2,pygame.K_KP2):
                        wanted='landscape' if e.key in (pygame.K_1,pygame.K_KP1) else 'portrait'
                        if wanted!=orientation:
                            orientation=wanted
                            winter=get_scene(screen.get_size())
                            # Scene construction is not animation time; resume the same moment.
                            clock.tick();dt=0.
                    elif e.key==pygame.K_F11:
                        fullscreen=not fullscreen
                        screen,winter=display()
                        clock.tick();dt=0.
                    elif e.key==pygame.K_s:
                        from datetime import datetime
                        folder=HERE/'captures';folder.mkdir(exist_ok=True)
                        pygame.image.save(output_frame(winter.render(t),orientation),str(folder/f'winter_{datetime.now():%Y%m%d_%H%M%S_%f}.png'))
            if not paused:t+=min(dt,.1)
            present(screen,winter.render(t),orientation)
            pygame.display.flip()
    finally:
        pygame.mouse.set_visible(True)
        pygame.quit()


if __name__=='__main__':
    main()
