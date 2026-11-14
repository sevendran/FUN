"""Animated glyph shading over a projected 3D winter surface.

The geometry is stable; material-specific characters and light keep evolving.
"""

import numpy as np
import pygame


CW,CH=6,9
CHARS=" .,:;~-=+*|/\\_1il!rtfjcvxzaeoun0{}[]<>08B$#&%Q"
AT={c:i for i,c in enumerate(CHARS)}
POOLS=["1il!;:","rtfjcvxz=+","aeoun0{}[]<>","08B$#&%Q"]


class AsciiSurface:
    def __init__(self,source,materials,depth):
        self.size=source.get_size()
        w,h=self.size
        self.cols,self.rows=max(1,w//CW),max(1,h//CH)
        ww,hh=self.cols*CW,self.rows*CH
        rgb=pygame.surfarray.array3d(source).transpose(1,0,2)[:hh,:ww].astype(np.float32)
        blocks=rgb.reshape(self.rows,CH,self.cols,CW,3).transpose(0,2,1,3,4)
        mat=materials[:hh,:ww].reshape(self.rows,CH,self.cols,CW).transpose(0,2,1,3)
        self.mat=mat.max((2,3))
        # Thin grass and twigs survive sampling: average their pixels rather than
        # diluting them into a cell full of white snow.
        weight=np.where(self.mat[:,:,None,None]>0,mat==self.mat[:,:,None,None],np.ones_like(mat,bool))
        self.rgb=(blocks*weight[:,:,:,:,None]).sum((2,3))/np.maximum(weight.sum((2,3))[:,:,None],1)
        self.on=(self.rgb.max(2)>7)
        self.lum=self.rgb@np.array([.2126,.7152,.0722])/255
        dep=depth[:hh,:ww].reshape(self.rows,CH,self.cols,CW).transpose(0,2,1,3)
        self.depth=np.min(dep,(2,3))
        self.rr,self.cc=np.mgrid[:self.rows,:self.cols]
        self.hash=(self.rr*7919+self.cc*104729)%9973
        self.phase=self.hash*.013
        self.center=(self.cols*.5,self.rows*.823)
        self.radius=np.sqrt(((self.cc-self.center[0])/(self.cols*.35))**2+
                            ((self.rr-self.center[1])/(self.rows*.12))**2)
        # Edge glyphs follow the silhouette and material boundary.
        padded=np.pad(self.mat,1,mode='edge')
        occupied=np.pad(self.on,1,mode='edge')
        gx=np.zeros_like(self.lum);gy=np.zeros_like(self.lum)
        self.edge=np.zeros_like(self.on)
        for dy,dx in ((0,-1),(0,1),(-1,0),(1,0)):
            neighbor=padded[1+dy:self.rows+1+dy,1+dx:self.cols+1+dx]
            empty=~occupied[1+dy:self.rows+1+dy,1+dx:self.cols+1+dx]
            boundary=self.on&(empty|((self.mat>0)&(neighbor!=self.mat)))
            gx+=dx*boundary;gy+=dy*boundary
            self.edge|=boundary
        self.outline=np.where(np.abs(gx)>2*np.abs(gy),AT['|'],
                     np.where(np.abs(gy)>2*np.abs(gx),AT['-'],
                     np.where(gx*gy>0,AT['/'],AT['\\'])))
        self.fill=np.array([[AT[p[k%len(p)]] for k in range(12)] for p in POOLS])
        font=pygame.font.SysFont('consolas,cascadiamono,dejavusansmono,couriernew,monospace',10)
        atlas=[]
        for c in CHARS:
            tile=pygame.Surface((CW,CH));tile.fill((0,0,0))
            g=font.render(c,True,(255,255,255))
            tile.blit(g,((CW-g.get_width())//2,(CH-g.get_height())//2))
            atlas.append(pygame.surfarray.array3d(tile).transpose(1,0,2)[:,:,0])
        self.atlas=np.stack(atlas)
        self.shape=pygame.Surface((ww,hh))
        self.trail=pygame.Surface(self.size);self.trail.fill((0,0,0))
        self.last_t=None

    def field(self,t):
        # Two slow waves change illumination, while per-cell rates stagger glyph swaps.
        wave=np.sin(self.cc*.042+self.rr*.11-t*.45)
        breathe=np.sin(t*.73+self.phase)
        light=.91+.055*wave+.035*breathe
        level=np.clip((self.lum*3.9+.16*wave).astype(int),0,3)
        tick=np.floor(t*(1.1+(self.hash%7)*.17)+self.phase).astype(int)
        idx=(self.hash+tick)%12
        char=self.fill[level,idx]
        grass=self.mat==2
        branch=self.mat==3
        cone=self.mat==4
        grasspool=np.array([AT[c] for c in "|/\\;!il"])
        branchpool=np.array([AT[c] for c in "-=+/\\x"])
        conepool=np.array([AT[c] for c in "0o8x#&"])
        char=np.where(grass,grasspool[(self.hash+tick//2)%len(grasspool)],char)
        char=np.where(branch,branchpool[(self.hash+tick//2)%len(branchpool)],char)
        char=np.where(cone,conepool[(self.hash+tick//2)%len(conepool)],char)
        char=np.where(self.edge&~grass&~cone&(self.mat!=5),self.outline,char)
        # More open foreground snow retains grain; no screen-space flat white fill.
        snow=(self.mat==0)&self.on
        grain=np.sin(self.phase*2.1+t*.31)
        sparse=snow&(self.hash%13==0)
        char=np.where(sparse,np.where(grain>.35,AT['+'],AT[':']),char)
        sparkle=snow&(self.hash%197==0)&(np.sin(t*1.1+self.phase)>.95)
        char=np.where(sparkle,AT['*'],char)
        char=np.where(self.on,char,AT[' '])
        color=self.rgb*light[:,:,None]*1.15
        # Cool silver -> neutral ivory variation, kept small to avoid a disco effect.
        tint=.5+.5*np.sin(self.cc*.025+self.rr*.067-t*.30)
        color[:,:,0]*=.94+.075*tint
        color[:,:,2]*=1.025-.055*tint
        # Keep the center decisively white, with a dimmer silver outer skirt.
        core=np.exp(-(self.radius/.62)**4)*(self.mat==0)*self.on
        color+=core[:,:,None]*np.array([39,39,39])
        color=np.where(sparkle[:,:,None],np.array([245,248,255]),color)
        color[~self.on]=0
        return char,np.clip(color,0,255).astype(np.uint8)

    def render(self,t):
        char,color=self.field(t)
        return self.render_field(char,color,t)

    def render_field(self,char,color,t):
        mask=self.atlas[char].transpose(0,2,1,3).reshape(self.rows*CH,self.cols*CW)
        pygame.surfarray.blit_array(self.shape,np.repeat(mask.T[:,:,None],3,axis=2))
        tint=pygame.surfarray.make_surface(color.transpose(1,0,2))
        self.shape.blit(pygame.transform.scale(tint,self.shape.get_size()),(0,0),special_flags=pygame.BLEND_RGB_MULT)
        # Time-aware max trail like test2: restart clears it, pause doesn't accumulate.
        if self.last_t is None or t<self.last_t or t-self.last_t>.3:
            self.trail.fill((0,0,0))
        elif t>self.last_t:
            decay=int(255*np.exp(-(t-self.last_t)/.026))
            self.trail.fill((decay,)*3,special_flags=pygame.BLEND_RGB_MULT)
        self.trail.blit(self.shape,(0,0),special_flags=pygame.BLEND_RGB_MAX)
        self.last_t=t
        out=self.trail.copy()
        small=pygame.transform.smoothscale(self.trail,(max(1,self.size[0]//5),max(1,self.size[1]//5)))
        halo=pygame.transform.smoothscale(small,self.size)
        halo.fill((28,28,31),special_flags=pygame.BLEND_RGB_MULT)
        out.blit(halo,(0,0),special_flags=pygame.BLEND_RGB_ADD)
        return out
