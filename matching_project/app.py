from flask import Flask, render_template, request, redirect, url_for

from distribution import generate_players
from team_matchmaking import find_best_team_match, team_average
from elo import expected_score, update_rating
from fairness import fairness_score
from translations import translations

app = Flask(__name__)

# 전역 저장
LAST_MATCH = None
LAST_RESULT = None


@app.route("/", methods=["GET", "POST"])
def index():
    global LAST_MATCH, LAST_RESULT

    lang = request.args.get("lang", "ko")
    text = translations.get(lang, translations["ko"])

    result = None
    error = None
    skill_value = ""

    if request.method == "POST":
        try:
            my_skill = int(request.form["skill"])
            skill_value = my_skill
        except (ValueError, KeyError):
            my_skill = 2500
            skill_value = ""

        my_skill = max(0, min(my_skill, 5000))

        players = generate_players(59)
        players.append({
            "id": "YOU",
            "skill": my_skill
        })

        best_match, avg_diff = find_best_team_match(players, target_player_id="YOU")

        # ❌ 매칭 실패 처리
        if best_match is None:
            error = "조건에 맞는 팀 매칭을 찾지 못했습니다. 점수를 바꿔 다시 시도해 주세요."
            return render_template(
                "index.html",
                text=text,
                result=None,
                lang=lang,
                error=error,
                skill_value=skill_value,
                last_result=LAST_RESULT
            )

        team1, team2 = best_match

        # 🔥 매칭 저장
        LAST_MATCH = (team1, team2)

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

    return render_template(
        "index.html",
        text=text,
        result=result,
        lang=lang,
        error=error,
        skill_value=skill_value,
        last_result=LAST_RESULT
    )


# 🔥 승패 반영
@app.route("/result", methods=["POST"])
def match_result():
    global LAST_MATCH, LAST_RESULT

    if LAST_MATCH is None:
        return redirect(url_for("index"))

    result = request.form.get("result")

    team1, team2 = LAST_MATCH

    avg1 = team_average(team1)
    avg2 = team_average(team2)

    if result == "A":
        new_avg1, new_avg2 = update_rating(avg1, avg2, 1)
        LAST_RESULT = "Team A 승리"
    else:
        new_avg1, new_avg2 = update_rating(avg1, avg2, 0)
        LAST_RESULT = "Team B 승리"

    # 점수 반영
    for p in team1:
        p["skill"] = int(new_avg1)

    for p in team2:
        p["skill"] = int(new_avg2)

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
    
