interface Model {
  _id: string;
}

type JobFunction = 'DES' | 'ENG' | 'BD';
type Job = {
  [J in JobFunction]: number // can be 0
}

type TaskPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';

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
  personIds: Model[];
  taskIds: Model[];
}

// input.json
interface Input {
  run: {
    // run for each team
    tasks: Task[];
    people: Person[];
  }[]
}

// output.json
interface Output {
  completed: boolean;
  assignments: {
    taskId: Model['_id'];
    people: {
      [J in JobFunction]?: Model['_id'];
    }
  }[];
}