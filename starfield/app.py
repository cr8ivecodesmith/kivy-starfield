__all__ = ('StarfieldApp',)

import math
from random import random

import kivy

kivy.require('1.9.0')

from kivy.app import App
from kivy.core.image import Image
from kivy.base import EventLoop
from kivy.clock import Clock
from kivy.graphics import Mesh
from kivy.graphics.instructions import RenderContext
from kivy.uix.widget import Widget


NSTARS = 1000


class Star(object):
    """ Helper class to encapsulate operating on a single star.

    Args:

    sf (obj) - Reference to the StarField widget.
    i (int) - Reference to this star's index as per NSTARS. This is used to
        calculate for `base_idx` which is the index of this star's first vertex
        in the array of vertices in `sf`.

    """
    angle = 0
    distance = 0
    size = 0.1

    def __init__(self, sf, i):
        self.sf = sf
        self.base_idx = 4 * i * sf.vsize

        # The star initializes somewhere around the center of the screen.
        self.reset()

    def reset(self):
        """ Revert attributes to a slightly randomized default.

        """
        self.angle = 2 * math.pi * random()
        self.distance = 90 * random() + 10
        self.size = 0.05 * random() + 0.05

    def iterate(self):
        return range(
            self.base_idx,
            self.base_idx + 4 * self.sf.vsize,
            self.sf.vsize
        )

    def update(self, x0, y0):
        """ Refresh the 4 vertices belonging to a star in the vertices array.

        """
        x = x0 + self.distance * math.cos(self.angle)
        y = y0 + self.distance * math.sin(self.angle)

        for i in self.iterate():
            self.sf.vertices[i:i + 3] = (x, y, self.size)


class Starfield(Widget):
    def __init__(self, **kwargs):
        super(Starfield, self).__init__(**kwargs)
        self.canvas = RenderContext(use_parent_projection=True)
        self.canvas.shader.source = 'starfield.glsl'

        self.vfmt = (
            (b'vCenter', 2, 'float'),     #  Denotes the star's center point on
                                          #  the screen.

            (b'vScale', 1, 'float'),      #  The star's scale factor. 1 being
                                          #  the original size (48x48 px)

            (b'vPosition', 2, 'float'),   #  Position of each vertex relative
                                          #  to the star's center point.

            (b'vTexCoords0', 2, 'float'), #  Refers to texture coordinates.
        )

        # Note the length of a single vertex in the array of vertices
        self.vsize = sum(attr[1] for attr in self.vfmt)

        self.indices = []
        for i in range(0, 4 * NSTARS, 4):
            self.indices.extend((
                i, i + 1, i + 2, i + 2,
                i + 2, i + 3, i
            ))

        # Essentially, the vertices contain all the data about our stars that
        # we need to retain, however this is not ideal to operate on.
        # So instead, we create a `Star()` class to encapsulate the operations
        # and computations. It will also contain additional properties such as
        # size, angle, distance from center, etc.
        self.vertices = []
        for i in range(NSTARS):
            self.vertices.extend((
                0, 0, 1, -24, -24, 0, 1,
                0, 0, 1, 24, -24, 1, 1,
                0, 0, 1, 24, 24, 1, 0,
                0, 0, 1, -24, 24, 0, 0,
            ))

        self.texture = Image('assets/star.png').texture
        self.stars = [Star(self, i) for i in range(NSTARS)]

    def update_glsl(self, nap):
        """ Implement the starfield motion algorithm.

        """
        # Determine the max distance a star will travel based on the starfield
        # widget's center.
        x0, y0 = self.center
        max_distance = 1.1 * max(x0, y0)

        for star in self.stars:
            # We then move the stars towards the max_distance, enlarging it at
            # the same time. When it reaches the max_distance, we reset it.
            star.distance *= 2 * nap + 1
            star.size += 0.25 * nap

            if star.distance > max_distance:
                star.reset()
            else:
                star.update(x0, y0)

        # Finally we draw them on the canvas
        self.canvas.clear()
        with self.canvas:
            Mesh(fmt=self.vfmt, mode='triangles', indices=self.indices,
                 vertices=self.vertices, texture=self.texture)


class StarfieldApp(App):
    def build(self):
        EventLoop.ensure_window()
        return Starfield()

    def on_start(self):
        Clock.schedule_interval(self.root.update_glsl, 1 / 60.0)
