import ew.static.cfg as ewcfg
import math
import random
from ..backend.yacht import EwYacht
import ew.backend.item as bknd_item
from ..backend import core as bknd_core
import ew.static.poi as poi_static
from ew.utils import core as coreutils
from ew.utils.district import EwDistrict
from ew.utils.combat import EwUser
import ew.utils.frontend as fe_utils
try:
    from ew.cmd import debug as ewdebug
except:
    from ew.cmd import debug_dummy as ewdebug


def load_boats_to_poi(id_server):
    boats = bknd_core.execute_sql_query(
        "SELECT thread_id from yachts where {direction} <> %s and {id_server} = %s".format(direction=ewcfg.col_direction, id_server=ewcfg.col_id_server), ('sunk', id_server))
    boat_poi = poi_static.id_to_poi.get('yacht')
    print("LOADING BOATS")
    for boat in boats:
        print('{}{}'.format('yacht', boat[0]))
        poi_static.id_to_poi['{}{}'.format('yacht', boat[0])] = boat_poi
        #boat_obj = EwYacht(id_server=id_server, id_thread=boat)



async def boat_tick(id_server, tick_count):
    boats = bknd_core.execute_sql_query(
        "SELECT thread_id from yachts where {direction} <> %s and {id_server} = %s".format(direction=ewcfg.col_direction, id_server=ewcfg.col_id_server),  ('sunk', id_server))
    for boat in boats:
        boat_obj = EwYacht(id_server=id_server, id_thread=boat[0])

        #If the ship is moving in a direction, allow it to move until it hits an obstruction.
        if boat_obj.direction == 'stop':
            boat_obj.speed = 0
        else:
            if tick_count == 1:
                spaces_to_advance = math.floor(boat_obj.speed / 2)
            else:
                spaces_to_advance = math.ceil(boat_obj.speed / 2)

            if boat_obj.direction in ['north', 'west']:
                direction_to_advance = -1
            else:
                direction_to_advance = 1

            seacursor_x = boat_obj.xcoord
            seacursor_y = boat_obj.ycoord
            response = ""
            radius = 0

            if boat_obj.direction in ['north', 'south', 'east', 'west'] and boat_obj.poopdeck != -1:
                player = EwUser(id_user=boat_obj.poopdeck, id_server=id_server)
                if player.poi == "yacht{}".format(boat_obj.thread_id):
                    radius = 3
            if boat_obj.direction in ['north', 'south', 'east', 'west'] and boat_obj.helm != -1:
                player = EwUser(id_user=boat_obj.helm, id_server=id_server)
                if player.poi == "yacht{}".format(boat_obj.thread_id):
                    radius = 4

            #if radius > 0:
                #response += draw_map(xcoord=boat_obj.xcoord, ycoord=boat_obj.ycoord, id_server=boat_obj.id_server, radius=radius)

            for x in range(spaces_to_advance):
                if boat_obj.direction in['north', 'south']:
                    seacursor_y += direction_to_advance
                else:
                    seacursor_x += direction_to_advance

                if ewdebug.seamap[seacursor_y][seacursor_x] == -1:
                    boat_obj.xcoord = seacursor_x
                    boat_obj.ycoord = seacursor_y
                    if radius > 0:
                        boat_obj.persist()
                        response += draw_map(xcoord=boat_obj.xcoord, ycoord=boat_obj.ycoord, id_server=boat_obj.id_server, radius=radius)
                    if response != "":
                        thread = await boat_obj.get_thread()
                        await fe_utils.send_message(None, thread, response)
                elif ewdebug.seamap[seacursor_y][seacursor_x] == -2:
                    dest = random.randint(0, 4)
                    new_coords = ewdebug.loc_arr.get(dest)
                    boat_obj.xcoord = new_coords[0]
                    boat_obj.ycoord = new_coords[1]
                    if radius > 0:
                        boat_obj.persist()
                        response += draw_map(xcoord=boat_obj.xcoord, ycoord=boat_obj.ycoord, id_server=boat_obj.id_server, radius=radius)
                    if response != "":
                        response += "\nThe whirlpool warped you somewhere else..."
                        thread = await boat_obj.get_thread()
                        await fe_utils.send_message(None, thread, response)
                elif ewdebug.seamap[seacursor_y][seacursor_x] == 0 and ewdebug.seamap[boat_obj.ycoord][boat_obj.xcoord] == -1:
                    boat_obj.xcoord = seacursor_x
                    boat_obj.ycoord = seacursor_y
                    if radius > 0:
                        boat_obj.persist()
                        response += draw_map(xcoord=boat_obj.xcoord, ycoord=boat_obj.ycoord, id_server=boat_obj.id_server, radius=radius)
                    boat_obj.direction = 'stop'
                    boat_obj.flood = 0
                    boat_obj.speed = 0
                    response += "\nLAND HO! Looks like we've arrived at an island."
                    thread = await boat_obj.get_thread()
                    await fe_utils.send_message(None, thread, response)
                    break
                elif ewdebug.seamap[seacursor_y][seacursor_x] in [3, 0]:
                    if radius > 0:
                        boat_obj.persist()
                        response += draw_map(xcoord=boat_obj.xcoord, ycoord=boat_obj.ycoord, id_server=boat_obj.id_server, radius=radius)
                    response += "\nThe {} suddenly stops. Did we hit something?".format(boat_obj.yacht_name)
                    thread = await boat_obj.get_thread()
                    await fe_utils.send_message(None, thread, response)
                    break




        stats = boat_obj.getYachtStats()

        for stat in stats:
            if stat == 'flood' and ewdebug.seamap[boat_obj.ycoord][boat_obj.xcoord] != 0:
                boat_obj.flood += stat.quantity
            elif stat == 'gangplanked':
                attached_yacht = EwYacht(id_server=boat_obj.id_server, id_thread=stat.target)
                if attached_yacht.xcoord != boat_obj.xcoord or attached_yacht.ycoord != boat_obj.ycoord:
                    boat_obj.clearStat(id_stat=stat.id_stat)

        if boat_obj.flood > 100:

            boatkill = bknd_core.execute_sql_query('select {target} from yacht_stats where {thread_id} = %s and {id_server} = %s group by {target} order by sum(quantity) desc limit 1'.format(
                thread_id=ewcfg.col_thread_id,
                id_server=ewcfg.col_id_server,
                target = 'target'
            ),(boat_obj.thread_id, boat_obj.id_server))

            boat_killer = boatkill[0][0]
            return await sink(thread_id=boat_obj.thread_id, id_server=id_server, killer_yacht=boat_killer)
        boat_obj.persist()




def find_local_boats(poi = None, name = None, id_server = None, current_coords = None):
    boats = []
    query = "select {} from yachts where {} = %s and {} <> %s".format(ewcfg.col_thread_id, ewcfg.col_id_server, ewcfg.col_direction)
    data = bknd_core.execute_sql_query(query, (id_server, 'sunk'))
    if current_coords is not None:
        if type(current_coords[0]) == int:
            current_coords = [current_coords]

    for id in data:
        yacht = EwYacht(id_server=id_server, id_thread=id[0])
        poi_match = 0
        if poi is not None:
            poi_found = poi_static.id_to_poi.get(poi)
            if poi_found.coord is None:
                continue

            else:
                for coord in poi_found.coord:
                    if yacht.xcoord == coord[0] and yacht.ycoord == coord[1]:
                        poi_match = 1
                        break
        elif current_coords is not None:
            for coord in current_coords:
                if yacht.xcoord == coord[0] and yacht.ycoord == coord[1]:
                    poi_match = 1
                    break
        else:
            poi_match = 1
        if poi_match == 1 and(name is None or coreutils.flattenTokenListToString(name).lower() in coreutils.flattenTokenListToString(yacht.yacht_name).lower()):
            boats.append(yacht)
    return boats


def clear_station(id_user, thread_id, id_server):
    yacht = EwYacht(id_thread=thread_id, id_server=id_server)
    if id_user == yacht.poopdeck:
        yacht.poopdeck = -1
    if id_user == yacht.storehouse:
        yacht.storehouse = -1
    if id_user == yacht.cannon:
        yacht.cannon = -1
    if id_user == yacht.helm:
        yacht.helm = -1
    yacht.persist()
    return yacht


async def sink(thread_id, id_server, killer_yacht = None):

    sunk_yacht = EwYacht(id_server=id_server, id_thread=thread_id)
    sunk_yacht.direction = 'sunk'
    sunk_yacht.speed = 0
    sunk_yacht.helm = -1
    sunk_yacht.poopdeck = -1
    sunk_yacht.storehouse = -1
    sunk_yacht.cannon = -1

    total_yield = 0
    if sunk_yacht.slimes > 0:
        total_yield += sunk_yacht.slimes

    sunk_yacht.change_slimes(n=-sunk_yacht.slimes)

    district_data = EwDistrict(id_server=id_server, district='yacht')
    players = district_data.get_players_in_district(poi_name="yacht{}".format(thread_id))

    sunk_yacht.persist()

    thread = await sunk_yacht.get_thread()
    members = await thread.fetch_members()

    for member in members:
        await thread.remove_user(member)

    for player in players:
        player_obj = EwUser(id_user=player, id_server=id_server)
        if player_obj.slimes > 0:
            total_yield += player_obj.slimes

        if player_obj.life_state != ewcfg.life_state_corpse:
            player_obj.change_slimes(n=-player_obj.slimes)
            player_obj.poi = "{}_{}_{}".format(ewcfg.poi_id_slimesea, sunk_yacht.xcoord, sunk_yacht.ycoord) #get items to sink to this region specifically
            await player_obj.die(cause=ewcfg.cause_shipsink, updateRoles=True)

    if killer_yacht is not None:
        killer_yacht_obj = EwYacht(id_server=id_server, id_thread=killer_yacht)
        if total_yield > 0:
            killer_yacht_obj.change_slimes(n=total_yield)
            killer_yacht_obj.persist()
    else:
        sewer_district = EwDistrict(id_server=sunk_yacht.id_server, district=ewcfg.poi_id_thesewers)
        sewer_district.change_slimes(n=total_yield)
        sewer_district.persist()



def draw_map(xcoord, ycoord, id_server, radius = 4, treasuremap = False):
    center_x = min(max(xcoord, radius+1), ewdebug.max_right_bound - radius)
    center_y = min(max(ycoord, radius+1), ewdebug.max_lower_bound - radius)
    search_coords = []
    for x in range(-radius, radius+1):
        for y in range(-radius, radius+1):
            search_coords.append([center_x + x, center_y + y])

    boats = find_local_boats(id_server=id_server, current_coords=search_coords)

    response = ''

    map_key = {
        -1: '🟦',  # blue
        3: '⬛',  # black
        0: '🟩',  # green
        -2: '🌀' #WARP ZONE

    }

    for y in range(-radius, radius+1):
        response += '\n'
        for x in range(-radius, radius+1):
            letter = map_key.get(ewdebug.seamap[y + center_y][x + center_x])
            if not treasuremap:
                for boat in boats:
                    if boat.ycoord == y + center_y and boat.xcoord == x + center_x:
                        letter = '⛵'
            else:
                if xcoord == x + center_x and ycoord == y + center_y:
                    letter = '❌'
            response += letter

    return response


def get_boat_coord_radius(xcoord, ycoord, radius):
    final_list = []

    for x in range(-radius + xcoord, radius + 1 + xcoord):
        for y in range(-radius + ycoord, radius + 1 + ycoord):
            if 0 <= x <= ewdebug.max_right_bound and 0 <= y <= ewdebug.max_lower_bound:
                final_list.append([x, y])

    return final_list


def draw_item_map(id_server):
    id_item = get_slimesea_item(id_server=id_server, treasuremap=True)
    if id_item is not None:
        item_obj = bknd_item.EwItem(id_item=id_item)
        coord_arr = item_obj.id_owner.split('_')
        if len(coord_arr) != 3:
            return "Map error. Someone fucked up and now the map is covered in jizz or something."
        map = draw_map(xcoord=int(coord_arr[1]), ycoord=int(coord_arr[2]), id_server=id_server, radius=6, treasuremap=True)
        if map is not None:
            bknd_core.execute_sql_query("delete from bazaar_wares where {id_server} = %s and {value} = %s".format(id_server=ewcfg.col_id_server, value=ewcfg.col_value), (id_server, 'treasuremap'))
            item_obj.item_props['mapped'] = 1
            item_obj.persist()
        return map

def get_slimesea_item(id_server, treasuremap = False, coords = None):
    cartesian_shit = [] #

    if coords == None:
        for x in range(ewdebug.max_right_bound):
            for y in range(ewdebug.max_lower_bound):
                cartesian_shit.append([x, y])

        random.shuffle(cartesian_shit)
    else:
        cartesian_shit.append(coords)

    for pair in cartesian_shit:
        poi_search = "{}_{}_{}".format(ewcfg.poi_id_slimesea, pair[0], pair[1])
        inv = bknd_item.inventory(id_server=id_server, id_user=poi_search)
        if len(inv) == 0:
            continue
        else:
            for item in inv:
                if not treasuremap:
                    return item.get('id_item')
                else:
                    item = bknd_item.EwItem(id_item=item.get('id_item'))
                    if item.item_props.get('mapped') is not None and item.item_props.get('mapped') != 0:
                        continue
                    elif item.template in ewdebug.raretreasures or item.item_type == ewcfg.it_relic:
                        return item.id_item
    return None


