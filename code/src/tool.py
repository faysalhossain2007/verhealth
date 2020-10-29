from src.utils import *
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import datetime
from src.paraphraseGenerator.paraphrasermaster.paraphraser.inference import generate_paraphrase, get_paraphraser
from src.paraphraseGenerator.paraphrasermaster.paraphraser.constant import *
from src.DisableSkill import *

# paraphraser = None

def get_dataset_statistics():
    data_list = get_alexa_dataset('../data/data_alexa_2019.json')

    unique_skill = {}
    unique_category = {}
    unique_voice_commands = {}
    unique_account_linking_info = {}

    for data in data_list:

        if TAG_CATEGORY in data:

            id = data[TAG_ID]
            category = data[TAG_CATEGORY]

            if data[TAG_ACCOUNT_LINKING]:
                unique_account_linking_info[id] = 0

            if category not in unique_category:
                unique_category[category] = 0
            unique_category[category] += 1

            if id not in unique_skill:
                unique_skill[id] = 0
            unique_skill[id] += 1

            commands = data[TAG_UTTERANCES]
            for command in commands:
                if command not in unique_voice_commands:
                    unique_voice_commands[command] = 0
                unique_voice_commands[command] += 1

    #print
    print("category: "+str(len(unique_category)))
    print("skill: " + str(len(unique_skill)))
    print("voice commands: " + str(len(unique_voice_commands)))
    print("account linking "+str(len(unique_account_linking_info)))

def get_explored_commands(process_number, file_dir):

    commands = []
    for i in range(process_number):
        filename = 'results.{}.jsonl'.format(i)
        if filename in os.listdir(file_dir):
            with open( file_dir + filename, 'r') as fileobj:
                for line in fileobj.readlines():
                    d = json.loads(line.strip())
                    commands.append([d[TAG_ID], d[TAG_COMMAND]])

    return commands

def get_headless_chrome(chrome_executable_path):


    # from pyvirtualdisplay import Display
    # from selenium import webdriver

    options = Options()
    # options.add_argument('--headless')
    # options.add_argument('--ignore-certificate-errors')
    # options.add_argument("--disable-gpu")


    # display = Display(visible=0, size=(800, 600))
    # display.start()




    print("headless chrome started")
    # options = Options()
    # # options.add_argument('--headless')
    # options.add_argument('--allow-running-insecure-content')
    # options.add_argument('--ignore-certificate-errors')

    # options.add_argument('--window-size=960,1080')
    # options.add_argument("--disable-gpu")
    # options.add_argument('--disable-extensions')
    # options.add_arguchment('--hide-scrollbars')
    # options.add_argument('--no-sandbox')
    # options.add_argument('--disable-infobars')
    # options.add_argument("--start-maximized")

    # if proxy is not None:
    #     options.add_argument('--proxy-server={}'.format(proxy))
    #
    # caps = DesiredCapabilities.CHROME
    # caps['loggingPrefs'] = {'performance': 'ALL'}

    option = webdriver.ChromeOptions()
    # prefs = {"download.default_directory": "./../data/downlaods"}
    # option.add_experimental_option("prefs", prefs)

    driver = None
    # driver = webdriver.Chrome(executable_path="./../chromedriver_linux", chrome_options=option
    #                           )
    # driver = webdriver.Chrome(executable_path="./../chromedriver_77_32_windows", chrome_options=option)

    # driver = webdriver.Chrome(executable_path="./../chromedriver_75", options=options)

    driver = webdriver.Chrome(executable_path=chrome_executable_path, options=options)


    # while driver == None:
    #     print("hs")
    #     try:
    #         driver = webdriver.Chrome(executable_path="./../chromedriver_75", options=option, desired_capabilities=caps)
    #         # driver = webdriver.Chrome(executable_path="./../chromedriver_linux", options=options,
    #         #                           desired_capabilities=caps)
    #             # driver = webdriver.Chrome(executable_path="./chromedriver", options=options,
    #             #                           desired_capabilities=caps)
    #     except Exception as e:
    #         print(e)
    #         print("Exception Occur.")
    #         pass

    print("driver load successfully")
    driver.set_page_load_timeout(30)
    return driver

def open_skill(driver, skill, test_url):

    driver.get(test_url)
    time.sleep(1)

    # print(driver.page_source.encode("utf-8"))
    text_input = driver.find_element_by_class_name('askt-utterance__input')
    # Open the skill
    open_cmd = 'alexa open {}'.format(skill)
    text_input.send_keys(open_cmd + '\n')

    return text_input

def quit_skill(text_input):
    text_input.send_keys('exit\n')

def one_command(driver, cmd, text_input):
    """
    This function is used by worker to test one single command.
    It firstly open the skill and then send the testing command.
    """

    # print("It is call")

    multiple_round = 1

    # The command itself
    test_cmd = cmd

    time.sleep(1)
    text_input.send_keys(test_cmd + '\n')
    # print("first command: "+test_cmd)

    time.sleep(2)

    # for _ in range(10):
    time.sleep(2)
    bubbles = driver.find_elements_by_class_name('askt-dialog__bubble')
    texts = [lower_text(bubble.text.strip()) for bubble in bubbles]
    if '' in texts:
        texts.remove('')

    # print(texts[len(texts)-1])
    terminating_code, cmd_to_send = check_for_multiple_round_of_interaction(texts[len(texts)-1], cmd, True)
    # print("hello"+ str(terminating_code))

    # print("cmd "+cmd_to_send)

    while(True):

        if terminating_code == RESPONSE_TYPE_UNDEFINED: # HERE RESPONSE TYPE UNDEFINED INDICATES IT IS A STATEMENT TYPE BECAUSE FOR THE PREVIOUS TWO STEPS IT REMAINS 0
            break

        if len(cmd_to_send) > 0:

            if terminating_code == RESPONSE_TYPE_QUESTION:
                multiple_round += 1

                try:
                    if len(cmd_to_send) > 1:
                        st_cmd  = cmd_to_send[0]
                        cmd_to_send = st_cmd
                    # time.sleep(1)
                    text_input.send_keys(cmd_to_send + '\n')
                    time.sleep(5)

                    bubbles = driver.find_elements_by_class_name('askt-dialog__bubble')
                    texts = [lower_text(bubble.text.strip()) for bubble in bubbles]
                    if '' in texts:
                        texts.remove('')

                    terminating_code, cmd_to_send = check_for_multiple_round_of_interaction(texts[len(texts) - 1], cmd,
                                                                                    True)
                except Exception as e:
                    print(e)
                    print(cmd_to_send)

                # rephrase only the original command
            if terminating_code == RESPONSE_TYPE_UNRECOGNIZE:
                # print(cmd_to_send)
                for cmd1 in cmd_to_send:

                    time.sleep(1)
                    text_input.send_keys(cmd1 + '\n')
                    time.sleep(5)

                    bubbles = driver.find_elements_by_class_name('askt-dialog__bubble')
                    texts = [lower_text(bubble.text.strip()) for bubble in bubbles]
                    if '' in texts:
                        texts.remove('')

                    terminating_code, cmd2 = check_for_multiple_round_of_interaction(texts[len(texts) - 1],
                                                                                     cmd1, False)
                    if terminating_code != RESPONSE_TYPE_UNDEFINED:
                        break

        # print(datetime.datetime.now(), len(texts), texts)
        # if len(texts) >= 8:
        #     print(texts)
        #     break
        else:
            break


    return texts, multiple_round


# three types of responses
# 1. Unrecognize
# 2. Statement
# 3. Question

def check_for_multiple_round_of_interaction(response, cmd, check_for_unrecognize):

    # cmd_to_send = ""
    response_type, cmd_to_send =  generate_answer(response)

    if response_type == RESPONSE_TYPE_UNDEFINED and check_for_unrecognize == True: #RESPONSE_TYPE_UNDEFINED = can be either unrecognize or statement
        response_type, cmd_to_send = check_for_unrecognize_message(response, cmd)
        return response_type, cmd_to_send
        # print(response_type, cmd_to_send)

    # check for statement / violation
    if response_type == RESPONSE_TYPE_UNDEFINED:
        response_type, cmd_to_send = extract_suggestion_cmd_from_statement(response, cmd)

    return  response_type, cmd_to_send

def extract_suggestion_cmd_from_statement(response, cmd):

    suggestion_indicator = ["say", "tell", "ask"]
    chunks = response.split(".")

    for item in chunks:
        for indicator in suggestion_indicator:
            if indicator in item:
                suggestions = item.split(indicator)
                return RESPONSE_TYPE_STATEMENT, suggestions[1]

    return RESPONSE_TYPE_UNDEFINED, ""



def check_for_unrecognize_message(message, cmd):

    unrecog_message = [
        "I don't understand", "Repeated response", "Audio only response", "I am having trouble understanding",
        "i could not find", "i don't know", "i do not have", "i cannot understand", "unable to find"
    ]

    for msg in unrecog_message:
        if lower_text(msg) in message:
            command_list = read_from_json(PARAPHRASER_SENTENCES_FILE)
            sents = []
            for k,v in command_list.items():
                if k == cmd:
                    sents = v
            # print("Unrecognize message "+ cmd)
            # sents = get_paraphrase_sentences(cmd, phraser)
            # print(sents)
            return RESPONSE_TYPE_UNRECOGNIZE, sents
    return RESPONSE_TYPE_UNDEFINED, ""

# Generates answers for Question type responses
def generate_answer(response):

    response = str(response)

    cmd_to_send  = ""
    if "you want me to remember" in response:
        cmd_to_send = "yes"
    elif "what's your current weight" in response:
        cmd_to_send = "150 pound"
    elif "what's your current height" in response:
        cmd_to_send = "5 feet"
    elif "tell me your weight" in response:
        cmd_to_send = "150 pound"
    elif "tell me your temperature" in response:
        cmd_to_send = "55 farenhit"
    elif "you haven't given me any reports" in response:
        cmd_to_send = "my report is i have a fever disease"
    elif "how much do you weigh" in response:
        cmd_to_send = "150 pound"
    elif "how much do you currently weigh" in response:
        cmd_to_send = "150 pound"
    elif "do you want to open it" in response:
        cmd_to_send = "yes"
    elif "did you just say" in response:
        cmd_to_send = "yes"
    elif "do you mean" in response:
        cmd_to_send = "yes"
    elif "systolic pressure" in response:
        cmd_to_send = "84"
    elif "dastolic pressure" in response:
        cmd_to_send = "78"
    elif "do you want to enable it again" in response:
        cmd_to_send = "yes"
    elif "please tell me what hurts" in response:
        cmd_to_send = "lower abdomen"
    elif "when would you" in response:
        cmd_to_send = "7"
    elif "tell me your birth date" in response:
        cmd_to_send = "22 january, 1986"

    elif "name your symptoms" in response:
        cmd_to_send = "fever"


    elif "by saying, my due date is," in response:
        cmd_to_send = "my due date is 15 Jan 2022"
    elif "saying, add stool" in response:
        cmd_to_send = "add stool"

    # elif "log" in response:
    #     cmd_to_send = "log"
    else:
        return RESPONSE_TYPE_UNDEFINED, "" #NOT AN QUESTION TYPE RESPONSE

    return RESPONSE_TYPE_QUESTION, cmd_to_send

def get_paraphrase_sentences(source_sentence, phraser):
    # phraser = get_paraphraser()
    return generate_paraphrase(source_sentence, SAMPLING_TEMP, HOW_MANY_PARAPHRASE, phraser)


def login_without_email(driver, test_url):
    try:
        driver.get(test_url)
        time.sleep(1)

        password = driver.find_element_by_id('ap_password')
        submit = driver.find_element_by_id('signInSubmit')

        password.send_keys(AMAZON_PASSWORD)

        # email.send_keys('hanghu@vt.edu')
        # password.send_keys('Timebeginner1!')

        submit.click()
        # driver.save_screenshot('screen.png')
        time.sleep(1)
    except:
        print("Exception Occured in login without email")
        return ERROR_CODE_LOGIN_TIMEOUT

    return SUCCESS_CODE_LOGIN


def login(driver, test_url):

    try:
        driver.get(test_url)
        time.sleep(1)

        email = driver.find_element_by_id('ap_email')
        password = driver.find_element_by_id('ap_password')
        submit = driver.find_element_by_id('signInSubmit')

        email.send_keys(AMAZON_USERNAME)
        password.send_keys(AMAZON_PASSWORD)

        # email.send_keys('hanghu@vt.edu')
        # password.send_keys('Timebeginner1!')


        submit.click()
        # driver.save_screenshot('screen.png')
        time.sleep(1)

    except Exception as e:
        code = login_without_email(driver, test_url)
        print("Exception Occured in login ")
        # send_email(str(code))
        print(e)
        return code

    print("Successfully Logged in")
    return SUCCESS_CODE_LOGIN


def worker(id, test_url, data_list, file_dir, chrome_executable_path):
    """
    Worker function of each independent testing interface.
    Each worker has its own process and browser.
    Each worker can use its own test url to test commands.
    Results of each worker will be saved at output/results.{id}.jsonl
    """
    # print("Data list len: ")
    # print(test_url)

    # global paraphraser
    # paraphraser = phraser

    driver = get_headless_chrome(chrome_executable_path = chrome_executable_path)

    while(True):
        ret = login(driver, test_url)
        if ret == SUCCESS_CODE_LOGIN:
            break
        time.sleep(10)

    print("Login Successful")

    # while len(commands) > 0:
    for data in data_list:
        print(data)
        command = data[TAG_COMMAND]

        category = data[TAG_CATEGORY]
        skill = data[TAG_INVOCATION]
        skill_id = data[TAG_ID]
        command_type = data[TAG_COMMAND_TYPE]


        while(True):
            try:
                text_input = open_skill(driver, skill, test_url)

                if text_input:
                    break
            except:
                print("Exception occured")
                while (True):
                    ret = login(driver, test_url)
                    if ret == SUCCESS_CODE_LOGIN:
                        break
                    time.sleep(10)

        print(data)
        result = {
            TAG_CATEGORY: category,
            TAG_SKILL: skill,
            TAG_ID: skill_id,
            TAG_COMMAND: command,
            TAG_RESPONSE: None,
            TAG_INTERACTION_ROUND: 1,
            TAG_INTERACTION_RECORD : None,
            TAG_COMMAND_TYPE: command_type,
            TAG_CORE_INFORMATION: data[TAG_CORE_INFORMATION]
        }

        print(command)

        # result = command

        #disable skill for testing skill's storing capability interval
        if DISABLE_SKILL:
            #Need to check whether the command is query or storing
            is_disabled = disable(skill_id, driver)
            if is_disabled:
                text_input = open_skill(driver, skill, test_url)
                print("Disabling the skill")
            else:
                print("Was not able to disable the skill")
                continue



        # try:
        interaction_record, interaction_round = one_command(driver= driver, cmd= command, text_input=text_input)
        # one_command is to finish just one command using the testing interface
        result[TAG_INTERACTION_RECORD] = interaction_record
        result[TAG_INTERACTION_ROUND] = interaction_round
        result[TAG_RESPONSE] = get_response_from_interaction(command, interaction_record)
        # print(datetime.datetime.now(), skill, command, result[TAG_RESPONSE])

        # Write result to the output file
        append_to_text(file_dir +'results.{}.jsonl'.format(id), json.dumps(result))

        append_to_text(file_dir +'results_with_format.{}.jsonl'.format(id), json.dumps(result, indent=2))

        # #add multiple round of interaction
        # check_for_multiple_round_of_interaction(text_input, result[TAG_RESPONSE])


        quit_skill(text_input)

        # print(datetime.datetime.now(), skill, command, result['response'])
        # except Exception as e:
        #     # Logging the error
        #     logging([datetime.datetime.now(), skill, command, str(e)])
        #     print(e)



    driver.close()
    driver.quit()

def get_response_from_interaction(cmd, interaction_record):

    response = ""

    flag = 0
    for record in interaction_record:
        if flag == 1:
            response = response + record
            print("now only considering one response per request")
            break
        if cmd == record:
            flag = 1

    return lower_text(response)




if __name__ == '__main__':
    get_dataset_statistics()