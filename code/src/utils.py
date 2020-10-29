# from keras import backend as K
from src.constant import *
from src.helper import *
from bs4 import BeautifulSoup
from nltk.tokenize import sent_tokenize
import keras

def check_units(y_true, y_pred):
    # print(y_pred.shape[1])
    # print(y_true.shape[1])
    # print("fff")
    if y_pred.shape[0] != 1:
        y_pred = y_pred[:, 1:2]
        y_true = y_true[:, 1:2]
    return y_true, y_pred

# def precision(y_true, y_pred):
#     print(y_true,"   ", y_pred)
#     # y_true, y_pred = check_units(y_true, y_pred)
#     true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
#     predicted_positives = K.sum(K.round(K.clip(y_pred, 0, 1)))
#     precision = true_positives / (predicted_positives + K.epsilon())
#     return precision
#
#
# def recall(y_true, y_pred):
#     # y_true, y_pred = check_units(y_true, y_pred)
#     true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
#     possible_positives = K.sum(K.round(K.clip(y_true, 0, 1)))
#     recall = true_positives / (possible_positives + K.epsilon())
#     return recall
#
#
# def f1_score(y_true, y_pred):
#     def recall(y_true, y_pred):
#         true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
#         possible_positives = K.sum(K.round(K.clip(y_true, 0, 1)))
#         recall = true_positives / (possible_positives + K.epsilon())
#         return recall
#
#     def precision(y_true, y_pred):
#         true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
#         predicted_positives = K.sum(K.round(K.clip(y_pred, 0, 1)))
#         precision = true_positives / (predicted_positives + K.epsilon())
#         return precision
#
#     # y_true, y_pred = check_units(y_true, y_pred)
#     precision = precision(y_true, y_pred)
#     recall = recall(y_true, y_pred)
#     return 2 * ((precision * recall) / (precision + recall + K.epsilon()))

# def print_accuracy_precision_recall_f1(y_true, y_pred):
#     print("Accuracy: "+"Precision: "+ str(precision(y_true, y_pred))+" Recall: "+str(recall(y_true, y_pred)) + " F1 Score: "+str(f1_score(y_true, y_pred)))

def make_balance_dataset(trainX, trainy, ratio):

    new_train_x = []
    new_train_y = []
    num_allowed_neg_sentence = 0


    for x,y in zip(trainX, trainy):
        if y == '1':
            new_train_x.append(x)
            new_train_y.append(y)
            num_allowed_neg_sentence += ratio
        else:
            if num_allowed_neg_sentence > 0:
                new_train_x.append(x)
                new_train_y.append(y)
                num_allowed_neg_sentence -= 1

    return new_train_x, new_train_y


def calculate_confusion_matrix(y_real, y_pred, sentences, exp_no):

    print("Actual:")
    print(y_real)
    print("Prediction:")
    print(y_pred)


    tp =0
    fp =0
    tn =0
    fn =0


    mismatch = []
    for real, pred, item in zip(y_real, y_pred, sentences):

        if real == pred :
            if real == 0:
                tn = tn + 1
            elif real == 1:
                tp = tp + 1
        elif real != pred:
            mismatch.append(item)

            print(item)
            print('Predicted: ', get_text_representation(pred, exp_no), '--- Actual: ',
                  get_text_representation(real, exp_no))

            if real == 0:
                fp = fp + 1
            elif real == 1:
                fn = fn + 1
    accuracy, precision, recall, f1 = calculate_performance(tp, fp, tn, fn)


    print("TP  : "+  str(tp))
    print("FP  : " + str(fp))
    print("TN  : " + str(tn))
    print("FN  : " + str(fn))

    print("Accuracy : " + str(accuracy))
    print("Precision : " + str(precision))
    print("Recall : " + str(recall))
    print("F1 : " + str(f1))

    return accuracy, precision, recall, f1, mismatch


def get_voice_command_from_dataset():

    data_list = get_alexa_dataset('../../../data/data_alexa_2019.json')
    command_list = []
    for data in data_list:
        commands = data[TAG_UTTERANCES]
        for command in commands:
            sent = format_voice_command(command)
            command_list.append(sent)

    return command_list

def convert_to_plain_from_unicode(text):
    return text.encode("utf-8")

def remove_html_tag(text):
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text().strip()

def get_skill_description_from_dataset(location):

    data_list = get_alexa_dataset(location)
    desc_list = []
    for data in data_list:
        description = convert_to_plain_from_unicode(remove_html_tag(data[TAG_DESCRIPTION]))
        desc_list.append(description)

    return desc_list


def get_sentence_from_description(desc):
    sentence_list = []
    token =  sent_tokenize(remove_html_tag(desc))
    # print(token)
    for sentence in token:
        sent = sentence.split('\n')
        for s in sent:
            sentence_list.append(s)


    return sentence_list




def get_alexa_dataset(location, category = None):
    if len(category) > 0:
        filtered_data_list = []
        data_list = read_from_json(location)

        for data in data_list:
            # print(data)
            try:
                cat = data[TAG_CATEGORY]
                if ((cat == category) and (data[TAG_ACCOUNT_LINKING] is None) and (data[
                    TAG_INVOCATION])):
                    filtered_data_list.append(data.copy())

            except Exception as e:
                # print(e)
                pass
        # print(filtered_data_list)
        return filtered_data_list

    return read_from_json(location)

def format_voice_command(cmd):

    cmd = remove_punctuation(cmd)


    clear_words = ["alexa,", "alexa", '"']
    cmd = lower_text(cmd)

    for c_word in clear_words:
        for w in cmd:
            if c_word in w:
                cmd = cmd.replace(c_word, "")
                cmd = cmd.strip()
    return cmd

def calculate_performance(tp, fp, tn, fn):

    print("TP TN FP FN "+str(tp)+" "+str(tn)+" "+str(fp)+" "+str(fn) )

    total = tp + fp + tn + fn
    accuracy = (tp+tn)*1.0 / total
    precision = (tp/ (tp+fp) *1.0 )
    recall = (tp/ (tp+fn))
    f1 = 2 * (precision* recall)/ (precision+recall)

    return accuracy, precision, recall, f1

# def print_list_len(tag, element_list):
#     print(tag)
#     for elem in element_list:
#         print(len(elem))


def save_model(model):

    model_json = model.to_json()
    with open(DISCLAIMER_DETECTION_MODEL_JSON, "w") as json_file:
        json_file.write(model_json)

    json_file.close()
    # serialize weights to HDF5
    model.save_weights(DISCLAIMER_DETECTION_MODEL_HDF5)

    print("Saved model to disk")


def load_model():

    with open(DISCLAIMER_DETECTION_MODEL_JSON, "r") as f:
        json_str = f.read()
    f.close()
    loaded_model = keras.models.model_from_json(json_str)

    # Weights
    loaded_model.load_weights(DISCLAIMER_DETECTION_MODEL_HDF5)

    print("Loaded model from disk")
    return loaded_model


if __name__ == '__main__':
    # get_alexa_dataset()
    accuracy, precision, recall, f1 = calculate_performance()
    print(accuracy, "   ", precision, "   ", recall, "   ", f1)