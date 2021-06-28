
async def old_menu(cmd):
    # get user_data 
    # - for shambler check
    # -for location check
    user_data = EwUser(member=cmd.message.author, data_level=2)


    # Cancel if player is shambler
    #if user_data.life_state == ewcfg.life_state_shambler and user_data.poi != ewcfg.poi_id_nuclear_beach_edge:
    #    response = "You lack the higher brain functions required to {}.".format(cmd.tokens[0])
    #    return await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(cmd.message.author, response))




    # get poi object to see if vendors are here
    # instead of this use poi_to_vendors
    poi = poi_static.id_to_poi.get(user_data.poi)


    # if you're in clinic tell them to buy zines
    if user_data.poi == ewcfg.poi_id_clinicofslimoplasty:
        response = "Try {}browse. The menu is in the zines.".format(ewcfg.cmd_prefix)


    # if no poi |OR| 0 vendors in poi |OR| #general-channel
    elif poi is None or len(poi.vendors) == 0 or ewutils.channel_name_is_poi(cmd.message.channel.name) == False:
        # Only allowed in the food court.
        response = "There’s nothing to buy here. If you want to purchase some items, go to a sub-zone with a vendor in it, like the food court, the speakeasy, or the bazaar."
    
    
    # yes player is in channel with vendor
    # proceed
    else:


        ### get disctict data for gang prices ####
        poi = poi_static.id_to_poi.get(user_data.poi)

        mother_district_data = None
        for mother_poi in poi.mother_districts:
            mother_poi_data = poi_static.id_to_poi.get(mother_poi)
            if mother_poi_data.is_district:
                # One of the mother pois was a district, get its controlling faction
                mother_district_data = EwDistrict(district=mother_poi, id_server=user_data.id_server)
                break
            else:
                # One of the mother pois was a street, get the father district of that street and its controlling faction
                father_poi = mother_poi_data.father_district
                mother_district_data = EwDistrict(district=father_poi, id_server=user_data.id_server)
                break
                
        controlling_faction = poi_utils.get_subzone_controlling_faction(user_data.poi, user_data.id_server)

        


        #depriciated shambled discrict check

        #district_data = EwDistrict(district=poi.id_poi, id_server=user_data.id_server)
        #shambler_multiplier = 1  # for speakeasy during shambler times
        #if district_data.is_degraded() and poi.id_poi != ewcfg.poi_id_nuclear_beach_edge:
        #    if poi.id_poi == ewcfg.poi_id_speakeasy:
        #        shambler_multiplier = 4
        #    else:
        #        response = "{} has been degraded by shamblers. You can't {} here anymore.".format(poi.str_name, cmd.tokens[0])
        #        return await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(cmd.message.author, response))


        response = "{} Menu:\n\n".format(poi.str_name)

        vendors_list = poi.vendors

        for vendor in vendors_list:

            if vendor == ewcfg.vendor_secretbodega:
                if user_data.freshness < ewcfg.freshnesslevel_4:
                    continue
                else:
                    response += '\nThe hipster behind the counter nearly falls out of his chair after laying eyes on the sheer, unadulterated freshness before him.\n"S-Sir! Your outfit... i-it is positively ***on fleek!!*** As I see you are a fashion enthusiast like myself, let me show you the good stuff…"\n'

            items = []
            
            # get market data 
            # - gets bazaar inventory
            market_data = EwMarket(id_server=cmd.guild.id)


            # If the vendor is the bazaar get the current rotation of items from the market_data
            vendor_inv = vendors.vendor_inv[vendor] if vendor != ewcfg.vendor_bazaar else market_data.bazaar_wares.values()
            for item_name in vendor_inv:
                item_item = static_items.item_map.get(item_name)
                food_item = static_food.food_map.get(item_name)
                cosmetic_item = static_cosmetics.cosmetic_map.get(item_name)
                furniture_item = static_items.furniture_map.get(item_name)
                weapon_item = static_weapons.weapon_map.get(item_name)

                # increase profits for the stock market
                stock_data = None
                if vendor in ewcfg.vendor_stock_map:
                    stock = ewcfg.vendor_stock_map.get(vendor)
                    stock_data = EwStock(id_server=user_data.id_server, stock=stock)

                value = 0

                if item_item:
                    value = item_item.price

                if food_item:
                    value = food_item.price

                if cosmetic_item:
                    value = cosmetic_item.price

                if furniture_item:
                    value = furniture_item.price

                if weapon_item:
                    value = weapon_item.price

                if stock_data != None:
                    value *= (stock_data.exchange_rate / ewcfg.default_stock_exchange_rate) ** 0.2

                # multiply by 4 is speakeasy is shambled
                value *= shambler_multiplier

                if mother_district_data != None:
                    if controlling_faction != "":
                        # prices are halved for the controlling gang
                        if controlling_faction == user_data.faction:
                            value /= 2

                        # and 4 times as much for enemy gangsters
                        elif user_data.faction != "":
                            value *= 4

                if vendor == ewcfg.vendor_breakroom and user_data.faction == ewcfg.faction_slimecorp:
                    value = 0

                value = int(value)

                if value != 0:
                    items.append('{} ({:,})'.format(item_name, value))
                else:
                    items.append(item_name)

            response += "**{}**: *{}*\n".format(vendor, ewutils.formatNiceList(names=items))

            if vendor == ewcfg.vendor_bodega:
                if user_data.freshness < ewcfg.freshnesslevel_1:
                    response += "\nThe hipster behind the counter is utterly repulsed by the fashion disaster in front of him. Looks like you just aren’t fresh enough for him."
            if user_data.has_soul == 0:
                if vendor == ewcfg.vendor_dojo:
                    response += "\n\nThe Dojo master looks at your soulless form with pity."
                elif vendor == ewcfg.vendor_bar:
                    response += "\n\nThe bartender, sensing your misery, asks if you're okay."
                elif vendor == ewcfg.vendor_diner:
                    response += "\n\nThe cook gives you a concerned look as he throws down another helping of flapjacks."
                elif vendor == ewcfg.vendor_seafood:
                    response += "\n\nThe waiter sneers at how soulless and unkempt you look. You try to ignore him."
                elif vendor == ewcfg.vendor_bazaar:
                    response += "\n\nAll the shops seem so lively. You wish you had a soul so you could be like them."
                elif vendor == ewcfg.vendor_beachresort or vendor == ewcfg.vendor_countryclub:
                    response += "\n\nEverything looks so fancy here, but it doesn't really appeal to you since you don't have a soul."
                elif vendor == ewcfg.vendor_bodega:
                    if user_data.freshness < ewcfg.freshnesslevel_1:
                        response += ".. and you probably never will be."
                elif vendor == ewcfg.vendor_glocksburycomics:
                    response += "\n\nThe cashier here tries to start up a conversation about life being worth living. You're having none of it."
                elif vendor == ewcfg.vendor_basedhardware:
                    response += "\n\nSo many industrial metals here... You contemplate which you could use to kill yourself..."
                elif vendor == ewcfg.vendor_basedhardware:
                    response += "\n\nNot even waffles could hope to make your emptiness go away."
                elif vendor == ewcfg.vendor_greencakecafe:
                    response += "\n\nThe barista behind the counter pauses to look at your soulless misery for a second, but decides you're not worth it and gets back to work."
                elif vendor == ewcfg.vendor_slimypersuits:
                    response += "\n\nYour mere presence in here ruins the cheery atmosphere."

    # Send the response to the player.
    await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(cmd.message.author, response))

# Buy items.
async def old_order(cmd):



    # get user data for 
    # - 
    user_data = EwUser(member=cmd.message.author)

    # get mutations
    # - for sticky fingers later
    mutations = user_data.get_mutations()


    # depreciated shamber check
    if user_data.life_state == ewcfg.life_state_shambler and user_data.poi != ewcfg.poi_id_nuclear_beach_edge:
        response = "You lack the higher brain functions required to {}.".format(cmd.tokens[0])
        return await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(cmd.message.author, response))



    # market data 
    # for bazaar item list
    market_data = EwMarket(id_server=cmd.guild.id)



    # get currencey for later
    currency_used = 'slime'
    current_currency_amount = user_data.slimes

    # get list of vendors
    poi = poi_static.id_to_poi.get(user_data.poi)
    if poi is None or len(poi.vendors) == 0 or ewutils.channel_name_is_poi(cmd.message.channel.name) == False:
        response = "There’s nothing to buy here. If you want to purchase some items, go to a sub-zone with a vendor in it, like the food court, the speakeasy, or the bazaar."

    # Correct zone continue
    else:

        #get district data
        poi = poi_static.id_to_poi.get(user_data.poi)
        district_data = EwDistrict(district=poi.id_poi, id_server=user_data.id_server)


        # depreciated shambler check 
        #shambler_multiplier = 1  # for speakeasy during shambler times
        #if district_data.is_degraded():
        #    if poi.id_poi == ewcfg.poi_id_speakeasy:
        #        shambler_multiplier = 4
        #    else:
        #        response = "{} has been degraded by shamblers. You can't {} here anymore.".format(poi.str_name, cmd.tokens[0])
        #        return await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(cmd.message.author, response))
        # value = ewutils.flattenTokenListToString(cmd.tokens[1:2])

        # if cmd.tokens_count > 1:
        #	value = cmd.tokens[1]
        #	value = value.lower()


        # parce tokens
        # value = desired item string
        # togo = togo bool
        value = None
        togo = False
        if cmd.tokens_count > 1:
            for token in cmd.tokens[1:]:
                if token.startswith('<@') == False and token.lower() not in "togo":  # togo can be spelled together or separate
                    value = token
                    break

            for token in cmd.tokens[1:]:
                if token.lower() in "togo":  # lets people get away with just typing only to or only go (or only t etc.) but whatever
                    togo = True
                    break



        # Finds the item if it's an EwGeneralItem.



        # special case for my little pony figures
        if value == "mylittleponyfigurine":
            value = random.choice(static_items.furniture_pony)



        #find if desired item is in item map
        #find item type
        item = static_items.item_map.get(value)

        item_type = ewcfg.it_item
        if item != None:
            item_id = item.id_item
            name = item.str_name

        # Finds the item if it's an EwFood item.
        if item == None:
            item = static_food.food_map.get(value)
            item_type = ewcfg.it_food
            if item != None:
                item_id = item.id_food
                name = item.str_name

        # Finds the item if it's an EwCosmeticItem.
        if item == None:
            item = static_cosmetics.cosmetic_map.get(value)
            item_type = ewcfg.it_cosmetic
            if item != None:
                item_id = item.id_cosmetic
                name = item.str_name

        if item == None:
            item = static_items.furniture_map.get(value)
            item_type = ewcfg.it_furniture
            if item != None:
                item_id = item.id_furniture
                name = item.str_name
                if item_id in static_items.furniture_pony:
                    item.vendors = [ewcfg.vendor_bazaar]

        if item == None:
            item = static_weapons.weapon_map.get(value)
            item_type = ewcfg.it_weapon
            if item != None:
                item_id = item.id_weapon
                name = item.str_weapon


        #if item has been found
        if item != None:
            item_type = item.item_type


            # find if desired item's vendor list matches with poi vendor list
            # very different way of doing things 

            # Gets a vendor that the item is available and the player currently located in
            try:
                current_vendor = (set(item.vendors).intersection(set(poi.vendors))).pop()
            except:
                current_vendor = None



            # Check if the item is available in the current bazaar item rotation
            if current_vendor == ewcfg.vendor_bazaar:
                if item_id not in market_data.bazaar_wares.values():
                    
                    #special handling for pony figures
                    if item_id in static_items.furniture_pony and "mylittleponyfigurine" in market_data.bazaar_wares.values():
                        pass
                    else:
                        current_vendor = None


            # depreciated shambler feature
            if current_vendor == ewcfg.vendor_downpourlaboratory:
                currency_used = 'brainz'
                current_currency_amount = user_data.gvs_currency


            # if player wants a real item but it isnt for sale at this location
            if current_vendor is None or len(current_vendor) < 1:
                response = "Check the {} for a list of items you can {}.".format(ewcfg.cmd_menu, ewcfg.cmd_order)



            # if desired item is at local vendor
            else:
                response = ""

                value = item.price


                # premium purchace condition
                premium_purchase = True if item_id in ewcfg.premium_items else False
                if premium_purchase:
                    togo = True  # Just in case they order a premium food item, don't make them eat it right then and there.

                    # limit premium purchase by cooldown
                    if ewcfg.cd_premium_purchase > (int(time.time()) - user_data.time_lastpremiumpurchase):
                        response = "That item is in very limited stock! The vendor asks that you refrain from purchasing it for a day or two."
                        return await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(cmd.message.author, response))

                    #what the fuck
                    elif ewcfg.cd_new_player > (int(time.time()) - user_data.time_joined):
                        response = "You've only been in the city for a few days. The vendor doesn't trust you with that item very much..."
                        return await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(cmd.message.author, response))



                # get stock price for cost multiplier
                # get company data to add to company.recent_profits
                stock_data = None
                company_data = None
                # factor in the current stocks
                for vendor in item.vendors:
                    if vendor in ewcfg.vendor_stock_map:
                        stock = ewcfg.vendor_stock_map.get(vendor)
                        company_data = EwCompany(id_server=user_data.id_server, stock=stock)
                        stock_data = EwStock(id_server=user_data.id_server, stock=stock)


                # add stock price multiplier
                if stock_data is not None:
                    value *= (stock_data.exchange_rate / ewcfg.default_stock_exchange_rate) ** 0.2



                #controlling faction multiplier 
                controlling_faction = poi_utils.get_subzone_controlling_faction(user_data.poi, user_data.id_server)
                if controlling_faction != "":
                    # prices are halved for the controlling gang
                    if controlling_faction == user_data.faction:
                        value /= 2
                    # and 4 times as much for enemy gangsters
                    elif user_data.faction != "":
                        value *= 4




                # DEPRECIATED raise shambled speakeasy price 4 times
                #value *= shambler_multiplier


                # modify price for togo food
                # Raise the price for togo ordering. This gets lowered back down later if someone does togo ordering on a non-food item by mistake.
                if togo:
                    value *= 1.5

                # depreciated free slimecorp breakroom food
                if current_vendor == ewcfg.vendor_breakroom and user_data.faction == ewcfg.faction_slimecorp:
                    value = 0


                #round price
                value = int(value)



                food_ordered = False
                target_data = None



                # Kingpins eat free.
                if (user_data.life_state == ewcfg.life_state_kingpin or user_data.life_state == ewcfg.life_state_grandfoe) and item_type == ewcfg.it_food:
                    value = 0




                #check if player can afford
                if value > current_currency_amount:
                    # Not enough money.
                    response = "A {} costs {:,} {}, and you only have {:,}.".format(name, value, currency_used, current_currency_amount)


                #if player can afford continue
                else:

                    #repeat mutation get lol
                    # only if player could afford item in the first place, roll to see of they steal it
                    mutations = user_data.get_mutations()
                    if random.randrange(5) == 0 and ewcfg.mutation_id_stickyfingers in mutations:
                        value = 0

                    # FOOD HANDLEING
                    # if not to go - eat immediatly
                    # "togo" cancels mentions - why?
                    # if mentions a target
                    # --cant feed possession ghost
                    # --cant feed someone who isnt here
                    # if togo, check food capacity
                    if item_type == ewcfg.it_food:
                        food_ordered = True

                        food_items = bknd_item.inventory(
                            id_user=cmd.message.author.id,
                            id_server=cmd.guild.id,
                            item_type_filter=ewcfg.it_food
                        )

                        target = None
                        target_data = None
                        if not togo:  # cant order togo for someone else, you can just give it to them in person
                            if cmd.mentions_count == 1:
                                target = cmd.mentions[0]
                                if target.id == cmd.message.author.id:
                                    target = None

                        if target != None:
                            target_data = EwUser(member=target)
                            if target_data.life_state == ewcfg.life_state_corpse and target_data.get_possession():
                                response = "How are you planning to feed them while they're possessing you?"
                                return await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(cmd.message.author, response))
                            elif target_data.poi != user_data.poi:
                                response = "You can't order anything for them because they aren't here!"
                                return await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(cmd.message.author, response))

                        if len(food_items) >= user_data.get_food_capacity() and target_data == None and togo:
                            # user_data never got persisted so the player won't lose money unnecessarily
                            response = "You can't carry any more food than that."
                            return await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(cmd.message.author, response))


                    # WEAPON HANDLEING
                    # check weapon capacity
                    # dont sell weapons to ghosts - ghost racism
                    elif item_type == ewcfg.it_weapon:
                        weapons_held = bknd_item.inventory(
                            id_user=user_data.id_user,
                            id_server=cmd.guild.id,
                            item_type_filter=ewcfg.it_weapon
                        )

                        if len(weapons_held) >= user_data.get_weapon_capacity():
                            response = "You can't carry any more weapons."
                            return await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(cmd.message.author, response))


                        elif user_data.life_state == ewcfg.life_state_corpse:
                            response = "Ghosts can't hold weapons."
                            return await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(cmd.message.author, response))


                    # IF OTHER ITEM TYPE
                    # check general inv capacity 
                    # food and weapon limits are different? huh interesting
                    else:
                        other_items_held = bknd_item.inventory(
                            id_user=user_data.id_user,
                            id_server=cmd.guild.id,
                            item_type_filter=item_type
                        )

                        if len(other_items_held) >= ewcfg.generic_inv_limit:
                            response = ewcfg.str_generic_inv_limit.format(item_type)
                            return await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(cmd.message.author, response))


                    #get item properties
                    item_props = itm_utils.gen_item_props(item)


                    # if not ordering food togo reduce price here == why is it done no matter what then undone conditionally???

                    # Only food should have the value multiplied. If someone togo orders a non-food item by mistake, lower it back down.
                    if not food_ordered and togo:
                        value = int(value / 1.5)



                    #hanndle differernt currency = depreciated system
                    if currency_used == 'slime':
                        user_data.change_slimes(n=-value, source=ewcfg.source_spending)
                    elif currency_used == 'brainz':
                        user_data.gvs_currency -= value


                    # add company data for stock market vendors
                    if company_data is not None:
                        company_data.recent_profits += value
                        company_data.persist()


                    # SPECAIL HANDLING arcade cabinet
                    if item.str_name == "arcade cabinet":
                        item_props['furniture_desc'] = random.choice(ewcfg.cabinets_list)

                    # SPECIAL HANDLING custom furniture
                    elif item.item_type == ewcfg.it_furniture:
                        if "custom" in item_props.get('id_furniture'):
                            if cmd.tokens_count < 4 or cmd.tokens[2] == "" or cmd.tokens[3] == "":
                                response = "You need to specify the customization text before buying a custom item. Come on, isn't that self-evident? (!order [custom item] \"custom name\" \"custom description\")"
                                return await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(cmd.message.author, response))
                            else:
                                customname = cmd.tokens[2]


                                if len(customname) > 32:
                                    response = "That name is too long. ({:,}/32)".format(len(customname))
                                    return await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(cmd.message.author, response))

                                customdesc = cmd.tokens[3]

                                if len(customdesc) > 500:
                                    response = "That description is too long. ({:,}/500)".format(len(customdesc))
                                    return await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(cmd.message.author, response))

                                name = item_props['furniture_name'] = item_props['furniture_name'].format(custom=customname)
                                item_props['furniture_desc'] = customdesc
                                item_props['furniture_look_desc'] = item_props['furniture_look_desc'].format(custom=customname)
                                item_props['furniture_place_desc'] = item_props['furniture_place_desc'].format(custom=customname)


                    # create item even if its about to be eaten as a eat in food
                    # create item
                    id_item = bknd_item.item_create(
                        item_type=item_type,
                        id_user=cmd.message.author.id,
                        id_server=cmd.guild.id,
                        stack_max=-1,
                        stack_size=0,
                        item_props=item_props
                    )

                    # change flavor text based on price 
                    if value == 0:
                        response = "You swipe a {} from the counter at {}.".format(name, current_vendor)
                    else:
                        response = "You slam {:,} {} down on the counter at {} for {}.".format(value, currency_used, current_vendor, name)



                    #if food wasnt to go, eat now
                    if food_ordered and not togo:
                        item_data = EwItem(id_item=id_item)

                        # feed someone else
                        if target_data != None:

                            target_player_data = EwPlayer(id_user=target_data.id_user)

                            if value == 0:
                                response = "You swipe a {} from the counter at {} and give it to {}.".format(name, current_vendor, target_player_data.display_name)
                            else:
                                response = "You slam {:,} slime down on the counter at {} for {} and give it to {}.".format(value, current_vendor, name, target_player_data.display_name)

                            response += "\n\n*{}*: ".format(target_player_data.display_name) + target_data.eat(item_data)
                            target_data.persist()
                            asyncio.ensure_future(loop_utils.decrease_food_multiplier(user_data.id_user))


                        #if eating yourself
                        else:
                            if value == 0:
                                response = "You swipe a {} from the counter at {} and eat it right on the spot.".format(name, current_vendor)
                            else:
                                response = "You slam {:,} slime down on the counter at {} for {} and eat it right on the spot.".format(value, current_vendor, name)

                            user_player_data = EwPlayer(id_user=user_data.id_user)

                            response += "\n\n*{}*: ".format(user_player_data.display_name) + user_data.eat(item_data)
                            user_data.persist()
                            asyncio.ensure_future(loop_utils.decrease_food_multiplier(user_data.id_user))


                    #set cooldown for premium purchase
                    if premium_purchase:
                        user_data.time_lastpremiumpurchase = int(time.time())

                    #persist data
                    user_data.persist()




        #desired item token does not match any item
        else:
            response = "Check the {} for a list of items you can {}.".format(ewcfg.cmd_menu, ewcfg.cmd_order)

    # Send the response to the player.
    await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(cmd.message.author, response))

