"""
Entry point for running kpub as a module: python -m kpub
"""
import sys
# Try relative import (when used as installed package)
# Fall back to absolute import (when imported directly from source)
try:
    from .kpub import make_parser, kpub_update, kpub_add, kpub_plot, kpub_plot_data, kpub_delete, kpub_import, kpub_export, kpub_stats, kpub_spreadsheet, kpub_update_citations
except ImportError:
    from kpub import make_parser, kpub_update, kpub_add, kpub_plot, kpub_plot_data, kpub_delete, kpub_import, kpub_export, kpub_stats, kpub_spreadsheet, kpub_update_citations
import logging

log = logging.getLogger('KPUB')

if __name__ == "__main__":
    cmd = sys.argv[1]
    parser = make_parser()
    margs = parser.parse_args(sys.argv[1:])
    if cmd == 'update':      kpub_update(margs.month)
    elif cmd == 'add':       kpub_add(margs.bibcode, margs.interactive)
    elif cmd == 'plot':      kpub_plot()
    elif cmd == 'plot_data': kpub_plot_data(margs.plotname, margs.instruments, margs.year_begin, margs.extrapolate)
    elif cmd == 'delete':    kpub_delete(margs.bibcode)
    elif cmd == 'import':    kpub_import(margs.jsonfile)
    elif cmd == 'export':    kpub_export(margs.monthyear, margs.begin_year, margs.filename, margs.affiliation, margs.csv, getattr(margs, 'all', False))
    elif cmd == 'stats':     kpub_stats()
    elif cmd == 'update_citations': kpub_update_citations(margs.year)
    elif cmd == 'spreadsheet': kpub_spreadsheet(margs.filename)
    else: log.error("Unknown kpub command")
