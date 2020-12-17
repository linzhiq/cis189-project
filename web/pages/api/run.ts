import type { NextApiRequest, NextApiResponse } from "next";
import * as fs from "fs";
import path from "path";
import * as child_process from "child_process";
import { Output } from "../../model";

export default (req: NextApiRequest, res: NextApiResponse) => {
  fs.writeFileSync(
    path.join(process.cwd(), "../engine/io/input.json"),
    JSON.stringify(req.body)
  );

  child_process.execSync("pipenv run engine", {
    cwd: path.join(process.cwd(), "../engine/"),
  });
  
  const output: Output = JSON.parse(
    fs.readFileSync(
      path.join(process.cwd(), "../engine/io/output.json"),
      "utf-8"
    )
  );
  
  res.status(200).json(output);
};
