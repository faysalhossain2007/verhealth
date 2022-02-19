import csv
import datetime
import getpass
import json
import pickle
import time
import os
import multiprocessing
import random

import requests
from pydub import AudioSegment
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from fake_useragent import UserAgent

import speech2text

AMAZON_EMAIL = 'provide your amazon account'
AMAZON_PASS = 'provide your amazon password'
AMAZON_DEV_SKILL_ID = 'provide your amazon skill id'

'''You can follow the following link to create test console in amazon dev : https://www.slideshare.net/faysalhossain77/testing-alexa-skill'''


AMAZON_DEV_URLs = [
        'https://developer.amazon.com/alexa/console/ask/test/'+AMAZON_DEV_SKILL_ID+'/development/en_US/'
    ]



def get_left_commands():
    """
    This function is to generate commands pair that haven't been finished yet.
    It reads all task from input/tasks.csv.
    The tasks.csv is in the format of category, skill name, command line
    It reads all finished task from output/results.[*].jsonl and remove finished task from the queue.
    Finally, it returns the all unfinished tasks as a list.

    Inputs:
        None
    Outputs:
        A list of unfinished tasks
        [
            [skillname, command],
            [skillname, command],
            ....
        ]
    """
    commands = []

    with open('input/tasks.csv', 'r') as fileobj:
        reader = csv.reader(fileobj)
        for row in reader:
            commands.append([row[1], row[2]])

    for i in range(5):
        filename = 'results.{}.jsonl'.format(i)
        if filename in os.listdir('output'):
            with open('output/' + filename, 'r') as fileobj:
                for line in fileobj.readlines():
                    d = json.loads(line.strip())
                    commands.remove([d['skill'], d['command']])

    commands = [[item.lower() for item in cmd] for cmd in commands]

    return commands


def main(commands, processes_num):
    """
    This is the main function of the virtual client.
    It will use multi-processes to run the several virtual clients in parallell.
    My Alexa developer account supports up to 5 virtual clients.
    You can manually set up more Alexa skills to support more virtual clients.
    """

    # Test URLs is the URL of setted up Alexa skills.
    # Each URL (or each Alexa skill) has a testing interface.
    # 5 skills can support testing commands in parrallel
    test_urls = AMAZON_DEV_URLs

    processes = []
    for i in range(processes_num):
        # Split test urls and command pairs

        start = len(commands) // processes_num * i
        end = len(commands) // processes_num * (i + 1)
        if i == processes_num - 1:
            end = len(commands)

        p = multiprocessing.Process(target=worker, args=(i, test_urls[i], commands[start:end]))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()


def worker(id, test_url, commands):
    """
    Worker function of each independent testing interface.
    Each worker has its own process and browser.
    Each worker can use its own test url to test commands.
    Results of each worker will be saved at output/results.{id}.jsonl
    """

    driver = get_headless_chrome()
    login(driver, test_url)

    count = 0
    while len(commands) > 0:
        count += 1
        # if count % 100 == 0:
        #     driver.close()
        #     driver.quit()
        #     driver = get_headless_chrome()
        #     login(driver, test_url)
        command_pair = random.choice(commands)
        skill = command_pair[0]
        command = command_pair[1]

        result = {
            'skill': skill,
            'command': command,
            'response': None,
        }

        try:
            # one_command is to finish just one command using the testing interface
            result['response'] = one_command(driver, test_url, skill, command)

            # Write result to the output file
            append_to_text('output/results.{}.jsonl'.format(id), json.dumps(result))

            # Remove the command pair from commands queue
            commands.remove(command_pair)

            print(datetime.datetime.now(), skill, command, result['response'])
        except Exception as e:
            # Logging the error
            logging([datetime.datetime.now(), skill, command, str(e)])

    driver.close()
    driver.quit()


def one_command(driver, test_url, skill, cmd):
    """
    This function is used by worker to test one single command.
    It firstly open the skill and then send the testing command.
    """

    # Open the skill
    open_cmd = 'alexa open {}'.format(skill)

    # The command itself
    test_cmd = cmd

    driver.get(test_url)
    time.sleep(1)

    text_input = driver.find_element_by_class_name('askt-utterance__input')

    text_input.send_keys(open_cmd + '\n')
    text_input.send_keys(test_cmd + '\n')

    for _ in range(10):
        time.sleep(2)
        bubbles = driver.find_elements_by_class_name('askt-dialog__bubble')
        texts = [bubble.text.strip() for bubble in bubbles]
        if '' in texts:
            texts.remove('')

        # print(datetime.datetime.now(), len(texts), texts)
        if len(texts) >= 4:
            break
    # print(datetime.datetime.now(), len(texts), texts)

    texts.remove(open_cmd)
    texts.remove(test_cmd)

    text_output = ' '
    for text in texts:
        if text not in text_output:
            text_output += text + ' '
    text_output = text_output.strip()

    """
    The following part is for converting audio file to text.
    Because a small part of the response are only in audio format not in text.
    However, it uses the service of Azure which makes it very slow.
    So in a large scale of analysis, it's not feasible to use it.
    The text response provided itself is enough to identify whether the command is supported or not.
    """


    return text_output


def login(driver, test_url):
    driver.get(test_url)
    time.sleep(1)


    email = driver.find_element_by_id('ap_email')
    password = driver.find_element_by_id('ap_password')
    submit = driver.find_element_by_id('signInSubmit')

    email.send_keys(AMAZON_EMAIL)
    password.send_keys(AMAZON_PASS)

    submit.click()
    # driver.save_screenshot('screen.png')
    time.sleep(1)


def get_headless_chrome(proxy=None):
    options = Options()
    # options.add_argument('--headless')
    options.add_argument('--allow-running-insecure-content')
    options.add_argument('--ignore-certificate-errors')

    options.add_argument('--window-size=960,1080')
    options.add_argument("--disable-gpu")
    options.add_argument('--disable-extensions')
    options.add_argument('--hide-scrollbars')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-infobars')
    options.add_argument("--start-maximized")

    if proxy is not None:
        options.add_argument('--proxy-server={}'.format(proxy))

    caps = DesiredCapabilities.CHROME
    caps['loggingPrefs'] = {'performance': 'ALL'}

    driver = None
    while driver == None:
        try:
            driver = webdriver.Chrome(executable_path="./chromedriver", options=options, desired_capabilities=caps)
        except Exception as e:
            print(e)
            pass

    driver.set_page_load_timeout(30)

    return driver


def quit_skill(text_input):
    text_input.send_keys('quit\n')
    text_input.send_keys('stop\n')
    # text_input.send_keys('cancel\n')


def append_to_csv(path, row):
    with open(path, 'a') as fileobj:
        writer = csv.writer(fileobj)
        writer.writerow(row)


def append_to_text(path, text):
    with open(path, 'a') as fileobj:
        fileobj.write(text + '\n')


def logging(entry):
    with open('output/logging.csv', 'a') as fileobj:
        writer = csv.writer(fileobj)
        writer.writerow(entry)


def mp32wav(src, dst):
    sound = AudioSegment.from_mp3(src)
    sound.export(dst, format='wav')


if __name__ == '__main__':
    commands = get_left_commands()
    processes_num = 1
    main(commands, processes_num)
