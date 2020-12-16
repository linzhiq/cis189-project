import React from "react";
import {TagInput} from "@blueprintjs/core";
import {GetServerSideProps} from "next";

const EditPage: React.FC = () => {
  return <div style={{paddingLeft: '10vw', width: '80vw'}}>
    <h2>Teams</h2>
    <TagInput leftIcon="user" values={['123']} large/>
  </div>
};

const EditPageProps: {
  teams: Team[];
}

export const getServerSideProps: GetServerSideProps = async context => ({
  props: {}, // will be passed to the page component as props
});

export default EditPage;
