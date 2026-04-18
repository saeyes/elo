from flask import Flask, render_template, request

from distribution import generate_players
from team_matchmaking import find_best_team_match, team_average
from elo import expected_score
from fairness import fairness_score
from translations import translations

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    lang = request.args.get("lang", "ko")
    text = translations.get(lang, translations["ko"])

    result = None

    if request.method == "POST":
        try:
            my_skill = int(request.form["skill"])
        except (ValueError, KeyError):
            my_skill = 2500

        my_skill = max(0, min(my_skill, 5000))

        players = generate_players(1009)
        players.append({
            "id": "YOU",
            "skill": my_skill
        })

        best_match, avg_diff = find_best_team_match(players, target_player_id="YOU")

        if best_match is not None:
            team1, team2 = best_match

            avg1 = round(team_average(team1), 2)
            avg2 = round(team_average(team2), 2)

            win_prob = round(expected_score(avg1, avg2) * 100, 2)

            for p in team1:
                p["mmr"] = p["skill"]
                p["name"] = p["id"]

            for p in team2:
                p["mmr"] = p["skill"]
                p["name"] = p["id"]

            fair = fairness_score(team1, team2)

            result = {
                "team1": team1,
                "team2": team2,
                "win_prob": win_prob,
                "avg_team1": avg1,
                "avg_team2": avg2,
                "fair_avg": fair["avg_diff"],
                "fair_std": fair["std_dev"],
                "team1_balance": fair["team1_std"],
                "team2_balance": fair["team2_std"],
                "match_count": 1
            }

    return render_template("index.html", text=text, result=result, lang=lang)


if __name__ == "__main__":
    app.run(debug=True)
