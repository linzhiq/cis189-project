import json
from ortools.sat.python import cp_model

class TaskScheduler:
    
    def __init__(self, durations, demands, successors, capacities, conflict_pairs):
        self.n_tasks = len(durations)
        self.n_resources = len(capacities)
        self.durations = durations              # durations[t] = duration of task t
        self.demands = demands                  # demands[t][r] = amount of resource r required by task t
        self.successors = successors            # successors[t] = a list of tasks that cannot start until t is finished
        self.capacities = capacities            # capacities[r] = total amount of resource r
        self.conflict_pairs = conflict_pairs    # a list of pairs of tasks that cannot start at the same time


    def create_interval_variables(self):
        model = self.model
        durations: [int] = self.durations
        n_tasks = self.n_tasks
        self.tasks = [None for _ in range(n_tasks)]
        tasks = self.tasks

        MAX_TIME = sum(durations)
        
        for n in range(n_tasks):
        start_time = model.NewIntVar(0, MAX_TIME, f'{n}: start time')
        end_time = model.NewIntVar(0, MAX_TIME, f'{n}: end time')
        tasks[n] = model.NewIntervalVar(
            start_time,
            durations[n],
            end_time,
            f'task {n}'
        )
        tasks[n].start = start_time
        tasks[n].end = end_time
        tasks[n].duration = durations[n]


    def precedence_constraints(self):
        model = self.model
        tasks = self.tasks
        successors: [[int]] = self.successors
        n_tasks = self.n_tasks
        
        for n in range(n_tasks):
        pred = tasks[n]
        for succ in successors[n]:
            succ = tasks[succ]
            model.Add(pred.end <= succ.start)


    def capacity_constraints(self):
        model, tasks = self.model, self.tasks
        demands: [[int]] = self.demands
        capacities: [int] = self.capacities
        n_tasks, n_resources = self.n_tasks, self.n_resources

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
        MAX_TIME = sum(durations)

        self.makespan = model.NewIntVar(0, MAX_TIME, 'makespan')
        model.Add(self.makespan == tasks[-1].end)
        makespan = self.makespan

        M = MAX_TIME + 1
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
