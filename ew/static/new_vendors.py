from ew.model.vendor import EwVendor, EwMenuItem

#EVENT TOGGLE
double_halloween_event = False
dr_downpour_event = False
slimecorp_breakroom_vendor = False



class Bunch:
    def __init__(self, **kwds):
        self.__dict__.update(kwds)

poi_id = Bunch(
    food_court = "food_court",
    outside_the_711 = "outside_the_711",
    speakeasy = "speakeasy",
    seafood = "seafood",
    diner = "diner",
    beach_resort = "beach_resort",
    country_club = "country_club",
    green_cake_cafe = "green_cake_cafe",
    waffle_house = "waffle_house",

    bodega = "bodega",

    bazaar = "bazaar",
    glocksbury_comics = "glocksbury_comics",
    slimy_persuits = "slimy_persuits",
    neo_milwaukee_state = "neo_milwaukee_state",
    nlacu = "nlacu",

    dojo = "dojo",
    based_hardware = "based_hardware",
    ooze_garden_farms = "ooze_garden_farms",

    slimeoid_labs = "slimeoid_labs",
)

#event poi ids
if (double_halloween_event):
    poi_id.__dict__.update({"rp_city": "rp_city"})
if (dr_downpour_event):
    poi_id.__dict__.update({"nuclear_beach_edge": "nuclear_beach_edge"})
if (slimecorp_breakroom_vendor):
    poi_id.__dict__.update({"slimecorp_breakroom": "slimecorp_breakroom"})
    




vendor_id = Bunch(
    fuck_energy_machine = "fuckenergy_machine",
    mtn_dew_machine = "mtndew_machine",
    pizza_hut = 'pizzahut',
    taco_bell = 'tacobell',
    kfc = 'kfc',
    mtn_dew_fountain = "mtndew_fountain",
    speakeasy = "speakeasy",
    red_mobster_seafood = "red_mobster_seafood",
    smokers_cough = "smokers_cough",
    beach_resort = "beach_resort",
    country_club = "country_club",
    neo_milwaukee_state = "neo_milwaukee_state",
    nlacu = "nlacu",
    glocksbury_comics = "glocksbury_comics",
    atomic_forest = "atomic_forest",
    slimeoid_labs = "slimeoid_labs",
    slimy_persuits = "slimy_persuits",
    green_cake_cafe = "green_cake_cafe",
    bodega = "bodega",
    secret_bodega_menu = "secret_bodega_menu",
    waffle_house = "waffle_house",
    based_hardware = "based_hardware",
    bazaar = "bazaar",
    dojo = "dojo",
)

#event vendor ids
if (double_halloween_event):
    vendor_id.__dict__.update({"rp_city": "rp_city"})
if (dr_downpour_event):
    vendor_id.__dict__.update({"downpour_laboratory": "downpour_laboratory"})
if (slimecorp_breakroom_vendor):
    vendor_id.__dict__.update({"slimecorp_breakroom": "slimecorp_breakroom"})
    



new_vendor_list = [

    ############
    ### FOOD ###
    ############

    # Food Court
    EwVendor(
        vendor_id = vendor_id.pizza_hut,
        display_name = "Pizza Hut",
        poi = poi_id.food_court
    ),
    EwVendor(
        vendor_id = vendor_id.taco_bell,
        display_name = "Taco Bell",
        poi = poi_id.food_court
    ),
    EwVendor(
        vendor_id = vendor_id.kfc,
        display_name = "KFC",
        poi = poi_id.food_court
    ),
    EwVendor(
        vendor_id = vendor_id.mtn_dew_fountain,
        display_name = "MTN DEW Fountain",
        poi = poi_id.food_court
    ),
    # Vending machines
    EwVendor(
        vendor_id = vendor_id.fuck_energy_machine,
        display_name = "FUCK ENERGY Vending Machine",
        poi = poi_id.outside_the_711
    ),
    EwVendor(
        vendor_id = vendor_id.mtn_dew_machine,
        display_name = "MTN DEW Vending Machine",
        poi = poi_id.outside_the_711
    ),
    # Speakeasy
    EwVendor(
        vendor_id = vendor_id.speakeasy,
        display_name = "The King's Wife's Son Speakeasy",
        poi = poi_id.speakeasy
    ),
    # Killer/Rowdy Restaurants
    EwVendor(
        vendor_id = vendor_id.red_mobster_seafood,
        display_name = "Red Mobster Seafood",
        poi = poi_id.seafood
    ),
    EwVendor(
        vendor_id = vendor_id.smokers_cough,
        display_name = "Smoker's Cough",
        poi = poi_id.diner
    ),
    # S Class Restaurants
    EwVendor(
        vendor_id = vendor_id.beach_resort,
        display_name = "The Resort",
        poi = poi_id.beach_resort
    ),
    EwVendor(
        vendor_id = vendor_id.country_club,
        display_name = "The Country Club",
        poi = poi_id.country_club
    ),
    # Green Cake Cafe
    EwVendor(
        vendor_id = vendor_id.green_cake_cafe,
        display_name = "Green Cake Cafe",
        poi = poi_id.green_cake_cafe
    ), 
    # Waffle House
    EwVendor(
        vendor_id = vendor_id.waffle_house,
        display_name = "Waffle House",
        poi = poi_id.waffle_house
    ),






    ###############
    ### FASHION ###
    ###############

    # Bodega
    EwVendor(
        vendor_id = vendor_id.bodega,
        display_name = "Bodega",
        poi = poi_id.bodega
    ), 
    # Secret Bodega Menu
    EwVendor(
        vendor_id = vendor_id.secret_bodega_menu,
        display_name = "Fashion For The Freshest",
        poi = poi_id.bodega
    ),






    ###############
    ### GENERAL ###
    ###############

    # Bazaar 
    EwVendor(
        vendor_id = vendor_id.bazaar,
        display_name = "The Bazaar",
        poi = poi_id.bazaar
    ),
    # Comics
    EwVendor(
        vendor_id = vendor_id.glocksbury_comics,
        display_name = "Glocksbury Comics",
        poi = poi_id.glocksbury_comics
    ),
    # Slimy Persuits 
    EwVendor(
        vendor_id = vendor_id.slimy_persuits,
        display_name = "Slimy Persuits",
        poi = poi_id.slimy_persuits
    ),
    # Colleges
    EwVendor(
        vendor_id = vendor_id.neo_milwaukee_state,
        display_name = "Neo Milwaukee State Book Store",
        poi = poi_id.neo_milwaukee_state
    ),
    EwVendor(
        vendor_id = vendor_id.nlacu,
        display_name = "New Los Angeles City University Book Store",
        poi = poi_id.nlacu
    ),






    ###############
    ### WEAPONS ###
    ###############

    # Dojo 
    EwVendor(
        vendor_id = vendor_id.dojo,
        display_name = "The Dojo",
        poi = poi_id.dojo
    ),
    # BASED Hardware
    EwVendor(
        vendor_id = vendor_id.based_hardware,
        display_name = "BASED Hardware",
        poi = poi_id.based_hardware
    ),
    # Ooze Garden Store
    EwVendor(
        vendor_id = vendor_id.atomic_forest,
        display_name = "Atomic Forest",
        poi = poi_id.ooze_garden_farms
    ),






    ####################
    ### DEPRECIATED? ###
    ####################

    # Labs 
    EwVendor(
        vendor_id = vendor_id.slimeoid_labs,
        display_name = "Brawlden Labs",
        poi = poi_id.slimeoid_labs
    ),
]

# RP City only for double halloween event only
if (double_halloween_event):
    new_vendor_list.append(
        EwVendor(
            vendor_id = vendor_id.rp_city,
            display_name = "RP City",
            poi = poi_id.rp_city
        )
    )

# Downpour Lab only for GvS event only
if (dr_downpour_event):
    new_vendor_list.append(
        EwVendor(
            vendor_id = vendor_id.downpour_laboratory,
            display_name = "Downpour Armament Vending Machines",
            poi = poi_id.nuclear_beach_edge
        )
    )

# RIP SlimeCorp
if (slimecorp_breakroom_vendor):
    new_vendor_list.append(
        EwVendor(
            vendor_id = vendor_id.slimecorp_breakroom,
            display_name = "Employee Breakroom",
            poi = poi_id.slimecorp_breakroom
        )
    )



# vendor_id -> EwVendor
id_to_vendor = {}

# poi_id -> list of vendor_id
poi_to_vendors = {}

# Build dictionaries
for vendor in new_vendor_list:
    id_to_vendor[vendor.vendor_id] = vendor

    vendor_list = poi_to_vendors.get(vendor.poi, [])
    vendor_list.append(vendor.vendor_id)

    poi_to_vendors.update({vendor.poi: vendor_list})




id_to_vendor[vendor_id.fuck_energy_machine] += [
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

id_to_vendor[vendor_id.mtn_dew_machine] += [
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




def secret_bodega_list(poi_id):
    return poi_to_vendors.get(poi_id, [])



def secret_bodega(vendor_id):
    return poi_to_vendors.get(vendor_id)





#print(id_to_vendor[vendor_id.fuck_energy_machine].menu_print())
#print(id_to_vendor[vendor_id.mtn_dew_machine].menu_print())












#temp code
#for poi, vendors in poi_to_vendor.items():
#    print(f"{poi}|{vendors}")
