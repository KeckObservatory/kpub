# kpub: Publication database

***A database of scientific publications related to a mission.***

`kpub` is a generic tool that enables an institution to keep track of it's scientific publications in an easy way. It leverages MongoDB and the [ADS API](https://github.com/adsabs/adsabs-dev-api) to create and curate a database that contains the metadata of mission-related articles.

This project has been expanded to run as a Python library. 
Data is configured to run on a MongoDB database. 
A Flask server handles HTTP requests to serve data, update affiliation information, and update the database.
It is designed to run at the W. M. Keck Observatory and may no longer function as it originally intended.

This tool is made possible thanks to the efforts of Geert Barentsen who wrote the original version of [kpub](https://github.com/KeplerGO/kpub) for Kepler/K2.  The major changes here are:

- Code is a library installed with `pip install .`
- Code is now config-file driven so it can be used by any facility or institution.
- Added optional tracking of instrument assocations and associated new plots.
- Added optional tracking of archive references and associated new plots.
- Estimates if the new articles are Keck Related and gives the reason why.
- Added affiliations mapping and plotting.
- Added automated PDF download, view, and search for highlight snippets.
- Removed reliance on 'andycasey/ads' third-party module (due to some limitations).
- Replaced installation script and Makefile with run script (due to some limitations).


## Installation and Configuration

1) Download the source code (assuming $HOME for examples below):
```
cd $HOME
git clone https://github.com/KeckObservatory/kpub.git
```

2) Create an account at https://ui.adsabs.harvard.edu/, generate an ADS API key (https://ui.adsabs.harvard.edu/user/settings/token) and copy it for use in step 3 below.

3) Edit the `config.live.yaml` file.  Read the config file and edit sections as needed.  At a minimum, you will need to add the `ADS_API_KEY` value.

4) Install dependencies:

Create a conda environment using the provided environment.yaml file:
```
cd $HOME/kpub
conda env create -f environment.yaml
```

Or, create a venv with Python 3.13+ yourself.

5) Install kpub as a module (this installs all dependencies from `pyproject.toml`, including the classifier's ML deps):

```
pip install .
```

There are additional options you can use to install the machine learning module 'classifier' capabilities by 

```
pip install .[classifier]
```

This is separate from the Flask application and should not be installed unless you want to use the transformer classification model when adding papers.

## Usage
Add `--help` to any command below to get full usage instructions

* `kpub update` adds new publications by searching ADS (interactive);
* `kpub add` adds a publication using its ADS bibcode;
* `kpub delete` deletes a publication using its ADS bibcode;
* `kpub import` imports publications from a JSON file;
* `kpub export` exports publications to a JSON file (or CSV with `-csv` flag) and saves to data/ dir
* `kpub plot` creates a visualization of the database and saves to data/plots/ dir;
* `kpub plot_data` creates the data needed to generate plots (used by the frontend);
* `kpub stats` creates publication stats in markdown format and saves to data/output/ dir;
* `kpub spreadsheet` exports the publications to an Excel spreadsheet
* `kpub update_citations` for a given year, update the cite_read_boost, citation_count and citation fields

## Example use

Main benefit is that you can call these function within a python script
```
import kpub
kpub.kpub_update('2025-07')
```
Otherwise you can call the functions from the command line.

Search ADS by pubdate month or year for new articles and add them without user input:
```
python -m kpub update 2015-07
python -m kpub update 2015
```

Update plots and stats files:
```
python -m kpub plot
python -m kpub stats
```

Add a new article to the database interactively using its bibcode:
```
python -m kpub add 2015arXiv150204715F -interactive
```

Remove an article using its bibcode:
```
python -m kpub delete 2015ApJ...800...46B
```

For example output, see the `data/output/` sub-directory in this repository.

# kpub-viewer Frontend build
This tool visualizes the data on a table/interactive plots. Data is served by a flask server
https://github.com/KeckObservatory/OperationAPIs/

1) Navigate to kpub-viewer and build the project with npm

```
cd kpub-viewer
npm run build
```
2) Make install and kdeploy to www3

```
cd -
make install
kdeploy -a /www/public/kpub
```

## Authors
This new python library version created by Tyler Coda (tcoda at keck.hawaii.edu).
This new configurable version created by Josh Riley (jriley at keck.hawaii.edu).
Original Kepler/K2-specific version created by Geert Barentsen (geert.barentsen at nasa.gov).



# Classifier

Automatic publication classification lives under `src/classifier/` (importable as `kpub.classifier`). It trains and runs transformer and LLM classifiers over articles in MongoDB, merging full text from `data/pubs/full_text/`.

Articles live in MongoDB. Full text stays on the filesystem (`data/pubs/full_text/`). Predictions write back to MongoDB as flat fields (`ilabel`, `keck_score`, `idrp`, `drp_reason`, `ikoa`, `koa_reason`).

Two collections are in play: `articles` is the production collection, and `test_articles` is a copy used for development and classifier experiments. The examples below use `--collection test_articles`; swap in `articles` when writing back to production.

### Setup

The classifier is installed as part of `pip install .` (see Installation above). Its dependencies (torch, transformers, sentence-transformers, PyMuPDF, ollama, etc.) come in with that command.

Mongo connection details are read from `src/config/config.live.yaml` (the same file the autokpub app uses). Make sure the `"kpub"` block (server/port/user/pwd) is filled in.

Copy the tracked config templates to their local (gitignored) counterparts and edit as needed. These live inside the classifier package:

```zsh
cp src/classifier/config/models.default.yaml src/classifier/config/models.yaml
cp src/classifier/config/article_subset.default.yaml src/classifier/config/article_subset.yaml
```

Runtime outputs (experiment logs) go to `classifier_runtime/` (gitignored). Trained model checkpoints are written to `data/models/trained/`.

### 1. Fetch Full Text

Reads bibcodes and `links_data` from MongoDB, downloads PDFs, extracts text to `data/pubs/full_text/{year}/{bibcode}.txt`. 

```zsh
python -m kpub.classifier.data.fetch_full_text --collection test_articles --year 2024
python -m kpub.classifier.data.fetch_full_text --collection test_articles --start-year 2020 --end-year 2025
```

### 2. Train / Test

Loads articles from MongoDB, derives labels from the `affiliation` field (`"keck"` → positive, everything else → negative), merges full text from the filesystem, and runs the standard train/test split. Docs without an `affiliation` set are skipped and reported in the run summary.

```zsh
python -m kpub.classifier.scripts.train transformer --year 2000-2023 --save
python -m kpub.classifier.scripts.train transformer --no-test --save  # train on all labeled data
```

Available models: `transformer` and `llm`. Hyperparameters live in `src/classifier/config/models.yaml`.

#### Fine-tuning workflow

Train a base model once on the full reviewed history, then fine-tune on newly reviewed years as they arrive. The reviewed-subset filter lives in `src/classifier/config/article_subset.yaml` (copied from its `.default.yaml` sibling; currently: 2020–2024 excluding `from_broad_query=true`; 2025+ completely included).

```zsh
# 1. Base model — full reviewed history
python -m kpub.classifier.scripts.train transformer --year 2000-2025 --collection articles --save

# 2. Fine-tune once 2025 data is reviewed
python -m kpub.classifier.scripts.train transformer --year 2020-2025 --collection articles \
    --save --finetune [BASE MODEL] --subset-articles
```

When 2026 data is reviewed, extend the year range (e.g. `--year 2020-2026`) and update `src/classifier/config/article_subset.yaml` to match, then fine-tune again.

### 3. Predict Labels

Loads articles from MongoDB, merges full text from the filesystem, runs classifiers, and writes predictions back to MongoDB. Three tasks are supported:

1. **keck** — Transformer classifier. Writes `ilabel`, `keck_score`.
2. **drp** — LLM classifier on keck-positive papers. Writes `idrp`, `drp_reason`.
3. **koa** — LLM classifier. Writes `ikoa`, `koa_reason`.

```zsh
# Keck classification (transformer)
python -m kpub.classifier.scripts.predict 2024 --collection test_articles --task keck

# DRP classification (LLM, runs on keck-positive papers only)
python -m kpub.classifier.scripts.predict 2024 --collection test_articles --task drp

# KOA classification (LLM)
python -m kpub.classifier.scripts.predict 2024 --collection test_articles --task koa
```

Year ranges (e.g. `2020-2024`) are supported. Use `--limit N` to cap the number of docs classified for quick iteration. The `drp` and `koa` tasks require a running Ollama host (defaults to `http://localhost:11434`); override with `--llm-host` and `--llm-model`.

> **Before running `--task keck`:** the transformer checkpoint is date-stamped and hard-coded as `DEFAULT_TRANSFORMER` at the top of `src/classifier/scripts/predict.py`. Update that constant to point at the checkpoint you want to use (under `data/models/trained/`) before running, or pass `--model-path` explicitly on the command line.

## Acknowledgements
This tool is made possible thanks to the efforts of Geert Barentsen who wrote the original version of [kpub](https://github.com/KeplerGO/kpub) for Kepler/K2.  Thanks also to NASA ADS for providing a web API to their database.

Last Update: 15-July-2026
