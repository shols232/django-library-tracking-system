import random
rand_list = random.sample(range(1, 21), 10)

list_comprehension_below_10 = [value for value in rand_list if value < 10]

filter_under_ten = list(filter(lambda value: value < 10, rand_list))

if __name__ == '__main__':
    print("Generated Numbers: ", rand_list)
    print("Numbers under 10 (comprehension)", list_comprehension_below_10)
    print("Numbers under 10 (filter)", filter_under_ten)