"""A faceted gold topper, one birth flash, warm breathing light and ring of gifts."""

import math
import numpy as np
import pygame

from ascii_surface import AT


def smooth(x):
    x=np.clip(x,0,1)
    return x*x*(3-2*x)


class ChristmasFinale:
    def __init__(self,scene,terrain_height):
        self.scene=scene;self.tree=scene.tree
        self.start=self.tree.decor.finished+.25
        self.gift_start=self.start+1.05
        self.gift_launch=self.gift_start+np.arange(16)*.46
        self.gift_fall=.82
        self.gift_bounce=.28
        self.gifts_finished=float(self.gift_launch[-1]+self.gift_fall+self.gift_bounce)
        self.yellow_start=self.gifts_finished+.25
        self.yellow_duration=6.5
        self.center=np.array([0,self.tree.base+8.52,13.])
        self.rng=np.random.default_rng(122531)
        self.star_p,self.star_color=self.make_star()
        self.gift_p,self.gift_color,self.gift_birth,self.gift_centers,self.gift_ids=self.make_gifts(terrain_height)
        self.make_yellow_spiral()
        self.halo_cache={}

    def make_star(self):
        outline=[]
        for i in range(10):
            a=math.pi/2+i*math.pi/5;r=.49 if i%2==0 else .22
            outline.append(np.array([math.cos(a)*r,math.sin(a)*r,0]))
        points=[];colors=[]
        # Two ridged faces: the back is a complete star too, with actual thickness.
        for side in (-1,1):
            for i in range(10):
                a=outline[i].copy();b=outline[(i+1)%10].copy()
                a[2]=b[2]=side*.055
                c=np.array([0,0,side*.19])
                uv=self.rng.random((520,2));flip=uv.sum(1)>1;uv[flip]=1-uv[flip]
                p=c+(a-c)*uv[:,0,None]+(b-c)*uv[:,1,None]
                points.append(p)
                shade=.78 if (i+int(side>0))%2==0 else 1.0
                colors.append(np.tile(np.array([255,213,89])*shade,(len(p),1)))
        return np.concatenate(points),np.concatenate(colors)

    def make_gifts(self,terrain_height):
        points=[];colors=[];births=[];ids=[];centers=[]
        palette=np.array([[176,32,45],[31,105,65],[229,210,167],[62,101,145],[128,42,65]])
        for j in range(16):
            a=j/16*math.tau+.22
            r=3.55+(j%3)*.43
            center=np.array([r*math.cos(a),0,13+r*math.sin(a)])
            center[1]=terrain_height(center[0],center[2])+.025
            centers.append(center)
            w=self.rng.uniform(.54,.84);h=self.rng.uniform(.43,.78);d=self.rng.uniform(.50,.74)
            yaw=a+self.rng.uniform(-.28,.28)
            dims=np.array([w,h,d]);born=self.gift_launch[j]
            for axis in range(3):
                for side in (-1,1):
                    n=600
                    q=(self.rng.random((n,3))-.5)*dims
                    q[:,axis]=side*dims[axis]/2;q[:,1]+=h/2
                    ribbon=(np.abs(q[:,0])<w*.085)|(np.abs(q[:,2])<d*.085)
                    if axis!=1:ribbon|=np.abs(q[:,1]-h*.52)<h*.07
                    col=np.tile(palette[j%len(palette)]*(1 if axis==1 else .76 if side<0 else .58),(n,1))
                    col[ribbon]=[242,195,86] if j%2==0 else [242,235,207]
                    q[:,[0,2]]=q[:,[0,2]]@np.array([[math.cos(yaw),-math.sin(yaw)],[math.sin(yaw),math.cos(yaw)]])
                    points.append(q+center);colors.append(col);births.append(np.full(n,born));ids.append(np.full(n,j))
            for side in (-1,1):
                a0=np.linspace(0,math.tau,150)
                q=np.stack([side*.15*(1-np.cos(a0)),h+.10*np.sin(a0)**2,.09*np.sin(a0)],1)
                points.append(q+center);colors.append(np.tile([250,211,116],(len(q),1)))
                births.append(np.full(len(q),born));ids.append(np.full(len(q),j))
        return (np.concatenate(points),np.concatenate(colors),np.concatenate(births),
                np.asarray(centers),np.concatenate(ids))

    def make_yellow_spiral(self):
        u=np.linspace(0,1,4600)
        y=.78+u*7.18
        # Offset it from the gold so the two ribbons remain distinct.
        a=u*math.tau*4.6+math.pi+.7
        r=3.05*(1-y/8.6)**.83+.14
        self.yellow_p=np.stack([r*np.cos(a),self.tree.base+y,13+r*np.sin(a)],1)
        self.yellow_birth=self.yellow_start+u*self.yellow_duration

    def gift_offsets(self,t):
        age=t-self.gift_launch
        u=np.clip(age/self.gift_fall,0,1)
        fall=11*(1-u*u)
        after=age-self.gift_fall
        b=np.clip(after/self.gift_bounce,0,1)
        hop=.17*4*b*(1-b)
        return np.where(after<0,fall,hop),age>=0

    def add_yellow(self,chars,colors,t):
        if t<self.yellow_start:return
        k=np.flatnonzero(t>=self.yellow_birth)
        p=self.tree.rotate(self.yellow_p[k],t)
        age=t-self.yellow_birth[k]
        head=np.exp(-(age/.20)**2)
        pulse=.86+.14*np.sin(t*1.6+k*.10)**2
        col=np.array([255,239,66])*pulse[:,None]
        col=col*(1-head[:,None])+np.array([255,255,203])*head[:,None]
        char=np.where((k%26<4)|(head>.65),AT['*'],AT['+'])
        self.tree.decor.raster(p,col,char,.75+head*.25,chars,colors)

    def pulse(self,t):
        age=t-self.start
        if age<0:return 0.
        return float(smooth(age/.45))*(.74+.26*(.5+.5*math.sin(age*.90)))

    def flash(self,t):
        age=t-self.start
        return 0. if age<0 else math.exp(-((age-.34)/.17)**2)

    def tint(self,color,p,t,strength=1.):
        if t<self.start:return color
        # The snow's microscopic contrast is preserved under the changing warm key.
        c=np.asarray(color,dtype=float)
        radius=p[:,0]**2+(p[:,2]-13)**2
        near=np.exp(-radius/31)
        level=np.clip((self.pulse(t)*.78+self.flash(t)*.55)*near*strength,0,1)
        warm=np.clip(c*np.array([1.17,1.045,.80])+[24,13,0],0,255)
        return np.clip(c+(warm-c)*level[:,None],0,255)

    def add(self,chars,colors,t):
        if t<self.start:return
        tree=self.tree
        age=t-self.start
        u=np.clip(age/.52,0,1)
        pop=1+2.4*(u-1)**3+1.4*(u-1)**2
        p=tree.rotate(self.star_p*pop+self.center,t)
        born=smooth(age/.18)
        col=self.star_color*(.88+.12*self.pulse(t))*(1+self.flash(t)*.65)*born
        char=np.full(len(p),AT['#']);char[::4]=AT['*']
        tree.decor.raster(p,col,char,np.full(len(p),self.pulse(t)),chars,colors)
        if t<self.gift_start:return
        k=np.flatnonzero(t>=self.gift_birth)
        age=t-self.gift_birth[k]
        center=self.gift_centers[self.gift_ids[k]]
        q=self.gift_p[k]-center
        # Drop the complete rigid box, then squash a little at contact and rebound.
        contact=np.exp(-((age-self.gift_fall)/.065)**2)
        q[:,0]*=1+.12*contact;q[:,2]*=1+.12*contact
        q[:,1]*=1-.17*contact
        tilt=.17*np.sin(age*5+self.gift_ids[k])*(1-smooth(age/self.gift_fall))
        x=q[:,0].copy();y=q[:,1].copy()
        q[:,0]=x*np.cos(tilt)-y*np.sin(tilt)
        q[:,1]=x*np.sin(tilt)+y*np.cos(tilt)
        p=center+q
        offsets,_=self.gift_offsets(t)
        p[:,1]+=offsets[self.gift_ids[k]]
        p=self.scene.rotate_stage(p,t)
        col=self.tint(self.gift_color[k],p,t)
        char=np.where(self.gift_ids[k]%2,AT['#'],AT['8'])
        tree.decor.raster(p,col,char,np.zeros(len(p)),chars,colors)
        self.add_yellow(chars,colors,t)

    def halo(self,radius,color):
        r=max(2,int(radius));key=(r,tuple(color))
        if key not in self.halo_cache:
            yy,xx=np.mgrid[-r:r+1,-r:r+1]
            fall=np.exp(-(xx*xx+yy*yy)/(r*.37)**2)
            pixels=np.clip(fall[:,:,None]*np.array(color),0,255).astype(np.uint8)
            self.halo_cache[key]=pygame.surfarray.make_surface(pixels.transpose(1,0,2))
        return self.halo_cache[key]

    def draw_glow(self,frame,t):
        if t<self.start:return
        scene=self.scene
        center=self.tree.rotate(self.center[None,:],t)[0]
        x,y,_=scene.project(*center)
        pulse=self.pulse(t);flash=self.flash(t)
        for radius,color,strength in ((scene.h*.15,[112,67,19],pulse),
                                      (scene.h*.045,[190,135,52],pulse),
                                      (scene.h*.30,[170,128,67],flash)):
            glow=self.halo(radius,color).copy()
            glow.fill((int(min(1,strength)*255),)*3,special_flags=pygame.BLEND_RGB_MULT)
            frame.blit(glow,(int(x-glow.get_width()/2),int(y-glow.get_height()/2)),special_flags=pygame.BLEND_RGB_ADD)
        # One broad birth flare retracts into a quiet periodic star glint.
        reach=scene.h*(.035*pulse+.14*flash)
        rays=pygame.Surface(scene.size,pygame.SRCALPHA)
        for a in (0,math.pi/2,math.pi/4,-math.pi/4):
            dx=math.cos(a)*reach;dy=math.sin(a)*reach
            for fraction in (1.,.55):
                pygame.draw.line(rays,(255,231,161,int(95*pulse+130*flash)),
                                 (x-dx*fraction,y-dy*fraction),(x+dx*fraction,y+dy*fraction),1)
        frame.blit(rays,(0,0))
