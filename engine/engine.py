import json
from ortools.sat.python import cp_model

# Each week contains 168 hours, so we set 168 as the max end an interval can have.
_MAX_TIME = 168

class TaskScheduler:

    def __init__(self, durations, all_demands, successors, capacities, conflict_pairs):
        self.n_resources, self.n_employees = len(capacities), len(capacities[0])
        self.all_demands = all_demands          # all_demands[t][r] = amount of hours of r required by task t.
        self.successors = successors            # successors[t] = a list of tasks that cannot start until t is finished
        self.capacities = capacities            # capacities[r][i] = total amount of resource hours r provided by employee i
        self.conflict_pairs = conflict_pairs    # a list of pairs of tasks that cannot start at the same time

    
    def analyze_demands(self):
        all_demands, successors = self.all_demands, self.successors

        # Split composite tasks into simple tasks
        orig_demands, simple_demands = list(), list()
        for i, demand in enumerate(all_demands):
            resources = [(i, v) for i, v in enumerate(demand) if v > 0]
            if len(resources) == 1:
                orig_demands.append(resources[0])
            else:
                orig_demands.append((0, 0))
                simple_demands.extend(resources)
                # Add future index of the simple demand as a successor of the orig_demand
                successors[i].extend(
                    len(all_demands) + i
                    for i
                    in range(len(simple_demands) - len(resources), len(simple_demands))
                )

        self.demands = orig_demands + simple_demands        
        self.n_tasks = len(self.demands)


    def create_interval_variables(self):
        model, n_tasks = self.model, self.n_tasks
        
        # Contains the interval variables for each task
        tasks = []       
        for n in range(n_tasks):
            start_time = model.NewIntVar(0, _MAX_TIME, f'{n}: start time')
            end_time = model.NewIntVar(0, _MAX_TIME, f'{n}: end time')
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
            tasks.append(task_interval)

        self.tasks = tasks


    def precedence_constraints(self):
        model = self.model
        tasks = self.tasks
        successors: [[int]] = self.successors
        n_tasks = self.n_tasks
        
        # TODO: Reify this so that it is only true if pred and succ are assigned
        # TODO: Pred and succ both unassigned is fine, pred assigned and succ not is fine
        # TODO: Succ assigned and pred not assigned is not fine
        for n in range(n_tasks):
            pred = tasks[n]
            for succ in successors[n]:
                succ = tasks[succ]
                model.Add(pred.end <= succ.start)


    def employee_assignments(self):
        model = self.model
        n_tasks, n_employees = self.n_tasks, self.n_employees
        self.task_of = [None] * n_tasks
        for n in range(n_tasks):
            # If the value is -1, it is unassigned
            self.task_of[n] = model.NewIntVar(-1, n_employees, f'employee for task {n}')


    def capacity_constraints(self):
        model, tasks = self.model, self.tasks
        demands: [[int]] = self.demands
        capacities: [int] = self.capacities
        n_tasks, n_resources = self.n_tasks, self.n_resources

        # TODO: Use reification to enforce user specific capacity constraints
        for r in range(n_resources):
            model.AddCumulative(
                tasks,
                [demands[i][r] for i in range(n_tasks)],
                capacities[r]
            )

    def create_conflict_penalty(self):
        model, tasks = self.model, self.tasks
        conflict_pairs: [(int, int)] = self.conflict_pairs

        conflict_indicators = []
        for i, j in conflict_pairs:
            pair_conflicted = model.NewBoolVar(f'pair {i}{j} is conflicted')
            i, j = tasks[i], tasks[j]
            model.Add(i.start != j.start).OnlyEnforceIf(pair_conflicted.Not())
            model.Add(i.start == j.start).OnlyEnforceIf(pair_conflicted)
            conflict_indicators.append(pair_conflicted)

        self.penalty = model.NewIntVar(0, len(conflict_pairs), 'penalty')
        model.Add(sum(conflict_indicators) == self.penalty)


    def minimize_objectives(self):
        model, tasks = self.model, self.tasks
        durations, penalty = self.durations, self.penalty

        self.makespan = model.NewIntVar(0, _MAX_TIME, 'makespan')
        model.Add(self.makespan == tasks[-1].end)
        makespan = self.makespan

        M = _MAX_TIME + 1
        model.Minimize((M * self.penalty) + self.makespan)


    def solve_model(self) -> Optional[List[Tuple[int, int]]]:
        n_tasks = self.n_tasks
        # Create a new model and solver
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()
        # Create variables and constraints
        self.create_interval_variables()
        self.precedence_constraints()
        self.capacity_constraints()
        self.create_conflict_penalty()
        self.minimize_objectives()

        # Set a time limit of 25 seconds and 4 logical cores
        self.solver.parameters.max_time_in_seconds = 25.0
        self.solver.parameters.num_search_workers = 4

        # Run model and return solution if it exists
        if self.solver.Solve(self.model) != cp_model.INFEASIBLE:
            return [
                (self.solver.Value(t.start), self.solver.Value(t.end))
                for t in self.tasks
            ]
        else:
            return None

    def pretty_print(self):
        tasks = self.tasks
        demands = self.demands
        for t in sorted(range(self.n_tasks), key=lambda t: self.solver.Value(tasks[t].start)):
            print(f'[{self.solver.Value(tasks[t].start)}, {self.solver.Value(tasks[t].end)}): task {t} (demands={demands[t]})')
        print('-------------------------------')
        print(f'MAKESPAN: {self.solver.Value(self.makespan)}')
        print(f'PENALTY: {self.solver.Value(self.penalty)}')
        print('-------------------------------')
        print(self.solver.ResponseStats())

if __name__ == "__main__":
    # Run the stuff/do stuff lololol
