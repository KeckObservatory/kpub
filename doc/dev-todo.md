
Must do: 
- [done] Move kepler specific variables to config file based.
- [done] Add PDF d/l, parse and search (with alt ADS requery fallback method)
- [done] Added ADS "highlight" text snippets to review text.
- [done] Write script to load and validate existing article data from CVS files and import to new database. 
- [done] Do a full proper import of all Keck article legacy data, including instrument associations.
- [done] Add instrument search, highlight and user prompt for inclusion to db.
- [done] Remove reliance on 'ads' third-party module?
- [done] Create affiliations mapping config for search criteria. 
- [done] Code algorithm for determining affiliation category. See plot.py for test code.
- [done] Auto search for KOA in full text and insert 1 or 0 in new 'archive' DB column.
- [done] Option to open local pdf in browser.
- [done] Add plotting of instruments per year
- [done] Add report/graph of pubs by affiliation type (1st auth, <= 3rd auth) 
- [done] Update README and other code docs with kepler/k2 mentions
- [done] Replace installation script and makefile with simple run script
- [done] Create keck-specific user guide (confluence?)
- Run kpub for all of 2020 up to present 
- Post ADS bibcodes files to www2.  See www:/home/jriley/test/kpub-copy.py.  Need to make kcron owner of 2 files
- Move plotting params to config, such as 'start year' (some are still hard-coded to 2005)
- Deal with data anomalies below
- pdftotext is faster but not as good, pdfminder is slower sometimes but i think works better
- Add plotting of KOA reference
- See if 'scripts' dir works with recent changes?
- "make refresh" with optional year param?
- Fix issue with 'kpub add' not highlighting by default?
- Create a webform to replace appeals email where the only input to form is bibcodes(reads our www file copy)? Send PIs a link/URL to search ADS by their name? Send link to https://www2.keck.hawaii.edu/library/adskeck.txt?
- Change plots to all use bokeh or all matplotlib


Low-priority:
- How will we query, insert and report on thesis papers?  doctype='phdthesis', property contains 'NONARTICLE'
- Try mysql version with install on keck server (see mysql branch; mostly done but did not have time to finish)
- Add full spelling of instruments as optional search params.  So 'KCWI' counts will search for 'KCWI' and "KECK Cosmic Web Imager".  Use OR in query. Reprocess records with empty instruments?
- Add ability to review and/or export 'unrelated' entries.
- Context: Make context snippet length a config item? Provide full sentence context?
- Might want to show KOA results to confirm.  There was a case 2020MNRAS.499.3775S that said "these data are available thru KOA" which does not mean they used koa.
- To speed things up, have code retrieve the pdf of the next article? 
- Create a GUI interface (flask or pyqt)