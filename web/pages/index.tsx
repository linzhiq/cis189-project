import React, { useState } from "react";
import { TagInput } from "@blueprintjs/core";
import { GetServerSideProps } from "next";

import { MongoClient } from "mongodb";

const url =
  "mongodb+srv://user:3HFHgEYkNgNIk462@cluster0.c6gib.mongodb.net/db?retryWrites=true&w=majority";

const EditPage: React.FC<EditPageProps> = ({ teams: _teams }) => {
  const [teams, setTeams] = useState(_teams);

  return (
    <div style={{ paddingLeft: "10vw", width: "80vw" }}>
      <h2>Teams</h2>
      <TagInput
        leftIcon="user"
        values={["123"]}
        large
        onAdd={(values) => {
          for (const value of values) {
            setTeams([
              ...teams,
              {
                name: value,
              },
            ]);
          }
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
      people: [],
      tasks: [],
      teams: [],
    },
  };
};

export default EditPage;
