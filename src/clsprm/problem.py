import itertools
from typing import TypeAlias

from pydantic import BaseModel, model_validator

Period: TypeAlias = int


class Product(BaseModel):
    inventory_cost_new: float
    inventory_cost_old: float
    production_cost: float
    production_setup_cost: float
    remanufacturing_cost: float
    remanufacturing_setup_cost: float
    demand: list[int]
    n_returns: list[int]
    production_time: float
    remanufacturing_time: float
    production_setup_time: float
    remanufacturing_setup_time: float


class Problem(BaseModel):
    products: list[Product]
    production_capacity: list[float] | float
    remanufacturing_capacity: list[float] | float

    @model_validator(mode="after")
    def validate_demands(self):
        if not all(
            len(p1.demand) == len(p2.demand)
            for p1, p2 in itertools.combinations(self.products, 2)
        ):
            raise ValueError(
                "Each product's demand list must have the same length."
            )

        for p1, p2 in itertools.combinations(self.products, 2):
            print(len(p1.n_returns), len(p2.n_returns), self.n_periods)
        if not all(
            len(p1.n_returns) == len(p2.n_returns)
            for p1, p2 in itertools.combinations(self.products, 2)
        ):
            raise ValueError(
                "Each product's returns must have the same length."
            )

        if any(len(p.n_returns) != self.n_periods for p in self.products):
            raise ValueError(
                "All products must have a number of returns with length"
                " matching the total periods."
            )

        if isinstance(self.production_capacity, list):
            assert len(self.production_capacity) == self.n_periods, (
                "Production capacity list length must equal"
                " the number of periods."
            )
        if isinstance(self.remanufacturing_capacity, list):
            assert len(self.remanufacturing_capacity) == self.n_periods, (
                "Remanufacturing capacity list length must equal"
                " the number of periods."
            )

        # populate capacity lists
        if isinstance(self.production_capacity, float):
            self.production_capacity = [
                self.production_capacity
            ] * self.n_periods

        if isinstance(self.remanufacturing_capacity, float):
            self.remanufacturing_capacity = [
                self.remanufacturing_capacity
            ] * self.n_periods

        return self

    @property
    def periods(self) -> list[Period]:
        return list(range(self.n_periods))

    @property
    def T(self) -> range:
        return range(self.n_periods)

    @property
    def P(self) -> range:
        return range(self.n_products)

    @property
    def n_periods(self) -> int:
        return len(self.products[0].demand)

    @property
    def n_products(self) -> int:
        return len(self.products)
