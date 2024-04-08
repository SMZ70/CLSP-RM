import itertools
from typing import TypeAlias

from docplex.mp.model import Model as MIPModel
from docplex.mp.vartype import BinaryVarType, IntegerVarType

from .problem import Problem

ProductPeriod: TypeAlias = tuple[int, int]
IntegerVarDict: TypeAlias = dict[ProductPeriod, IntegerVarType]
BinaryVarDict: TypeAlias = dict[ProductPeriod, BinaryVarType]


class MIPSolver(MIPModel):
    problem: Problem
    X: IntegerVarDict
    X_r: IntegerVarDict
    L: IntegerVarDict
    L_r: IntegerVarDict
    Gamma: BinaryVarDict
    Gamma_r: BinaryVarDict

    def __init__(self, problem: Problem, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.problem = problem
        self._build_vars()
        self._add_objective()
        self._add_constraints()
        self._add_kpis()

    def _add_objective(self) -> None:
        self.minimize(
            self.sum(
                product.inventory_cost_new * self.L[p, t]
                + product.inventory_cost_old * self.L_r[p, t]
                + product.production_cost * self.X[p, t]
                + product.remanufacturing_cost * self.X_r[p, t]
                + product.production_setup_cost * self.Gamma[p, t]
                + product.remanufacturing_setup_cost * self.Gamma[p, t]
                for p, product in enumerate(self.problem.products)
                for t in self.problem.T
            )
        )

    def _add_constraints(self) -> None:
        # Inventory balance constraints -- new production
        self.add_constraints(
            self.L[p, t]
            == (self.L[p, t - 1] if t > 0 else 0)
            + self.X[p, t]
            + self.X_r[p, t]
            - product.demand[t]
            for p, product in enumerate(self.problem.products)
            for t in self.problem.T
        )

        # Inventory balance constraints -- RM
        self.add_constraints(
            self.L_r[p, t]
            == (self.L_r[p, t - 1] if t > 0 else 0)
            + product.n_returns[t]
            - self.X_r[p, t]
            for p, product in enumerate(self.problem.products)
            for t in self.problem.T
        )

        # Capacity - Production
        self.add_constraints(
            self.sum(
                product.production_time * self.X[p, t]
                + product.production_setup_time * self.Gamma[p, t]
                for p, product in enumerate(self.problem.products)
            ).le(self.problem.production_capacity[t])
            for t in self.problem.T
        )

        # Capacity - RM
        self.add_constraints(
            self.sum(
                product.remanufacturing_time * self.X_r[p, t]
                + product.remanufacturing_setup_time * self.Gamma_r[p, t]
                for p, product in enumerate(self.problem.products)
            ).le(self.problem.remanufacturing_capacity[t])
            for t in self.problem.T
        )

        # Setup conditional - Production
        for p, _ in enumerate(self.problem.products):
            for t in self.problem.T:
                self.add((self.Gamma[p, t] == 0) >> (self.X[p, t] == 0))
                self.add((self.Gamma_r[p, t] == 0) >> (self.X_r[p, t] == 0))

    def _add_kpis(self) -> None:
        for t in self.problem.T:
            self.add_kpi(
                self.sum(
                    product.production_time * self.X[p, t]
                    + product.production_setup_time * self.Gamma[p, t]
                    for p, product in enumerate(self.problem.products)
                ),
                publish_name=f"UsedProd_{t}",
            )
            self.add_kpi(
                self.sum(
                    product.remanufacturing_time * self.X_r[p, t]
                    + product.remanufacturing_setup_time * self.Gamma_r[p, t]
                    for p, product in enumerate(self.problem.products)
                ),
                publish_name=f"UsedRM_{t}",
            )

    def _build_vars(self) -> None:
        self.X = self.integer_var_dict(
            keys=itertools.product(self.problem.P, self.problem.T),
            name="X",
        )
        self.X_r = self.integer_var_dict(
            keys=itertools.product(self.problem.P, self.problem.T),
            name="X_r",
        )
        self.L = self.integer_var_dict(
            keys=itertools.product(self.problem.P, self.problem.T),
            name="L",
        )
        self.L_r = self.integer_var_dict(
            keys=itertools.product(self.problem.P, self.problem.T),
            name="L_r",
        )
        self.Gamma = self.binary_var_dict(
            keys=itertools.product(self.problem.P, self.problem.T),
            name="G",
        )
        self.Gamma_r = self.binary_var_dict(
            keys=itertools.product(self.problem.P, self.problem.T),
            name="Gr",
        )
