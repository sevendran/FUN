"""One shared, clockwise rigid transform for snow, props, tree and ornaments."""

import math
import numpy as np


ROTATION_START=1.08
ANGULAR_SPEED=.095


def angle(t):
    # Positive x travels toward positive z: clockwise in the x/right, z/down top view.
    return max(0.,t-ROTATION_START)*ANGULAR_SPEED


def rotate(p,t):
    a=angle(t);c,s=math.cos(a),math.sin(a)
    p=np.asarray(p)
    q=p.copy();x=p[:,0];z=p[:,2]-13.
    q[:,0]=x*c-z*s;q[:,2]=13.+x*s+z*c
    return q
