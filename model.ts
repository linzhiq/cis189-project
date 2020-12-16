interface Model {
  _id?: string;
}

const jobFunctions = ["DES", "ENG", "BD"] as const;
type JobFunction = typeof jobFunctions[number];

type Job = {
  [J in JobFunction]: number; // can be 0
};

const taskPriorities = ["LOW", "MEDIUM", "HIGH", "URGENT"];
type TaskPriority = typeof taskPriorities[number];

interface Person extends Model {
  capacity: Job;

  // UI
  name: string;
  teamId: Model;
}

interface Task extends Model {
  requirement: Job;

  dependsOnIds: Model[];
  blockIds: Model[];

  priority: TaskPriority;

  // UI
  name: string;
  teamId: Model;
  labels: string[];
}

interface Team extends Model {
  // UI
  name: string;
}

// input.json
interface Input {
  run: {
    // run for each team
    tasks: Task[];
    people: Person[];
  }[];
}

// output.json
interface Output {
  completed: boolean;
  assignments: {
    taskId: Model["_id"];
    people: {
      [J in JobFunction]?: Model["_id"];
    };
  }[];
}
