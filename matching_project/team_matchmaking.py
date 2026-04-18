import random

ROLES = ["tank", "dps", "dps", "support", "support"]


def assign_roles(players):
    players = players[:]
    random.shuffle(players)

    for i, p in enumerate(players):
        p["role"] = ROLES[i % 5]

    return players


def split_teams(players):
    random.shuffle(players)
    return players[:5], players[5:10]


def team_avg(team):
    return sum(p["skill"] for p in team) / len(team)


def team_std(team):
    avg = team_avg(team)
    return (sum((p["skill"] - avg) ** 2 for p in team) / len(team)) ** 0.5


def score(team1, team2):
    return abs(team_avg(team1) - team_avg(team2)) + (team_std(team1) + team_std(team2)) * 0.1


def find_best_team_match(players, target_player_id=None, trials=200):
    players = assign_roles(players)

    best = None
    best_score = float("inf")

    for _ in range(trials):
        sample = random.sample(players, 10)

        team1, team2 = split_teams(sample)

        if target_player_id:
            ids = [p["id"] for p in team1 + team2]
            if target_player_id not in ids:
                continue

        s = score(team1, team2)

        if s < best_score:
            best_score = s
            best = (team1, team2)

    return best, best_score
