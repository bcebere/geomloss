"""
Gradient flows in 2D
====================

Let's showcase the properties of **kernel MMDs**, **Hausdorff**
and **Sinkhorn** divergences on a simple toy problem:
the registration of one blob onto another.
"""


##############################################
# Setup
# ---------------------

import numpy as np
import matplotlib.pyplot as plt
import time

import torch
from geomloss import SamplesLoss

use_cuda = torch.cuda.is_available()
dtype = torch.cuda.FloatTensor if use_cuda else torch.FloatTensor

###############################################
# Display routine
# ~~~~~~~~~~~~~~~~~


import numpy as np
import torch
from random import choices
from imageio import imread
from matplotlib import pyplot as plt


def load_image(fname):
    img = imread(fname, as_gray=True)  # Grayscale
    img = (img[::-1, :]) / 255.0
    return 1 - img


def draw_samples(fname, n, dtype=torch.FloatTensor):
    A = load_image(fname)
    xg, yg = np.meshgrid(
        np.linspace(0, 1, A.shape[0]),
        np.linspace(0, 1, A.shape[1]),
        indexing="xy",
    )

    grid = list(zip(xg.ravel(), yg.ravel()))
    dens = A.ravel() / A.sum()
    dots = np.array(choices(grid, dens, k=n))
    dots += (0.5 / A.shape[0]) * np.random.standard_normal(dots.shape)

    return torch.from_numpy(dots).type(dtype)


def display_samples(ax, x, color):
    x_ = x.detach().cpu().numpy()
    ax.scatter(x_[:, 0], x_[:, 1], 25 * 500 / len(x_), color, edgecolors="none")


###############################################
# Dataset
# ~~~~~~~~~~~~~~~~~~
#
# Our source and target samples are drawn from intervals of the real line
# and define discrete probability measures:
#
# .. math::
#   \alpha ~=~ \frac{1}{N}\sum_{i=1}^N \delta_{x_i}, ~~~
#   \beta  ~=~ \frac{1}{M}\sum_{j=1}^M \delta_{y_j}.

N, M = (100, 100) if not use_cuda else (10000, 10000)

X_i = draw_samples("data/density_a.png", N, dtype)
Y_j = draw_samples("data/density_b.png", M, dtype)


###############################################
# Wasserstein gradient flow
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# To study the influence of the :math:`\text{Loss}` function in measure-fitting
# applications, we perform gradient descent on the positions
# :math:`x_i` of the samples that make up :math:`\alpha`
# as we minimize the cost :math:`\text{Loss}(\alpha,\beta)`.
# This procedure can be understood as a discrete (Lagrangian)
# `Wasserstein gradient flow <https://arxiv.org/abs/1609.03890>`_
# and as a "model-free" machine learning program, where
# we optimize directly on the samples' locations.


def gradient_flow(loss, lr=0.05):
    """Flows along the gradient of the cost function, using a simple Euler scheme.

    Parameters:
        loss ((x_i,y_j) -> torch float number):
            Real-valued loss function.
        lr (float, default = .05):
            Learning rate, i.e. time step.
    """

    # Parameters for the gradient descent
    Nsteps = int(5 / lr) + 1
    display_its = [int(t / lr) for t in [0, 0.25, 0.50, 1.0, 2.0, 5.0]]

    # Use colors to identify the particles
    colors = (10 * X_i[:, 0]).cos() * (10 * X_i[:, 1]).cos()
    colors = colors.detach().cpu().numpy()

    # Make sure that we won't modify the reference samples
    x_i, y_j = X_i.clone(), Y_j.clone()

    # We're going to perform gradient descent on Loss(α, β)
    # wrt. the positions x_i of the diracs masses that make up α:
    x_i.requires_grad = True

    t_0 = time.time()
    plt.figure(figsize=(12, 8))
    k = 1
    for i in range(Nsteps):  # Euler scheme ===============
        # Compute cost and gradient
        L_αβ = loss(x_i, y_j)
        [g] = torch.autograd.grad(L_αβ, [x_i])

        if i in display_its:  # display
            ax = plt.subplot(2, 3, k)
            k = k + 1
            plt.set_cmap("hsv")
            plt.scatter(
                [10], [10]
            )  # shameless hack to prevent a slight change of axis...

            display_samples(ax, y_j, [(0.55, 0.55, 0.95)])
            display_samples(ax, x_i, colors)

            ax.set_title("t = {:1.2f}".format(lr * i))

            plt.axis([0, 1, 0, 1])
            plt.gca().set_aspect("equal", adjustable="box")
            plt.xticks([], [])
            plt.yticks([], [])
            plt.tight_layout()

        # in-place modification of the tensor's values
        x_i.data -= lr * len(x_i) * g
    plt.title(
        "t = {:1.2f}, elapsed time: {:.2f}s/it".format(
            lr * i, (time.time() - t_0) / Nsteps
        )
    )


###############################################
# Kernel norms, MMDs
# ------------------------------------
#
# Gaussian MMD
# ~~~~~~~~~~~~~~~
#
# The smooth Gaussian kernel
# :math:`k(x,y) = \exp(-\|x-y\|^2/2\sigma^2)`
# is blind to details which are smaller than the blurring scale :math:`\sigma`:
# its gradient stops being informative when :math:`\alpha`
# and :math:`\beta` become equal "up to the high frequencies".

gradient_flow(SamplesLoss("gaussian", blur=0.5))


###############################################
# On the other hand, if the radius :math:`\sigma`
# of the kernel is too small, particles :math:`x_i`
# won't be attracted to the target, and may **spread out**
# to minimize the auto-correlation term
# :math:`\tfrac{1}{2}\langle \alpha, k\star\alpha\rangle`.

gradient_flow(SamplesLoss("gaussian", blur=0.1))


###############################################
# Laplacian MMD
# ~~~~~~~~~~~~~~~~
#
# The pointy exponential kernel
# :math:`k(x,y) = \exp(-\|x-y\|/\sigma)`
# tends to provide a better fit, but tends to zero at infinity
# and is still very prone to **screening artifacts**.

gradient_flow(SamplesLoss("laplacian", blur=0.1))


###############################################
# Energy Distance MMD
# ~~~~~~~~~~~~~~~~~~~~~~
#
# The scale-equivariant kernel
# :math:`k(x,y)=-\|x-y\|` provides a robust baseline:
# the Energy Distance.


# sphinx_gallery_thumbnail_number = 4
gradient_flow(SamplesLoss("energy"))


###############################################
# Sinkhorn divergence
# ----------------------
#
# (Unbiased) Sinkhorn divergences have recently been
# introduced in the machine learning litterature,
# and can be understood as modern iterations
# of the classic `SoftAssign <https://en.wikipedia.org/wiki/Point_set_registration#Robust_point_matching>`_ algorithm
# from `economics <http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.228.9750&rep=rep1&type=pdf>`_ and
# `computer vision <http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.86.9769&rep=rep1&type=pdf>`_.
#
#
# Wasserstein-1 distance
# ~~~~~~~~~~~~~~~~~~~~~~~~
#
# When ``p = 1``, the Sinkhorn divergence :math:`\text{S}_\varepsilon`
# interpolates between the Energy Distance (when :math:`\varepsilon` is large):

gradient_flow(SamplesLoss("sinkhorn", p=1, blur=1.0))

###############################################
# And the Earth-Mover's (Wassertein-1) distance:
#

gradient_flow(SamplesLoss("sinkhorn", p=1, blur=0.01))


###############################################
# Wasserstein-2 distance
# ~~~~~~~~~~~~~~~~~~~~~~~~
#
# When ``p = 2``, :math:`\text{S}_\varepsilon`
# interpolates between the degenerate kernel norm
#
# .. math::
#   \tfrac{1}{2}\| \alpha-\beta\|^2_{-\tfrac{1}{2}\|\cdot\|^2}
#   ~=~ \tfrac{1}{2}\| \int x \text{d}\alpha(x)~-~\int y \text{d}\beta(y)\|^2,
#
# which only registers the means of both measures with each other
# (when :math:`\varepsilon` is large):

gradient_flow(SamplesLoss("sinkhorn", p=2, blur=1.0))

###############################################
# And the quadratic, Wasserstein-2 Optimal Transport
# distance which has been studied so well by mathematicians
# from the 80's onwards (when :math:`\varepsilon` is small):

gradient_flow(SamplesLoss("sinkhorn", p=2, blur=0.01))

###############################################
# Introduced in 2016-2018, the *unbalanced*
# setting (Gaussian-Hellinger, Wasserstein-Fisher-Rao, etc.)
# provides a principled way of introducing a **threshold**
# in Optimal Transport computations:
# it allows you to introduce **laziness** in the transportation problem
# by replacing distance fields :math:`\|x-y\|`
# with a robustified analogous :math:`\rho\cdot( 1 - e^{-\|x-y\|/\rho} )`,
# whose gradient saturates beyond a given **reach**, :math:`\rho`
# - at least, that's the idea.
#
# In real-life applications, this tunable parameter could allow
# you to be a little bit more **robust to outliers**!

gradient_flow(SamplesLoss("sinkhorn", p=2, blur=0.01, reach=0.3))
