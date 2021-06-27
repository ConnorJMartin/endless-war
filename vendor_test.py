##demo code
import discord

from ew.static import cfg as ewcfg
import ew.utils.core as ewutils
import ew.utils.frontend as fe_utils

intents = discord.Intents.all()
client = discord.Client(intents=intents)
##demo code



    

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






#make demo vendors
fe_machine = EwVendor(
    vendor_id = "fuckenergy_machine",
    display_name = "FUCK ENERGY Vending Machine",
    poi = ewcfg.poi_id_711
)
md_machine = EwVendor(
    vendor_id = "mtndew_machine",
    display_name = "MTN DEW Vending Machine",
    poi = ewcfg.poi_id_711
)

#fill demo vendors
fe_machine += [
    EwMenuItem(
        item_id = "khaotickilliflowerfuckenergy",
        display_name = "Khaotic Killiflower FUCK ENERGY",
        price = 6000,
        lookup_names = ["kkfe","killiflower"]
    ),
    EwMenuItem(
        item_id = "goonshinefuckenergy",
        display_name = "Goonshine FUCK ENERGY",
        price = 6000,
        lookup_names = ["gsfe","goonshine"]
    ),
    EwMenuItem(
        item_id = "drfuckerfuckenergy",
        display_name = "Dr. Fucker FUCK ENERGY",
        price = 6000,
        lookup_names = ["dffe","drfucker"]
    )
]

md_machine += [
    EwMenuItem(
        item_id = "mtndew",
        display_name = "MTN DEW",
        price = 50
    ),
    EwMenuItem(
        item_id = "bajablast",
        display_name = "MTN DEW Baja Blast",
        price = 50
    ),
    EwMenuItem(
        item_id = "codered",
        display_name = "MTN DEW Code Red",
        price = 50
    )
]


##demo function
async def grab_item(check_vendor, check_item, channel):
    if (check_vendor.menu_has_item(check_item)):
        menu_entry = check_vendor.get_menu_entry(check_item)
        await fe_utils.send_response(f"{menu_entry.display_name} is sold at {check_vendor.display_name} for {menu_entry.price} {menu_entry.currency_type}", channel = channel)
    else:
        await fe_utils.send_response(f"{check_item} is not sold at {check_vendor.display_name}", channel = channel)

#Demo Code to print stuff on startup
@client.event
async def on_ready():
    print("connected")
    channel = None
    for x in client.get_all_channels():
        #print(x.name)
        if x.name.lower() == "playground":
            
            print("found playground")
            channel = x

    if (channel != None):
        print(channel)

        #demo menu print
        await fe_utils.send_response(fe_machine.menu_print(), channel = channel)
        await fe_utils.send_response(md_machine.menu_print(), channel = channel)

        #demo check for items
        await grab_item(fe_machine, "gsfe", channel)
        await grab_item(fe_machine, "mtndew", channel)
        await grab_item(md_machine, "mtndew", channel)
    else:
        print("no channel")


#demo code to connect to discord
# find our REST API token
token = ewutils.getToken()

if token == None or len(token) == 0:
    ewutils.logMsg('Please place your API token in a file called "token", in the same directory as this script.')
    sys.exit(0)
# connect to discord and run indefinitely
try:
    client.run(token)
finally:
    ewutils.TERMINATE = True
    ewutils.logMsg("main thread terminated.")