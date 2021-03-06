from faker import Faker
import numpy as np
import sys
from datetime import date
import random
import demographics
from main_config import MainConfig
import pandas as pd


class Headers:
    """Store the headers and print to stdout to pipe into csv"""

    def __init__(self):
        header = ['ssn', 'cc_num', 'first', 'last', 'gender', 'street',
                  'city', 'state', 'zip', 'lat', 'long', 'city_pop',
                  'job', 'dob', 'acct_num', 'profile']
        self.headers = header

    def toString(self):
        return str(self.headers)


class Customer:
    """Randomly generates all the attributes for a customer"""

    def __init__(self):
        self.ssn = fake.ssn()
        self.gender, self.dob = self.generate_age_gender()
        self.first = self.get_first_name()
        self.last = fake.last_name()
        self.street = fake.street_address()
        self.addy = self.get_random_location()
        self.job = fake.job()
        self.cc = fake.credit_card_number()
        self.email = fake.email()
        self.account = fake.random_number(digits=12)
        self.profile = self.find_profile()

    def get_first_name(self):
        if self.gender == 'M':
            return fake.first_name_male()
        else:
            return fake.first_name_female()

    def generate_age_gender(self):

        a = np.random.random()
        c = []
        for b in age_gender.keys():
            if b > a:
                c.append(b)
        g_a = age_gender[min(c)]

        while True:
            dob = fake.date_time_this_century()

            # adjust the randomized date to yield the correct age
            start_age = (date.today() - date(dob.year, dob.month, dob.day)).days / 365.
            dob_year = dob.year - int(g_a[1] - int(start_age))

            # since the year is adjusted, sometimes Feb 29th won't be a day
            # in the adjusted year
            try:
                # return first letter of gender and dob
                return g_a[0][0], date(dob_year, dob.month, dob.day)
            except:
                pass

    # find nearest city
    def get_random_location(self):
        return cities[min(cities, key=lambda x: abs(x - random.random()))]

    def find_profile(self):
        age = (date.today() - self.dob).days / 365.25
        city_pop = float(self.addy.split('|')[-1])

        match = []
        for pro in all_profiles:
            # -1 represents infinity
            if self.gender in all_profiles[pro]['gender'] and \
                    age >= all_profiles[pro]['age'][0] and \
                    (age < all_profiles[pro]['age'][1] or all_profiles[pro]['age'][1] == -1) and \
                    city_pop >= all_profiles[pro]['city_pop'][0] and \
                    (city_pop < all_profiles[pro]['city_pop'][1] or
                     all_profiles[pro]['city_pop'][1] == -1):
                match.append(pro)
        if match == []:
            match.append('leftovers.json')

        # found overlap -- write to log file but continue
        if len(match) > 1:
            f = open('profile_overlap_warnings.log', 'a')
            output = ' '.join(match) + ': ' + self.gender + ' ' + \
                     str(age) + ' ' + str(city_pop) + '\n'
            f.write(output)
            f.close()
        return match[0]

    def toDataFrame(self):
        addy = self.addy.split("|")
        city = addy[0]
        state = addy[1]
        zip = addy[2]
        lat = addy[3]
        long = addy[4]
        city_pop = addy[5]
        customer_info = [[self.ssn, self.cc, self.first, self.last, self.gender,
                          self.street, city, state, zip, lat, long, city_pop, self.job, self.dob, self.account,
                          self.profile]]

        customer_df = pd.DataFrame(customer_info, columns=Headers().headers)
        return customer_df


def validate(argvs):
    print(argvs)
    global num_cust, seed_num, main, file_path

    def print_err(n):
        if n == 1:
            print('Error: invalid number of customers')
        elif n == 2:
            print('Error: invalid (non-integer) random seed')
        else:
            print('Error: main.config could not be opened')

        output = '\nENTER:\n (1) Number of customers\n '
        output += '(2) Random seed (int)\n '
        output += '(3) main_config.json'
        print(output)

    try:
        num_cust = int(argvs[0])
        ## num_cust = 15
    except:
        print_err(1)
    try:
        seed_num = int(argvs[1])
        ## seed_num = 4444
    except:
        print_err(2)
    try:
        m = argvs[2]
        print(m == 'profiles/main_config.json')
        m = 'profiles/main_config.json'
        main = open(m, 'r').read()
    except:
        print_err(3)

    try:
        file_path = argvs[3]
        ## data_path = '.\data\customers_test.csv'
    except:
        print_err(4)

    return num_cust, seed_num, main, file_path


# shell ?????? python datagen_customer_new.py 10 4444 ".\profiles\main_config.json" ".\data\customers3.csv"
# num_cust???????????? seed_num??????????????? main main_config.json??????  file_path csv??????????????????
if __name__ == '__main__':
    # read and validate stdin
    argvs = input().split(' ')

    num_cust, seed_num, main, file_path = validate(argvs)
    # num_cust = 10
    # seed_num = 4444
    # main = open(".\profiles\main_config.json", 'r').read()
    # data_path = '.\data\customers_test.csv'
    # from demographics module
    cities = demographics.make_cities()
    age_gender = demographics.make_age_gender_dict()

    fake = Faker()
    Faker.seed(seed_num)

    # turn all profiles into dicts to work with
    all_profiles = MainConfig(main).config

    data = pd.DataFrame()
    for _ in range(num_cust):
        data = data.append(Customer().toDataFrame())
    data.to_csv(file_path, index=False)
