import json
from ortools.sat.python import cp_model

# Each week contains 168 hours, so we set 168 as the max end an interval can have.
_MAX_TIME = 168

class TaskScheduler:

    def __init__(self, all_demands, blocked_by, capacities):
        self.n_resources, self.n_employees = len(capacities), len(capacities[0])
        self.all_demands = all_demands          # all_demands[t][r] = amount of hours of r required by task t.
        self.blocked_by = blocked_by            # blocked_by[t] = a list of tasks that must be finished before t is started
        self.capacities = capacities            # capacities[r][i] = total amount of resource hours r provided by employee i

    
    def analyze_demands(self):
        all_demands, blocked_by = self.all_demands, self.blocked_by

        # Split composite tasks into simple tasks
        orig_demands, simple_demands = list(), list()
        for i, demand in enumerate(all_demands):
            resources = [(i, v) for i, v in enumerate(demand) if v > 0]
            if len(resources) == 1:
                orig_demands.append(resources[0])
            else:
                orig_demands.append((0, 0))
                simple_demands.extend(resources)
                # Add future index of the simple demand as a predecessor of the orig_demand
                blocked_by[i].extend(
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
            tasks.append(task_interval)

        self.tasks = tasks


    def employee_assignments(self):
        n_tasks, n_employees = self.n_tasks, self.n_employees
        model, tasks = self.model, self.tasks

        for n in range(n_tasks):
            # If the value is -1, it is unassigned
            employee = model.NewIntVar(-1, n_employees, f'employee for task {n}')
            tasks[n].employee = employee

            # Reify is_assigned with assignment bool
            is_assigned = model.NewBoolVar()
            model.Add(employee < 0).OnlyEnforceIf(is_assigned.Not())
            model.Add(employee >= 0).OnlyEnforceIf(is_assigned)
            tasks[n].is_assigned = is_assigned

        self.task_of = task_of


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
                    .OnlyEnforceIf(pred.is_assigned, succ.is_assigned)
                # If pred is not assigned succ is not assigned
                model.Add(succ.is_assigned.Not()).OnlyEnforceIf(pred.is_assigned.Not())


    def capacity_constraints(self):
        model, tasks = self.model, self.tasks
        demands: [[int]] = self.demands
        capacities: [int] = self.capacities
        n_tasks, n_resources, n_employees\
            = self.n_tasks, self.n_resources, self.n_employees

        # TODO: Use reification to enforce user specific capacity constraints
        for r in range(n_resources):
            model.AddCumulative(
                tasks,
                [demands[i][r] for i in range(n_tasks)],
                capacities[r]
            )

        # Force no overlap on all the tasks for each employee
        # TODO: Talk to Jediah about this
        # for e in range(self.n_employees):
        #     model.AddNoOverlap(
        #         task
        #         for task in tasks
        #         if task.employee == e
        #     )


    def create_capacity_penalty(self):
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


    # Minimize the number of unassigned tasks
    def minimize_objectives(self):
        model, tasks = self.model, self.tasks
        unassigned_tasks = model.NewIntVar(0, self.n_tasks, 'unassigned tasks')
        model.Add(unassigned_tasks == sum(b.is_assigned % 1 for b in tasks))
        model.Minimize(unassigned_tasks)

    def solve_model(self) -> Optional[List[Tuple[int, int]]]:
        n_tasks = self.n_tasks
        # Create a new model and solver
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()
        # Create variables and constraints
        self.analyze_demands()
        self.create_interval_variables()
        self.employee_assignments()
        self.precedence_constraints()
        self.capacity_constraints()
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
    JOB_FUNCTION = ['DES', 'END', 'BD']
    TASK_PRIORITY = ['LOW', 'MEDIUM', 'HIGH', 'URGENT']
    
    with open('io/input.json') as json_file:
        data = json.load(json_file)['run']
        tasks, people = data.tasks, data.people

        '''
        self.all_demands = all_demands          # all_demands[t][r] = amount of hours of r required by task t.
        self.successors = successors            # successors[t] = a list of tasks that cannot start until t is finished
        self.capacities = capacities            # capacities[r][i] = total amount of resource hours r provided by employee i
        '''

        all_demands, blocked_by = [None] * len(tasks), [None] * len(tasks)
        name_to_index = dict((tasks.name, index) for index, task in enumerate(tasks))

        for n, task in enumerate(tasks):
            demand, task_blocked_by = task.requirement, task.blockedByIds
            demand = [
                requirement[job] if job in requirement else 0
                for job in JOB_FUNCTION
            ]
            task_blocked_by = [
                name_to_index[name] for name in task_blocked_by
            ]
            all_demands[n] = demand
            blocked_by[n] = task_blocked_by

        capacities = [[0] * len(JOB_FUNCTION) for _ in range(len(people))]
        for i, person in enumerate(people):
            capacities[i] = [
                person.requirement[job] if job in person.requirement else 0
                for job in JOB_FUNCTION
            ]
        
        scheduler = TaskScheduler(all_demands, blocked_by, capacities)
        scheduler.solve_model()
