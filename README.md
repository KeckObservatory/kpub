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

Or, install them manually:
```
pip install textract pyyaml requests jinja2 pymongo matplotlib bokeh
```

5) Install kpub as a module:

```
pip install -e .
```

## Usage
Add `--help` to any command below to get full usage instructions

* `kpub update` adds new publications by searching ADS (interactive);
* `kpub add` adds a publication using its ADS bibcode;
* `kpub delete` deletes a publication using its ADS bibcode;
* `kpub import` imports bibcodes from a csv file;
* `kpub export` exports bibcodes to a csv file and saves to data/ dir
* `kpub plot` creates a visualization of the database and saves to data/plots/ dir here;
* `kpub plot_data` creates the data needed to generate plots. This is used by the frontend;
* `kpub stats` creates publications stats in markdown format and saves to data/output dir here;
* `kpub spreadsheet` exports the publications to an Excel spreadsheet

## Example use

Main benefit is that you can call these function within a python script
```
import kpub
kpub.kpub_update('2025-07')
```
Otherwise you can call the functions from the command line.

Search ADS by pubdate month or year for new articles and add them interactively (and push to repo):
```
python -m kpub update 2015-07
python -m pub update 2015
```

Update plots and stats files (and push to repo):
```
python -m kpub plot
python -m kpub stats
python -m kpub push
```

Add a new article to the database interactively using its bibcode:
```
python -m kpub add 2015arXiv150204715F
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



## Acknowledgements
This tool is made possible thanks to the efforts of Geert Barentsen who wrote the original version of [kpub](https://github.com/KeplerGO/kpub) for Kepler/K2.  Thanks also to NASA ADS for providing a web API to their database.

