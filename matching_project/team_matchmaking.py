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


def pick_near_players(players, target_player_id=None, count=14):
    if target_player_id is None:
        return sorted(players, key=lambda x: x["skill"])[:count]

    target = None
    for p in players:
        if p["id"] == target_player_id:
            target = p
            break

    if target is None:
        return None

    target_limit = allowed_gap(target["skill"])
    others = [p for p in players if p["id"] != target_player_id]

    close_players = [
        p for p in others
        if abs(p["skill"] - target["skill"]) <= target_limit
    ]
    close_players = sorted(close_players, key=lambda x: abs(x["skill"] - target["skill"]))

    mid_players = [
        p for p in others
        if target_limit < abs(p["skill"] - target["skill"]) <= target_limit + 400
    ]
    mid_players = sorted(mid_players, key=lambda x: abs(x["skill"] - target["skill"]))

    far_players = [
        p for p in others
        if abs(p["skill"] - target["skill"]) > target_limit + 400
    ]
    random.shuffle(far_players)

    selected = [target]
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


def balance_role_group(group):
    group = sorted(group, key=lambda x: x["skill"], reverse=True)

    team1 = []
    team2 = []

    for i, p in enumerate(group):
        if i % 2 == 0:
            team1.append(p)
        else:
            team2.append(p)

    return team1, team2


def is_team_gap_valid(team):
    skills = [p["skill"] for p in team]
    diff = max(skills) - min(skills)

    for p in team:
        if diff > allowed_gap(p["skill"]):
            return False
    return True


def build_balanced_teams(players):
    role_map = split_by_role(players)

    tanks = sorted(role_map["tank"], key=lambda x: x["skill"], reverse=True)
    dpss = sorted(role_map["dps"], key=lambda x: x["skill"], reverse=True)
    supports = sorted(role_map["support"], key=lambda x: x["skill"], reverse=True)

    if len(tanks) < 2 or len(dpss) < 4 or len(supports) < 4:
        return None

    tanks = tanks[:2]
    dpss = dpss[:4]
    supports = supports[:4]

    t1_tank, t2_tank = balance_role_group(tanks)
    t1_dps, t2_dps = balance_role_group(dpss)
    t1_sup, t2_sup = balance_role_group(supports)

    team1 = t1_tank + t1_dps + t1_sup
    team2 = t2_tank + t2_dps + t2_sup

    if len(team1) != 5 or len(team2) != 5:
        return None

    if not is_team_gap_valid(team1):
        return None
    if not is_team_gap_valid(team2):
        return None

    return team1, team2


def score_match(team1, team2):
    avg_diff = abs(team_average(team1) - team_average(team2))
    std_penalty = team_std(team1) + team_std(team2)
    return avg_diff + std_penalty * 0.1


def fallback_random_teams(players):
    shuffled = players[:]
    random.shuffle(shuffled)

    assigned = assign_roles(shuffled[:10])
    role_map = split_by_role(assigned)

    if len(role_map["tank"]) < 2 or len(role_map["dps"]) < 4 or len(role_map["support"]) < 4:
        return assigned[:5], assigned[5:10]

    tanks = role_map["tank"][:2]
    dpss = role_map["dps"][:4]
    supports = role_map["support"][:4]

    team1 = [tanks[0], dpss[0], dpss[1], supports[0], supports[1]]
    team2 = [tanks[1], dpss[2], dpss[3], supports[2], supports[3]]

    return team1, team2


def find_best_team_match(players, target_player_id=None, trials=150):
    candidate_players = pick_near_players(players, target_player_id, 14)

    if candidate_players is None or len(candidate_players) < 10:
        if len(players) < 10:
            return None, None
        team1, team2 = fallback_random_teams(players)
        return (team1, team2), round(abs(team_average(team1) - team_average(team2)), 2)

    best_pair = None
    best_score = float("inf")
    best_avg_diff = None

    for _ in range(trials):
        assigned = assign_roles(candidate_players)
        built = build_balanced_teams(assigned)

        if built is None:
            team1, team2 = fallback_random_teams(candidate_players)
        else:
            team1, team2 = built

        avg_diff = abs(team_average(team1) - team_average(team2))
        current_score = score_match(team1, team2)

        if current_score < best_score:
            best_score = current_score
            best_avg_diff = avg_diff
            best_pair = (team1, team2)

    if best_pair is None:
        return None, None

    return best_pair, round(best_avg_diff, 2)   


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


def pick_near_players(players, target_player_id=None, count=14):
    """
    target 주변 플레이어를 우선적으로 뽑되,
    너무 같은 점수대만 모이지 않게 일부는 넓은 범위에서 섞음
    """
    if target_player_id is None:
        return sorted(players, key=lambda x: x["skill"])[:count]

    target = None
    for p in players:
        if p["id"] == target_player_id:
            target = p
            break

    if target is None:
        return None

    target_limit = allowed_gap(target["skill"])
    others = [p for p in players if p["id"] != target_player_id]

    close_players = [
        p for p in others
        if abs(p["skill"] - target["skill"]) <= target_limit
    ]
    close_players = sorted(close_players, key=lambda x: abs(x["skill"] - target["skill"]))

    mid_players = [
        p for p in others
        if target_limit < abs(p["skill"] - target["skill"]) <= target_limit + 400
    ]
    mid_players = sorted(mid_players, key=lambda x: abs(x["skill"] - target["skill"]))

    far_players = [
        p for p in others
        if abs(p["skill"] - target["skill"]) > target_limit + 400
    ]
    random.shuffle(far_players)

    selected = [target]
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


def balance_role_group(group):
    group = sorted(group, key=lambda x: x["skill"], reverse=True)

    team1 = []
    team2 = []

    for i, p in enumerate(group):
        if i % 2 == 0:
            team1.append(p)
        else:
            team2.append(p)

    return team1, team2


def is_team_gap_valid(team):
    skills = [p["skill"] for p in team]
    diff = max(skills) - min(skills)

    for p in team:
        if diff > allowed_gap(p["skill"]):
            return False
    return True


def build_balanced_teams(players):
    role_map = split_by_role(players)

    # 후보 중 역할 많은 순으로 상위 사용
    tanks = sorted(role_map["tank"], key=lambda x: x["skill"], reverse=True)
    dpss = sorted(role_map["dps"], key=lambda x: x["skill"], reverse=True)
    supports = sorted(role_map["support"], key=lambda x: x["skill"], reverse=True)

    if len(tanks) < 2 or len(dpss) < 4 or len(supports) < 4:
        return None

    tanks = tanks[:2]
    dpss = dpss[:4]
    supports = supports[:4]

    t1_tank, t2_tank = balance_role_group(tanks)
    t1_dps, t2_dps = balance_role_group(dpss)
    t1_sup, t2_sup = balance_role_group(supports)

    team1 = t1_tank + t1_dps + t1_sup
    team2 = t2_tank + t2_dps + t2_sup

    if len(team1) != 5 or len(team2) != 5:
        return None

    if not is_team_gap_valid(team1):
        return None
    if not is_team_gap_valid(team2):
        return None

    return team1, team2


def score_match(team1, team2):
    avg_diff = abs(team_average(team1) - team_average(team2))
    std_penalty = team_std(team1) + team_std(team2)
    return avg_diff + std_penalty * 0.1


def find_best_team_match(players, target_player_id=None, trials=150):
    """
    실패 시 평균 차이 허용 범위를 단계적으로 완화
    """
    relax_steps = [0, 100, 200, 300, 400]

    candidate_players = pick_near_players(players, target_player_id, 14)

    if candidate_players is None or len(candidate_players) < 10:
        return None, None

    for relax in relax_steps:
        best_pair = None
        best_score = float("inf")
        best_avg_diff = None

        for _ in range(trials):
            assigned = assign_roles(candidate_players)
            built = build_balanced_teams(assigned)

            if built is None:
                continue

            team1, team2 = built
            avg_diff = abs(team_average(team1) - team_average(team2))

            # 단계적 완화
            if avg_diff > (300 + relax):
                continue

            current_score = score_match(team1, team2)

            if current_score < best_score:
                best_score = current_score
                best_avg_diff = avg_diff
                best_pair = (team1, team2)

        if best_pair is not None:
            return best_pair, round(best_avg_diff, 2)

    return None, None
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


def pick_near_players(players, target_player_id=None, count=10):
    if target_player_id is None:
        return sorted(players, key=lambda x: x["skill"])[:count]

    target = None
    for p in players:
        if p["id"] == target_player_id:
            target = p
            break

    if target is None:
        return None

    target_limit = allowed_gap(target["skill"])
    others = [p for p in players if p["id"] != target_player_id]

    close_players = [
        p for p in others
        if abs(p["skill"] - target["skill"]) <= target_limit
    ]
    close_players = sorted(close_players, key=lambda x: abs(x["skill"] - target["skill"]))

    mid_players = [
        p for p in others
        if target_limit < abs(p["skill"] - target["skill"]) <= target_limit + 300
    ]
    mid_players = sorted(mid_players, key=lambda x: abs(x["skill"] - target["skill"]))

    far_players = [
        p for p in others
        if abs(p["skill"] - target["skill"]) > target_limit + 300
    ]
    random.shuffle(far_players)

    selected = [target]
    selected += close_players[:6]
    selected += mid_players[:3]

    remaining = count - len(selected)
    if remaining > 0:
        selected += far_players[:remaining]

    return selected[:count]


def split_by_role(players):
    role_map = {"tank": [], "dps": [], "support": []}
    for p in players:
        role_map[p["role"]].append(p)
    return role_map


def balance_role_group(group):
    group = sorted(group, key=lambda x: x["skill"], reverse=True)

    team1, team2 = [], []

    for i, p in enumerate(group):
        if i % 2 == 0:
            team1.append(p)
        else:
            team2.append(p)

    return team1, team2


def is_team_gap_valid(team):
    skills = [p["skill"] for p in team]
    diff = max(skills) - min(skills)

    for p in team:
        if diff > allowed_gap(p["skill"]):
            return False
    return True


def build_balanced_teams(players):
    role_map = split_by_role(players)

    if len(role_map["tank"]) < 2 or len(role_map["dps"]) < 4 or len(role_map["support"]) < 4:
        return None

    tanks = role_map["tank"][:2]
    dpss = role_map["dps"][:4]
    supports = role_map["support"][:4]

    t1_tank, t2_tank = balance_role_group(tanks)
    t1_dps, t2_dps = balance_role_group(dpss)
    t1_sup, t2_sup = balance_role_group(supports)

    team1 = t1_tank + t1_dps + t1_sup
    team2 = t2_tank + t2_dps + t2_sup

    if not is_team_gap_valid(team1):
        return None
    if not is_team_gap_valid(team2):
        return None

    return team1, team2


def score_match(team1, team2):
    avg_diff = abs(team_average(team1) - team_average(team2))
    std_penalty = team_std(team1) + team_std(team2)
    return avg_diff + std_penalty * 0.1


def find_best_team_match(players, target_player_id=None, trials=120):
    """
    실패 시 조건을 자동 완화
    """

    relax_steps = [0, 100, 200, 300]

    for relax in relax_steps:

        candidate_players = pick_near_players(players, target_player_id, 10)

        if candidate_players is None or len(candidate_players) < 10:
            continue

        best_pair = None
        best_score = float("inf")

        for _ in range(trials):
            assigned = assign_roles(candidate_players)
            built = build_balanced_teams(assigned)

            if built is None:
                continue

            team1, team2 = built
            avg_diff = abs(team_average(team1) - team_average(team2))

            # 🔥 조건 완화 적용
            if avg_diff > (300 + relax):
                continue

            score = score_match(team1, team2)

            if score < best_score:
                best_score = score
                best_pair = (team1, team2)

        if best_pair:
            return best_pair, round(avg_diff, 2)

    return None, None
