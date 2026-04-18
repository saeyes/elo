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

    # 다이아부터 더 엄격하게
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
    """
    특정 플레이어를 기준으로:
    - 가까운 플레이어 위주
    - 일부는 조금 더 넓은 범위
    를 섞어서 선택
    """
    if target_player_id is None:
        sorted_players = sorted(players, key=lambda x: x["skill"])
        return sorted_players[:count]

    target = None

    # 1. 먼저 target 찾기
    for p in players:
        if p["id"] == target_player_id:
            target = p
            break

    # target 없으면 실패
    if target is None:
        return None

    target_limit = allowed_gap(target["skill"])
    others = [p for p in players if p["id"] != target_player_id]

    # 2. 아주 가까운 플레이어
    close_players = [
        p for p in others
        if abs(p["skill"] - target["skill"]) <= target_limit
    ]
    close_players = sorted(
        close_players,
        key=lambda x: abs(x["skill"] - target["skill"])
    )

    # 3. 중간 범위 플레이어
    mid_players = [
        p for p in others
        if target_limit < abs(p["skill"] - target["skill"]) <= target_limit + 300
    ]
    mid_players = sorted(
        mid_players,
        key=lambda x: abs(x["skill"] - target["skill"])
    )

    # 4. 먼 플레이어
    far_players = [
        p for p in others
        if abs(p["skill"] - target["skill"]) > target_limit + 300
    ]
    random.shuffle(far_players)

    selected = [target]

    # 가까운 플레이어 우선
    selected += close_players[:6]

    # 중간 범위 일부
    selected += mid_players[:3]

    # 부족하면 먼 플레이어로 채움
    remaining = count - len(selected)
    if remaining > 0:
        selected += far_players[:remaining]

    return selected[:count]


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
    한 팀 내부 최대 점수 차이가 각 플레이어 기준 허용 범위를 넘지 않는지 검사
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

    # 역할 수 부족하면 실패
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

    # 팀 내부 격차 검사
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
    candidate_players = pick_near_players(players, target_player_id=target_player_id, count=10)

    if candidate_players is None or len(candidate_players) < 10:
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
