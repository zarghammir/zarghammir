"""Draw my GitHub contribution chart as two SVGs (light and dark) for the profile README.

Reads the same calendar github.com/zarghammir shows, through the GraphQL API.
Needs GITHUB_TOKEN in the environment. Writes assets/contributions-{light,dark}.svg.
"""
import datetime
import json
import os
import urllib.request

LOGIN = os.environ.get("CHART_USER", "zarghammir")
QUERY = """query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{
  totalContributions weeks{contributionDays{date contributionCount contributionLevel weekday}}}}}}"""

THEMES = {
    "light": {"text": "#59636e", "border": "#d1d9e0",
              "levels": ["#eff2f5", "#aceebb", "#4ac26b", "#2da44e", "#116329"]},
    "dark": {"text": "#9198a1", "border": "#3d444d",
             "levels": ["#151b23", "#033a16", "#196c2e", "#2ea043", "#56d364"]},
}
LEVEL = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}
FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans',Helvetica,Arial,sans-serif"
CELL, GAP = 11, 3
STEP = CELL + GAP
LEFT, TOP = 36, 46


def fetch():
    body = json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", data=body, headers={
        "Authorization": f"bearer {os.environ['GITHUB_TOKEN']}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)["data"]["user"]["contributionsCollection"]["contributionCalendar"]


def svg(cal, theme):
    t = THEMES[theme]
    weeks = cal["weeks"]
    width = LEFT + len(weeks) * STEP + 4
    height = TOP + 7 * STEP + 30
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
           f'font-family="{FONT}" role="img" aria-label="{cal["totalContributions"]:,} contributions in the last year">']
    out.append(f'<text x="0" y="16" font-size="15" fill="{t["text"]}">'
               f'{cal["totalContributions"]:,} contributions in the last year</text>')
    labels, last_month = [], None
    for i, w in enumerate(weeks):
        first = datetime.date.fromisoformat(w["contributionDays"][0]["date"])
        if first.month != last_month:
            if labels and i - labels[-1][0] < 3:
                labels.pop()  # too close to the next month's label; keep the later one
            labels.append((i, f"{first:%b}"))
            last_month = first.month
    for i, name in labels:
        if i <= len(weeks) - 2:
            out.append(f'<text x="{LEFT + i * STEP}" y="{TOP - 8}" font-size="10" fill="{t["text"]}">{name}</text>')
    for i, w in enumerate(weeks):
        for d in w["contributionDays"]:
            fill = t["levels"][LEVEL.get(d["contributionLevel"], 0)]
            out.append(f'<rect x="{LEFT + i * STEP}" y="{TOP + d["weekday"] * STEP}" width="{CELL}" height="{CELL}" '
                       f'rx="2" fill="{fill}"><title>{d["contributionCount"]} on {d["date"]}</title></rect>')
    for row, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        out.append(f'<text x="0" y="{TOP + row * STEP + 9}" font-size="10" fill="{t["text"]}">{name}</text>')
    y = TOP + 7 * STEP + 14
    x = width - 4 - 5 * STEP - 34
    out.append(f'<text x="{x - 30}" y="{y + 9}" font-size="10" fill="{t["text"]}">Less</text>')
    for k, c in enumerate(t["levels"]):
        out.append(f'<rect x="{x + k * STEP}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{c}"/>')
    out.append(f'<text x="{x + 5 * STEP + 4}" y="{y + 9}" font-size="10" fill="{t["text"]}">More</text>')
    out.append("</svg>")
    return "\n".join(out)


def main():
    cal = fetch()
    here = os.path.dirname(os.path.abspath(__file__))
    assets = os.path.join(here, "..", "..", "assets")
    os.makedirs(assets, exist_ok=True)
    for theme in THEMES:
        with open(os.path.join(assets, f"contributions-{theme}.svg"), "w") as f:
            f.write(svg(cal, theme))
    print(f"{cal['totalContributions']} contributions, {len(cal['weeks'])} weeks")


if __name__ == "__main__":
    main()
