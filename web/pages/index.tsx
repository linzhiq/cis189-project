import React, { useState } from "react";
import {
  Button,
  FormGroup,
  InputGroup,
  NumericInput,
  TagInput,
  Toaster,
} from "@blueprintjs/core";
import { GetServerSideProps } from "next";
import styles from "./index.module.scss";

import { MongoClient } from "mongodb";

import {
  Input,
  Job,
  jobFunctions,
  Person,
  Task,
  taskPriorities,
  TaskPriority,
  Team,
} from "../model";

import https from "https";

const url =
  "mongodb+srv://user:3HFHgEYkNgNIk462@cluster0.c6gib.mongodb.net/db?retryWrites=true&w=majority";

let newPersonName: string | undefined;
let newPersonTeam: string | undefined;
let newPersonCapacity: Job | undefined;

let newTaskName: string | undefined;
let newTaskPriority: TaskPriority | undefined;
let newTaskRequirement: Job | undefined;

const EditPage: React.FC<EditPageProps> = ({
  teams: _teams,
  people: _people,
  tasks: _tasks,
}) => {
  const [teams, setTeams] = useState(_teams);
  const [people, setPeople] = useState(_people);
  const [tasks, setTasks] = useState(_tasks);

  const [newTaskTeam, setNewTaskTeam] = useState(undefined);
  const [newTaskBlockedByNames, setNewTaskBlockedByNames] = useState<
    string[] | undefined
  >(undefined);

  const serialize = (): Input => ({
    run: teams.map((team) => ({
      tasks: tasks.filter((task) => task.teamName === team.name),
      people: people.filter((person) => person.teamName === team.name),
    })),
  });

  return (
    <div style={{ paddingLeft: "10vw", width: "80vw" }}>
      <h1>Scheduler</h1>
      <h3>Teams</h3>
      <TagInput
        leftIcon="people"
        values={teams.map((team) => team.name)}
        large
        onAdd={(values) => {
          for (const value of values) {
            for (const team of teams) {
              if (team.name === value) {
                // team already exists
                return;
              }
            }

            setTeams([
              ...teams,
              {
                name: value,
              },
            ]);
          }
        }}
        onRemove={(value) => {
          setTeams(teams.filter((team) => team.name !== value));
          setPeople(people.filter((person) => person.teamName !== value));
          setTasks(tasks.filter((task) => task.teamName !== value));
        }}
      />
      <h3>People</h3>
      {[...people, undefined].map((person) => (
        <div
          style={{ display: "flex" }}
          key={person?.name}
          className={styles.flex_container}
        >
          <FormGroup label="Name">
            {person ? (
              <InputGroup id="text-input" value={person.name} disabled />
            ) : (
              <InputGroup
                id="text-input"
                placeholder="New person"
                onChange={(event) => (newPersonName = event.target.value)}
              />
            )}
          </FormGroup>
          <FormGroup label="Team">
            <div className="bp3-select">
              <select
                style={{ width: 200 }}
                disabled={!!person}
                onChange={(event) => (newPersonTeam = event.target.value)}
              >
                {person ? (
                  <>
                    <option selected>{person.teamName}</option>
                  </>
                ) : (
                  <>
                    <option selected>Select team</option>
                    {teams.map((team) => {
                      return <option value={team.name}>{team.name}</option>;
                    })}
                  </>
                )}
              </select>
            </div>
          </FormGroup>
          {jobFunctions.map((jobFunction) => {
            return (
              <FormGroup label={`${jobFunction} capacity`} helperText="hours">
                <NumericInput
                  value={person ? person.capacity[jobFunction] : undefined}
                  style={{ width: 80 }}
                  disabled={!!person}
                  min={0}
                  defaultValue={0}
                  onValueChange={(value) => {
                    newPersonCapacity = {
                      BD: newPersonCapacity?.BD || 0,
                      DES: newPersonCapacity?.DES || 0,
                      ENG: newPersonCapacity?.ENG || 0,
                    };

                    newPersonCapacity = {
                      ...newPersonCapacity,
                      [jobFunction]: value,
                    };
                  }}
                />
              </FormGroup>
            );
          })}
          {person ? (
            <Button
              icon="delete"
              intent={"danger"}
              style={{ height: 30, marginTop: 24 }}
              onClick={() => {
                setPeople(
                  people.filter((_person) => _person.name !== person.name)
                );
              }}
            />
          ) : (
            <Button
              icon="add"
              intent={"success"}
              style={{ height: 30, marginTop: 24 }}
              onClick={() => {
                if (!newPersonCapacity || !newPersonName || !newPersonTeam) {
                  Toaster.create({ position: "bottom", maxToasts: 1 }).show({
                    message: "Missing information for person",
                    intent: "danger",
                  });

                  return;
                }

                for (const person of people) {
                  if (person.name === newPersonName) {
                    Toaster.create({ position: "bottom", maxToasts: 1 }).show({
                      message: "Duplicate name for person",
                      intent: "danger",
                    });

                    return;
                  }
                }

                setPeople([
                  ...people,
                  {
                    name: newPersonName,
                    teamName: newPersonTeam,
                    capacity: newPersonCapacity,
                  },
                ]);

                newPersonTeam = undefined;
                newPersonTeam = undefined;
                newPersonCapacity = undefined;
              }}
            />
          )}
        </div>
      ))}
      <h3>Tasks</h3>
      {[...tasks, undefined].map((task) => (
        <div
          style={{ display: "flex", flexWrap: "wrap" }}
          key={task?.name}
          className={styles.flex_container}
        >
          <FormGroup label="Name">
            {task ? (
              <InputGroup id="text-input" value={task.name} disabled />
            ) : (
              <InputGroup
                id="text-input"
                placeholder="New task"
                onChange={(event) => (newTaskName = event.target.value)}
              />
            )}
          </FormGroup>
          <FormGroup label="Team">
            <div className="bp3-select">
              <select
                style={{ width: 200 }}
                disabled={!!task}
                onChange={(event) => {
                  setNewTaskTeam(
                    event.target.value === "undefined"
                      ? undefined
                      : event.target.value
                  );
                }}
              >
                {task ? (
                  <>
                    <option selected>{task.teamName}</option>
                  </>
                ) : (
                  <>
                    <option selected value={"undefined"}>
                      Select team
                    </option>
                    {teams.map((team) => {
                      return <option value={team.name}>{team.name}</option>;
                    })}
                  </>
                )}
              </select>
            </div>
          </FormGroup>
          {jobFunctions.map((jobFunction) => {
            return (
              <FormGroup label={`${jobFunction} reqt.`} helperText="hours">
                <NumericInput
                  value={task ? task.requirement[jobFunction] : undefined}
                  style={{ width: 80 }}
                  disabled={!!task}
                  min={0}
                  defaultValue={0}
                  onValueChange={(value) => {
                    newTaskRequirement = {
                      BD: newTaskRequirement?.BD || 0,
                      DES: newTaskRequirement?.DES || 0,
                      ENG: newTaskRequirement?.ENG || 0,
                    };

                    newTaskRequirement = {
                      ...newTaskRequirement,
                      [jobFunction]: value,
                    };
                  }}
                />
              </FormGroup>
            );
          })}

          <FormGroup label="Priority">
            <div className="bp3-select">
              <select
                style={{ width: 168 }}
                disabled={!!task}
                onChange={(event) => (newTaskPriority = event.target.value)}
              >
                {task ? (
                  <>
                    <option selected>{task.priority}</option>
                  </>
                ) : (
                  <>
                    <option selected>Select priority</option>
                    {taskPriorities.map((value) => {
                      return <option value={value}>{value}</option>;
                    })}
                  </>
                )}
              </select>
            </div>
          </FormGroup>

          <FormGroup label="Blocked by" helperText="tasks">
            <TagInput
              leftIcon="flow-end"
              values={task ? task.blockedByNames : newTaskBlockedByNames || []}
              disabled={!!task || (!task && newTaskTeam === undefined)}
              onAdd={(values) => {
                const teamTasks = new Set(
                  tasks
                    .filter(
                      (_task) =>
                        _task.teamName === (task ? task.teamName : newTaskTeam)
                    )
                    .map((task) => task.name)
                );

                for (const value of values) {
                  if (!teamTasks.has(value)) {
                    Toaster.create({ position: "bottom", maxToasts: 1 }).show({
                      message: "Task does not exist for team",
                      intent: "danger",
                    });

                    return;
                  }

                  setNewTaskBlockedByNames(
                    newTaskBlockedByNames
                      ? [...newTaskBlockedByNames, value]
                      : [value]
                  );
                }
              }}
              onRemove={(value) => {
                setTeams(teams.filter((team) => team.name !== value));
                setPeople(people.filter((person) => person.teamName !== value));
                setTasks(tasks.filter((task) => task.teamName !== value));
              }}
            />
          </FormGroup>
          {task ? (
            <Button
              icon="delete"
              text={"Delete task"}
              intent={"none"}
              style={{ height: 30, marginTop: 24 }}
              onClick={() => {
                setTasks(
                  tasks
                    .filter((_task) => _task.name !== task.name)
                    .map((_task) => ({
                      ..._task,
                      blockedByNames: _task.blockedByNames.filter(
                        (name) => name != task.name
                      ),
                    }))
                );

                if (newTaskBlockedByNames) {
                  setNewTaskBlockedByNames(
                    newTaskBlockedByNames.filter((name) => name != task.name)
                  );
                }
              }}
            />
          ) : (
            <Button
              icon="add"
              text={"Add task"}
              intent={"success"}
              style={{ height: 30, marginTop: 24 }}
              onClick={() => {
                if (
                  !newTaskName ||
                  !newTaskTeam ||
                  !newTaskRequirement ||
                  !newTaskPriority
                ) {
                  Toaster.create({ position: "bottom", maxToasts: 1 }).show({
                    message: "Missing information for task",
                    intent: "danger",
                  });

                  return;
                }

                for (const task of tasks) {
                  if (task.name === newTaskName) {
                    Toaster.create({ position: "bottom", maxToasts: 1 }).show({
                      message: "Duplicate name for task",
                      intent: "danger",
                    });

                    return;
                  }
                }

                setTasks([
                  ...tasks,
                  {
                    name: newTaskName,
                    teamName: newTaskTeam,
                    blockedByNames: newTaskBlockedByNames || [],
                    priority: newTaskPriority,
                    requirement: newTaskRequirement,
                  },
                ]);

                newTaskName = undefined;
                setNewTaskTeam(undefined);
                newTaskPriority = undefined;
                setNewTaskBlockedByNames(undefined);
                newTaskRequirement = undefined;
              }}
            />
          )}
        </div>
      ))}
      <Button
        text={"Schedule"}
        onClick={() => {
          const data = JSON.stringify(serialize());

          const options = {
            path: "/api/run",
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "Content-Length": data.length,
            },
          };

          const req = https.request(options);

          req.on("error", (error) => {
            console.error(error);
          });

          req.write(data);
          req.end();
        }}
      />
    </div>
  );
};

type EditPageProps = {
  teams: Team[];
  tasks: Task[];
  people: Person[];
};

export const getServerSideProps: GetServerSideProps<EditPageProps> = async (
  context
) => {
  return {
    props: {
      teams: [{ name: "Team 1" }, { name: "Team 2" }],
      people: [
        {
          name: "Meredith Ford",
          teamName: "Team 1",
          capacity: { DES: 5, ENG: 20, BD: 0 },
        },
      ],
      tasks: [
        {
          name: "Task 1",
          teamName: "Team 1",
          blockedByNames: [],
          priority: "HIGH",
          requirement: { DES: 2, ENG: 5, BD: 0 },
        },
        {
          name: "Task 2",
          teamName: "Team 1",
          blockedByNames: ["Task 1"],
          priority: "MEDIUM",
          requirement: { DES: 3, ENG: 10, BD: 0 },
        },
      ],
    },
  };
};

export default EditPage;
