

async def help(cmd):
    response = ""

    if (no_desired_topic):
        # Give expinations of district specific mechanics
        if (in_mines_channel):
            response = mine_explanation
            
        elif (in_vendor_channel):
            response = vendor_explanation
            
        elif (in_zine_store_channel):
            response = zine_store_explanation
            
        elif (in_farms_channel):
            response = farm_explanation
            
        elif (in_transport_channel):
            response = transport_explanation
            
        elif (in_stock_exchange_channel):
            response = stocks_explanation
            
        elif (in_casino_channel):
            response = casino_explanation

        elif (in_real_estate_channel):
            response = real_estate_explanation

        elif (in_fishing_spot_channel):
            response = fishing_spot_explanation
            
        elif (in_outskirts_channel):
            response = hunting_explanation
            
        elif (in_sewers_channel):
            response = death_explanation

        elif (in_apartment_channel):
            response = apartment_explanation

        # districts that grant access to keyword topics
        elif (in_college):
            response = college_explanation
            response += list_of_topics

        elif (in_dojo):
            response = dojo_explanation
            response += list_of_additional_dojo_topics
            
        elif (in_labs):
            response = labs_explanation
            response += list_of_additional_lab_topics
        
        elif (in_chemo_clinic):
            response = clinic_explanation
            response += list_of_additional_clinic_topics

        # Aditionally, add gameguide list of topics
        # do not do if in college because this would duplicate the list of topics
        if (has_gameguide and not_in_college):
            response += gameguide
            response += list_of_topics

        if response == "":
            
            response = catch_all_generic_response

    elif (desired_topic)

        accessible_topics = []
        
        if (in_college or has_gameguide):
            # allow access to all topics keywords
            accessible_topics += all_topics_list

        elif (in_dojo):
            # allow access to limited topics 
            # weapon and combat wisdom courtesy of the dojo master
            accessible_topics += weapons_topics
            accessible_topics += combat_topics

        elif (in_labs):
            # allow access to limited topics
            # explinations of slimeoids and mutations
            accessible_topics += slimeoids_topics
            accessible_topics += mutations_topics
        
        elif (in_chemo_clinic):
            # allow access to limited topics
            # explinations of mutations
            accessible_topics += mutations_topics

        if desired_topic in accessible_topics:
            response = desired_topic_response
        else:
            response = "You cant look that up"
            if (len(accessible_topics) > 0):
                response += "try these topics"
            else:
                response += "go to college or buy a game guide"
    

    send_response(response, cmd)






district_help_responses = {
    #mines_channels = mine_explanation
    ewcfg.poi_id_mine: help_mine_explaniation,
    ewcfg.poi_id_cv_mines: help_mine_explaniation,
    ewcfg.poi_id_tt_mines: help_mine_explaniation,
            
    #farms_channel = farm_explanation
    ewcfg.poi_id_jr_farms: help_farm_explaniation,
    ewcfg.poi_id_og_farms: help_farm_explaniation,
    ewcfg.poi_id_ab_farms: help_farm_explaniation,
            
    #stock_exchange_channel = stocks_explanation
    ewcfg.poi_id_stockexchange: help_investing_explaniation,
            
    #casino_channel = casino_explanation
    ewcfg.poi_id_casino: help_casino_explaniation,

    #real_estate_channel = real_estate_explanation
    ewcfg.poi_id_realestate: help_real_estate_explaniation,

    #sewers_channel = death_explanation
    ewcfg.poi_id_thesewers: help_death_explaniation,
    
    #college_channel = college_explanation
    ewcfg.poi_id_neomilwaukeestate: help_college_explaniation,
    ewcfg.poi_id_nlacu: help_college_explaniation,

    #dojo_channel = dojo_explanation
    ewcfg.poi_id_dojo: help_dojo_explaniation,
            
    #labs_channel = labs_explanation
    ewcfg.poi_id_slimeoidlab: help_labs_explaniation,

    #chemo_clinic_channel = clinic_explanation
    ewcfg.poi_id_clinicofslimoplasty: help_clinic_explaniation,




    #transport_channel = transport_explanation
    #generate list of transport stations 
    #make different ones for ferry and blimp
    
    #fishing_spot_channel = fishing_spot_explanation
    #generate list of fishing spots

    #outskirts_channel = hunting_explanation
    #generate list of outskirts


    #apartment_channel = apartment_explanation
    #generate list of apartment


    ### make different explinations for different vendors
    #vendor_channel = vendor_explanation
            
    #zine_store_channel = zine_store_explanation

}













async def old_help(cmd):
    response = ""
    topic = None

    user_data = EwUser(member=cmd.message.author)

    # setup response container for long messages
    resp_cont = EwResponseContainer(id_server=cmd.guild.id)


    # If user is in a college or if they have a game guide, allow access to many topics
    gameguide = bknd_item.find_item(item_search="gameguide", id_user=cmd.message.author.id, id_server=cmd.guild.id if cmd.guild is not None else None, item_type_filter=ewcfg.it_item)
    if user_data.poi == ewcfg.poi_id_neomilwaukeestate or user_data.poi == ewcfg.poi_id_nlacu or gameguide:
        if not len(cmd.tokens) > 1:
            topic_counter = 0
            topic_total = 0
            weapon_topic_counter = 0
            weapon_topic_total = 0

            # list off help topics to player at college
            response = "(Use !help [topic] to learn about a topic. Example: '!help gangs')\n\nWhat would you like to learn about? Topics include: \n"

            # display the list of topics in order
            topics = ewcfg.help_responses_ordered_keys
            for topic in topics:
                topic_counter += 1
                topic_total += 1
                response += "**{}**".format(topic)
                if topic_total != len(topics):
                    response += ", "

                if topic_counter == 5:
                    topic_counter = 0
                    response += "\n"

            response += '\n\n'

            weapon_topics = ewcfg.weapon_help_responses_ordered_keys
            for weapon_topic in weapon_topics:
                weapon_topic_counter += 1
                weapon_topic_total += 1
                response += "**{}**".format(weapon_topic)
                if weapon_topic_total != len(weapon_topics):
                    response += ", "

                if weapon_topic_counter == 5:
                    weapon_topic_counter = 0
                    response += "\n"

            resp_cont.add_channel_response(cmd.message.channel, fe_utils.formatMessage(cmd.message.author, response))

        else:
            topic = ewutils.flattenTokenListToString(cmd.tokens[1:])
            if topic in ewcfg.help_responses:
                response = ewcfg.help_responses[topic]
                resp_cont.add_channel_response(cmd.message.channel, fe_utils.formatMessage(cmd.message.author, response))
                if topic == 'mymutations':
                    mutations = user_data.get_mutations()
                    if len(mutations) == 0:
                        response = "\nWait... you don't have any!"
                        resp_cont.add_channel_response(cmd.message.channel, fe_utils.formatMessage(cmd.message.author, response))
                    else:
                        for mutation in mutations:
                            response = "**{}**: {}".format(mutation, ewcfg.mutation_descriptions[mutation])
                            resp_cont.add_channel_response(cmd.message.channel, response)

            else:
                response = 'ENDLESS WAR questions your belief in the existence of such a topic. Try referring to the topics list again by using just !help.'
                resp_cont.add_channel_response(cmd.message.channel, fe_utils.formatMessage(cmd.message.author, response))
   
   
    # If player has no Guide show limited topics
    else:

        poi = poi_static.id_to_poi.get(user_data.poi)

        dojo_topics = [
            "dojo", "sparring", "combat", ewcfg.weapon_id_revolver,
            ewcfg.weapon_id_dualpistols, ewcfg.weapon_id_shotgun, ewcfg.weapon_id_rifle,
            ewcfg.weapon_id_smg, ewcfg.weapon_id_minigun, ewcfg.weapon_id_bat, ewcfg.weapon_id_brassknuckles,
            ewcfg.weapon_id_katana, ewcfg.weapon_id_broadsword, ewcfg.weapon_id_nunchucks,
            ewcfg.weapon_id_scythe, ewcfg.weapon_id_yoyo, ewcfg.weapon_id_bass,
            ewcfg.weapon_id_umbrella, ewcfg.weapon_id_knives, ewcfg.weapon_id_molotov,
            ewcfg.weapon_id_grenades, ewcfg.weapon_id_garrote,
            "normal", "multiple-hit", "variable-damage",
            "small-game", "heavy", "defensive",
            "precision", "incendiary", "explosive",
        ]




        if poi is None:
            # catch-all response for when user isn't in a sub-zone with a help response
            response = ewcfg.generic_help_response
        elif cmd.message.channel.name in [ewcfg.channel_mines, ewcfg.channel_cv_mines, ewcfg.channel_tt_mines]:
            # mine help
            response = ewcfg.help_responses['mining']

        elif (len(poi.vendors) >= 1) and not cmd.message.channel.name in [ewcfg.channel_dojo, ewcfg.channel_greencakecafe, ewcfg.channel_glocksburycomics]:
            # food help
            response = ewcfg.help_responses['food']
        elif cmd.message.channel.name in [ewcfg.channel_greencakecafe, ewcfg.channel_glocksburycomics]:
            # zines help
            response = ewcfg.help_responses['zines']


        elif cmd.message.channel.name in ewcfg.channel_dojo and not len(cmd.tokens) > 1:
            # dojo help
            response = "For general dojo information, do **'!help dojo'**. For information about the sparring and weapon rank systems, do **'!help sparring.'**. For general information about combat, do **'!help combat'**. For information about a specific weapon, do **'!help [weapon/weapon type]'**. The different weapon types are: **normal**, **multiple-hit**, **variable-damage**, **small-game**, **heavy**, **defensive**, **precision**, **incendiary**, and **explosive**."  # For information about the sap system, do **'!help sap'**.
        
        
        elif cmd.message.channel.name in ewcfg.channel_dojo and len(cmd.tokens) > 1:
            topic = ewutils.flattenTokenListToString(cmd.tokens[1:])
            if topic in dojo_topics and topic in ewcfg.help_responses:
                response = ewcfg.help_responses[topic]
            else:
                response = 'ENDLESS WAR questions your belief in the existence of such information regarding the dojo. Try referring to the topics list again by using just !help.'
        
        elif cmd.message.channel.name in [ewcfg.channel_jr_farms, ewcfg.channel_og_farms, ewcfg.channel_ab_farms]:
            # farming help
            response = ewcfg.help_responses['farming']
        elif cmd.message.channel.name in ewcfg.channel_slimeoidlab and not len(cmd.tokens) > 1:
            # labs help
            response = "For information on slimeoids, do **'!help slimeoids'**. To learn about your current mutations, do **'!help mymutations'**"
        elif cmd.message.channel.name in ewcfg.channel_slimeoidlab and len(cmd.tokens) > 1:
            topic = ewutils.flattenTokenListToString(cmd.tokens[1:])
            if topic == 'slimeoids':
                response = ewcfg.help_responses['slimeoids']
            elif topic == 'mymutations':
                response = ewcfg.help_responses['mymutations']
                mutations = user_data.get_mutations()
                if len(mutations) == 0:
                    response += "\nWait... you don't have any!"
                else:
                    for mutation in mutations:
                        response += "\n**{}**: {}".format(mutation, ewcfg.mutation_descriptions[mutation])
            else:
                response = 'ENDLESS WAR questions your belief in the existence of such information regarding the laboratory. Try referring to the topics list again by using just !help.'
        
        
        
        elif cmd.message.channel.name in poi_static.transport_stops_ch:
            # transportation help
            response = ewcfg.help_responses['transportation']
        elif cmd.message.channel.name in ewcfg.channel_stockexchange:
            # stock exchange help
    
            response = ewcfg.help_responses['stocks']
        elif cmd.message.channel.name in ewcfg.channel_casino:
            # casino help
            response = ewcfg.help_responses['casino']
        elif cmd.message.channel.name in ewcfg.channel_sewers:
            # death help
            response = ewcfg.help_responses['death']

        elif cmd.message.channel.name in ewcfg.channel_realestateagency:
            # real estate help
            response = ewcfg.help_responses['realestate']
        elif cmd.message.channel.name in [
            ewcfg.channel_tt_pier,
            ewcfg.channel_afb_pier,
            ewcfg.channel_jr_pier,
            ewcfg.channel_cl_pier,
            ewcfg.channel_se_pier,
            ewcfg.channel_jp_pier,
            ewcfg.channel_ferry
        ]:
            # fishing help
            response = ewcfg.help_responses['fishing']
        elif user_data.poi in poi_static.outskirts:
            # hunting help
            response = ewcfg.help_responses['hunting']
        elif poi_static.id_to_poi.get(user_data.poi).is_apartment:
            response = "This is your apartment, your home away from home. You can store items here, but if you can't pay rent they will be ejected to the curb. You can store slimeoids here, too, but eviction sends them back to the real estate agency. You can only access them once you rent another apartment. Rent is charged every two IRL days, and if you can't afford the charge, you are evicted. \n\nHere's a command list. \n!depart: Leave your apartment. !goto commands work also.\n!look: look at your apartment, including all its items.\n!inspect <item>: Examine an item in the room or in your inventory.\n!stow <item>: Place an item in the room.\n!fridge/!closet/!decorate <item>: Place an item in a specific spot.\n!snag <item>: Take an item from storage.\n!unfridge/!uncloset/!undecorate <item>: Take an item from a specific spot.\n!freeze/!unfreeze <slimeoid name>: Deposit and withdraw your slimeoids. You can have 3 created at a time.\n!aptname <new name>:Change the apartment's name.\n!aptdesc <new name>: Change the apartment's base description.\n!bootall: Kick out any unwanted visitors in your apartment.\n!shelve <zine>:Store zines on your bookshelf.\n!unshelve <zine>: Take zines out of your bookshelf"
        else:
            # catch-all response for when user isn't in a sub-zone with a help response
            response = ewcfg.generic_help_response

        resp_cont.add_channel_response(cmd.message.channel, fe_utils.formatMessage(cmd.message.author, response))

    # Send the response to the player.
    await resp_cont.post()

