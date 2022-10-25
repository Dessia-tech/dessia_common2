"""
Tests for dessia_common.optimization package
"""
from math import pi, exp, sin
from itertools import product
import matplotlib.pyplot as plt
from typing import List

from dessia_common.core import DessiaObject
import dessia_common.optimization as opt

class Engine(DessiaObject):
    """
    Dummy and unrealistic engine, only for tests on optimization package.
    Do not use to optimize an engine.
    """
    _vector_features = ['diameter', 'stroke', 'power', 'mass', 'costs']
    def __init__(self, n_cyl: int, diameter: float, stroke: float, r_pow_cyl: float = 1., r_diam_strok: float = 1.,
                 name: str = ''):
        DessiaObject.__init__(self, name=name)
        self.n_cyl = n_cyl
        self.diameter = diameter
        self.stroke = stroke
        self.r_pow_cyl = r_pow_cyl
        self.r_diam_strok = r_diam_strok
        self.cyl_volume = self.compute_cyl_volume()
        self.power = self._power()
        self.mass = self._mass()
        self.costs = self._costs()

    def compute_cyl_volume(self):
        return (self.diameter/2)**2 * pi * self.stroke

    def cylinder_power(self):
        return (self.cyl_volume * self.r_pow_cyl *
                abs(sin(
                    (self.r_diam_strok * (1 + 0.5 * (self.stroke / self.diameter + self.diameter / self.stroke)))**2)))

    def _power(self):
        return self.n_cyl * self.cylinder_power()

    def carter_volume(self):
        return self.stroke * 1.5 * (1 - exp(-self.diameter)) * 3. * self.diameter * 1.2 * self.n_cyl

    def _mass(self):
        return 7800*(self.carter_volume() - self.n_cyl * self.cyl_volume)

    def _costs(self):
        return (400*((0.175 - self.stroke)**2 + 2*(0.07 - self.diameter)**2) +
                (sin(self.power/self.r_pow_cyl) + sin(self.mass/10))**2)


    def to_vector(self):
        return [self.diameter, self.stroke, self.power, self.mass, self.costs]


class EngineOptimizer(opt.InstantiatingModelOptimizer):
    """
    Optimizer for Engine
    """
    def __init__(self, fixed_parameters: List[opt.FixedAttributeValue],
                 optimization_bounds: List[opt.BoundedAttributeValue],
                 name: str = ''):
        opt.InstantiatingModelOptimizer.__init__(self, fixed_parameters, optimization_bounds, name)

    def instantiate_model(self, attributes_values):
        return Engine(**attributes_values)

    def objective_from_model(self, model, clearance: float = 0.003):
        return model.costs


def check_costs_function(cylinders, diameters, strokes, r_pow_cyl, r_diam_strok):
    points = []
    engines = []
    for n_cyl, diameter, stroke in product(cylinders, diameters, strokes):
        engines.append(Engine(n_cyl, diameter, stroke, r_pow_cyl, r_diam_strok))
        points.append([diameter, stroke, engines[-1].power, engines[-1].mass, engines[-1].costs])

    costs = list(zip(*points))[-2]
    sorted_idx = (costs.index(cost) for cost in sorted(costs))
    sorted_points = [points[idx] for idx in sorted_idx]
    transposed_points = list(zip(*sorted_points))

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.plot(transposed_points[0], transposed_points[1], transposed_points[-1],
            linestyle = 'None', marker = 'o', markersize = 0.5)


# Script
list_cma = []
list_fx = []
for _ in range(250):
    diameter = opt.BoundedAttributeValue("diameter", 0.05, 0.5)
    stroke = opt.BoundedAttributeValue("stroke", 0.1, 0.3)
    cylinders = opt.FixedAttributeValue("n_cyl", 4)
    r_pow_cyl = opt.FixedAttributeValue("r_pow_cyl", 1e9)
    r_diam_strok = opt.FixedAttributeValue("r_diam_strok", 1.)

    engine_optimizer = EngineOptimizer([cylinders, r_pow_cyl, r_diam_strok], [diameter, stroke])
    model_cma, fx_opt = engine_optimizer.optimize_cma()
    model_grad, fx_opt_grad = engine_optimizer.optimize_gradient()
    model_mix, fx_opt_mix = engine_optimizer.optimize_cma_then_gradient()

    diameters = (x / 1000 for x in range(30, 100, 1))
    strokes = (x / 1000 for x in range(100, 250, 1))
    cylinders = [4]
    list_fx.append(fx_opt_mix)

    # Set to True to see optimization results on complex cost function (the mix approach should be prefered)
if False:
    check_costs_function(cylinders, diameters, strokes, 1e8, 1.)
    plt.plot(model_cma.diameter, model_cma.stroke, model_cma.costs,
             linestyle = 'None', marker = 'D', markersize = 6, color = 'r', label='Solution CMA')

    plt.plot(model_grad.diameter, model_grad.stroke, model_grad.costs,
             linestyle = 'None', marker = 'D', markersize = 6, color = 'm', label='Solution Gradient Descent')

    plt.plot(model_mix.diameter, model_mix.stroke, model_mix.costs,
             linestyle = 'None', marker = 'D', markersize = 6, color = 'g', label='Solution approche mixte')

    plt.legend()

assert(sum(list_fx)/len(list_fx) <= 0.05)
