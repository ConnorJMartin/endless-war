from ew.utils import core as ewutils
from ew.utils import frontend as fe_utils


#TODO: should these utility function be somewhere else?
from ew.static.new_vendors import get_vendor_list, get_vendor, vendor_id


async def menu(cmd):
    user_data = EwUser(member=cmd.message.author, data_level=2)
    local_vendor_id_list = get_vendor_list(user_data.poi)

    # If player trys menu in mutation clinic, tell them to order the mutation menu zine
    if user_data.poi == ewcfg.poi_id_clinicofslimoplasty:
        response = "Try {}browse. The menu is in the zines.".format(ewcfg.cmd_prefix)

    # If 0 vendors in poi |OR| #general-channel, tell player to go somewhere else
    elif len(local_vendor_list) == 0 or ewutils.channel_name_is_poi(cmd.message.channel.name) == False:
        response = "There’s nothing to buy here. If you want to purchase some items, go to a sub-zone with a vendor in it, like the food court, the speakeasy, or the bazaar."
    
    # Vendors are in this location
    # Continue
    else:
        response = ""
        #TODO: get district gang alignment
        controlling_faction = ""


        for vendor_name in local_vendor_id_list:
            # if player is not fresh enough, skip secret_bodega_menu menu
            if vendor_name == vendor_id.secret_bodega_menu:
                if user_data.freshness < ewcfg.freshnesslevel_4:
                    continue
                else:
                    response += '\nThe hipster behind the counter nearly falls out of his chair after laying eyes on the sheer, unadulterated freshness before him.\n"S-Sir! Your outfit... i-it is positively ***on fleek!!*** As I see you are a fashion enthusiast like myself, let me show you the good stuff…"\n'

            vendor = get_vendor(vendor_name)


            price_multiplier = 1
            #TODO: check stock data for multiplier
            #if stock_data != None:
            #   price_multiplier *= (stock_data.exchange_rate / ewcfg.default_stock_exchange_rate) ** 0.2
            
            if controlling_faction != "":
                # vendor is contolled by ally faction
                if controlling_faction == user_data.faction:
                    price_multiplier /= 2

                # vendor is contolled by enemy faction
                elif user_data.faction != "":
                    price_multiplier *= 4


            response += vendor.menu_print(price_multiplier)
        
        # Special Bodega Handleing
        # If in bodega and low fashion, add hipster distain flavor text
        if vendor == ewcfg.vendor_bodega:
            if user_data.freshness < ewcfg.freshnesslevel_1:
                response += "\n\nThe hipster behind the counter is utterly repulsed by the fashion disaster in front of him. Looks like you just aren’t fresh enough for him."
                if user_data.has_soul == 0:
                    response += ".. and you probably never will be."


        # If no soul, add extra flavor text
        elif user_data.has_soul == 0:
            no_soul_dict = {
                vendor_id.dojo : "\n\nThe Dojo master looks at your soulless form with pity.",
                vendor_id.speakeasy : "\n\nThe bartender, sensing your misery, asks if you're okay.",
                vendor_id.smokers_cough : "\n\nThe cook gives you a concerned look as he throws down another helping of flapjacks.",
                vendor_id.red_mobster_seafood : "\n\nThe waiter sneers at how soulless and unkempt you look. You try to ignore him.",
                vendor_id.bazaar : "\n\nAll the shops seem so lively. You wish you had a soul so you could be like them.",
                vendor_id.beach_resort : "\n\nEverything looks so fancy here, but it doesn't really appeal to you since you don't have a soul.",
                vendor_id.country_club : "\n\nEverything looks so fancy here, but it doesn't really appeal to you since you don't have a soul.",
                vendor_id.glocksbury_comics : "\n\nThe cashier here tries to start up a conversation about life being worth living. You're having none of it.",
                vendor_id.based_hardware : "\n\nSo many industrial metals here... You contemplate which you could use to kill yourself...",
                vendor_id.waffle_house : "\n\nNot even waffles could hope to make your emptiness go away.",
                vendor_id.green_cake_cafe : "\n\nThe barista behind the counter pauses to look at your soulless misery for a second, but decides you're not worth it and gets back to work.",
                vendor_id.slimy_persuits : "\n\nYour mere presence in here ruins the cheery atmosphere."
            }
            response += no_soul_dict.get(vendor.vendor_id, "")
    
    #return message
    return await fe_utils.send_response(response, cmd)



async def order(cmd):

    # TODO: check for premium_purchase cooldown
    
    user_data = EwUser(member=cmd.message.author)
    local_vendor_id_list = get_vendor_list(user_data.poi)

    # If 0 vendors in poi |OR| #general-channel, tell player to go somewhere else
    if len(local_vendor_list) == 0 or ewutils.channel_name_is_poi(cmd.message.channel.name) == False:
        response = "There’s nothing to buy here. If you want to purchase some items, go to a sub-zone with a vendor in it, like the food court, the speakeasy, or the bazaar."
    

    # Vendors are in this location
    # Continue
    else:

        # Parse tokens
        desired_item = None
        order_togo = False

        # TODO: this is copied from old function, could do with some polish
        if cmd.tokens_count > 1:
            for token in cmd.tokens[1:]:
                if token.startswith('<@') == False and token.lower() not in "togo":  # togo can be spelled together or separate
                    desired_item = token
                    break

            for token in cmd.tokens[1:]:
                if token.lower() in "togo":  # lets people get away with just typing only to or only go (or only t etc.) but whatever
                    togo = True
                    break


        vendor = None
        menu_item = None

        for vendor_name in local_vendor_id_list:
            # if player is not fresh enough, skip secret_bodega_menu menu
            if vendor_name == vendor_id.secret_bodega_menu:
                if user_data.freshness < ewcfg.freshnesslevel_4:
                    continue
                                        
            try_vendor = get_vendor(vendor_name)
            menu_id = try_vendor.lookup_names.get(desired_item)

            if menu_id != None:
                # return vendor obj and menu obj
                vendor = try_vendor
                menu_item = try_vendor.menu.get(menu_id)
                break



        # Desired item is not in any local vendors
        if menu_item == None:
            response = "Check the {} for a list of items you can {}.".format(ewcfg.cmd_menu, ewcfg.cmd_order)

        # Desired item is in a local vendors
        # continue
        else:

                response = ""


                #get price modifier
                price_multiplier = 1
                   
                #TODO: check stock data for multiplier
                #if stock_data != None:
                #   price_multiplier *= (stock_data.exchange_rate / ewcfg.default_stock_exchange_rate) ** 0.2

                #TODO: get district gang alignment
                controlling_faction = "" 
                if controlling_faction != "":
                    # vendor is contolled by ally faction
                    if controlling_faction == user_data.faction:
                        price_multiplier /= 2
                    # vendor is contolled by enemy faction
                    elif user_data.faction != "":
                        price_multiplier *= 4


                # TODO: get togo modifier if ordering food togo
                # does it even need to be this way?
                # food capacity is a far better balance mechanic then this
                #if togo:
                #    price_multiplier *= 1.5



                cost = menu_item.modified_price(price_multiplier)

                
                # TODO: KINGPINS EAT FREE
                #if user_data.life_state == ewcfg.life_state_kingpin and item_type == ewcfg.it_food:
                #    cost = 0



                # TODO: handle different types of currency
                currency_used = "slime"
                current_currency_amount = user_data.slimes


                # If player cannot afford, tell player they dont have enough money
                if value > current_currency_amount:
                    # Not enough money.
                    response = "A {} costs {:,} {}, and you only have {:,}.".format(name, value, currency_used, current_currency_amount)



                # If player has enough money
                else:
                    


                    # SPECIAL HANDLEING pony figurines
                    if menu_item.item_id == "mylittleponyfigurine":
                        menu_item.item_id = random.choice(static_items.furniture_pony)



                    # TODO: simplifiy this with a master item lookup dictionaty
                    #check if general item type
                    item = static_items.item_map.get(menu_item.item_id)
                    #check if food item type
                    if item == None:
                        item = static_food.food_map.get(menu_item.item_id)
                    #check if cosmetic item type
                    if item == None:
                        item = static_cosmetics.cosmetic_map.get(menu_item.item_id)
                    #check if furniture item type
                    if item == None:
                        item = static_items.furniture_map.get(menu_item.item_id)
                    #check if weapon item type
                    if item == None:    
                        item = static_weapons.weapon_map.get(menu_item.item_id)
                    
                    item_type = item.item_type
                    item_props = itm_utils.gen_item_props(item)


                    # TODO: FOOD HANDLEING
                    # if not to go - eat immediatly
                    # "togo" cancels mentions - why?
                    # if mentions a target
                    # --cant feed possession ghost
                    # --cant feed someone who isnt here
                    # if togo, check food capacity

                    # TODO: WEAPON HANDLEING
                    # check weapon capacity
                    # dont sell weapons to ghosts - ghost racism

                    # TODO: IF OTHER ITEM TYPE
                    # check general inv capacity 


                    #if item is none by this point something is very wrong
                    if item != None:

                        # Attemt to steal if player has sticky fingers mutation
                        stolen = False
                        mutations = user_data.get_mutations()
                        if random.randrange(5) == 0 and ewcfg.mutation_id_stickyfingers in mutations:
                            cost = 0
                            stolen = True
                        
                        # TODO: SPECIAL HANDLEING arcade cabient    
                        # change item_props['furniture_desc'] to random game cabinet


                        # TODO: SPECIAL HANDLEING custom furniture    
                        # change various item_props to custom name

                        # Create item
                        # TODO: maybe dont do this if the food item is immediatly eaten
                        id_item = bknd_item.item_create(
                            item_type=item_type,
                            id_user=cmd.message.author.id,
                            id_server=cmd.guild.id,
                            stack_max=-1,
                            stack_size=0,
                            item_props=item_props
                        )
                    
                        # Remove slime
                        if currency_used == 'slime':
                            user_data.change_slimes(n=-cost, source=ewcfg.source_spending)
                        # TODO: Handle other currencies 

                        # TODO: add to EwComapany profits


                        # TODO: set response string

                        # TODO: handle eat in food
                        # TODO: handle order for a friend


                        # TODO: set premium purchase cooldown
                        

                        # Save user_data
                        user_data.persist()

    #finally
    await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(cmd.message.author, response))
