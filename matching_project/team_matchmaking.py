import random
from itertools import combinations

TEAM_ROLES = ["tank", "dps", "dps", "support", "support"]


def get_tier(skill):
    if skill < 1500:
        return "Bronze"
    elif skill < 2000:
        return "Silver"
    elif skill < 2500:
        return "Gold"
    elif skill < 3000:
        return "Platinum"
    elif skill < 3500:
        return "Diamond"
    elif skill < 4000:
        return "Master"
    elif skill < 4500:
        return "Grandmaster"
    else:
        return "Champion"


def get_range_type(skill):
    if skill < 2000:
        return "low"
    elif skill < 3000:
        return "mid"
    else:
        return "high"


def allowed_gap(skill):
    range_type = get_range_type(skill)

    if range_type == "low":
        return 1500
    elif range_type == "mid":
        return 1100
    else:
        return 600


def candidate_count(skill):
    range_type = get_range_type(skill)

    if range_type == "low":
        return 24
    elif range_type == "mid":
        return 18
    else:
        return 14


def team_average(team):
    return sum(p["skill"] for p in team) / len(team)


def team_std(team):
    avg = team_average(team)
    variance = sum((p["skill"] - avg) ** 2 for p in team) / len(team)
    return variance ** 0.5


def assign_roles(players):
    shuffled = players[:]
    random.shuffle(shuffled)

    assigned = []
    for i, p in enumerate(shuffled):
        new_p = p.copy()
        new_p["role"] = TEAM_ROLES[i % len(TEAM_ROLES)]
        assigned.append(new_p)

    return assigned


def pick_near_players(players, target_player_id=None):
    if target_player_id is None:
        return sorted(players, key=lambda x: x["skill"])[:14]

    target = None
    for p in players:
        if p["id"] == target_player_id:
            target = p
            break

    if target is None:
        return None

    count = candidate_count(target["skill"])
    target_limit = allowed_gap(target["skill"])

    others = [p for p in players if p["id"] != target_player_id]

    close_players = [
        p for p in others
        if abs(p["skill"] - target["skill"]) <= target_limit
    ]
    close_players = sorted(
        close_players,
        key=lambda x: abs(x["skill"] - target["skill"])
    )

    mid_players = [
        p for p in others
        if target_limit < abs(p["skill"] - target["skill"]) <= target_limit + 500
    ]
    mid_players = sorted(
        mid_players,
        key=lambda x: abs(x["skill"] - target["skill"])
    )

    far_players = [
        p for p in others
        if abs(p["skill"] - target["skill"]) > target_limit + 500
    ]
    random.shuffle(far_players)

    selected = [target]

    if count >= 20:
        selected += close_players[:10]
        selected += mid_players[:8]
    elif count >= 18:
        selected += close_players[:8]
        selected += mid_players[:6]
    else:
        selected += close_players[:8]
        selected += mid_players[:4]

    remaining = count - len(selected)
    if remaining > 0:
        selected += far_players[:remaining]

    return selected[:count]


def split_by_role(players):
    role_map = {"tank": [], "dps": [], "support": []}
    for p in players:
        role_map[p["role"]].append(p)
    return role_map


def build_team_from_role_groups(tanks, dpss, supports):
    team1 = [tanks[0], dpss[0], dpss[1], supports[0], supports[1]]
    team2 = [tanks[1], dpss[2], dpss[3], supports[2], supports[3]]
    return team1, team2


def is_team_gap_valid(team):
    skills = [p["skill"] for p in team]
    diff = max(skills) - min(skills)

    for p in team:
        if diff > allowed_gap(p["skill"]):
            return False
    return True


def score_match(team1, team2):
    avg_diff = abs(team_average(team1) - team_average(team2))
    std_penalty = team_std(team1) + team_std(team2)
    return avg_diff + std_penalty * 0.1


def fallback_random_teams(players):
    pool = players[:]
    random.shuffle(pool)

    if len(pool) < 10:
        return None

    selected = assign_roles(pool[:10])
    return selected[:5], selected[5:10]


def build_best_pair_from_candidates(players):
    role_map = split_by_role(players)

    tanks = sorted(role_map["tank"], key=lambda x: x["skill"], reverse=True)
    dpss = sorted(role_map["dps"], key=lambda x: x["skill"], reverse=True)
    supports = sorted(role_map["support"], key=lambda x: x["skill"], reverse=True)

    if len(tanks) < 2 or len(dpss) < 4 or len(supports) < 4:
        return None, None, None

    tanks = tanks[:2]
    dpss = dpss[:4]
    supports = supports[:4]

    best_valid_pair = None
    best_valid_score = float("inf")
    best_valid_diff = None

    best_any_pair = None
    best_any_score = float("inf")
    best_any_diff = None

    dps_combos = list(combinations(dpss, 2))
    sup_combos = list(combinations(supports, 2))

    for dps_team1 in dps_combos:
        dps_team2 = [p for p in dpss if p not in dps_team1]

        for sup_team1 in sup_combos:
            sup_team2 = [p for p in supports if p not in sup_team1]

            team1 = [tanks[0]] + list(dps_team1) + list(sup_team1)
            team2 = [tanks[1]] + list(dps_team2) + list(sup_team2)

            avg_diff = abs(team_average(team1) - team_average(team2))
            current_score = score_match(team1, team2)

            if current_score < best_any_score:
                best_any_score = current_score
                best_any_diff = avg_diff
                best_any_pair = (team1, team2)

            if is_team_gap_valid(team1) and is_team_gap_valid(team2):
                if current_score < best_valid_score:
                    best_valid_score = current_score
                    best_valid_diff = avg_diff
                    best_valid_pair = (team1, team2)

    if best_valid_pair is not None:
        return best_valid_pair[0], best_valid_pair[1], round(best_valid_diff, 2)

    if best_any_pair is not None:
        return best_any_pair[0], best_any_pair[1], round(best_any_diff, 2)

    return None, None, None


def find_best_team_match(players, target_player_id=None, trials=60):
    candidate_players = pick_near_players(players, target_player_id)

    if candidate_players is None or len(candidate_players) < 10:
        fallback = fallback_random_teams(players)
        if fallback is None:
            return None, None
        team1, team2 = fallback
        return (team1, team2), round(abs(team_average(team1) - team_average(team2)), 2)

    best_pair = None
    best_score = float("inf")
    best_avg_diff = None

    for _ in range(trials):
        assigned = assign_roles(candidate_players)

        team1, team2, avg_diff = build_best_pair_from_candidates(assigned)

        if team1 is None or team2 is None:
            fallback = fallback_random_teams(candidate_players)
            if fallback is None:
                continue
            team1, team2 = fallback
            avg_diff = abs(team_average(team1) - team_average(team2))

        current_score = score_match(team1, team2)

        if current_score < best_score:
            best_score = current_score
            best_avg_diff = avg_diff
            best_pair = (team1, team2)

    if best_pair is None:
        fallback = fallback_random_teams(players)
        if fallback is None:
            return None, None
        team1, team2 = fallback
        return (team1, team2), round(abs(team_average(team1) - team_average(team2)), 2)

    return best_pair, round(best_avg_diff, 2)
