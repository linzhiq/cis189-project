import json
from collections import defaultdict
from typing import Optional, List, Tuple
from ortools.sat.python import cp_model

# Each week contains 168 hours, so we set 168 as the max end an interval can have.
_MAX_TIME = 168
_JOB_FUNCTION = ['DES', 'ENG', 'BD']
_TASK_PRIORITY = ['LOW', 'MEDIUM', 'HIGH', 'URGENT']

class TaskScheduler:

    def __init__(self, all_demands, blocked_by, capacities, priorities = None):
        self.n_resources, self.n_employees = len(capacities[0]), len(capacities)
        self.all_demands = all_demands          # all_demands[t][r] = amount of hours of r required by task t.
        self.blocked_by = blocked_by            # blocked_by[t] = a list of tasks that must be finished before t is started
        self.capacities = capacities            # capacities[i][r] = total amount of resource hours r provided by employee i
        self.priorities = priorities if priorities else [1 for _ in range(len(all_demands))]

    
    def analyze_demands(self):
        all_demands, blocked_by, priorities\
            = self.all_demands, self.blocked_by, self.priorities

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
                    priorities.append(0)

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


    def priority_constraints(self):
        model, priorities, tasks = self.model, self.priorities, self.tasks
        priority_indicators = []
        for n in range(len(tasks)):
            priority_val, task = priorities[n], tasks[n]
            curr_task_priority = model.NewIntVar(0, priority_val, f'Contributed priority of task {n}')
            # curr_task_priority is the rated priority_val iff the task is assigned
            model.Add(curr_task_priority == 0).OnlyEnforceIf(task.is_assigned.Not())
            model.Add(curr_task_priority == priority_val).OnlyEnforceIf(task.is_assigned)

            priority_indicators.append(curr_task_priority)
            tasks[n].priority = curr_task_priority

        total_priority = model.NewIntVar(0, sum(priorities), f'Current assignment priority value')
        model.Add(total_priority == sum(priority_indicators))
        self.total_priority = total_priority


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


    # TODO: Balance tasks across employees
    # Maximize the number of assigned tasks + employees
    def maximize_objectives(self):
        model, tasks = self.model, self.tasks
        # Track number of assigned tasks
        assigned_tasks = model.NewIntVar(0, self.n_tasks, 'unassigned tasks')
        model.Add(assigned_tasks == sum(t.is_assigned for t in tasks))
        self.assigned_tasks = assigned_tasks

        # Alias priority utility
        total_priority = self.total_priority
        MAX_PRIORITY = sum(self.priorities)
        P = MAX_PRIORITY + 1

        model.Maximize((assigned_tasks * P) + total_priority)


    def solve_model(self) -> Optional[List[Tuple[int, int]]]:
        # Create a new model and solver
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()
        # Create variables and constraints
        self.analyze_demands()
        self.create_interval_variables()
        self.employee_assignments()
        self.priority_constraints()
        self.precedence_constraints()
        self.capacity_constraints()
        self.maximize_objectives()

        # Set a time limit of 10 seconds and 1 logical core
        self.solver.parameters.max_time_in_seconds = 10.0
        self.solver.parameters.num_search_workers = 1

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
        print(f'NUM_TASKS: {self.solver.Value(self.assigned_tasks)}')
        print('-------------------------------')
        print(f'PRIORITY: {self.solver.Value(self.total_priority)}')
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
            priority = self.solver.Value(tasks[t].priority)
            print(f'task {t} (start={start}) (assigned={is_assigned}) (employee={employee}) (demand={demands[t]}) (priority={priority})')


    def jsonize(self, task_names, person_names):
        data = {
            'completed': False,
            'assignments': [],
            'error': 'Something went wrong with reading the SAT result.'
        }
        if self.last_result == cp_model.OPTIMAL or self.last_result == cp_model.FEASIBLE:
            solver, tasks, blocked_by, demands\
                = self.solver, self.tasks, self.blocked_by, self.demands
            assignments = []

            for i, task in enumerate(self.orig_tasks):
                if solver.Value(task.is_assigned):
                    resource, requirement = self.demands[i]
                    # If the task is a composite sink and all predecessors are assigned
                    if (resource, requirement) == (0, 0) and all(
                        solver.Value(tasks[pred].is_assigned)
                        for pred in blocked_by[i]
                    ):
                        people = {}
                        for pred in blocked_by[i]:
                            pred, pred_demand = tasks[pred], demands[pred]
                            pred_res, _ = pred_demand
                            people[_JOB_FUNCTION[pred_res]] = person_names[solver.Value(task.employee)]
                        assignment = {
                            'taskName': task_names[i],
                            'people': people
                        }
                        assignments.append(assignment)

                    # Otherwise, this is a simple task: just assign it.
                    elif requirement > 0:
                        people = {}
                        people[_JOB_FUNCTION[resource]] = person_names[solver.Value(task.employee)]
                        assignment = {
                            'taskName': task_names[i],
                            'people': people
                        }
                        assignments.append(assignment)
            
            data = {
                'completed': True,
                'assignments': assignments
            }

        else:
            data['error'] = 'The provided problem is UNSAT or INVALID.'

        return data 
            

# Quick and dirty JSON parse and data marshall
if __name__ == "__main__":
    def parse_json(data):
        tasks, people = data['tasks'], data['people']

        all_demands, blocked_by, priorities =\
            [None] * len(tasks), [None] * len(tasks), [None] * len(tasks)
        name_to_index = dict((task['name'], index) for index, task in enumerate(tasks))

        for n, task in enumerate(tasks):
            demand, task_blocked_by, priority_class\
                = task['requirement'], task['blockedByNames'], task['priority']
            demand = [
                demand[job] if job in demand else 0
                for job in _JOB_FUNCTION
            ]
            task_blocked_by = [
                name_to_index[name] for name in task_blocked_by
            ]
            all_demands[n] = demand
            blocked_by[n] = task_blocked_by
            priorities[n] = _TASK_PRIORITY.index(priority_class) + 1

        capacities = [[0] * len(_JOB_FUNCTION) for _ in range(len(people))]
        for i, person in enumerate(people):
            capacities[i] = [
                person['capacity'][job] if job in person['capacity'] else 0
                for job in _JOB_FUNCTION
            ]
        return all_demands, blocked_by, capacities, priorities,\
            [task["name"] for task in tasks], [person["name"] for person in people]
    

    def run_scheduler(all_demands, blocked_by, capacities, priorities, names, people):
        # The scheduler doesn't handle lists of differing lengths/empty lists. Guard for that here.
        if (not all_demands or not blocked_by or not capacities):
            return {
                'completed': True,
                'assignments': []
            }
        scheduler = TaskScheduler(all_demands, blocked_by, capacities, priorities)
        scheduler.solve_model()
        scheduler.pretty_print()
        return scheduler.jsonize(names, people)

    with open('io/input.json') as json_file:
        teams = json.load(json_file)['run']
        inputs = [parse_json(team) for team in teams]
        outputs = [run_scheduler(a, b, c, p, tn, pn) for a, b, c, p, tn, pn in inputs]
        with open('io/output.json', 'w') as out_file:
            json.dump(outputs, out_file)
        
