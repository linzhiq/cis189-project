export const jobFunctions = ["DES", "ENG", "BD"] as const;
export type JobFunction = typeof jobFunctions[number];

export type Job = {
  [J in JobFunction]: number; // can be 0
};

export const taskPriorities = ["LOW", "MEDIUM", "HIGH", "URGENT"];
export type TaskPriority = typeof taskPriorities[number];

export interface Person {
  name: string;
  capacity: Job;

  // UI
  teamName: Team["name"];
}

export interface Task {
  name: string;
  priority: TaskPriority;

  requirement: Job;
  blockedByNames: Task["name"][];

  // UI
  teamName: Team["name"];
}

export interface Team {
  // UI
  name: string;
}

// input.json
export type Input = {
  run: {
    // run for each team
    tasks: Task[];
    people: Person[];
  }[];
};

// output.json
export type Output = {
  completed: boolean;
  assignments: {
    taskName: Task["name"];
    people: {
      [J in JobFunction]?: Person["name"];
    };
  }[];
}[];
