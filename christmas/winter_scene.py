"""Perspective height-field snow, pointillist grains, and world-space snowfall."""

import math

import numpy as np
import pygame

from ground_details import add_ground_details
from ascii_surface import AsciiSurface
from impact_intro import ImpactIntro, FINISH
from growing_tree import GrowingTree, START, COMPLETE
from stage_motion import rotate as rotate_stage, angle as stage_angle
from rotating_stage import RotatingStage
from christmas_finale import ChristmasFinale
from christmas_greeting import ChristmasGreeting
from christmas_fireworks import ChristmasFireworks
from santa_flyby import SantaFlyby


def height(x, z):
    """World-space drifts, in metres. Kept stable for a future tree's footing."""
    # Low, softly domed snow disc: a rounded top instead of lumpy hill silhouettes.
    dome=np.exp(-(x/5.5)**2-((z-13)/4.5)**2)
    ripple=.018*np.sin(.65*x+.32*z)+.012*np.sin(.31*x-.57*z)
    return .10+.25*dome+ripple


class Winter:
    def __init__(self, size):
        self.size = size
        self.w, self.h = size
        # A pulled-back, elevated overview, like 2.png: see the circular branch
        # tops and the whole stage instead of looking up from beside the trunk.
        self.camera_distance=26.
        self.portrait=self.h>self.w
        self.focal = min(self.h*1.62,self.w*(2.50 if self.portrait else 1.50))
        self.cx, self.cy = self.w*.5, self.h*(.66 if self.portrait else .56)
        self.eye = 12.0
        self.pitch = .35
        self.cp, self.sp = math.cos(self.pitch), math.sin(self.pitch)
        self.yaw=.28
        self.yc,self.ys=math.cos(self.yaw),math.sin(self.yaw)
        self.eye_x=self.camera_distance*self.ys
        self.eye_z=13-self.camera_distance*self.yc
        self.rng = np.random.default_rng(1225)
        self.flakes = self.rng.random((1800, 8))
        self.atlas = self.make_atlas()
        self.sparkle_atlas=self.make_sparkles()
        self.base = self.build_ground()
        self.ascii = AsciiSurface(self.base,self.material,self.world_z)
        self.stage=RotatingStage(self)
        self.intro = ImpactIntro(self,height)
        self.tree = GrowingTree(self,height)
        self.finale = ChristmasFinale(self,height)
        self.greeting = ChristmasGreeting(size,start=COMPLETE)
        star=self.tree.rotate(self.finale.center[None,:],self.finale.yellow_start)[0]
        _,star_y,_=self.project(*star)
        sky_band=(self.greeting.bounds[0].centery,max(self.greeting.bounds[0].centery+self.h*.04,float(star_y)))
        self.fireworks = ChristmasFireworks(size, self.finale.yellow_start,sky_band)
        self.santa = SantaFlyby(size, COMPLETE)

    @staticmethod
    def rotate_stage(p,t):
        return rotate_stage(p,t)

    @staticmethod
    def stage_angle(t):
        return stage_angle(t)

    def project(self, x, y, z):
        rx=x-self.eye_x;rz=z-self.eye_z
        horizontal=rx*self.yc+rz*self.ys
        distance=-rx*self.ys+rz*self.yc
        rel_y = y-self.eye
        forward = distance*self.cp-rel_y*self.sp
        up = rel_y*self.cp+distance*self.sp
        safe = np.maximum(forward,.05)
        return self.cx+horizontal/safe*self.focal, self.cy-up/safe*self.focal, forward

    def unproject_z(self,sx,sy,z):
        right=(sx-self.cx)/self.focal
        up=(self.cy-sy)/self.focal
        local_z=up*self.sp+self.cp
        dx=right*self.yc-local_z*self.ys
        dz=right*self.ys+local_z*self.yc
        dy=up*self.cp-self.sp
        distance=(z-self.eye_z)/np.maximum(dz,1e-5)
        return np.stack([self.eye_x+dx*distance,self.eye+dy*distance,z],-1)

    def make_atlas(self):
        result=[]
        for px in (7,10,13):
            font=pygame.font.SysFont('consolas,cascadiamono,dejavusansmono,monospace',px)
            row=[]
            for c in ('.','+','*'):
                g=font.render(c,True,(226,235,247)).convert_alpha() if pygame.display.get_surface() else font.render(c,True,(226,235,247))
                row.append(g)
            result.append(row)
        return result

    def make_sparkles(self):
        result=[]
        for px in (9,13,17):
            font=pygame.font.SysFont('consolas,cascadiamono,dejavusansmono,monospace',px,bold=True)
            core=font.render('*',True,(245,252,255))
            size=px*3
            sprite=pygame.Surface((size,size),pygame.SRCALPHA)
            # Tiny ASCII satellite points and a soft icy halo, not large flares.
            for dx,dy in ((-px//2,0),(px//2,0),(0,-px//2),(0,px//2)):
                dot=font.render('.',True,(153,208,240));dot.set_alpha(95)
                sprite.blit(dot,dot.get_rect(center=(size//2+dx,size//2+dy)))
            sprite.blit(core,core.get_rect(center=(size//2,size//2)))
            result.append(sprite)
        return result

    def snow_twinkle(self,t):
        # Only a few flakes can glint, and each has a different rare bright peak.
        eligible=self.flakes[:,7]>.982
        phase=self.flakes[:,5]*math.tau*5
        pulse=np.maximum(0,np.sin(t*.95+phase))**18
        return np.where(eligible,pulse,0.)

    def build_ground(self):
        # Cast camera rays into the height field. This is a depth-bearing surface,
        # not horizontal bands or a screen-space silhouette mask.
        yy,xx=np.mgrid[:self.h,:self.w].astype(np.float32)
        screen_up=(self.cy-yy)/self.focal
        dy=screen_up*self.cp-self.sp
        local_z=screen_up*self.sp+self.cp
        local_x=(xx-self.cx)/self.focal
        dz=local_x*self.ys+local_z*self.yc
        dx=local_x*self.yc-local_z*self.ys
        distance=self.eye/np.maximum(-dy,.0001)
        for _ in range(7):
            wx=self.eye_x+dx*distance;wz=self.eye_z+dz*distance
            surface=height(wx,wz)
            distance=(self.eye-surface)/np.maximum(-dy,.0001)
        wx=self.eye_x+dx*distance;wz=self.eye_z+dz*distance
        # Finite oval stage in world space, with no straight horizon across the screen.
        stage_radius=np.sqrt((wx/8.6)**2+((wz-13)/5.2)**2)
        valid=(dy<-.012)&(wz>1)&(wz<65)&(stage_radius<1.16)
        h=height(wx,wz)
        eps=.035
        nx=-(height(wx+eps,wz)-h)/eps
        nz=-(height(wx,wz+eps)-h)/eps
        norm=np.sqrt(nx*nx+1+nz*nz)
        diffuse=np.clip((-.45*nx+.83-.32*nz)/norm,0,1)
        # Small ripples follow the world surface rather than the pixel grid.
        ripples=.5+.5*np.sin(wx*8+wz*3+1.4*np.sin(wz*2.7))
        grain=self.rng.random((self.h,self.w))
        shade=(.48+.46*diffuse+.035*ripples)*(.93+.07*grain)
        fade=np.clip((65-wz)/23,0,1)
        fade=fade*fade*(3-2*fade)
        edge=np.clip((1.16-stage_radius)/.32,0,1)
        edge=edge*edge*(3-2*edge)
        shade*=fade
        image=np.zeros((self.h,self.w,3),np.uint8)
        # Neutral white on top, only a small blue bias in shade.
        color=np.array([213,222,234],np.float32)
        image[valid]=np.clip(shade[valid,None]*color,0,255).astype(np.uint8)
        # Pointillist crust, inspired by flow.py's small round splats.
        # Each grain is positioned on the 3D surface and projected with perspective.
        n=int(np.clip(self.w*self.h*.07,35000,160000))
        z=np.exp(self.rng.uniform(np.log(3.5),np.log(65),n))
        half=z*(self.w/self.focal)*.59
        x=self.rng.uniform(-1,1,n)*half
        y=height(x,z)+self.rng.uniform(.002,.023,n)
        sx,sy,depth=self.project(x,y,z)
        radius=np.clip(self.focal/depth*self.rng.uniform(.006,.018,n),.55,3.1)
        e=.03
        surface_y=height(x,z)
        hx=-(height(x+e,z)-surface_y)/e
        hz=-(height(x,z+e)-surface_y)/e
        brightness=(.58+.40*np.clip((-.45*hx+.83-.32*hz)/np.sqrt(hx*hx+1+hz*hz),0,1))
        brightness*=self.rng.uniform(.83,1.06,n)
        grain_fade=np.clip((65-z)/23,0,1)
        brightness*=grain_fade*grain_fade*(3-2*grain_fade)
        palette=np.array([[245,247,250],[225,233,243],[201,215,233],[255,252,243]],float)
        colors=np.clip(palette[self.rng.integers(0,4,n)]*brightness[:,None],0,255).astype(np.uint8)
        order=np.argsort(-depth,kind='stable')
        self.splat(image,sx[order],sy[order],radius[order],colors[order])
        radial=(.32+.68*np.exp(-(stage_radius/.83)**6))*edge
        image=(image.astype(np.float32)*radial[:,:,None]).astype(np.uint8)
        # Keep every far/empty ray truly black; no speckles outside the snow terrain.
        image[~valid]=0
        self.depth=np.where(valid,distance*np.sqrt(dx*dx+dy*dy+dz*dz),np.inf)
        self.ground_mask=valid
        self.world_z=np.where(valid,wz,np.inf)
        self.material=np.zeros((self.h,self.w),np.uint8)
        image=self.stage_rim(image)
        image=add_ground_details(self,image,height)
        # A directional soft shadow and contact shade anchor the growing tree.
        contact=np.exp(-(wx/1.65)**2-((wz-13)/1.05)**2)
        along=(wx*.55+(wz-13)*.83)
        across=wx*.83-(wz-13)*.55
        cast=np.exp(-(across/(.9+np.maximum(along,0)*.16))**2)
        cast*=np.clip(along/.7,0,1)*np.exp(-np.maximum(along,0)/4.2)
        self.tree_shadow=np.clip((contact*.38+cast*.32)*valid,0,.55).astype(np.float32)
        return pygame.surfarray.make_surface(image.transpose(1,0,2))

    def stage_rim(self,image):
        # A rounded snow lip and shaded front wall give the disc actual thickness.
        rng=np.random.default_rng(815)
        n=16000;a=rng.uniform(0,math.tau,n);v=rng.random(n)
        x=8.6*1.07*np.cos(a);z=13+5.2*1.07*np.sin(a)
        top=height(x,z)
        y=top-.04-v*.36
        x*=1-.025*v
        z=13+(z-13)*(1-.025*v)
        sx,sy,d=self.project(x,y,z)
        ix=np.rint(sx).astype(int);iy=np.rint(sy).astype(int)
        on=(ix>=0)&(ix<self.w)&(iy>=0)&(iy<self.h)&(d>.1)
        k=np.flatnonzero(on);key=iy[k]*self.w+ix[k]
        order=np.lexsort((d[k],key));_,first=np.unique(key[order],return_index=True)
        k=k[order[first]];xx,yy=ix[k],iy[k]
        front=z[k]<self.world_z[yy,xx]+.01
        k,xx,yy=k[front],xx[front],yy[front]
        shade=(.24+.28*np.clip(-.6*np.cos(a[k])-.7*np.sin(a[k]),0,1))*(1-.5*v[k])
        image[yy,xx]=np.clip(np.array([170,196,223])*shade[:,None],0,255).astype(np.uint8)
        self.world_z[yy,xx]=z[k]
        self.material[yy,xx]=5
        self.ground_mask[yy,xx]=True
        return image

    @staticmethod
    def splat(image,x,y,radius,colors):
        h,w=image.shape[:2]
        xi=np.rint(x).astype(int);yi=np.rint(y).astype(int)
        # Loop over a small stamp, not over hundreds of thousands of grains.
        for oy in range(-3,4):
            for ox in range(-3,4):
                ok=((ox*ox+oy*oy)<=radius*radius)&(xi+ox>=0)&(xi+ox<w)&(yi+oy>=0)&(yi+oy<h)
                image[yi[ok]+oy,xi[ok]+ox]=colors[ok]

    def snow_positions(self,t):
        a=self.flakes
        z=3.2+a[:,2]**1.7*51
        half=z*(self.w/self.focal)*.62
        drift=.18*t+.30*np.sin(t*.23)
        x=((a[:,0]*2-1)*half+drift*(.6+a[:,4])
           +.13*np.sin(t*(.5+a[:,5])+a[:,6]*math.tau))
        x=(x+half)%(2*half)-half
        floor=height(x,z)
        ceiling=20 if self.portrait else 10
        drop=ceiling-floor
        y=ceiling-(a[:,1]*drop+t*(.38+.35*a[:,3]))%drop
        return x,y,z

    def render(self,t):
        frame=self.intro.render(t) if t<FINISH else self.stage.render(t)
        if t>=START:
            self.tree.draw(frame,t)
            self.finale.draw_glow(frame,t)
        if t>=self.fireworks.start:
            background=pygame.Surface(self.size)
            self.fireworks.draw(background,t)
            # Fill each depth-bearing silhouette row, including gaps between glyphs.
            # This prevents distant sparks from showing through the tree's letters.
            blocked=np.isfinite(self.tree.depth)|np.isfinite(self.stage.cell_z)
            for row in blocked:
                occupied=np.flatnonzero(row)
                if len(occupied):row[occupied[0]:occupied[-1]+1]=True
            mask=pygame.surfarray.make_surface(np.repeat(blocked.T[:,:,None]*255,3,axis=2).astype(np.uint8))
            mask=pygame.transform.scale(mask,(self.ascii.cols*6,self.ascii.rows*9))
            background.blit(mask,(0,0),special_flags=pygame.BLEND_RGB_SUB)
            frame.blit(background,(0,0),special_flags=pygame.BLEND_RGB_ADD)
        x,y,z=self.snow_positions(t)
        sx,sy,depth=self.project(x,y,z)
        visible=(sx>=0)&(sx<self.w)&(sy>=0)&(sy<self.h)&(depth>.1)
        indices=np.flatnonzero(visible)
        twinkle=self.snow_twinkle(t)
        # Far-to-near flakes make the same physical fall faster/larger nearby.
        for k in indices[np.argsort(-depth[indices])]:
            px,py=int(sx[k]),int(sy[k])
            if t>=FINISH:
                row=min(self.ascii.rows-1,py//9);col=min(self.ascii.cols-1,px//6)
                if z[k]>self.stage.cell_z[row,col]+.06:continue
            if t>=START:
                row=min(self.ascii.rows-1,py//9);col=min(self.ascii.cols-1,px//6)
                if z[k]>self.tree.depth[row,col]+.04:continue
            layer=2 if depth[k]<8 else 1 if depth[k]<19 else 0
            kind=2 if self.flakes[k,7]>.90 else 1 if self.flakes[k,7]>.68 else 0
            glyph=self.atlas[layer][kind]
            # Dim the far layers, retain a clean white foreground.
            alpha=int(np.clip(265-depth[k]*3.5,70,245))
            glyph.set_alpha(alpha)
            frame.blit(glyph,(px-glyph.get_width()//2,py-glyph.get_height()//2))
            if twinkle[k]>.16:
                spark=self.sparkle_atlas[layer]
                spark.set_alpha(int(80+175*twinkle[k]))
                frame.blit(spark,spark.get_rect(center=(px,py)))
        self.greeting.draw(frame,t)
        self.santa.draw(frame,t)
        return frame
