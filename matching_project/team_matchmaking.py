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

    # 다이아부터는 500으로 더 엄격하게
    if tier in ["Diamond", "Master", "Grandmaster", "Champion"]:
        return 500
    else:
        return 1000


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


def pick_near_players(players, target_player_id=None, count=10):
    if target_player_id is None:
        return sorted(players, key=lambda x: x["skill"])[:count]

    target = None
    for p in players:
        if p["id"] == target_player_id:
            target = p
            break

    if target is None:
        return sorted(players, key=lambda x: x["skill"])[:count]

    target_limit = allowed_gap(target["skill"])

    others = []
    for p in players:
        if p["id"] == target_player_id:
            continue

        diff = abs(p["skill"] - target["skill"])

        # target 기준 허용 범위
        if diff <= target_limit:
            others.append(p)

    others = sorted(others, key=lambda x: abs(x["skill"] - target["skill"]))

    selected = [target] + others[:count - 1]
    return selected


def split_by_role(players):
    role_map = {
        "tank": [],
        "dps": [],
        "support": []
    }

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

    if len(team1) > len(team2) + 1:
        team2.append(team1.pop())
    elif len(team2) > len(team1) + 1:
        team1.append(team2.pop())

    return team1, team2


def is_team_gap_valid(team):
    """
    같은 팀 안에서 팀원 간 점수 차이가 허용 범위를 넘는지 검사
    각 플레이어의 tier 기준을 모두 만족해야 함
    """
    skills = [p["skill"] for p in team]
    max_skill = max(skills)
    min_skill = min(skills)
    diff = max_skill - min_skill

    for p in team:
        if diff > allowed_gap(p["skill"]):
            return False

    return True


def build_balanced_teams(players):
    role_map = split_by_role(players)

    if len(role_map["tank"]) < 2 or len(role_map["dps"]) < 4 or len(role_map["support"]) < 4:
        return None

    tanks = sorted(role_map["tank"], key=lambda x: x["skill"], reverse=True)[:2]
    dpss = sorted(role_map["dps"], key=lambda x: x["skill"], reverse=True)[:4]
    supports = sorted(role_map["support"], key=lambda x: x["skill"], reverse=True)[:4]

    tank_team1, tank_team2 = balance_role_group(tanks)
    dps_team1, dps_team2 = balance_role_group(dpss)
    sup_team1, sup_team2 = balance_role_group(supports)

    if not (len(tank_team1) == 1 and len(tank_team2) == 1):
        return None
    if not (len(dps_team1) == 2 and len(dps_team2) == 2):
        return None
    if not (len(sup_team1) == 2 and len(sup_team2) == 2):
        return None

    team1 = tank_team1 + dps_team1 + sup_team1
    team2 = tank_team2 + dps_team2 + sup_team2

    # 새 규칙 적용
    if not is_team_gap_valid(team1):
        return None
    if not is_team_gap_valid(team2):
        return None

    return team1, team2


def score_match(team1, team2):
    avg_diff = abs(team_average(team1) - team_average(team2))
    std_penalty = team_std(team1) + team_std(team2)
    return avg_diff + std_penalty * 0.1


def find_best_team_match(players, target_player_id=None, trials=50):
    candidate_players = pick_near_players(players, target_player_id=target_player_id, count=10)

    # 사람이 너무 적으면 실패
    if len(candidate_players) < 10:
        return None, None

    best_pair = None
    best_score = float("inf")
    best_avg_diff = None

    for _ in range(trials):
        assigned = assign_roles(candidate_players)
        built = build_balanced_teams(assigned)

        if built is None:
            continue

        team1, team2 = built
        current_score = score_match(team1, team2)
        current_avg_diff = abs(team_average(team1) - team_average(team2))

        if current_score < best_score:
            best_score = current_score
            best_avg_diff = current_avg_diff
            best_pair = (team1, team2)

    if best_pair is None:
        return None, None

    return best_pair, round(best_avg_diff, 2)
