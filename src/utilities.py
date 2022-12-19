def set_chooser(chooser, choice):
    model = chooser.get_model()
    for index, option in enumerate(model):
        if option.get_string() == choice:
            chooser.set_selected(index)

def empty_chooser(chooser):
    model = chooser.get_model()
    for item in model:
        model.remove(0)
        print("Removing")
    print("done removing")


def populate_chooser(chooser, chooser_list):
    model = chooser.get_model()
    for item in model:
        model.remove(0)
    for item in chooser_list:
        if item != "nothing":
            model.append(str(item))

def get_datalist(parent):
    return list(parent.datadict.keys())

def get_dict_by_value(dictionary, value):
    new_dict = dict((v, k) for k, v in dictionary.items())
    if value == "none":
        return "none"
    return new_dict[value]
