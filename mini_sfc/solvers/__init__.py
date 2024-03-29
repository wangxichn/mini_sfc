from .solution import SOLUTION_TYPE, Solution, SolutionGroup
from .solver import Solver, SolverRegistrar, SOLVER_REGISTRAR, SolverMode

import importlib
import os

current_file = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file)
all_files = os.listdir(current_dir)
subdirs = []
for file in all_files:
    full_path = os.path.join(current_dir, file)
    if os.path.isdir(full_path):
        subdirs.append(file)

for subdir in subdirs:
    module = importlib.import_module("."+subdir,__package__)

__all__ = {
    'SOLUTION_TYPE',
    'Solution',
    'SolutionGroup',
    'Solver',
    'SolverRegistrar',
    'SOLVER_REGISTRAR',
    'SolverMode'
}