from komisarik import factorial, fibonacci, count_vowels, \
    count_words, validate_email
import pytest


def test_factorial():
    with pytest.raises(ValueError):
        factorial(-1)
        factorial("not int")
        factorial(0.5)
    assert factorial(0) == 1
    assert factorial(1) == 1
    assert factorial(5) == 120


def test_fibonacci():
    assert fibonacci(1) == [0]
    assert fibonacci(2) == [0, 1]
    assert fibonacci(7) == [0, 1, 1, 2, 3, 5, 8]


def test_count_vowels():
    assert count_vowels("lol") == 1
    assert count_vowels("break") == 2
    assert count_vowels("") == 0
    for syllable in "bcdfghjklmnpqrstvwxz":
        assert count_vowels(syllable) == 0


def test_count_words():
    assert count_words("") == 0
    assert count_words("dread") == 1
    assert count_words("google en passant. holy hell") == 5


def test_validate_email():
    assert validate_email("") is False
    assert validate_email("wrong.a") is False
    assert validate_email("wrong@some.g") is False
    assert validate_email("some email@gmail.com") is False
    assert validate_email("e\"ma!il@y$a n/de^x.r#u") is False
    assert validate_email("n%um_s.NU+MS-1234@nums-NUMS.1234.cOM") is True
