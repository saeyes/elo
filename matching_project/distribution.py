import random


def generate_players(n=60):
    players = []

    for i in range(n):
        r = random.random()

        if r < 0.024:
            skill = random.randint(0, 1499)
        elif r < 0.024 + 0.124:
            skill = random.randint(1500, 1999)
        elif r < 0.024 + 0.124 + 0.317:
            skill = random.randint(2000, 2499)
        elif r < 0.024 + 0.124 + 0.317 + 0.349:
            skill = random.randint(2500, 2999)
        elif r < 0.024 + 0.124 + 0.317 + 0.349 + 0.149:
            skill = random.randint(3000, 3499)
        elif r < 0.024 + 0.124 + 0.317 + 0.349 + 0.149 + 0.032:
            skill = random.randint(3500, 3999)
        elif r < 0.024 + 0.124 + 0.317 + 0.349 + 0.149 + 0.032 + 0.003:
            skill = random.randint(4000, 4499)
        else:
            skill = random.randint(4500, 5000)

        players.append({
            "id": f"P{i+1}",
            "skill": skill
        })

    return players
