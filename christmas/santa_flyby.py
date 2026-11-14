"""ASCII Santa sleigh flyby that writes the Christmas greeting."""

import math
import numpy as np
import pygame

DURATION = 7.0


def reveal_front(age):
    return float(np.clip(age / DURATION, 0, 1)) * 1.9 - .30


class SantaFlyby:
    def __init__(self, size, start):
        self.w, self.h = size
        self.start = start
        self.width = round(self.w * (.56 if self.h > self.w else .34))
        self.poses = [self.make_pose(i) for i in range(2)]
        font=pygame.font.SysFont("consolas,monospace",9)
        self.trail=[font.render(".",True,(150-i*6,100-i*4,35)) for i in range(18)]

    def make_pose(self, pose):
        src = pygame.Surface((360, 110))
        red=(235,49,58);gold=(255,194,78);white=(255,244,223)
        brown=(183,119,65)
        # Sleigh runners, curved prow, body, and gold trim.
        pygame.draw.lines(src,gold,False,[(9,91),(21,100),(112,100),(133,91),(136,83)],3)
        pygame.draw.line(src,gold,(33,84),(28,99),2)
        pygame.draw.line(src,gold,(103,82),(109,99),2)
        pygame.draw.polygon(src,red,[(12,65),(40,65),(53,78),(106,78),(122,52),(135,50),(128,79),(110,90),(29,88)])
        pygame.draw.lines(src,gold,False,[(14,65),(40,65),(53,78),(106,78),(122,52),(135,50)],3)
        # Gift sack and wrapped parcels behind Santa.
        pygame.draw.ellipse(src,(129,97,48),(17,35,36,39))
        pygame.draw.rect(src,(47,156,90),(24,48,21,23))
        pygame.draw.line(src,gold,(34,48),(34,71),3)
        # Santa: coat, belt, face, white beard, red hat and pom-pom.
        pygame.draw.ellipse(src,red,(54,42,43,37))
        pygame.draw.line(src,white,(57,75),(94,75),4)
        pygame.draw.line(src,(35,29,29),(57,65),(94,65),4)
        pygame.draw.rect(src,gold,(74,62,7,7),2)
        pygame.draw.circle(src,(255,193,154),(78,34),12)
        pygame.draw.polygon(src,white,[(65,34),(68,50),(79,58),(91,45),(91,35),(80,41)])
        pygame.draw.polygon(src,red,[(65,25),(77,8),(94,13),(101,24),(86,20),(89,28)])
        pygame.draw.line(src,white,(65,26),(91,28),4)
        pygame.draw.circle(src,white,(101,24),4)
        pygame.draw.line(src,red,(91,48),(109,60),8)
        pygame.draw.circle(src,white,(111,60),4)
        # Reins run to two flying reindeer, led by Rudolph's red nose.
        pygame.draw.lines(src,gold,False,[(110,60),(173,70),(242,51),(322,49)],1)
        for n,x in enumerate((176,272)):
            y=48-n*8
            pygame.draw.ellipse(src,brown,(x,y,48,21))
            pygame.draw.line(src,brown,(x+37,y+9),(x+48,y-12),9)
            pygame.draw.ellipse(src,brown,(x+43,y-20,24,13))
            pygame.draw.polygon(src,brown,[(x+47,y-17),(x+42,y-29),(x+53,y-22)])
            pygame.draw.line(src,gold,(x+49,y-20),(x+44,y-38),2)
            pygame.draw.line(src,gold,(x+45,y-29),(x+36,y-33),2)
            pygame.draw.line(src,gold,(x+45,y-31),(x+51,y-38),2)
            pygame.draw.line(src,brown,(x+3,y+5),(x-8,y-3),3)
            for leg,dx in enumerate((7,16,33,41)):
                step=(1 if (leg+pose)%2 else -1)*10
                pygame.draw.lines(src,brown,False,[(x+dx,y+15),(x+dx+step,y+27),(x+dx+step+9,y+30)],3)
            pygame.draw.line(src,red,(x+41,y-4),(x+50,y),3)
            pygame.draw.circle(src,white,(x+59,y-16),1)
            if n==1:
                pygame.draw.circle(src,(255,45,50),(x+68,y-14),4)
        # Convert every visible part to colored ASCII, including the reins.
        size=(max(120,self.width),max(36,round(self.width*110/360)))
        src=pygame.transform.smoothscale(src,size)
        cw,ch=3,4
        cols,rows=size[0]//cw,size[1]//ch
        rgb=pygame.surfarray.array3d(src)[:cols*cw,:rows*ch].transpose(1,0,2)
        blocks=rgb.reshape(rows,ch,cols,cw,3).transpose(0,2,1,3,4)
        color=blocks.max((2,3))
        out=pygame.Surface((cols*cw,rows*ch),pygame.SRCALPHA)
        font=pygame.font.SysFont('consolas,monospace',6,bold=True)
        for r,c in zip(*np.nonzero(color.max(2)>40)):
            glyph=font.render('*+#:'[(r*7+c*3)%4],True,tuple(color[r,c]))
            out.blit(glyph,(c*cw,r*ch))
        return out

    def draw(self, frame, t):
        age=t-self.start
        if not 0<=age<=DURATION:return
        sprite=self.poses[int(age*7)%2]
        nose=reveal_front(age)*self.w
        x=nose-sprite.get_width()
        y=self.h*(.075 if self.h>self.w else .125)+math.sin(age*2)*self.h*.006
        # A short golden character trail follows the sleigh.
        for i in range(18):
            px=x-i*7
            py=y+sprite.get_height()*.8+math.sin(age*4+i)*5
            if px>=0:
                dot=self.trail[i]
                frame.blit(dot,(round(px),round(py)))
        frame.blit(sprite,(round(x),round(y)))
