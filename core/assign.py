#Functions to help take in a file with multiple CSVs and then
# assigns them to the correct variable based on their names.

from typing import Dict, List, Tuple

#Role -> keywords we expect in filenames
ROLE_KEYWORDS: Dict[str, List[str]] = {
    "telemetry": ["telemetry", "telemetry_data", "logger", "can"],
    "laps":      ["lap_time", "lap time", "lap", "lapresults"],
    "weather":   ["weather", "ambient"],
    "results":   ["results", "classification", "standings"],
    "sectors":   ["analysisendurancewithsections", "analysisendurance", "sectors", "sector", "splits"],
}

#Assigning roles by the name
def assign_roles_by_name(files:List[Tuple[str,bytes]]) ->Dict[str,Dict]:
    """
    files: [(filename, bytes), ...]
    returns: {role: {"filename": str, "index": int}}
    Rule: first filename containing any keyword for that role wins.
    """ 
    picks: Dict[str,Dict] = {}
    taken = set()

    # lowercase names once
    lowered = [(i, fname, fname.lower()) for i, (fname, _) in enumerate(files)]

    for role, keywords in ROLE_KEYWORDS.items():
        for i, fname, low in lowered:
            if i in taken:
                continue
            if any(k in low for k in keywords):
                picks[role] = {"filename": fname, "index": i}
                taken.add(i)
                break
    return picks