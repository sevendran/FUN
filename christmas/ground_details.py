"""Small world-space winter props, sampled as grains like the snow surface."""

import math

import numpy as np


def add_ground_details(scene, image, terrain_height):
    rng = np.random.default_rng(241225)
    points, colors, radii, materials = [], [], [], []
    current_material = 0
    records = []

    def emit(p, color, radius=.008):
        p=np.asarray(p)
        points.append(p)
        colors.append(np.broadcast_to(color,(len(p),3)).copy())
        radii.append(np.broadcast_to(radius,len(p)).copy())
        materials.append(np.full(len(p),current_material,np.uint8))

    def anchor(u,z):
        z=9+(z-6)*.38
        available=7.4*np.sqrt(max(.10,1-((z-13)/5.2)**2))
        x=(u-.5)*2*available
        return np.array([x,terrain_height(x,z)-.025,z])

    def shadow(center, width, length):
        sx,sy,d=scene.project(*center)
        rx=max(2,scene.focal/d*width*1.4)
        ry=max(1,scene.focal/d*length*.35)
        x0,x1=max(0,int(sx-rx*2)),min(scene.w,int(sx+rx*2)+1)
        y0,y1=max(0,int(sy-ry*2)),min(scene.h,int(sy+ry*2)+1)
        if x0>=x1 or y0>=y1:return
        yy,xx=np.mgrid[y0:y1,x0:x1]
        shade=1-.22*np.exp(-((xx-sx)/rx)**2-((yy-sy)/ry)**2)
        image[y0:y1,x0:x1]=(image[y0:y1,x0:x1]*shade[:,:,None]).astype(np.uint8)

    def stroke(p, color, radius=.009):
        emit(p,color,radius)

    def rock(u,z,size):
        nonlocal current_material
        current_material=1
        c=anchor(u,z)
        shadow(c,size,size)
        n=4300
        theta=rng.uniform(0,math.tau,n)
        ny=rng.uniform(0,1,n)
        radial=np.sqrt(1-ny*ny)
        normal=np.stack([radial*np.cos(theta),ny,radial*np.sin(theta)],1)
        rough=1+.055*np.sin(theta*5+ny*11)+.035*np.sin(theta*9-ny*7)
        p=c+normal*np.array([size,size*.65,size*.72])*rough[:,None]
        light=.48+.46*np.clip(normal@np.array([-.45,.83,-.32]),0,1)
        col=np.array([117,122,127])[None,:]*light[:,None]*rng.uniform(.85,1.13,(n,1))
        # Irregular snow cap follows the rock, leaving dark exposed stone below.
        cap=ny>.51+.10*np.sin(theta*4)+.045*np.sin(theta*11)
        p[cap,1]+=.025
        col[cap]=np.array([239,243,249])*(.77+.23*light[cap,None])
        emit(p,col,rng.uniform(.007,.014,n))
        records.append(('rock',c,size))

    def grass(u,z,size):
        nonlocal current_material
        current_material=2
        c=anchor(u,z)
        shadow(c,size*.45,size*.4)
        for _ in range(rng.integers(7,14)):
            s=np.linspace(0,1,60)
            a=rng.uniform(0,math.tau)
            lean=rng.uniform(.15,.55)*size
            h=size*rng.uniform(.6,1.1)
            base=c+rng.normal(0,.025,3)*[1,0,1]
            p=base+np.stack([np.cos(a)*lean*s**1.6,h*s-.22*h*s*s,np.sin(a)*lean*s**1.6],1)
            col=np.tile(rng.choice([[117,101,68],[151,129,83],[176,153,104],[106,103,82]]),(len(s),1))
            col=(col*(.8+.2*s[:,None])).astype(float)
            stroke(p,col,.006)
            # Several thin seed heads, rather than lush green summer leaves.
            if rng.random()<.45:
                for at in (.77,.86,.94):
                    idx=int(at*(len(s)-1))
                    q=np.linspace(0,1,12)[:,None]
                    side=np.array([np.cos(a)*.03,.035,np.sin(a)*.03])*size/.3
                    stroke(p[idx]+q*side,[165,145,102],.008)
        records.append(('grass',c,size))

    def twig(u,z,size):
        nonlocal current_material
        current_material=3
        c=anchor(u,z)
        angle=rng.uniform(-.7,.7)
        direction=np.array([math.cos(angle),0,math.sin(angle)])
        s=np.linspace(-.5,.5,260)
        p=c+s[:,None]*direction*size
        p[:,1]=terrain_height(p[:,0],p[:,2])+.025+.018*np.sin(s*7)
        stroke(p,[96,72,52],.018)
        stroke(p+[0,.013,0],[152,122,89],.008)
        for at,side in ((-.15,1),(.12,-1),(.3,1)):
            base=p[np.argmin(np.abs(s-at))]
            end=base+np.array([.16, .035, side*.20])*size
            q=np.linspace(0,1,70)[:,None]
            stroke(base+(end-base)*q,[113,87,61],.011)
        # Broken, patchy dusting of snow along the upper bark.
        mask=(np.sin(s*28)>0)&(s<.23)
        stroke(p[mask]+[0,.026,0],[225,231,238],.012)
        shadow(c,size*.45,.12)
        records.append(('twig',c,size))

    def cone(u,z,size):
        nonlocal current_material
        current_material=4
        c=anchor(u,z)
        shadow(c,size,size*.7)
        for ring in range(7):
            v=ring/6
            r=size*.37*math.sin(math.pi*(.12+.8*v))
            for petal in range(9):
                a=petal*math.tau/9+ring*.43
                q=np.linspace(0,1,22)
                rr=r*(.65+.45*np.sin(q*math.pi))
                p=c+np.stack([rr*np.cos(a+q*.25),size*(v*.83+.12*q),rr*np.sin(a+q*.25)],1)
                shade=.68+.32*max(0,math.cos(a+1))
                stroke(p,np.array([135,92,52])*shade,.012)
                if ring>4 and petal%3==0:
                    stroke(p[-8:]+[0,.012,0],[225,231,238],.012)
        records.append(('cone',c,size))

    for args in ((.13,7,.34),(.84,8.3,.40),(.26,12,.25),(.72,15,.28),(.06,19,.30),(.93,26,.30)):
        rock(*args)
    for args in ((.28,6.3,.78),(.77,9.8,.72),(.10,13,1.0),(.91,17,.9)):
        twig(*args)
    for args in ((.19,6.6,.19),(.86,10,.20),(.37,8.3,.15),(.07,11,.17)):
        cone(*args)
    # Tufts cluster near props and along the sides; never fill the tree footprint.
    for u,z,size in ((.08,6.7,.34),(.17,7.5,.23),(.27,6,.29),(.34,9,.21),
                     (.66,6.5,.24),(.81,7.3,.32),(.91,8.5,.26),(.96,6,.30),
                     (.08,12,.27),(.22,13,.24),(.77,14,.23),(.90,12,.26),
                     (.16,20,.25),(.86,21,.23),(.38,22,.18),(.67,24,.20)):
        grass(u,z,size)

    p=np.concatenate(points);col=np.concatenate(colors);rad=np.concatenate(radii)
    material=np.concatenate(materials)
    sx,sy,depth=scene.project(p[:,0],p[:,1],p[:,2])
    ix=np.rint(sx).astype(int);iy=np.rint(sy).astype(int)
    radius=np.clip(scene.focal/depth*rad,.55,2.5)
    order=np.argsort(-depth,kind='stable')
    ix,iy,p,col,radius,material=(a[order] for a in (ix,iy,p,col,radius,material))
    # Per-pixel world z is also used by falling snow for front/back occlusion.
    for oy in range(-2,3):
        for ox in range(-2,3):
            on=(ox*ox+oy*oy<=radius*radius)&(ix+ox>=0)&(ix+ox<scene.w)&(iy+oy>=0)&(iy+oy<scene.h)
            k=np.flatnonzero(on)
            xx,yy=ix[k]+ox,iy[k]+oy
            front=p[k,2]<=scene.world_z[yy,xx]+.10
            k,xx,yy=k[front],xx[front],yy[front]
            image[yy,xx]=np.clip(col[k],0,255).astype(np.uint8)
            scene.material[yy,xx]=material[k]
            scene.world_z[yy,xx]=p[k,2]
            scene.ground_mask[yy,xx]=True
    scene.prop_records=records
    return image
