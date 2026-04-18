import random

# 5인 팀 역할 구성
TEAM_ROLES = ["tank", "dps", "dps", "support", "support"]


def team_average(team):
    return sum(p["skill"] for p in team) / len(team)


def team_std(team):
    avg = team_average(team)
    variance = sum((p["skill"] - avg) ** 2 for p in team) / len(team)
    return variance ** 0.5


def assign_roles(players):
    """
    플레이어들에게 1탱 2딜 2힐 구조가 반복되도록 역할 부여
    """
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
    특정 플레이어(YOU)를 기준으로 점수가 가까운 플레이어 count명을 선택
    """
    if target_player_id is None:
        sorted_players = sorted(players, key=lambda x: x["skill"])
        return sorted_players[:count]

    target = None
    for p in players:
        if p["id"] == target_player_id:
            target = p
            break

    if target is None:
        return sorted(players, key=lambda x: x["skill"])[:count]

    others = [p for p in players if p["id"] != target_player_id]
    others = sorted(others, key=lambda x: abs(x["skill"] - target["skill"]))

    selected = [target] + others[:count - 1]
    return selected


def split_by_role(players):
    """
    역할별로 분리
    """
    role_map = {
        "tank": [],
        "dps": [],
        "support": []
    }

    for p in players:
        role_map[p["role"]].append(p)

    return role_map


def balance_role_group(group):
    """
    같은 역할군 안에서 강한 사람/약한 사람을 교차 분배해
    양 팀 평균을 비슷하게 맞춤
    """
    group = sorted(group, key=lambda x: x["skill"], reverse=True)

    team1 = []
    team2 = []

    for i, p in enumerate(group):
        if i % 2 == 0:
            team1.append(p)
        else:
            team2.append(p)

    # 역할군 인원이 홀수면 더 균형 맞게 조정
    if len(team1) > len(team2) + 1:
        team2.append(team1.pop())
    elif len(team2) > len(team1) + 1:
        team1.append(team2.pop())

    return team1, team2


def build_balanced_teams(players):
    """
    선택된 플레이어들로 역할 균형 + 점수 균형 팀 구성
    """
    role_map = split_by_role(players)

    # 역할이 부족하면 실패
    if len(role_map["tank"]) < 2 or len(role_map["dps"]) < 4 or len(role_map["support"]) < 4:
        return None

    # 필요한 수만 사용
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

    return team1, team2


def score_match(team1, team2):
    """
    낮을수록 좋은 매칭
    - 팀 평균 차이
    - 팀 내부 편차
    """
    avg_diff = abs(team_average(team1) - team_average(team2))
    std_penalty = team_std(team1) + team_std(team2)
    return avg_diff + std_penalty * 0.1


def find_best_team_match(players, target_player_id=None, trials=30):
    """
    여러 번 역할을 랜덤 배정해보고 가장 균형 좋은 팀 찾기
    조합 완전탐색 대신 trials번 반복으로 속도 개선
    """
    candidate_players = pick_near_players(players, target_player_id=target_player_id, count=10)

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
