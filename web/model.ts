interface Model {
  _id?: string;
}

export const jobFunctions = ["DES", "ENG", "BD"] as const;
export type JobFunction = typeof jobFunctions[number];

export type Job = {
  [J in JobFunction]: number; // can be 0
};

export const taskPriorities = ["LOW", "MEDIUM", "HIGH", "URGENT"];
export type TaskPriority = typeof taskPriorities[number];

export interface Person extends Model {
  capacity: Job;

  // UI
  name: string;
  teamName: Team["name"];
}

export interface Task extends Model {
  requirement: Job;

  dependsOnIds: Model["_id"][];
  blockIds: Model["_id"][];

  priority: TaskPriority;

  // UI
  name: string;
  teamName: Team["name"];
  labels: string[];
}

export interface Team extends Model {
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
    taskId: Model["_id"];
    people: {
      [J in JobFunction]?: Model["_id"];
    };
  }[];
}
