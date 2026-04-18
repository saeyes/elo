import random
from itertools import combinations

# 역할 구성: 1탱 2딜 2힐
ROLES = ["tank", "dps", "dps", "support", "support"]


def assign_roles(players):
    """
    플레이어에게 역할을 순환 방식으로 배정
    """
    shuffled = players[:]
    random.shuffle(shuffled)

    assigned = []
    for i, p in enumerate(shuffled):
        new_p = p.copy()
        new_p["role"] = ROLES[i % len(ROLES)]
        assigned.append(new_p)

    return assigned


def valid_team(team):
    """
    팀이 1탱 2딜 2힐인지 확인
    """
    roles = sorted([p["role"] for p in team])
    return roles == ["dps", "dps", "support", "support", "tank"]


def team_average(team):
    """
    팀 평균 MMR 계산
    👉 app.py에서 import해서 쓰는 핵심 함수
    """
    return sum(p["skill"] for p in team) / len(team)


def team_std(team):
    """
    팀 내부 점수 편차 계산
    """
    avg = team_average(team)
    variance = sum((p["skill"] - avg) ** 2 for p in team) / len(team)
    return variance ** 0.5


def score_match(team1, team2):
    """
    매칭 점수 (낮을수록 좋음)
    - 팀 평균 차이
    - 팀 내부 편차
    """
    avg_diff = abs(team_average(team1) - team_average(team2))
    balance_penalty = team_std(team1) + team_std(team2)

    return avg_diff + (balance_penalty * 0.1)


def find_best_team_match(players, target_player_id=None):
    """
    가장 공정한 팀 매칭 찾기
    """
    players_with_roles = assign_roles(players)

    candidate_teams = [
        team for team in combinations(players_with_roles, 5)
        if valid_team(team)
    ]

    best_pair = None
    best_score = float("inf")
    best_avg_diff = float("inf")

    for team1, team2 in combinations(candidate_teams, 2):
        ids1 = {p["id"] for p in team1}
        ids2 = {p["id"] for p in team2}

        # 같은 플레이어 중복 방지
        if ids1 & ids2:
            continue

        # 특정 플레이어 포함 조건 (YOU)
        if target_player_id is not None:
            if target_player_id not in ids1 and target_player_id not in ids2:
                continue

        current_score = score_match(team1, team2)
        current_avg_diff = abs(team_average(team1) - team_average(team2))

        if current_score < best_score:
            best_score = current_score
            best_avg_diff = current_avg_diff
            best_pair = (list(team1), list(team2))

    if best_pair is None:
        return None, None

    return best_pair, round(best_avg_diff, 2)
