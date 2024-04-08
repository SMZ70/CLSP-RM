import json
import pathlib
from clsprm import Problem, MIPSolver


def test_301_single_product():
    problem_path = (
        pathlib.Path(__file__).parent
        / "data"
        / "clsp"
        / "301_single_product.json"
    )
    problem = Problem(**json.loads(problem_path.read_text()))
    mip_solver = MIPSolver(problem=problem)
    sol = mip_solver.solve()
    assert sol is not None, "Problem could not be solved."
    assert sol.objective_value == 580
