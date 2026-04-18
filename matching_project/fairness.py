import statistics


def fairness_score(team1, team2):
    avg1 = sum(p["skill"] for p in team1) / len(team1)
    avg2 = sum(p["skill"] for p in team2) / len(team2)

    team1_skills = [p["skill"] for p in team1]
    team2_skills = [p["skill"] for p in team2]

    return {
        "avg_diff": round(abs(avg1 - avg2), 2),
        "std_dev": round(statistics.pstdev([avg1, avg2]), 2),
        "team1_std": round(statistics.pstdev(team1_skills), 2),
        "team2_std": round(statistics.pstdev(team2_skills), 2),
    }
