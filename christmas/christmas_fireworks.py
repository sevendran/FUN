"""Distant ASCII fireworks with randomized Christmas silhouettes and colors."""

import math
import numpy as np
import pygame

SHAPES = ('circle', 'heart', 'stocking', 'cookie', 'snowman', 'snowflake', 'bell', 'gingerbread')
PALETTES = (
    ((255,191,48),(255,104,29)), ((255,63,94),(255,159,177)),
    ((89,224,255),(209,247,255)), ((76,230,137),(214,255,123)),
    ((190,114,255),(255,170,244)), ((255,228,152),(255,255,238)),
    ((255,137,71),(255,222,96)), ((94,147,255),(175,237,255)),
)


def silhouette(kind):
    """Sample procedural outlines; only ASCII particles reach the final frame."""
    pieces=[]
    def path(points, closed=False):
        if closed:points=points+[points[0]]
        for a,b in zip(points,points[1:]):
            a,b=np.array(a),np.array(b)
            count=max(2,round(np.linalg.norm(b-a)*24))
            pieces.append(a+(b-a)*np.linspace(0,1,count,endpoint=False)[:,None])
    def ring(x,y,rx,ry=None):
        a=np.linspace(0,math.tau,max(16,round(rx*85)),endpoint=False)
        pieces.append(np.stack((x+rx*np.cos(a),y+(rx if ry is None else ry)*np.sin(a)),1))
    if kind=='circle':
        for r in (.55,.78,1.):ring(0,0,r)
    elif kind=='heart':
        a=np.linspace(0,math.tau,110,endpoint=False)
        pieces.append(np.stack((np.sin(a)**3,-(13*np.cos(a)-5*np.cos(2*a)-2*np.cos(3*a)-np.cos(4*a))/16),1))
    elif kind=='stocking':
        path([(-.48,-.9),(.28,-.9),(.28,.24),(.77,.32),(.92,.57),(.78,.83),(.08,.9),(-.38,.66),(-.48,.37)],True)
        path([(-.48,-.62),(.28,-.62)])
        path([(.3,.29),(.2,.62),(.08,.9)])
    elif kind=='cookie':
        a=np.linspace(0,math.tau,110,endpoint=False);r=.86+.045*np.sin(a*14)
        pieces.append(np.stack((r*np.cos(a),r*np.sin(a)),1))
        for x,y in ((-.3,-.37),(.3,-.25),(-.4,.22),(.22,.4),(0,0)):
            ring(x,y,.075)
    elif kind=='snowman':
        ring(0,.48,.50,.47);ring(0,-.18,.36,.34);ring(0,-.69,.25,.24)
        path([(-.33,-.9),(.33,-.9)]);path([(-.22,-.91),(-.22,-1.1),(.2,-1.1),(.2,-.91)])
        path([(-.30,-.02),(.30,-.02),(.30,.1),(-.30,.1)],True)
        path([(.08,-.68),(.34,-.63),(.08,-.60)],True)
        for y in (.3,.5,.7):ring(0,y,.035)
        for side in (-1,1):
            path([(side*.38,.25),(side*.78,-.02),(side*.91,.01)])
            path([(side*.73,.02),(side*.77,-.15)])
    elif kind=='snowflake':
        for a in np.arange(6)*math.tau/6:
            v=np.array([math.cos(a),math.sin(a)])
            normal=np.array([-v[1],v[0]])
            path([(0,0),tuple(v)])
            for d in (.48,.76):
                for sign in (-1,1):path([tuple(v*d),tuple(v*(d-.22)+normal*.22*sign)])
    elif kind=='bell':
        path([(-.77,.55),(-.51,.23),(-.42,-.42),(-.25,-.72),(0,-.81),(.25,-.72),(.42,-.42),(.51,.23),(.77,.55)],True)
        path([(-.77,.55),(-.71,.70),(.71,.70),(.77,.55)])
        ring(0,.78,.15,.13);ring(0,-.94,.13)
        path([(-.1,-.75),(-.5,-.97),(-.48,-.63),(0,-.76),(.48,-.97),(.5,-.63)],True)
    else:
        ring(0,-.64,.29,.30)
        path([(-.23,-.35),(-.64,-.48),(-.83,-.26),(-.42,.05),(-.36,.26),(-.60,.77),(-.35,.94),(0,.46),(.35,.94),(.60,.77),(.36,.26),(.42,.05),(.83,-.26),(.64,-.48),(.23,-.35)])
        for y in (-.03,.18):ring(0,y,.045)
        path([(-.12,-.53),(0,-.46),(.12,-.53)])
    return np.concatenate(pieces)


class ChristmasFireworks:
    INTERVAL=1.5
    LIFETIME=5.1

    def __init__(self,size,start,sky_band=None):
        self.w,self.h=size;self.start=start
        self.sky_band=sky_band or (self.h*.07,self.h*.24)
        self.scale=min(self.w/1080,self.h/1080)
        self.font=pygame.font.SysFont('consolas,cascadiamono,dejavusansmono,monospace',max(7,round(10*self.scale)),bold=True)
        self.glyphs={};self.events={}
        self.outlines={kind:silhouette(kind) for kind in SHAPES}

    def event(self,index):
        if index not in self.events:
            rng=np.random.default_rng(251225+index)
            kind=str(rng.choice(SHAPES))
            palette=int(rng.integers(len(PALETTES)))
            if kind=='heart':palette=1
            lo,hi=sorted(self.sky_band)
            cy=float(rng.uniform(lo,hi))
            radius=min(self.w*rng.uniform(.065,.13),self.h*rng.uniform(.045,.077))
            # Any horizontal position, including directly behind the top of the tree.
            cx=float(rng.uniform(radius*1.15,self.w-radius*1.15))
            cy=max(radius*1.18+self.h*.01,cy)
            points=self.outlines[kind].copy()
            points*=rng.uniform(.985,1.015,(len(points),1))
            launch=float(rng.uniform(.65,1.25))
            origin=float(np.clip(cx+rng.uniform(-.17,.17)*self.w,self.w*.05,self.w*.95))
            self.events[index]=dict(cx=cx,cy=cy,radius=radius,points=points,
                energy=rng.uniform(.72,1.,len(points)),kind=kind,palette=palette,
                launch=launch,origin=origin,fall=float(rng.uniform(.012,.027)))
        return self.events[index]

    def point(self,frame,x,y,char,palette,brightness,accent=False):
        if brightness<=.018:return
        level=max(1,min(7,round(brightness*7)))
        key=(char,palette,level,accent)
        if key not in self.glyphs:
            color=PALETTES[palette][int(accent)]
            self.glyphs[key]=self.font.render(char,True,tuple(round(c*level/7) for c in color))
        sprite=self.glyphs[key]
        frame.blit(sprite,sprite.get_rect(center=(round(x),round(y))),)

    def draw(self,frame,t):
        elapsed=t-self.start
        if elapsed<0:return
        latest=int(elapsed/self.INTERVAL)
        first=max(0,latest-math.ceil(self.LIFETIME/self.INTERVAL))
        for old in list(self.events):
            if old<first:del self.events[old]
        for index in range(first,latest+1):
            age=elapsed-index*self.INTERVAL
            if age>=self.LIFETIME:continue
            e=self.event(index)
            cx,cy,r=e['cx'],e['cy'],e['radius']
            launch=e['launch'];palette=e['palette']
            if age<launch:
                for tail in range(10):
                    u=max(0,age/launch-tail*.026)
                    x=e['origin']+(cx-e['origin'])*u
                    y=cy+self.h*.32*(1-u)**1.6
                    self.point(frame,x,y,'+' if tail==0 else '.',palette,(1-tail/11)*.8,True)
                continue
            burst=age-launch
            fade=max(0,1-burst/(self.LIFETIME-launch))**1.1
            for k,(vx,vy) in enumerate(e['points']):
                for trail in (1,0):
                    past=max(0,burst-trail*.075)
                    spread=1-math.exp(-past*3.1)
                    # Briefly hold the recognizable outline, then drift down gently.
                    scatter=max(0.,past-1.25)**1.5
                    x=cx+r*vx*spread+math.sin(k*17.3)*r*.075*scatter
                    y=cy+r*vy*spread+r*e['fall']*past**2+math.cos(k*11.7)*r*.06*scatter
                    sparkle=.75+.25*math.sin(k*7.1+burst*10)**2
                    char='.' if trail else '*+:'[(k+int(burst*7))%3]
                    self.point(frame,x,y,char,palette,fade*e['energy'][k]*sparkle*(.22 if trail else .85),k%5==0)
            if burst<.16:
                self.point(frame,cx,cy,'*',palette,1-burst/.16,True)
