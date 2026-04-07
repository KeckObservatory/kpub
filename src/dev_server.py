"""
Minimal Flask dev server for kpub-viewer.
Connects to a local MongoDB and serves the endpoints the frontend needs.

Usage:
    conda run -n KPUB python src/dev_server.py
    # Then in another terminal: cd src/kpub-viewer && npm run dev
    # Open http://localhost:5173
"""
import datetime
import json
from flask import Flask, request, jsonify
from bson import ObjectId
from pymongo import MongoClient, DESCENDING

app = Flask(__name__)

# Connect to local MongoDB
client = MongoClient("localhost", 27017)
db = client["mongo_dump"]["articles"]

# Instruments list (matches config.yaml)
INSTRUMENTS = [
    "DEIMOS", "ESI", "KPIC", "KPF", "SCALES",
    "HIRES", "KCWI", "LRIS", "MOSFIRE",
    "NIRC2", "NIRES", "NIRSPEC", "OSIRIS",
]
YEAR_BEGIN = 2009

# Palette matching bokeh Category20
CATEGORY20 = [
    "#1f77b4", "#aec7e8", "#ff7f0e", "#ffbb78", "#2ca02c",
    "#98df8a", "#d62728", "#ff9896", "#9467bd", "#c5b0d5",
    "#8c564b", "#c49c94", "#e377c2", "#f7b6d2", "#7f7f7f",
    "#c7c7c7", "#bcbd22", "#dbdb8d", "#17becf", "#9edae5",
]


class MongoEncoder(json.JSONEncoder):
    """Handle datetime, ObjectId, and other MongoDB types."""
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)

app.json_provider_class = None  # use custom encoder below

@app.after_request
def after_request(response):
    response.headers["Content-Type"] = "application/json"
    return response


def json_response(data, status=200):
    return app.response_class(
        json.dumps(data, cls=MongoEncoder),
        status=status,
        mimetype="application/json",
    )


@app.route("/api/kpub/get_table")
def get_table():
    monthyear = request.args.get("monthyear", "")
    parts = monthyear.split("-")
    year = int(parts[0])
    month = int(parts[1]) if len(parts) > 1 else None

    query = {"year": year}
    if month:
        query["month"] = month

    articles = list(db.find(query).sort("date", DESCENDING))
    return json_response({"articles": articles, "isAdmin": True})


@app.route("/api/kpub/get_plot")
def get_plot():
    plotname = request.args.get("plotname")
    if plotname == "plot_by_year":
        return json_response(_plot_by_year())
    elif plotname == "plot_author_count":
        return json_response(_plot_author_count())
    elif plotname == "plot_by_instrument":
        instruments_param = request.args.get("instruments", "")
        instruments = [i for i in instruments_param.split("|") if i]
        return json_response(_plot_by_instrument(instruments))
    else:
        return json_response({"error": f"Unknown plot: {plotname}"}, 400)


@app.route("/api/kpub/update_affiliation", methods=["PUT"])
def update_affiliation():
    body = request.json
    affiliation = body["affiliation"]
    articles = body["articles"]
    updated = []
    for article in articles:
        now = datetime.datetime.now()
        db.update_one(
            {"_id": article["_id"]},
            {"$set": {
                "affiliation": affiliation,
                "last_modifier": "dev_user",
                "date_modified": now,
            }},
        )
        article["affiliation"] = affiliation
        article["last_modifier"] = "dev_user"
        article["date_modified"] = now
        updated.append(article)
    return json_response({"updated_articles": updated})


# --- Plot data helpers (reimplemented from plot.py to avoid heavy imports) ---

def _get_counts_by_year(year_begin, year_end, instrument=None):
    """Get article counts per year, optionally filtered by instrument."""
    pipeline = []
    query = {"year": {"$gte": year_begin, "$lte": year_end}, "affiliation": "keck"}
    group = {"_id": {"year": "$year"}, "count": {"$sum": 1}}
    if instrument:
        pipeline.append({"$unwind": "$instruments"})
        query["instruments"] = instrument
        group["_id"]["instrument"] = "$instruments"
    pipeline.append({"$match": query})
    pipeline.append({"$group": group})
    pipeline.append({"$sort": {"_id.year": 1}})
    rows = list(db.aggregate(pipeline))
    yeardict = {year: 0 for year in range(year_begin, year_end + 1)}
    for row in rows:
        yeardict[row["_id"]["year"]] = row["count"]
    return yeardict


def _plot_by_year():
    current_year = datetime.datetime.now().year
    extrapolate = request.args.get("extrapolate", "false").lower() == "true"
    counts = _get_counts_by_year(YEAR_BEGIN, current_year)
    current_total = None
    expected = None
    if extrapolate:
        now = datetime.datetime.now()
        fraction = float(now.strftime("%-j")) / 365.2425
        current_total = counts[current_year]
        expected = (1 / fraction - 1) * current_total
    return {
        "current_year": current_year,
        "current_total": current_total,
        "expected": expected,
        "year_begin": YEAR_BEGIN,
        "counts": counts,
        "colors": ["#3498db", "#27ae60", "#95a5a6"],
    }


def _plot_author_count():
    current_year = datetime.datetime.now().year
    pipeline = [
        {"$match": {"year": {"$gte": YEAR_BEGIN, "$lte": current_year}, "affiliation": "keck"}},
        {"$unwind": "$author_norm"},
        {"$group": {
            "_id": "$year",
            "author_set": {"$addToSet": "$author_norm"},
            "first_author_set": {"$addToSet": "$first_author_norm"},
            "bibcodes": {"$addToSet": "$bibcode"},
        }},
        {"$project": {
            "paper_count": {"$size": "$bibcodes"},
            "author_count": {"$size": "$author_set"},
            "first_author_count": {"$size": "$first_author_set"},
        }},
        {"$sort": {"_id": 1}},
    ]
    results = list(db.aggregate(pipeline))
    cum_years, cum_papers, cum_authors, cum_first = [], [], [], []
    papers = authors = first_authors = 0
    for r in results:
        papers += r["paper_count"]
        authors += r["author_count"]
        first_authors += r["first_author_count"]
        cum_years.append(r["_id"])
        cum_papers.append(papers)
        cum_authors.append(authors)
        cum_first.append(first_authors)
    return {
        "cumulative_years": cum_years,
        "paper_counts": cum_papers,
        "author_counts": cum_authors,
        "first_author_counts": cum_first,
    }


def _plot_by_instrument(instruments):
    if not instruments:
        instruments = INSTRUMENTS
    current_year = datetime.datetime.now().year
    years = [str(y) for y in range(YEAR_BEGIN, current_year + 1)]
    values = []
    for instr in instruments:
        counts = _get_counts_by_year(YEAR_BEGIN, current_year, instr)
        values.append([counts[y] for y in range(YEAR_BEGIN, current_year + 1)])
    palette = CATEGORY20[: len(instruments)]
    return {
        "years": years,
        "values": values,
        "columns": instruments,
        "color": palette,
    }


if __name__ == "__main__":
    print("Starting kpub dev server on http://localhost:5001")
    print("Make sure 'npm run dev' is running in src/kpub-viewer/")
    app.run(port=5001, debug=True)
