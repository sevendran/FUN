"""Reproject the cached snow terrain and props in 3D every frame."""

import numpy as np

from ascii_surface import CW,CH


class RotatingStage:
    def __init__(self,scene):
        self.scene=scene;a=scene.ascii
        # Supersample the original surface so rotation does not open holes.
        yy,xx=np.mgrid[0:scene.h:2,0:scene.w:2]
        valid=np.isfinite(scene.world_z[yy,xx])
        xx,yy=xx[valid],yy[valid]
        self.local=scene.unproject_z(xx+.5,yy+.5,scene.world_z[yy,xx])
        self.sr=np.minimum(yy//CH,a.rows-1)
        self.sc=np.minimum(xx//CW,a.cols-1)
        keep=a.on[self.sr,self.sc]
        self.local=self.local[keep];self.sr=self.sr[keep];self.sc=self.sc[keep]
        self.cell_z=np.full((a.rows,a.cols),np.inf)
        self.cell_mask=np.zeros((a.rows,a.cols),bool)

    def field(self,t):
        scene=self.scene;a=scene.ascii
        source_char,source_color=a.field(t)
        p=scene.rotate_stage(self.local,t)
        sx,sy,d=scene.project(p[:,0],p[:,1],p[:,2])
        ix=np.floor(sx/CW).astype(int);iy=np.floor(sy/CH).astype(int)
        ok=(d>.1)&(ix>=0)&(ix<a.cols)&(iy>=0)&(iy<a.rows)
        k=np.flatnonzero(ok);key=iy[k]*a.cols+ix[k]
        # Depth wins; a tiny bias keeps thin grass from disappearing into snow.
        priority=(a.mat[self.sr[k],self.sc[k]]>0)*.025
        order=np.lexsort((d[k]-priority,key))
        _,first=np.unique(key[order],return_index=True)
        k=k[order[first]];r,c=iy[k],ix[k]
        char=np.zeros((a.rows,a.cols),int)
        color=np.zeros((a.rows,a.cols,3),np.uint8)
        sr,sc=self.sr[k],self.sc[k]
        char[r,c]=source_char[sr,sc]
        shade=np.ones(len(k))
        if t>6.65:
            x=p[k,0];z=p[k,2]-13
            contact=np.exp(-(x/1.65)**2-(z/1.05)**2)
            along=x*.55+z*.83;across=x*.83-z*.55
            cast=np.exp(-(across/(.9+np.maximum(along,0)*.16))**2)
            cast*=np.clip(along/.7,0,1)*np.exp(-np.maximum(along,0)/4.2)
            shade-=np.clip(contact*.38+cast*.32,0,.55)*min(1,(t-6.65)/7)
        lit=source_color[sr,sc]*shade[:,None]
        lit=scene.finale.tint(lit,p[k],t)
        color[r,c]=lit.astype(np.uint8)
        self.cell_z.fill(np.inf);self.cell_z[r,c]=p[k,2]
        self.cell_mask=char>0
        return char,color

    def render(self,t):
        char,color=self.field(t)
        return self.scene.ascii.render_field(char,color,t)
