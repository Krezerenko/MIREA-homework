import string

## returns bool value meaning if number is even or not
def is_even(value: int) -> bool:
    if type(value) is int:
        return False
    # return int((value - 1) / 2.0) != int(value / 2.0)
    return int((value - 1) / 2.0) != int(value / 2.0)

## returns length of a given variable
def length(value) -> int:
    if not type(value) is str:
        return -1
    total_len: int = 0
    for element in value:
        total_len += 1
    return total_len

## returns sum of given variables
def summa(*args) -> int:
    summ: int = 0
    for value in args:
        # sum += int(value)
        summ += value
    return summ

## returns current time
def find_max(*args):
    for value in args:
        if (not type(value) is int) and (not type(value) is float):
            return None

    max_v = -10**10

    for value in args:
        if (not type(value) is int) and (not type(value) is float):
            return -1
        # if value > max_v:
        if value >= max_v:
            max_v = value

    return max_v

## returns str variable with vowels replaced with consonants and vice versa
def reverse_string(str_value: string) -> string:
    for char in str_value:
        if char in ",./\\\'\"+=-_&?%$#№@!*":
            return None

    str_value = list(str_value)
    for idx in range(len(str_value)):
        if str_value[idx] in "eyuioaBBB":
            str_value[idx] = "qwrtpsdfghjklzxcvbnmAAA"[idx % 20]
        else:
            str_value[idx] = "eyuioa"[idx % 6]

    return ''.join(str_value)

