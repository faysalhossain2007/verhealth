import json
import math
import string
from nltk.corpus import stopwords
import re
import inflect
import csv
import os
from sklearn.metrics import confusion_matrix
from src.constant import *


def write_to_json(data, filename, type):
    with open(filename, type) as output:
        outstr = json.dumps(data, indent=2)
        output.write(outstr)

def read_from_json(filename):
    with open(filename, 'r') as input_file:
        data_list = json.load(input_file)
    return data_list

def read_from_json_text_format(filename):
    lst = []
    with open(filename, 'r') as fileobj:
        for line in fileobj.readlines():
            d = json.loads(line.strip())
            lst.append(d)

    return lst

def append_to_text(path, text):
    with open(path, 'a') as fileobj:
        fileobj.write(text + '\n')

def data_preparation_for_rule_based_approach(txt):
    return lower_text(txt)

def ascii_to_text(sent):
    from unidecode import unidecode
    return unidecode(sent).lower()

def get_statistics(data_list):

    skill = {}
    core_info = {}

    for data in data_list:

        # if data["category"] == "health":

        if data[TAG_ID] not in skill:
            skill[data[TAG_ID]] = 0
        if data[TAG_CORE_INFORMATION] not in core_info:
            core_info[data[TAG_CORE_INFORMATION]] = 0
        skill[data[TAG_ID]] += 1
        core_info[data[TAG_CORE_INFORMATION]] += 1

    for k,v in core_info.items():
        print(k, "  ", v)

    print("Total Length of data_list = "+str(len(data_list)))
    print("Total unique skill = "+ str(len(skill)))


def get_text_representation_for_req_type(val, labeling_type):
    if labeling_type == TAG_LABELING_TYPE_THREE:
        return get_text_representation_for_three_labelling(val)
    elif labeling_type == TAG_LABELING_TYPE_SIXTEEN:
        return get_text_representation_for_sixteen_labelling(val)

def get_text_representation(val, exp_no):

    if exp_no == 1:
        if val == 0:
            return "Not Storing Information"
        else:
            return  "Storing Information"

    if exp_no == 2:
        if val == 0:
            return "Not Behaving like a doctor"
        else:
            return  "Behaving like a doctor"

    if exp_no == 4:
        if val == 0:
            return "Not Disclaimer"
        else:
            return  "Disclaimer"

def combine_all_data(exp_file_dir):

    # exp_file_dir = '../../output/exp-1/'
    data_list = []

    for i in range(PROCESS_NUMBER):
        filename = exp_file_dir+"results."+str(i)+".jsonl"
        print(filename)
        data = read_from_json_text_format(filename)
        data_list += data
        # data_list.append(data)

    # write_to_json(data_list, exp_file_dir+"combine_data.jsonl", "w")

    return data_list

def get_three_labelling(val):
    label = int(val)
    if label >= 1 and label <= 8:
        type = 0
    elif label >= 9 and label <= 14:
        type = 1
    elif label>= 15 and label <= 16:
        type = 2
    return type


def get_statistics_about_data(data_list):
    data_class = {}
    unique_data = {}

    for data in data_list:

        if data[TAG_SENTENCE] not in unique_data:
            if data[TAG_MANUAL_SENT_LABEL] not in data_class:
                data_class[data[TAG_MANUAL_SENT_LABEL]] = 0
            unique_data[data[TAG_SENTENCE]] = 0
            data_class [data[TAG_MANUAL_SENT_LABEL]] += 1


    # import collections
    # tmp = collections.OrderedDict(data_class)

    # import operator
    # tmp = sorted(data_class.items(), key=operator.itemgetter(1))

    total = 0
    for key,value in data_class.items():
        if key != "0":
            total += int (value)
        print("class {} : {}".format(int(key)-1, value))
    print("Total Data: {} ".format(total))

def get_text_representation_for_sixteen_labelling(val):
    label = int(val)
    label += 1

    if label == 1:  # yes-no question
        type = "yes-no question"
    elif label == 2:  # wh question
        type = "wh question"
    elif label == 3:  # declarative yes-no-question
        type = "declarative yes-no-question"
    elif label == 4:  # backchannel-question
        type = "backchannel-question"
    elif label == 5:  # open-question
        type = "open-question"
    elif label == 6:  # or-clause
        type = "or-clause"
    elif label == 7:  # tag-question
        type = "tag-question"
    elif label == 8:  # declarative wh-clause
        type = "declarative wh-clause"
    elif label == 9:  # statement
        type = "statement"
    elif label == 10:  # agreement
        type = "agreement"
    elif label == 11:  # yes answers
        type = "yes answers"
    elif label == 12:  # no answers
        type = "no answers"
    elif label == 13:  # conventional closing
        type = "conventional closing"
    elif label == 14:  # affirmative-non-yes answers
        type = "affirmative-non-yes answers"
    elif label == 15:  # apology
        type = "apology"
    elif label == 16:  # other
        type = "other"
    else:
        type = "other"
    return type


def get_text_representation_for_three_labelling(val):
    label = int(val)
    type = ""
    if label == 0:  # yes-no question
        type = "question"
    elif label == 1:  # wh question
        type = "confirmation"
    elif label == 2:  # declarative yes-no-question
        type = "unrecognized"
    return type

def store_data(data, label, filename):

    file = open(filename, "w")
    for txt,lbl in zip(data, label):
        file.write(str(lbl) + "\t" + txt + "\n")
    file.close()

def clean_text(s):
    s = remove_url(s)
    s = remove_punctuation(s)
    s = remove_special_character(s)
    # s = remove_stop_words(s)
    s = num2words(s) # we want - to be present in numbers, that's why need to place num2words after remove_punctuation and special character
    s = lower_text(s)
    return s.strip()


def compute_confusion_matrix(actual, predictions):
    return confusion_matrix(actual, predictions)


def num2words(s):
    # it will convert 99 to ninety-nine
    p = inflect.engine()
    words = s.split()
    sent = ""

    for w in words:
        if w.isdigit():
            w = p.number_to_words(w)
        sent += (" "+w)

    return sent.strip()

def remove_url(s):
    return re.sub(r'^https?:\/\/.*[\r\n]*', '', s, flags=re.MULTILINE)

def remove_punctuation(s):
    return s.translate(string.punctuation)

def lower_text(s):
    return s.lower()

def remove_special_character(s):
    return re.sub('[^A-Za-z0-9 ]+', '', s)
    # return ''.join(e for e in s if e.isalnum())

def remove_stop_words(s):
    return [word for word in s if word not in stopwords.words('english')]

def normal_round(n):

    if n - math.floor(n) < 0.5:
        return math.floor(n)
    return math.ceil(n)


def logging(entry):
    with open('output/logging.csv', 'a') as fileobj:
        writer = csv.writer(fileobj)
        writer.writerow(entry)


def read_result_file(process_number, output_file_dir):

    data_list = []
    for i in range(process_number):
        filename = 'results.{}.jsonl'.format(i)
        if filename in os.listdir(output_file_dir):
            with open(output_file_dir + filename, 'r') as fileobj:
                for line in fileobj.readlines():
                    d = json.loads(line.strip())
                    data_list.append(d)
                    # write a code to sort the data according to skill name


    # newlist = sorted(data_list, key=lambda k: k['skill'])

    return data_list







if __name__ == '__main__':
    s = "**** Disclaimer hellwo 12212 2"
    s = remove_special_character(s)
    s = num2words(s)
    print(s)