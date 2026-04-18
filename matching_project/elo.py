def expected_score(a, b):
    return 1 / (1 + 10 ** ((b - a) / 400))

def update_rating(rating_a, rating_b, result_a, k=32):
    exp_a = expected_score(rating_a, rating_b)

    new_a = rating_a + k * (result_a - exp_a)
    new_b = rating_b + k * ((1 - result_a) - (1 - exp_a))

    return round(new_a), round(new_b)
