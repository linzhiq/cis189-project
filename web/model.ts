export const jobFunctions = ["DES", "ENG", "BD"] as const;
export type JobFunction = typeof jobFunctions[number];

export type Job = {
  [J in JobFunction]: number; // can be 0
};

export const taskPriorities = ["LOW", "MEDIUM", "HIGH", "URGENT"];
export type TaskPriority = typeof taskPriorities[number];

export interface Person {
  capacity: Job;

  // UI
  name: string;
  teamName: Team["name"];
}

export interface Task {
  requirement: Job;

  blockedByIds: Task["name"][];

  priority: TaskPriority;

  // UI
  name: string;
  teamName: Team["name"];
}

export interface Team {
  // UI
  name: string;
}

// input.json
export interface Input {
  run: {
    // run for each team
    tasks: Task[];
    people: Person[];
  }[];
}

// output.json
export interface Output {
  completed: boolean;
  assignments: {
    taskName: Task["name"];
    people: {
      [J in JobFunction]?: Person["name"];
    };
  }[];
}
