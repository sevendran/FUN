"""A solid ASCII snowball breaks into glyphs that spread and recoil."""

import math

import numpy as np
import pygame

from ascii_surface import AT, CW, CH


IMPACT=1.08
FINISH=6.2


def smooth(x):
    x=np.clip(x,0,1)
    return x*x*(3-2*x)


class ImpactIntro:
    def __init__(self,scene,terrain_height):
        self.scene=scene
        self.surface=scene.ascii
        self.ground=terrain_height
        self.origin=np.array([0,float(terrain_height(0,13)),13.])
        self.rows,self.cols=np.nonzero(self.surface.on)
        a=self.surface
        self.target_color=a.rgb[self.rows,self.cols]
        z=a.depth[self.rows,self.cols]
        # Invert the camera projection so each target glyph owns a 3D destination.
        sx=(self.cols+.5)*CW;sy=(self.rows+.5)*CH
        self.targets=scene.unproject_z(sx,sy,z)
        x=self.targets[:,0]
        self.offset=self.targets[:,[0,2]]-self.origin[[0,2]]
        self.radius=np.linalg.norm(self.offset,axis=1)
        self.angle=np.arctan2(self.offset[:,1],self.offset[:,0])
        self.rng=np.random.default_rng(404)
        self.rand=self.rng.random((len(x),5))
        self.snowball=self.make_snowball()
        self.last_t=None
        self.trail=pygame.Surface(scene.size);self.trail.fill((0,0,0))

    def make_snowball(self):
        # A filled spherical surface, shaded from its normals, sampled into ASCII.
        # Empty space between glyphs remains transparent; there is no central hole.
        diameter=max(48,round(self.scene.h*.15))
        cols=max(8,round(diameter/CW));rows=max(6,round(diameter/CH))
        yy,xx=np.meshgrid((np.arange(rows)+.5)/rows*2-1,
                          (np.arange(cols)+.5)/cols*2-1,indexing='ij')
        r2=xx*xx+yy*yy;inside=r2<=1
        zz=np.sqrt(np.maximum(1-r2,0))
        shade=np.clip(-.42*xx-.48*yy+.77*zz,0,1)
        grain=np.random.default_rng(999).random((rows,cols))
        light=(.38+.62*shade)*(.88+.12*grain)
        pools=np.array([AT[c] for c in ':+aeo08B#&%'])
        chars=pools[np.clip((light*(len(pools)-1)).astype(int),0,len(pools)-1)]
        chars=np.where(inside,chars,0)
        color=np.array([239,247,255])*light[:,:,None]
        color[~inside]=0
        mask=self.surface.atlas[chars].transpose(0,2,1,3).reshape(rows*CH,cols*CW)
        sprite=pygame.surfarray.make_surface(np.repeat(mask.T[:,:,None],3,axis=2))
        tint=pygame.surfarray.make_surface(color.astype(np.uint8).transpose(1,0,2))
        sprite.blit(pygame.transform.scale(tint,sprite.get_size()),(0,0),special_flags=pygame.BLEND_RGB_MULT)
        sprite.set_colorkey((0,0,0))
        return sprite

    def positions(self,age):
        # An outward impulse and drag, followed by an inward pull toward each
        # destination. Independent velocities and angular drift prevent group zoom.
        a=max(0.,age)
        launch=1-np.exp(-a*8)
        impulse=(19+15*self.rand[:,0])*a*np.exp(-a/(.38+.16*self.rand[:,1]))
        r=self.radius*launch+impulse
        turn=.38*np.sin(a*4+self.rand[:,2]*5)*np.exp(-a*1.6)*(1-np.exp(-a*9))
        theta=self.angle+turn
        x=self.origin[0]+np.cos(theta)*r
        z=self.origin[2]+np.sin(theta)*r
        # Different particles arc through the air and land at different times.
        v=1.4+4.3*self.rand[:,3]
        airborne=np.maximum(v*a-.5*10.5*a*a,0)
        settle=smooth((a-1.4)/3.72)
        terrain=self.ground(x,z)
        y=terrain+airborne
        p=np.stack([x,y,z],1)
        # Exact destination approach, with no snap when switching to final shading.
        p=p*(1-settle)+self.targets*settle
        return p

    def particle_field(self,t):
        scene=self.scene;a=self.surface
        chars=np.zeros((a.rows,a.cols),int)
        colors=np.zeros((a.rows,a.cols,3),np.uint8)
        age=t-IMPACT
        if age<0:return chars,colors
        p=scene.rotate_stage(self.positions(age),t)
        x,y,d=scene.project(p[:,0],p[:,1],p[:,2])
        ix=np.floor(x/CW).astype(int);iy=np.floor(y/CH).astype(int)
        good=(d>.3)&(ix>=0)&(ix<a.cols)&(iy>=0)&(iy<a.rows)
        k=np.flatnonzero(good)
        key=iy[k]*a.cols+ix[k]
        order=np.lexsort((d[k],key))
        _,first=np.unique(key[order],return_index=True)
        k=k[order[first]]
        final_char,final_color=a.field(t)
        target=final_char[self.rows,self.cols]
        bright=1-smooth((age-.7)/3.6)
        # Directional glyphs tumble, then become the final terrain/material glyphs.
        pool=np.array([AT[c] for c in ".:+*-=|/\\"])
        animated=pool[(self.rand[:,4]*23+t*14).astype(int)%len(pool)]
        glyph=np.where(age>2.5,target,animated)
        col=final_color[self.rows,self.cols].astype(float)*(1-bright)+np.array([248,251,255])*bright
        flash=np.exp(-((age-.04)/.09)**2)
        col=np.clip(col*(1+.7*flash),0,255).astype(np.uint8)
        chars[iy[k],ix[k]]=glyph[k]
        colors[iy[k],ix[k]]=col[k]
        return chars,colors

    def render(self,t):
        scene=self.scene;a=self.surface
        chars,colors=self.particle_field(t)
        shape=pygame.Surface(scene.size);shape.fill((0,0,0))
        mask=a.atlas[chars].transpose(0,2,1,3).reshape(a.rows*CH,a.cols*CW)
        art=pygame.surfarray.make_surface(np.repeat(mask.T[:,:,None],3,axis=2))
        tint=pygame.surfarray.make_surface(colors.transpose(1,0,2))
        art.blit(pygame.transform.scale(tint,art.get_size()),(0,0),special_flags=pygame.BLEND_RGB_MULT)
        shape.blit(art,(0,0))
        if self.last_t is None or t<self.last_t or t-self.last_t>.25:self.trail.fill((0,0,0))
        elif t>self.last_t:
            decay=int(255*np.exp(-(t-self.last_t)/.075))
            self.trail.fill((decay,)*3,special_flags=pygame.BLEND_RGB_MULT)
        self.trail.blit(shape,(0,0),special_flags=pygame.BLEND_RGB_MAX)
        self.last_t=t
        frame=self.trail.copy()
        age=t-IMPACT
        if age<.11:
            u=np.clip(t/IMPACT,0,1)
            # Accelerated free fall ends exactly on the invisible impact plane.
            y=self.origin[1]+9.4*(1-u*u)
            sx,sy,_=scene.project(0,y,13.)
            squash=1-.73*smooth(max(age,0)/.10)
            letter=pygame.transform.smoothscale(self.snowball,(self.snowball.get_width(),max(3,round(self.snowball.get_height()*squash))))
            if age<0:
                for lag,alpha in ((.045,45),(.022,90)):
                    past=np.clip((t-lag)/IMPACT,0,1)
                    _,gy,_=scene.project(0,self.origin[1]+9.4*(1-past*past),13.)
                    ghost=letter.copy();ghost.set_alpha(alpha)
                    frame.blit(ghost,ghost.get_rect(center=(round(sx),round(gy))))
            frame.blit(letter,letter.get_rect(center=(round(sx),round(sy))))
        if age>=0:
            if age<.22:
                x0,y0,_=scene.project(*self.origin)
                strength=math.exp(-(age/.095)**2)
                rays=pygame.Surface(scene.size,pygame.SRCALPHA)
                reach=scene.h*.11*(1+age*3)
                for scale in (1.,.65,.3):
                    pygame.draw.line(rays,(238,246,255,int(210*strength)),
                                     (x0-reach*scale,y0),(x0+reach*scale,y0),max(1,round(3*scale)))
                frame.blit(rays,(0,0))
            # Two sharp shock fronts and a bright impact core, sampled in 3D.
            for delay,speed in ((0,20),(.13,15)):
                b=age-delay
                if b<0 or b>1.25:continue
                r=speed*b/(1+1.3*b)
                angles=np.linspace(0,math.tau,520)
                xx=np.cos(angles)*r;zz=13+np.sin(angles)*r
                yy=self.ground(xx,zz)+.018
                ring=scene.rotate_stage(np.stack([xx,yy,zz],1),t)
                sx,sy,d=scene.project(ring[:,0],ring[:,1],ring[:,2])
                brightness=int(230*np.exp(-b*2.5))
                for x,y,z in zip(sx,sy,d):
                    if z>.3 and 0<=x<scene.w and 0<=y<scene.h:
                        pygame.draw.circle(frame,(brightness,brightness,min(255,brightness+12)),(int(x),int(y)),1)
            # Short camera recoil, not a resize: a decaying vertical displacement.
            shake=round(scene.h*.008*math.sin(age*47)*math.exp(-age*5))
            if shake:
                shifted=pygame.Surface(scene.size);shifted.fill((0,0,0));shifted.blit(frame,(0,shake));frame=shifted
        # Restrained bloom from the actual moving glyph field.
        small=pygame.transform.smoothscale(frame,(max(1,scene.w//5),max(1,scene.h//5)))
        glow=pygame.transform.smoothscale(small,scene.size)
        glow.fill((75,75,83),special_flags=pygame.BLEND_RGB_MULT)
        frame.blit(glow,(0,0),special_flags=pygame.BLEND_RGB_ADD)
        return frame
