import random

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


def allowed_gap(skill):
    tier = get_tier(skill)

    if tier in ["Diamond", "Master", "Grandmaster", "Champion"]:
        base = 600
    else:
        base = 1000

    # 저점 구간 보정
    if skill < 2000:
        base += 400

    return base


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

    return best_pair, round(best_avg_diff, 2)    return base


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
