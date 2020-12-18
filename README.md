# cis189-project

## Setting up the environment
### `engine`
From wd `./engine`, run `pipenv install`.

### `web`
From wd `./web`, run `npm install` or `yarn`.

## Running the app
### With GUI
From wd `./web`, run `npm run dev` or `yarn dev`.

### For Testing
Edit and run `./engine/data_gen.py` to produce an input json

Create a dir `./engine/io` that contains `input.json`, and run `./engine/engine.py`. The script will consume the input json and create `./engine/io/output.json` containing the results.

Experimental data can be found in `./engine/data`

![Screenshot](./screenshot.png)