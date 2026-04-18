import random
import itertools


def team_average(team):
    return sum(p["skill"] for p in team) / len(team)


def team_std(team):
    avg = team_average(team)
    return (sum((p["skill"] - avg) ** 2 for p in team) / len(team)) ** 0.5


def score_match(team1, team2):
    avg_diff = abs(team_average(team1) - team_average(team2))
    std_diff = abs(team_std(team1) - team_std(team2))
    return avg_diff + std_diff


def fallback_random_teams(players):
    if len(players) < 10:
        return None

    pool = players[:]
    random.shuffle(pool)
    return pool[:5], pool[5:10]


def find_best_team_match(players, target_player_id=None, trials=1):
    if len(players) < 10:
        return None, None

    best_pair = None
    best_score = float("inf")
    best_avg_diff = float("inf")

    combos = list(itertools.combinations(players, 5))

    if len(combos) > 3000:
        combos = random.sample(combos, 3000)

    for team1_tuple in combos:
        team1 = list(team1_tuple)
        team2 = [p for p in players if p not in team1]

        if len(team2) < 5:
            continue

        team2 = team2[:5]

        avg_diff = abs(team_average(team1) - team_average(team2))
        current_score = score_match(team1, team2)

        if current_score < best_score:
            best_score = current_score
            best_avg_diff = avg_diff
            best_pair = (team1, team2)

    if best_pair is not None:
        return best_pair, round(best_avg_diff, 2)

    fallback = fallback_random_teams(players)
    if fallback is not None:
        team1, team2 = fallback
        return (team1, team2), round(abs(team_average(team1) - team_average(team2)), 2)

    players = players[:10]
    team1 = players[:5]
    team2 = players[5:10]
    return (team1, team2), round(abs(team_average(team1) - team_average(team2)), 2)
