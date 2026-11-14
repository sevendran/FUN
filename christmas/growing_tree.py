"""A lush, undecorated ASCII fir growing one branch tier at a time."""

import math

import numpy as np
import pygame

from ascii_surface import AT,CW,CH
from tree_decorations import TreeDecorations


START=6.65
TIERS=14
FIRST_BRANCH=START+.85
TIER_STEP=.72
COMPLETE=FIRST_BRANCH+(TIERS-1)*TIER_STEP+1.25


def smooth(x):
    x=np.clip(x,0,1)
    return x*x*(3-2*x)


class GrowingTree:
    def __init__(self,scene,terrain_height):
        self.scene=scene
        self.z=13.
        self.base=float(terrain_height(0,self.z))
        self.width_scale=1.23
        # Keep the finished star clear of the fixed title in both output layouts.
        self.height_scale=1.12 if scene.portrait else 1.005
        self.rng=np.random.default_rng(122512)
        self.p=[];self.birth=[];self.color=[];self.kind=[];self.tier=[]
        self.make_trunk()
        self.make_branches()
        self.p=np.concatenate(self.p)
        self.birth=np.concatenate(self.birth)
        self.color=np.concatenate(self.color)
        self.kind=np.concatenate(self.kind)
        self.tier=np.concatenate(self.tier)
        self.hash=np.arange(len(self.p))*7919%9973
        self.pool=np.array([AT[c] for c in 'rtfjcvxzaeoun0{}[]<>08B#&%'])
        self.depth=np.full((scene.ascii.rows,scene.ascii.cols),np.inf)
        self.light=np.zeros_like(self.depth)
        self.settled_samples=None
        self.sample_key=None
        self.make_lights()
        self.decor=TreeDecorations(self,COMPLETE)

    def add(self,p,birth,color,kind,tier):
        n=len(p)
        self.p.append(p)
        self.birth.append(np.broadcast_to(birth,n).copy())
        self.color.append(np.broadcast_to(color,(n,3)).copy())
        self.kind.append(np.full(n,kind))
        self.tier.append(np.full(n,tier))

    def make_trunk(self):
        rng=self.rng;n=7800
        a=rng.uniform(0,math.tau,n);h=rng.uniform(0,8.05,n)
        radius=.15*(1-.78*h/8.1)
        p=np.stack([np.cos(a)*radius,self.base+h,self.z+np.sin(a)*radius],1)
        birth=np.where(h<.95,START+h*.65,FIRST_BRANCH+(h-.7)/.53*TIER_STEP-.12)
        shade=.55+.45*np.clip(-np.cos(a)*.4-np.sin(a)*.7,0,1)
        col=np.array([129,91,49])*shade[:,None]
        self.add(p,birth,col,0,-1)

    def make_branches(self):
        rng=self.rng
        for i in range(TIERS):
            h=.66+i*.53
            outer=3.05*(1-h/8.6)**.83
            # Concentric branch rings expose their near and far arcs, like 2.png.
            # Small radial offsets preserve a feathery silhouette without filling
            # every cell into a flat triangular slab.
            theta,u=np.meshgrid(np.linspace(0,math.tau,144,endpoint=False),np.linspace(.08,1,14))
            theta=theta.ravel()+i*.17
            u=np.clip(u.ravel()+rng.normal(0,.010,theta.size),.025,1)
            n=len(u)
            lobes=13-i//3
            frond=.87+.13*(.5+.5*np.cos(theta*lobes+i*.82))**2
            r=outer*u*frond
            yy=h+.65*(1-u)**1.35-.11*u*u
            yy+=.037*np.sin(theta*lobes+u*14+i)+rng.normal(0,.011,n)
            p=np.stack([r*np.cos(theta),self.base+yy,self.z+r*np.sin(theta)],1)
            slope=.88/outer*np.maximum(1-u,.02)**.35+.22*u/outer
            normal=np.stack([slope*np.cos(theta),np.ones(n),slope*np.sin(theta)],1)
            normal/=np.linalg.norm(normal,axis=1,keepdims=True)
            light=.40+.78*np.clip(normal@np.array([-.69,.52,-.50]),0,1)
            # A branch canopy darkens its inner recess; tips catch the key light.
            light*=.65+.35*u**.55
            light*=rng.uniform(.90,1.10,n)
            palette=np.array([[34,133,61],[28,113,52],[45,162,72],[64,182,87],[22,98,49]])
            col=palette[rng.integers(0,len(palette),n)]*light[:,None]*1.20
            # Radial birth time is a wave moving out along every branch.
            born=FIRST_BRANCH+i*TIER_STEP+.53*u+rng.uniform(0,.10,n)
            self.add(p,born,col,1,i)
            # Fine paired needle tips give the layers a full, feathery silhouette.
            tips=p+np.stack([.025*np.cos(theta),np.full(n,.045),.025*np.sin(theta)],1)
            self.add(tips,born+.025,col*1.10,1,i)
            # A lit rim on each circular branch skirt makes its elliptical near
            # arc readable independently of the darker interior volume.
            angle=np.linspace(0,math.tau,380,endpoint=False)
            edge_r=outer*(.87+.13*(.5+.5*np.cos(angle*lobes+i*.82))**2)*1.025
            edge_y=h-.11+.037*np.sin(angle*lobes+14+i)
            edge_p=np.stack([edge_r*np.cos(angle),self.base+edge_y,self.z+edge_r*np.sin(angle)],1)
            edge_col=np.array([65,172,99])*(.76+.24*np.cos(angle+2))[:,None]
            self.add(edge_p,FIRST_BRANCH+i*TIER_STEP+.57,edge_col,2,i)

    def rotation(self,t):
        return self.scene.stage_angle(t)

    def rotate(self,p,t):
        q=np.asarray(p).copy()
        q[:,0]*=self.width_scale
        q[:,2]=self.z+(q[:,2]-self.z)*self.width_scale
        q[:,1]=self.base+(q[:,1]-self.base)*self.height_scale
        return self.scene.rotate_stage(q,t)

    def make_lights(self):
        positions=[];births=[];phases=[]
        for i in range(TIERS):
            indices=np.flatnonzero((self.tier==i)&(self.kind==1))
            radius=np.linalg.norm(self.p[indices][:,[0,2]]-np.array([0,self.z]),axis=1)
            candidates=indices[radius>radius.max()*.73]
            chosen=self.rng.choice(candidates,size=7,replace=False)
            for k in chosen:
                p=self.p[k].copy();p[0]*=1.045;p[2]=self.z+(p[2]-self.z)*1.045;p[1]+=.025
                positions.append(p);births.append(self.birth[k]+.12)
                phases.append(float(self.rng.uniform(0,math.tau)))
        self.light_positions=np.asarray(positions)
        self.light_birth=np.asarray(births)
        self.light_phase=np.asarray(phases)

    def add_lights(self,chars,colors,t):
        a=self.scene.ascii
        p=self.rotate(self.light_positions,t)
        sx,sy,d=self.scene.project(p[:,0],p[:,1],p[:,2])
        ix=np.floor(sx/CW).astype(int);iy=np.floor(sy/CH).astype(int)
        shown=(t>=self.light_birth)&(ix>=0)&(ix<a.cols)&(iy>=0)&(iy<a.rows)&(d>.1)
        for k in np.flatnonzero(shown):
            r,c=iy[k],ix[k]
            # Rear ornaments are hidden by the actual branch geometry.
            if p[k,2]>self.depth[r,c]+.12:continue
            fade=float(smooth((t-self.light_birth[k])/.28))
            pulse=.70+.30*(.5+.5*math.sin(t*1.35+self.light_phase[k]))
            chars[r,c]=AT['*'] if pulse>.84 else AT['+']
            colors[r,c]=np.array([236,246,255])*pulse*fade
            self.depth[r,c]=min(self.depth[r,c],p[k,2])
            self.light[r,c]=max(self.light[r,c],pulse*.65*fade)
            # Tiny satellite dots make each ornament a small beaded light,
            # rather than a nearly invisible single pixel full stop.
            for dr,dc in ((0,-1),(0,1),(-1,0),(1,0)):
                rr,cc=r+dr,c+dc
                if 0<=rr<a.rows and 0<=cc<a.cols and self.depth[rr,cc]>=p[k,2]-.10:
                    chars[rr,cc]=AT['.']
                    colors[rr,cc]=np.array([195,218,246])*pulse*fade*.7

    def samples(self,t):
        cache_key=math.floor(t*15)
        if t>=COMPLETE and self.settled_samples is not None and self.sample_key==cache_key:
            return self.settled_samples
        a=self.scene.ascii
        age=t-self.birth
        visible=age>=0
        k=np.flatnonzero(visible)
        progress=smooth(age[k]/.30)
        p=self.p[k].copy()
        # A new needle extends from its branch axis; existing layers do not resize.
        p[:,0]*=.28+.72*progress
        p[:,2]=self.z+(p[:,2]-self.z)*(.28+.72*progress)
        p[:,1]-=.10*(1-progress)
        p=self.rotate(p,t)
        x,y,depth=self.scene.project(p[:,0],p[:,1],p[:,2])
        ix=np.floor(x/CW).astype(int);iy=np.floor(y/CH).astype(int)
        on=(ix>=0)&(ix<a.cols)&(iy>=0)&(iy<a.rows)&(depth>.1)
        k,p,ix,iy,depth=(v[on] for v in (k,p,ix,iy,depth))
        key=iy*a.cols+ix
        order=np.lexsort((depth,key))
        _,first=np.unique(key[order],return_index=True)
        chosen=order[first]
        k,p,ix,iy,depth=(v[chosen] for v in (k,p,ix,iy,depth))
        # Terrain/prop occlusion uses the existing stable world-space depth map.
        px=np.minimum(ix*CW+CW//2,self.scene.w-1)
        py=np.minimum(iy*CH+CH//2,self.scene.h-1)
        front=p[:,2]<=self.scene.stage.cell_z[iy,ix]+.08
        k,p,ix,iy=(v[front] for v in (k,p,ix,iy))
        result=(k,p,ix,iy)
        if t>=COMPLETE:
            self.settled_samples=result;self.sample_key=cache_key
        return result

    def field(self,t):
        a=self.scene.ascii
        chars=np.zeros((a.rows,a.cols),int)
        colors=np.zeros((a.rows,a.cols,3),np.uint8)
        self.depth.fill(np.inf);self.light.fill(0)
        if t<START:return chars,colors
        k,p,ix,iy=self.samples(t)
        head=np.exp(-np.maximum(t-self.birth[k]-.10,0)**2/.075)
        phase=self.hash[k]*.009
        light=.91+.055*np.sin(t*.65+phase)+.035*np.sin(iy*.16-t*.4)
        # Broad rounded volume and tier recesses survive the small ASCII cells.
        relative=p[:,[0,2]]-np.array([0,self.z])
        theta=np.arctan2(relative[:,1],relative[:,0])
        directional=.70+.42*np.clip(-.77*np.cos(theta)-.64*np.sin(theta),0,1)
        rim=np.clip(np.abs(np.sin(theta+self.scene.yaw)),0,1)**7*.13
        branch_height=(p[:,1]-self.base)/self.height_scale
        tier_shadow=.65+.35*np.sin((branch_height-.66)/.53*math.tau+.6)**2
        volume=directional*tier_shadow+rim
        volume=np.where(self.kind[k]==0,1.,volume)
        col=self.color[k]*light[:,None]*volume[:,None]*1.28
        col=col*(1-head[:,None])+np.array([242,253,255])*head[:,None]
        tick=np.floor(t*(1.3+self.hash[k]%5*.13)).astype(int)
        level=np.clip((col[:,1]/65).astype(int)+1,0,3)
        char=a.fill[level,(self.hash[k]+tick)%12]
        rim_cells=self.kind[k]==2
        char=np.where(rim_cells,AT['~'],char)
        trunk=self.kind[k]==0
        char=np.where(trunk,np.where(self.hash[k]%3,AT['|'],AT[':']),char)
        char=np.where(head>.65,np.where(self.hash[k]%4,AT['+'],AT['*']),char)
        chars[iy,ix]=char
        colors[iy,ix]=np.clip(col,0,255).astype(np.uint8)
        self.depth[iy,ix]=p[:,2]
        self.light[iy,ix]=head
        self.add_lights(chars,colors,t)
        self.decor.add(chars,colors,t)
        # The topper warms nearby branches and existing ornaments as well as snow.
        if t>=self.scene.finale.start:
            rr,cc=np.nonzero(np.isfinite(self.depth)&(chars>0))
            p=self.scene.unproject_z((cc+.5)*CW,(rr+.5)*CH,self.depth[rr,cc])
            colors[rr,cc]=self.scene.finale.tint(colors[rr,cc],p,t,.45).astype(np.uint8)
        self.scene.finale.add(chars,colors,t)
        return chars,colors

    def draw(self,frame,t):
        a=self.scene.ascii
        chars,color=self.field(t)
        if not np.any(chars):return
        rr,cc=np.nonzero(chars)
        r0,r1=int(rr.min()),int(rr.max())+1
        c0,c1=int(cc.min()),int(cc.max())+1
        chars=chars[r0:r1,c0:c1];color=color[r0:r1,c0:c1]
        rows,cols=chars.shape
        position=(c0*CW,r0*CH)
        # Assemble the tree as glyphs while preserving the black gaps between them.
        mask=a.atlas[chars].transpose(0,2,1,3).reshape(rows*CH,cols*CW)
        art=pygame.surfarray.make_surface(np.repeat(mask.T[:,:,None],3,axis=2))
        tint=pygame.surfarray.make_surface(color.transpose(1,0,2))
        art.blit(pygame.transform.scale(tint,art.get_size()),(0,0),special_flags=pygame.BLEND_RGB_MULT)
        # Color key makes empty cells transparent; the actual tree pixels stay ASCII.
        art.set_colorkey((0,0,0))
        frame.blit(art,position)
        grow=color.astype(float)*self.light[r0:r1,c0:c1,None]
        glow=pygame.surfarray.make_surface(np.clip(grow,0,255).astype(np.uint8).transpose(1,0,2))
        glow=pygame.transform.smoothscale(glow,(max(1,art.get_width()//5),max(1,art.get_height()//5)))
        glow=pygame.transform.smoothscale(glow,art.get_size())
        glow.fill((70,80,80),special_flags=pygame.BLEND_RGB_MULT)
        frame.blit(glow,position,special_flags=pygame.BLEND_RGB_ADD)
