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

import { MongoClient } from "mongodb";

import { Job, jobFunctions, Person, Task, Team } from "../model";

const url =
  "mongodb+srv://user:3HFHgEYkNgNIk462@cluster0.c6gib.mongodb.net/db?retryWrites=true&w=majority";

let newPersonName: string | undefined;
let newPersonTeam: string | undefined;
let newPersonCapacity: Job | undefined;

const EditPage: React.FC<EditPageProps> = ({
  teams: _teams,
  people: _people,
}) => {
  const [teams, setTeams] = useState(_teams);
  const [people, setPeople] = useState(_people);

  return (
    <div style={{ paddingLeft: "10vw", width: "80vw" }}>
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
          ``;
        }}
        onRemove={(value) => {
          setTeams(teams.filter((team) => team.name !== value));
        }}
      />
      <h3>People</h3>
      {[...people, undefined].map((person) => (
        <div
          style={{ display: "flex", justifyContent: "space-between" }}
          key={person?._id}
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
                  people.filter((_person) => _person._id !== person._id)
                );
              }}
            />
          ) : (
            <Button
              icon="add"
              intent={"success"}
              style={{ height: 30, marginTop: 24 }}
              onClick={() => {
                console.log(newPersonCapacity, newPersonName, newPersonTeam);
  
                if (!newPersonCapacity || !newPersonName || !newPersonTeam) {
                  Toaster.create({ position: "bottom", maxToasts: 1 }).show({
                    message: "Missing information for person",
                    intent: "danger",
                  });
                  
                  return;
                }
                
                setPeople([
                  ...people,
                  {
                    name: newPersonName,
                    teamName: newPersonTeam,
                    capacity: newPersonCapacity,
                  },
                ]);
              }}
            />
          )}
        </div>
      ))}
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
          _id: "1",
          name: "Meredith Ford",
          teamName: "Team 1",
          capacity: { DES: 5, ENG: 20, BD: 0 },
        },
      ],
      tasks: [],
    },
  };
};

export default EditPage;
