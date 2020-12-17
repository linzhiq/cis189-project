import json
from collections import defaultdict
from typing import Optional, List, Tuple
from ortools.sat.python import cp_model

# Each week contains 168 hours, so we set 168 as the max end an interval can have.
_MAX_TIME = 168
_JOB_FUNCTION = ['DES', 'ENG', 'BD']
_TASK_PRIORITY = ['LOW', 'MEDIUM', 'HIGH', 'URGENT']

class TaskScheduler:

    def __init__(self, all_demands, blocked_by, capacities):
        self.n_resources, self.n_employees = len(capacities[0]), len(capacities)
        self.all_demands = all_demands          # all_demands[t][r] = amount of hours of r required by task t.
        self.blocked_by = blocked_by            # blocked_by[t] = a list of tasks that must be finished before t is started
        self.capacities = capacities            # capacities[i][r] = total amount of resource hours r provided by employee i

    
    def analyze_demands(self):
        all_demands, blocked_by = self.all_demands, self.blocked_by

        # Split composite tasks into simple tasks
        orig_demands, simple_demands, new_deps = list(), list(), defaultdict(list)
        for i, demand in enumerate(all_demands):
            resources = [(i, v) for i, v in enumerate(demand) if v > 0]
            if len(resources) == 1:
                orig_demands.append(resources[0])
            else:
                orig_demands.append((0, 0))
                # Mark down some relative indices for blocking preds
                for resource in resources:
                    tail = len(simple_demands)
                    simple_demands.append(resource)
                    new_deps[i].append(tail)
                    blocked_by.append([])

        for k in new_deps:
            for i in new_deps[k]:
                blocked_by[k].append(len(orig_demands) + i)

        self.demands = orig_demands + simple_demands       
        self.orig_demands = orig_demands
        self.simple_demands = simple_demands
        self.n_tasks = len(self.demands)


    def create_interval_variables(self):
        model, demands, n_tasks = self.model, self.demands, self.n_tasks
        
        # Contains the interval variables for each task
        orig_tasks, simple_tasks = [], []

        def create_task_interval(n):
            # If the start time is -1, the time is unassigned
            start_time = model.NewIntVar(-1, _MAX_TIME, f'{n}: start time')
            end_time = model.NewIntVar(-1, _MAX_TIME, f'{n}: end time')
            duration = demands[n][1]
            task_interval = model.NewIntervalVar(
                start_time,
                duration,
                end_time,
                f'task {n}'
            )
            task_interval.start = start_time
            task_interval.end = end_time
            task_interval.duration = duration
            return task_interval

        for n in range(len(self.orig_demands)):
            orig_tasks.append(create_task_interval(n))

        for n in range(len(self.simple_demands)):
            simple_tasks.append(create_task_interval(len(orig_tasks) + n))

        self.tasks = orig_tasks + simple_tasks
        self.orig_tasks = orig_tasks


    def employee_assignments(self):
        n_tasks, n_employees = self.n_tasks, self.n_employees
        model, tasks = self.model, self.tasks

        for n in range(n_tasks):
            task = tasks[n]
            # If the value is -1, it is unassigned
            employee = model.NewIntVar(-1, n_employees - 1, f'employee for task {n}')
            task.employee = employee

            # Reify is_assigned with assignment bool
            is_assigned = model.NewBoolVar(f'task {n} is assigned')
            model.Add(employee < 0).OnlyEnforceIf(is_assigned.Not())
            model.Add(employee >= 0).OnlyEnforceIf(is_assigned)
            task.is_assigned = is_assigned

            # Iff start_time is -1, employee is not assigned
            model.Add(task.start < 0).OnlyEnforceIf(is_assigned.Not())
            model.Add(task.start >= 0).OnlyEnforceIf(is_assigned)


    def precedence_constraints(self):
        model = self.model
        tasks = self.tasks
        blocked_by: [[int]] = self.blocked_by
        n_tasks = self.n_tasks
        
        for n in range(n_tasks):
            succ = tasks[n]
            for pred in blocked_by[n]:
                pred = tasks[pred]
                # If both pred and succ are assigned, pred.end <= succ start
                model.Add(pred.end <= succ.start)\
                    .OnlyEnforceIf([pred.is_assigned, succ.is_assigned])
                # If pred is not assigned succ is not assigned
                model.AddImplication(succ.is_assigned, pred.is_assigned)


    def capacity_constraints(self):
        model, tasks = self.model, self.tasks
        demands = self.demands
        capacities = self.capacities
        n_resources, n_employees = self.n_resources, self.n_employees

        resource_to_tasks = defaultdict(list)
        for i, tup in enumerate(demands):
            task = tasks[i]
            resource, requirement = tup
            resource_to_tasks[resource].append((task, requirement))

        employee_loads = []
        for e in range(self.n_employees):
            employee_load = []
            for r in range(self.n_resources):
                employee_tasks = []
                # Create an "indicator" variable for each task
                for i, task_tuple in enumerate(resource_to_tasks[r]):
                    task, requirement = task_tuple
                    # BoolVar to represent if current task is assigned to current employee
                    task_assigned = model.NewBoolVar(f'Task {i} is assigned to employee {e}')
                    employee_task_load = model.NewIntVar(
                    0,
                        requirement,
                        f'Task {i} contributes {requirement} to employee {e}'
                )
                    # task_assigned iff task.employee == e
                    model.Add(task.employee == e).OnlyEnforceIf(task_assigned)
                    model.Add(task.employee != e).OnlyEnforceIf(task_assigned.Not())
                    # employee_task_load is contributed iff task_assigned
                    model.Add(employee_task_load == requirement).OnlyEnforceIf(task_assigned)
                    model.Add(employee_task_load == 0).OnlyEnforceIf(task_assigned.Not())
                    employee_tasks.append(employee_task_load)
                
                employee_resource_load = model.NewIntVar(0, _MAX_TIME, f'Load of resource {r} on emp {e}')
                model.Add(employee_resource_load == sum(employee_tasks))
                model.Add(employee_resource_load <= capacities[e][r])
                employee_load.append(employee_resource_load)
            employee_loads.append(employee_load)

        self.employee_loads = employee_loads


    # Maximize the number of assigned tasks + employees
    def maximize_objectives(self):
        model, tasks = self.model, self.tasks
        assigned_tasks = model.NewIntVar(0, self.n_tasks, 'unassigned tasks')
        model.Add(assigned_tasks == sum(t.is_assigned for t in tasks))
        model.Maximize(assigned_tasks)
        self.assigned_tasks = assigned_tasks


    def solve_model(self) -> Optional[List[Tuple[int, int]]]:
        # Create a new model and solver
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()
        # Create variables and constraints
        self.analyze_demands()
        self.create_interval_variables()
        self.employee_assignments()
        self.precedence_constraints()
        self.capacity_constraints()
        self.maximize_objectives()

        # Set a time limit of 25 seconds and 4 logical cores
        self.solver.parameters.max_time_in_seconds = 25.0
        self.solver.parameters.num_search_workers = 4

        # Run model and return solution if it exists
        self.last_result = self.solver.Solve(self.model)
        if self.last_result == cp_model.INFEASIBLE:
            return 'UNSAT'
        elif self.last_result == cp_model.MODEL_INVALID or self.last_result == cp_model.UNKNOWN:
            return 'UNKNOWN'
        else:
            return 'SAT'


    def pretty_print(self):
        # Overall runtime stats
        print(self.solver.ResponseStats())
        print('-------------------------------')
        print(f'UTILITY: {self.solver.Value(self.assigned_tasks)}')
        print('-------------------------------')

        for e in range(self.n_employees):
            print(f'employee {e}:')
            for r in range(self.n_resources):
                print(f'resource {r}: {self.solver.Value(self.employee_loads[e][r])}')
            print('-------------------------------')

        tasks = self.tasks
        demands = self.demands
        for t in range(self.n_tasks):
            is_assigned = self.solver.Value(tasks[t].is_assigned)
            employee = self.solver.Value(tasks[t].employee)
            start = self.solver.Value(tasks[t].start)
            print(f'task {t} (start={start}) (assigned={is_assigned}) (employee={employee}) (demand={demands[t]})')


# Quick and dirty JSON parse and data marshall
if __name__ == "__main__":
    JOB_FUNCTION = ['DES', 'ENG', 'BD']
    TASK_PRIORITY = ['LOW', 'MEDIUM', 'HIGH', 'URGENT']
    
    with open('io/input.json') as json_file:
        data = json.load(json_file)['run'][0]
        tasks, people = data['tasks'], data['people']

        all_demands, blocked_by = [None] * len(tasks), [None] * len(tasks)
        name_to_index = dict((task['name'], index) for index, task in enumerate(tasks))

        for n, task in enumerate(tasks):
            demand, task_blocked_by = task['requirement'], task['blockedByNames']
            demand = [
                demand[job] if job in demand else 0
                for job in _JOB_FUNCTION
            ]
            task_blocked_by = [
                name_to_index[name] for name in task_blocked_by
            ]
            all_demands[n] = demand
            blocked_by[n] = task_blocked_by

        capacities = [[0] * len(_JOB_FUNCTION) for _ in range(len(people))]
        for i, person in enumerate(people):
            capacities[i] = [
                person['capacity'][job] if job in person['capacity'] else 0
                for job in _JOB_FUNCTION
            ]

    # One resource, one task sanity test
    all_demands = [[0, 168], [1, 0]]
    blocked_by = [[], [0]]
    capacities = [[1, 168], [2, 0]]
        
        scheduler = TaskScheduler(all_demands, blocked_by, capacities)
    ret = scheduler.solve_model() 
    print('SAT' if ret else 'UNSAT')
    if ret:
        scheduler.pretty_print()
