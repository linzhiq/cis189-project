import type { NextApiRequest, NextApiResponse } from "next";
import * as fs from "fs";
import path from "path";

type Data = {
  name: string;
};

export default (req: NextApiRequest, res: NextApiResponse<Data>) => {
  console.log(req.body);
  fs.writeFileSync(
    path.join(process.cwd(), "../engine/io/input.json"),
    JSON.stringify(req.body)
  );

  res.status(200);
};
