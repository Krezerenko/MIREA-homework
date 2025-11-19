from activate_this import length, find_max, summa, reverse_string, is_even

def test_len_function():
    assert length("asdasd") == 6, "Error: wrong len outcome"
    assert length("borda") == 5, "Error: wrong len outcome"
    assert length("ani_shima_") == 10, "Error: wrong len outcome"

def test_find_max_time_function():
    assert find_max(4, 2, 2, 4.000006) == 4.000006, "Error: wrong max value outcome"
    assert find_max(-3, -1, -199, -32) == -1, "Error: wrong max value outcome"
    assert find_max(-1023, 123, 123.000000000000000000000000000006) == 123.000000000000000000000000000006, "Error: wrong max value outcome"

def test_sum_function():
    assert summa(1,2,3) == 6, "Error sum returns wrong answer"
    assert summa(12, -5, -3, 7, 1, 0.5) == 12.5, "Error sum returns wrong answer"

def test_reverse_string_function():
    assert reverse_string("aboba") == "qyrip", "Error reverse_string returns wrong answer"
    assert reverse_string("ginger") == "ewuipa", "Error reverse_string returns wrong answer"

def test_is_even_function():
    assert is_even(5) == False, "Error is_even returns wrong answer"
    assert is_even(10000) == True, "Error is_even returns wrong answer"
