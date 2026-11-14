"""A gold spiral draws upward, then red/gold baubles appear bottom to top."""

import math
import numpy as np

from ascii_surface import AT,CW,CH


GARLAND_DURATION=7.2


class TreeDecorations:
    def __init__(self,tree,complete):
        self.tree=tree;self.start=complete
        self.ball_start=complete+GARLAND_DURATION+.35
        rng=np.random.default_rng(122526)
        u=np.linspace(0,1,4200)
        y=.73+u*7.18
        angle=u*math.tau*4.6+.7
        r=3.05*(1-y/8.6)**.83+.11
        self.line=np.stack([r*np.cos(angle),tree.base+y,13+r*np.sin(angle)],1)
        self.line_birth=complete+u*GARLAND_DURATION
        self.line_u=u
        self.ball_centers=[];self.ball_birth=[]
        positions=[];normals=[];color=[];birth=[];ids=[]
        for row in range(7):
            y=1.0+row*.97
            count=8 if row<3 else 6
            for j in range(count):
                theta=j/count*math.tau+row*.73
                yy=y+rng.uniform(-.1,.1)
                rr=3.05*(1-yy/8.6)**.83+.11
                center=np.array([rr*math.cos(theta),tree.base+yy,13+rr*math.sin(theta)])
                born=self.ball_start+row*.8+j*.045
                number=len(self.ball_centers)
                self.ball_centers.append(center);self.ball_birth.append(born)
                a=rng.uniform(0,math.tau,540);v=rng.uniform(-1,1,len(a))
                n=np.stack([np.sqrt(1-v*v)*np.cos(a),v,np.sqrt(1-v*v)*np.sin(a)],1)
                radius=.155-row*.006
                positions.append(center+n*radius);normals.append(n)
                rgb=[213,28,39] if (j+row)%3 else [239,174,48]
                color.append(np.tile(rgb,(len(a),1)))
                birth.append(np.full(len(a),born));ids.append(np.full(len(a),number))
        self.p=np.concatenate(positions);self.n=np.concatenate(normals)
        self.color=np.concatenate(color);self.birth=np.concatenate(birth);self.ids=np.concatenate(ids)
        self.ball_centers=np.asarray(self.ball_centers);self.ball_birth=np.asarray(self.ball_birth)
        self.finished=self.ball_start+6*.8+.5

    def progress(self,t):
        return float(np.clip((t-self.start)/GARLAND_DURATION,0,1))

    def add(self,chars,colors,t):
        if t<self.start:return
        tree=self.tree;scene=tree.scene
        alive=t>=self.line_birth
        k=np.flatnonzero(alive)
        p=tree.rotate(self.line[k],t)
        age=t-self.line_birth[k]
        head=np.exp(-(age/.18)**2)
        twinkle=.82+.18*np.sin(t*1.15+k*.08)**2
        col=np.tile([243,182,57],(len(k),1))*twinkle[:,None]
        col=col*(1-head[:,None])+np.array([255,248,188])*head[:,None]
        glyph=np.where(k%34<3,AT['*'],AT['~'])
        self.raster(p,col,glyph,.42+head*.58,chars,colors)
        if t<self.ball_start:return
        k=np.flatnonzero(t>=self.birth)
        age=t-self.birth[k]
        u=np.clip(age/.38,0,1);pop=u*u*(3-2*u)
        center=self.ball_centers[self.ids[k]]
        p=center+(self.p[k]-center)*pop[:,None]
        p=tree.rotate(p,t)
        # Rotate normals with the same rigid transform (translation cancels).
        n=scene.rotate_stage(self.n[k]+[0,0,13],t)-[0,0,13]
        light=np.clip(n@np.array([-.45,.7,-.55]),0,1)
        spec=np.clip(n@np.array([-.2,.45,-.87]),0,1)**22
        col=self.color[k]*(.33+.67*light[:,None])+spec[:,None]*[220,207,167]
        col*=pop[:,None]
        glyph=np.where(spec>.35,AT['*'],np.where(light>.55,AT['8'],AT['0']))
        self.raster(p,col,glyph,spec*.55,chars,colors)

    def raster(self,p,col,glyph,glow,chars,colors):
        tree=self.tree;scene=tree.scene;a=scene.ascii
        sx,sy,d=scene.project(p[:,0],p[:,1],p[:,2])
        ix=np.floor(sx/CW).astype(int);iy=np.floor(sy/CH).astype(int)
        on=(d>.1)&(ix>=0)&(ix<a.cols)&(iy>=0)&(iy<a.rows)
        k=np.flatnonzero(on);key=iy[k]*a.cols+ix[k]
        order=np.lexsort((d[k],key));_,first=np.unique(key[order],return_index=True)
        k=k[order[first]];r,c=iy[k],ix[k]
        # Gold on the rear of the cone and rear baubles remain occluded.
        front=(p[k,2]<=tree.depth[r,c]+.10)&(p[k,2]<=scene.stage.cell_z[r,c]+.08)
        k,r,c=k[front],r[front],c[front]
        chars[r,c]=glyph[k]
        colors[r,c]=np.clip(col[k],0,255).astype(np.uint8)
        tree.depth[r,c]=np.minimum(tree.depth[r,c],p[k,2])
        tree.light[r,c]=np.maximum(tree.light[r,c],glow[k])
