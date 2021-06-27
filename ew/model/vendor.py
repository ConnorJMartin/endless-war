class EwMenuItem:
    def __init__(self, item_id, display_name, price, currency_type = "slime", lookup_names = []):
        self.item_id = item_id
        self.display_name = display_name
        self.price = price
        self.currency_type = currency_type
        self.lookup_names = lookup_names

    def __repr__(self):
        return(f"<EwMenuItem - {self.display_name}>")

class EwVendor:
    def __init__(self, vendor_id, display_name, poi):
        self.vendor_id = vendor_id
        self.display_name = display_name
        self.poi = poi
        self.menu = {}
        self.lookup_names = {}

    def add_item(self, _menu_obj):
        #check type for error
        if (isinstance(_menu_obj, EwMenuItem)): 
            #check if item is already in menu
            if (self.menu.get(_menu_obj.item_id) is None):
                #add to menu and add lookup_names to dictionary
                self.menu[_menu_obj.item_id] = _menu_obj
                self.lookup_names[_menu_obj.item_id] = _menu_obj.item_id
                for name in _menu_obj.lookup_names:
                    self.lookup_names[name] = _menu_obj.item_id
            else:
                print("error: " + _menu_obj.item_id + " is already in vendor's menu")
        else:
            raise ValueError(f"{_menu_obj} is not EwMenuItem. Could not be added to {self.vendor_id}")


    """ self += (EwMenuItem) operator """
    def __iadd__(self, other):
        if (isinstance(other, list)):
            for item in other:
                self.add_item(item)
        else:
            self.add_item(other)
        return self

    def remove_item(self, _item_id):
        for key in dict(self.menu).keys():
            if key == _item_id:
                del self.menu[key]
        for key, value in dict(self.lookup_names).items():
            if value == _item_id:
                del self.lookup_names[key]
        return self

    """ self -= (item_id) operator """
    def __isub__(self, other):
        if (isinstance(other, list)):
            for item in other:
                self.remove_item(item)
        else:
            self.remove_item(other)
        return self

    """ clear all menu items """
    def clear_menu(self):
        self.menu = {}
        self.lookup_names = {}

    """ Return menu of vendor """
    def menu_print(self):
        # Bold text store name
        menu_str = f"**{self.display_name}:**\n"
        
        # Start code block for list of items
        menu_str += "```\n"

        # Loop through items and get string length for padding
        max_name_len = 0
        max_price_len = 0
        for item in self.menu:
            item = self.menu[item]
            if (len(item.display_name) > max_name_len):
                max_name_len = len(item.display_name)

            if (len(str(item.price)) > max_price_len):
                max_price_len = len(str(item.price))

        # Loop through items and add to message
        for item in self.menu:
            item = self.menu[item]
            padding = ''.join("-" for i in range(max_price_len - len(str(item.price))))

            #menu_str += f"{item.display_name : >{max_name_len}} -{padding} {item.price} {item.currency_type}\n" #can use this later if different curenency types are implemented
            menu_str += f"{item.display_name : >{max_name_len}} -{padding} {item.price}\n"

        # End code block and return str
        menu_str += "```\n"
        return menu_str
    
    """ Return true if item is in vendor """
    def menu_has_item(self, keyword):
        if (self.lookup_names.get(keyword) is None):
            return False
        else:
            return True

    """ Return menu object """
    def get_menu_entry(self, keyword):
        item_id = self.lookup_names.get(keyword)

        if (item_id is None):
            return None
        else:
            return self.menu.get(item_id)
