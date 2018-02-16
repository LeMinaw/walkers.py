"""Module for drawing pictures from walkers walking towards each other."""

import os
import pickle
from colormaps import ColorMap, black
from utils     import lin_interp, is_sequence, clamp
from math      import sqrt

class Walker():
    """Class representating a walker object."""

    def __init__(self, position=(0, 0, 0)):
        """Creates a new Walker.
        - position: (x, y, z)"""
        self.start_position = tuple(position)
        self.position       = list(position)

    def __str__(self):
        """Simple informal string representation."""
        return "Walker at %s" % str(self.position)

    def __repr__(self):
        """Reliable object representation."""
        return "Walker %s" % id(self)

    def distance_from(self, other):
        return sqrt(sum([(other.position[i] - self.position[i]) ** 2 for i in range(len(self.position))]))


class WalkingSystem:
    """Class representing a system of walkers walking to each other."""

    def __init__(self, walkers, iterations=100, cmap=black):
        """Creates a new system.
        - walkers: A dict describing Walkers and relations they have:
        {
            walker_1: {                walker_2: 0.2, walker_3: 0.5},
            walker_2: {walker_1: -0.2,                walker_3: 0.3},
            walker_3: {walker_1:  0.1, walker_2: 0.3               }
        }
        Positive value is attraction, and negative is repulsion.
        Omitting a key is permitted and is equivalent to a value of 0.
        Values superior to 1 or inferior to -1 are likely to do funky things.
        - iterations: The number of iterations on wich this system is defined.
        - cmap: ColorMap for plotting rings."""
        self.walkers    = walkers
        self.iterations = iterations
        self.cmap       = cmap
        self.curves, self.rings = None, None

    @property
    def curves(self):
        if self.__curves is None:
            raise ValueError("No curves vectrices values found."
                "Please use compute_3d_vectrices() first.")
        return self.__curves

    @curves.setter
    def curves(self, crvs): self.__curves = crvs

    @property
    def rings(self):
        if self.__rings is None:
            raise ValueError("No rings vectrices values found."
                "Please use compute_3d_vectrices() first.")
        return self.__rings

    @rings.setter
    def rings(self, rngs): self.__rings = rngs

    def __str__(self):
        """Simple informal string representation."""
        return "Walking system: %s" % str([str(wlkr) for wlkr in self.walkers])

    def __repr__(self):
        """Reliable object representation."""
        return "WalkingSystem_%s" % id(self)

    def save(self, name=None, path=''):
        """Saves this WalkingSystem to filesystem."""
        if not name:
            name = repr(self) + '.pkl'
        to_save = copy(self)
        to_save.rings  = None # Don't save rings and curves vectrices data,
        to_save.curves = None # to save disk space and forward compatibility
        with open(path + name, 'wb') as f:
            pickle.dump(to_save, f, pickle.HIGHEST_PROTOCOL)
        return

    @staticmethod
    def load(path=''):
        """Creates a new WalkingSystem by loading it from filesystem."""
        with open(path, 'rb') as f:
            return pickle.load(f)

    def get_current_state(self):
        """Returns current system state."""
        return tuple([wlkr.position for wlkr in self.walkers])

    def next_state(self):
        """Computes and returns the next system state."""
        for wlkr, relations in self.walkers.items():
            pos = wlkr.position
            for related_wlkr, relation in relations.items():
                for i in range(len(pos)):
                    pos[i] += (related_wlkr.position[i] - pos[i]) * (relation)
            wlkr.position = pos
        return self.get_current_state()

    def states(self):
        """Return a generator yielding the states of the walkers."""
        for iteration in range(self.iterations):
            yield self.get_current_state()
            self.next_state()

    def compute_3d_vectrices(self):
        """Computes, stores and returns 3d vectrices data."""
        curves = tuple([[[] for j in range(3)] for i in range(len(self.walkers))])
        rings = []

        for state in self.states():
            ring = [[] for i in range(3)]
            for i, position in enumerate(state):
                for j, coord in enumerate(position):
                    curves[i % len(self.walkers)][j % 3].append(coord)
                    ring[j % 3].append(coord)

            for i in range(len(ring)): # Adds a segment at the end of each ring
                ring[i].append(ring[i][0])
            rings.append(ring)

        self.curves = curves
        self.rings  = rings
        return curves, rings

    def plot(self, engine='pyplot', iterations=None):
        """Plots the system using a specified render engine.
        Needs compute_3d_vectrices() to be called before.
        - engine: String for the render engine. Can be 'visvis' or 'pyplot'.
        visvis is faster, but pyplot is nicer.
        - iterations: Limits the plotting to this number of iterations.
        If None, the whole system states will be plotted."""
        engine = engine.lower()
        if iterations is None:
            iterations = self.iterations
        elif iterations > self.iterations:
            raise ValueError("Unable to plot %s out of %s iterations"
                % (iterations, self.iterations))

        if engine == 'visvis':
            try:
                import visvis as vv
            except ImportError:
                raise ImportError("visvis must be installed in order to use it."
                "Try to 'pip install visvis' in a command line.")
            app = vv.use()
            fig = vv.clf()
            ax  = vv.cla()

        elif engine == 'pyplot':
            try:
                import matplotlib.pyplot as plt
                from mpl_toolkits.mplot3d import Axes3D
            except ImportError:
                raise ImportError("pyplot must be installed in order to use it."
                "Try to 'pip install matplotlib' in a command line.")
            fig = plt.figure(figsize=(32, 18), dpi=100)
            ax = fig.gca(projection='3d')
            ax.set_axis_off()

        else:
            raise ValueError("%s is not a supported render engine." % engine)


        rings  = self.rings[:iterations]
        for i, ring in enumerate(rings):
            color = self.cmap(i, 0, len(self.rings) / 2, 1)
            if engine == 'visvis':
                vv.plot(*ring, lc=color, mw=0, alpha=.2)
            else:
                ax.plot(*ring, c=color+(.4,)) # Adding alpha as (r, g, b, a)

        curves = [curve[:iterations] for curve in self.curves]
        for curve in curves:
            if engine == 'visvis':
                vv.plot(*curve, lc='k', mw=0, lw=2)
            else:
                ax.plot(*curve, c=(0, 0, 0, .8))

        if engine == 'visvis':
            ax = vv.gca()
            app.Run()
            return

        else:
            fig.tight_layout()
            # plt.draw()
            mng = plt.get_current_fig_manager()
            mng.full_screen_toggle()
            plt.show()
            return

    # def animation(self):
    #     path = "stuff{:04d}/".format(randint(0, 9999))
    #     if os.path.isdir(path):
    #         raise ValueError("Dir already exists")
    #     os.makedirs(path)
    #
    #     for iteration in range(self.iterations):
    #         ax.view_init(lin_interp(iteration, 0, states, 0, 5), lin_interp(iteration, 0, states, 0, 40))
    #
    #         lim = lin_interp(iteration, 0, states, 100, 150)
    #         ax.set_xlim3d(-lim, lim)
    #         ax.set_ylim3d(-lim, lim)
    #         ax.set_zlim3d(-lim, lim)
    #
    #         name = "{:04d}.png".format(iteration)
    #         print("saving %s..." % path + name)
    #         fig.savefig(path + name, dpi=100)
    #         plt.cla()

if __name__ == '__main__':
    from random import randint, random, shuffle
    from utils import shuffled
    from colormaps import red_to_black, cyan_to_red

    #-----------------------------[FIRST EXEMPLE]--------------------------------#
    #       Manually building the ColorMap, the Walkers, and their system        #
    #----------------------------------------------------------------------------#

    # cmap = ColorMap((255, 0, 0),(255, 220, 0)

    # w1 = Walker((-10,  50, -70))
    # w2 = Walker((-20,  70, -50))
    # w3 = Walker(( 0,   50, -40))
    # w4 = Walker(( 20, -40,  0))

    # sys = WalkingSystem({
    #     w1: {        w2: .1,  w3:-.15, w4: .2},
    #     w2: {w1: .1,          w3: .1,  w4:-.1},
    #     w3: {w1: .1, w2: .03,          w4:-.1},
    #     w4: {w1:-.1, w2: .1,  w3: .03        }
    # }, iterations=100, cmap=cmap)

    #----------------------------[SECOND EXEMPLE]--------------------------------#
    # Random based generation for the ColorMap, the Walkers, and their relations #
    #----------------------------------------------------------------------------#

    def crd(): return randint(-170, 170)          # Random coord for walker init
    def rel(): return (random() - .3) / 20        # Random relation factor
    def cmp(): return randint(0, 255)             # Random 8-bit color composant
    def col(): return shuffled([cmp(), cmp(), 0]) # Random color for cmap

    cmap = ColorMap(col(), col())
    walkers = [Walker((crd(), crd(), crd())) for i in range(8)]
    rels = {wlkr: {rel_wlkr: rel() for rel_wlkr in walkers if rel_wlkr is not wlkr} for wlkr in walkers}
    sys = WalkingSystem(rels, iterations=80, cmap=cmap)

    #----------------------------[THIRD] EXEMPLE]--------------------------------#
    #          Loading a previously saved WalkingSystem from file system         #
    #----------------------------------------------------------------------------#

    # sys = WalkingSystem.load("last-system.pkl")

    #----------------------------------------------------------------------------#

    sys.save("last-system.pkl")
    sys.compute_3d_vectrices()
    sys.plot()
    # sys.plot('visvis')
