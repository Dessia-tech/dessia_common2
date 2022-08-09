"""
Tests for dessia_common.optimization package
"""
from math import pi, exp, log, sin
from itertools import product
import matplotlib.pyplot as plt
from typing import List

from dessia_common.core import DessiaObject, HeterogeneousList
import dessia_common.optimization as opt

class Engine(DessiaObject):
    """
    Dummy and unrealistic engine, only for tests on optimization package.
    Do not use to optimize an engine.
    """
    _vector_features = ['diameter', 'stroke', 'mass', 'costs']
    def __init__(self, n_cyl: int, diameter: float, stroke: float, r_pow_cyl: float = 1., r_diam_strok: float = 1.,
                 name: str = ''):
        DessiaObject.__init__(self, name=name)
        self.n_cyl = n_cyl
        self.diameter = diameter
        self.stroke = stroke
        self.r_pow_cyl = r_pow_cyl
        self.r_diam_strok = r_diam_strok
        self.cyl_volume = self.compute_cyl_volume()
        self._power = None
        self._mass = None
        self._costs = None

    def compute_cyl_volume(self):
        return (self.diameter/2)**2 * pi * self.stroke

    def cylinder_power(self):
        return (self.cyl_volume * self.r_pow_cyl *
                abs(sin(
                    (self.r_diam_strok * (1 + 0.5 * (self.stroke / self.diameter + self.diameter / self.stroke)))**2)
                    ))
    @property
    def power(self):
        if self._power is None:
            self._power = self.n_cyl * self.cylinder_power()
        return self._power

    def carter_volume(self):
        return self.stroke * 1.5 * (1 - exp(-self.diameter)) * 3. * self.diameter * 1.2 * self.n_cyl

    @property
    def mass(self):
        if self._mass is None:
            self._mass = 7800*(self.carter_volume() - self.n_cyl * self.cyl_volume)
        return self._mass

    @property
    def costs(self):
        if self._costs is None:
            self._costs = (110*((0.4 - 2*self.stroke)**2 + (0.3 - self.diameter)**2) +
                           (1 / (1 + log(1 + self.power)) - sin(self.mass/100))**2)
        return self._costs

    def to_vector(self):
        return [self.diameter, self.stroke, self.mass, self.costs]

class EngineOptimizer(opt.InstantiatingModelOptimizer):
    """
    Abstract class, to be subclassed by real class
    Instantiate a new model at each point request
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

    gg = HeterogeneousList(engines)
    gg.plot()



diameter = opt.BoundedAttributeValue("diameter", 0.05, 0.5)
stroke = opt.BoundedAttributeValue("stroke", 0.1, 0.3)
cylinders = opt.FixedAttributeValue("n_cyl", 4)
r_pow_cyl = opt.FixedAttributeValue("r_pow_cyl", 1e9)
r_diam_strok = opt.FixedAttributeValue("r_diam_strok", 1.)

engine_optimizer = EngineOptimizer([cylinders, r_pow_cyl, r_diam_strok], [diameter, stroke])
model, fx_opt = engine_optimizer.optimize_cma()
model_grad, fx_opt_grad = engine_optimizer.optimize_gradient()

diameters = (x / 1000 for x in range(50, 500, 10))
strokes = (x / 1000 for x in range(100, 300, 4))
cylinders = [3, 4, 5, 6, 8]
check_costs_function(cylinders, diameters, strokes, 1e9, 1.)

fig = plt.gcf()
ax = fig.gca()
ax.plot(model.diameter, model.stroke, model.costs,
        linestyle = 'None', marker = 'o', markersize = 2, color = 'r')

ax.plot(model_grad.diameter, model_grad.stroke, model_grad.costs,
        linestyle = 'None', marker = 'o', markersize = 2, color = 'm')

