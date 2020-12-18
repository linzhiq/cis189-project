'''
Script that generates some test data and feeds it into io/input.json. Quick and dirty.
'''
import random, json

_RESOURCES = ['DES', 'ENG', 'BD']
_PRIORITIES = ['LOW', 'MEDIUM', 'HIGH', 'URGENT']


with open('io/input.json', 'w') as out:
    teams = []
    for team_num in range(1000):
        team = {}

        # Generate tasks for each team
        team_tasks = []
        for task_num in range(random.randint(10, 100)):
            requirement = dict()
            for resource in _RESOURCES:
                requirement[resource] = random.randint(0, 15)

            priority = random.choice(_PRIORITIES)
            blocked_by = random.sample(
                range(task_num), random.randint(0, task_num)
            ) if task_num > 0 else []
            blocked_by = [str(i) for i in blocked_by]
            # Build and add task
            task = {
                "name": str(task_num),
                "teamName": str(team_num),
                "priority": priority,
                "blockedByNames": blocked_by,
                "requirement": requirement
            }
            team_tasks.append(task)
        team["tasks"] = team_tasks

        # Generate team members
        team_members = []
        for emp_num in range(random.randint(1, 10)):
            capacity = dict()
            for resource in _RESOURCES:
                capacity[resource] = random.randint(0, 30)

            # Build and add task
            task = {
                "name": str(emp_num),
                "teamName": str(team_num),
                "capacity": capacity
            }
            team_members.append(task)
        team["people"] = team_members

        teams.append(team)

    json.dump({
        "run": teams
    }, out)

