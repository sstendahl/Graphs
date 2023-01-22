from gi.repository import Gdk

def set_chooser(chooser, choice):
    model = chooser.get_model()
    for index, option in enumerate(model):
        if option.get_string() == choice:
            chooser.set_selected(index)

def empty_chooser(chooser):
    model = chooser.get_model()
    for item in model:
        model.remove(0)


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
    
def get_font_weight(font_name):
    valid_weights = ['normal', 'bold', 'heavy', 'light', 'ultrabold', 'ultralight']
    if font_name[-2] != "italic":
        new_weight = font_name[-2]
    else:
        new_weight = font_name[-3]
    if new_weight not in valid_weights:
        new_weight = "normal"
    return new_weight

def get_font_style(font_name):
    new_style = "normal"
    if font_name[-2] == ("italic" or "oblique" or "normal"):
        new_style = font_name[-2]
    return new_style

def get_selected_keys(self):
    selected_keys = []
    for key, item in self.item_rows.items():
        if item.selected == True:
            selected_keys.append(item.id)
    return selected_keys
    
def create_rgba(r, g, b, a=1):
    res = Gdk.RGBA()
    res.red = r
    res.green = g
    res.blue = b
    res.alpha = a
    return res
