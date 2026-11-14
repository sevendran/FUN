"""An entirely ASCII Christmas greeting with icy filigree and steady radiance."""

import math
from pathlib import Path

import numpy as np
import pygame
from santa_flyby import reveal_front


CW,CH=4,6
GLYPHS=" .,:;-=+*|/\\x08#%&@"
INDEX={c:i for i,c in enumerate(GLYPHS)}


class ChristmasGreeting:
    def __init__(self,size,start=18.11):
        self.size=size;self.w,self.h=size;self.start=start
        self.portrait=self.h>self.w
        candidates=[Path('C:/Windows/Fonts/Gabriola.ttf'),Path('C:/Windows/Fonts/segoesc.ttf')]
        self.font_path=next((str(p) for p in candidates if p.is_file()),None)
        self.source=pygame.Surface(size);self.source.fill((0,0,0))
        self.bounds=[]
        if self.portrait:
            self.put(self.letter('Merry',self.w*.44,self.h*.060,True),round(self.h*.044))
            self.put(self.letter('Christmas',self.w*.83,self.h*.080),
                     self.bounds[-1].bottom+round(self.h*.010))
        else:
            self.put(self.letter('Merry Christmas',self.w*.61,self.h*.075),round(self.h*.018))
        self.bottom=max(r.bottom for r in self.bounds)
        self.decorate()
        self.prepare_ascii()

    def letter(self,text,max_w,max_h,red=False):
        px=max(14,round(max_h*1.8))
        for _ in range(12):
            font=pygame.font.Font(self.font_path,px) if self.font_path else pygame.font.SysFont('georgia,serif',px,italic=True)
            raw=font.render(text,True,(255,255,255));box=raw.get_bounding_rect(min_alpha=5)
            if box.width<=max_w and box.height<=max_h:break
            px=max(8,int(px*min(max_w/max(1,box.width),max_h/max(1,box.height))*.98))
        alpha=pygame.surfarray.array_alpha(raw.subsurface(box)).T/255.
        h,w=alpha.shape;yy,xx=np.mgrid[:h,:w];y=yy/max(1,h-1)
        if red:
            lo=np.array([210,63,81]);hi=np.array([255,221,171])
        else:
            lo=np.array([105,190,249]);hi=np.array([239,253,255])
        shine=.36+.64*np.sin(y*math.pi+.18)
        col=lo+(hi-lo)*shine[:,:,None]
        # Ice facets and a warm outline unite Frozen-like frost and Christmas gold.
        facet=(np.sin(xx*.035+yy*.18)>.73)&(alpha>.15)
        col[facet]=[225,250,255]
        above=np.pad(alpha,((2,0),(0,0)))[:h]
        edge=(alpha>.25)&(above<.1)
        col[edge]=[255,235,173] if red else [247,255,255]
        image=np.clip(col*alpha[:,:,None],0,255).astype(np.uint8)
        return pygame.surfarray.make_surface(image.transpose(1,0,2))

    def put(self,art,y):
        rect=art.get_rect(midtop=(self.w//2,y))
        self.source.blit(art,rect);self.bounds.append(rect)

    def snowflake(self,cx,cy,r):
        for j in range(6):
            a=j*math.tau/6
            dx,dy=math.cos(a),math.sin(a)
            pygame.draw.line(self.source,(151,216,252),(cx,cy),(cx+dx*r,cy+dy*r),2)
            for u in (.45,.72):
                x=cx+dx*r*u;y=cy+dy*r*u
                for side in (-1,1):
                    b=a+math.pi+side*.65
                    pygame.draw.line(self.source,(187,237,255),(x,y),
                                     (x+math.cos(b)*r*.24,y+math.sin(b)*r*.24),2)
        pygame.draw.circle(self.source,(247,253,255),(round(cx),round(cy)),3)

    def decorate(self):
        w,h=self.w,self.h
        scale=w/1080 if self.portrait else h/1080
        y=self.bottom+max(9,round(h*.015))
        # Icy snowflakes around the lettering, all converted to glyphs below.
        if self.portrait:
            for cx,cy,r in ((w*.15,h*.078,w*.035),(w*.85,h*.078,w*.035),
                            (w*.08,h*.155,w*.026),(w*.92,h*.155,w*.026)):
                self.snowflake(cx,cy,r)
        else:
            self.snowflake(w*.16,h*.058,h*.034)
            self.snowflake(w*.84,h*.058,h*.034)
        # A sweeping frozen garland with evergreen needles and red berries.
        reach=w*(.34 if self.portrait else .23)
        points=[]
        for u in np.linspace(-1,1,240):
            points.append((w*.5+reach*u,y+math.sin(u*math.pi)*7*scale))
        pygame.draw.lines(self.source,(147,216,247),False,points,2)
        for side in (-1,1):
            cx=w*.5+side*reach*.66
            for j in range(12):
                x=cx+side*j*6*scale;yy=y-2*scale*j
                for flip in (-1,1):
                    pygame.draw.line(self.source,(52,165,112),(x,yy),(x+side*10*scale,yy+flip*12*scale),2)
            for dx,dy in ((0,0),(7,-4),(5,6)):
                pygame.draw.circle(self.source,(247,78,91),(round(cx+dx*scale),round(y+dy*scale)),max(2,round(4*scale)))
        self.snowflake(w*.5,y,12*scale)
        # Small hanging crystal prisms at both ends of the flourish.
        for side in (-1,1):
            x=w*.5+side*reach
            pygame.draw.line(self.source,(124,197,242),(x,y),(x,y+13*scale),1)
            r=6*scale;cy=y+21*scale
            pygame.draw.polygon(self.source,(169,230,255),[(x,cy-r*1.7),(x+r,cy),(x,cy+r*1.7),(x-r,cy)],2)
        self.decor_bottom=round(y+35*scale)

    def prepare_ascii(self):
        # All display pixels come from this glyph atlas, never the font/spline mask.
        self.cols=max(1,self.w//CW)
        self.rows=max(1,min(self.h, self.decor_bottom+10)//CH)
        rgb=pygame.surfarray.array3d(self.source).transpose(1,0,2)[:self.rows*CH,:self.cols*CW]
        blocks=rgb.reshape(self.rows,CH,self.cols,CW,3).transpose(0,2,1,3,4).astype(float)
        energy=blocks.max(4)
        occupied=energy>22
        weight=occupied[:,:,:,:,None]
        self.color=(blocks*weight).sum((2,3))/np.maximum(occupied.sum((2,3))[:,:,None],1)
        self.on=occupied.any((2,3))
        self.rr,self.cc=np.mgrid[:self.rows,:self.cols]
        self.hash=(self.rr*7919+self.cc*104729)%9973
        self.phase=self.hash*.017
        density=occupied.mean((2,3))
        # Thin frost lines are * / + ; thicker calligraphy has rich crystalline fill.
        self.base_chars=np.where(density>.50,INDEX['#'],np.where(density>.24,INDEX['*'],INDEX['+']))
        self.base_chars=np.where(self.on,self.base_chars,0)
        font=pygame.font.SysFont('consolas,cascadiamono,dejavusansmono,monospace',7)
        atlas=[]
        for c in GLYPHS:
            tile=pygame.Surface((CW,CH));tile.fill((0,0,0))
            g=font.render(c,True,(255,255,255))
            tile.blit(g,((CW-g.get_width())//2,(CH-g.get_height())//2))
            atlas.append(pygame.surfarray.array3d(tile).transpose(1,0,2)[:,:,0])
        self.atlas=np.stack(atlas)
        self.shape=pygame.Surface((self.cols*CW,self.rows*CH))
        self.pool=np.array([INDEX[c] for c in '#%&@8'])
        self.glint=np.zeros_like(self.rr,dtype=float)
        self.glint_epoch=None
        self.glint_spec=None
        del self.source

    def random_glint(self,t):
        age=t-self.start-2.5
        if age<0:return np.zeros_like(self.glint)
        # Irregular offsets, durations, word choice and locations; stable under
        # pause/restart and independent of frame rate.
        epoch=int(age//6.)
        if epoch!=self.glint_epoch:
            rng=np.random.default_rng(77125+epoch)
            rect=self.bounds[int(rng.integers(0,len(self.bounds)))]
            self.glint_spec=(rect,float(rng.uniform(.5,2.8)),float(rng.uniform(.8,1.55)),
                             float(rng.uniform(.18,.82)),float(rng.uniform(.10,.24)),bool(rng.random()<.27))
            self.glint_epoch=epoch
        rect,delay,duration,position,width,whole=self.glint_spec
        u=(age%6.-delay)/duration
        if not 0<u<1:return np.zeros_like(self.glint)
        envelope=math.sin(math.pi*u)**2
        x=(self.cc+.5)*CW;y=(self.rr+.5)*CH
        word=(x>=rect.left)&(x<rect.right)&(y>=rect.top)&(y<rect.bottom)
        if whole:region=word.astype(float)
        else:
            center=rect.left+rect.width*(position+(u-.5)*.16)
            region=np.exp(-((x-center)/max(2,rect.width*width))**2)*word
        return region*envelope*self.on

    def field(self,t):
        age=t-self.start
        self.glint=self.random_glint(t)
        if age<0:return np.zeros_like(self.base_chars),np.zeros_like(self.color,dtype=np.uint8)
        # The flying sleigh writes both lines from left to right behind its nose.
        local=(self.cc+.5)/max(1,self.cols)
        k=np.clip((reveal_front(age)-local)/.055,0,1)
        chars=self.base_chars.copy()
        inside=self.on&(self.hash%4==0)
        tick=np.floor(t*.8+self.phase).astype(int)
        chars=np.where(inside,self.pool[(self.hash+tick)%len(self.pool)],chars)
        chars=np.where(k>0,chars,0)
        shimmer=.95+.05*np.sin(t*.65+self.phase)**2
        bright=np.clip(self.color*1.24*shimmer[:,:,None],0,255)
        # Preserve each letter's palette: amber/red stays warm, ice stays blue-white.
        icy=self.color[:,:,2]>self.color[:,:,0]+10
        highlight=np.where(icy[:,:,None],np.array([185,235,255]),np.array([255,224,151]))
        bright=bright*(1+self.glint[:,:,None]*.38)+highlight*self.glint[:,:,None]*.16
        head=(k>0)&(k<1)
        bright=np.where(head[:,:,None],np.array([245,253,255]),bright)
        return chars,np.clip(bright*k[:,:,None],0,255).astype(np.uint8)

    def draw(self,frame,t):
        if t<self.start:return
        chars,color=self.field(t)
        mask=self.atlas[chars].transpose(0,2,1,3).reshape(self.rows*CH,self.cols*CW)
        pygame.surfarray.blit_array(self.shape,np.repeat(mask.T[:,:,None],3,axis=2))
        tint=pygame.surfarray.make_surface(color.transpose(1,0,2))
        self.shape.blit(pygame.transform.scale(tint,self.shape.get_size()),(0,0),special_flags=pygame.BLEND_RGB_MULT)
        # Persistent bright halo, with only a small shimmer instead of fading out.
        small=pygame.transform.smoothscale(self.shape,(max(1,self.shape.get_width()//5),max(1,self.shape.get_height()//5)))
        glow=pygame.transform.smoothscale(small,self.shape.get_size())
        glow.fill((125,151,170),special_flags=pygame.BLEND_RGB_MULT)
        frame.blit(glow,(0,0),special_flags=pygame.BLEND_RGB_ADD)
        frame.blit(self.shape,(0,0),special_flags=pygame.BLEND_RGB_ADD)
        if np.any(self.glint>.01):
            extra=np.clip(self.color*self.glint[:,:,None]*.9,0,255).astype(np.uint8)
            halo=pygame.surfarray.make_surface(extra.transpose(1,0,2))
            halo=pygame.transform.smoothscale(halo,(max(1,self.shape.get_width()//9),max(1,self.shape.get_height()//9)))
            halo=pygame.transform.smoothscale(halo,self.shape.get_size())
            frame.blit(halo,(0,0),special_flags=pygame.BLEND_RGB_ADD)
