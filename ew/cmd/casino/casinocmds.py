import asyncio
import random
import time

from ew.backend import item as bknd_item
from ew.backend.item import EwItem
from ew.static import cfg as ewcfg
from ew.static import poi as poi_static
from ew.utils import cmd as cmd_utils
from ew.utils import core as ewutils
from ew.utils import frontend as fe_utils
from ew.utils import item as item_utils
from ew.utils import rolemgr as ewrolemgr
from ew.utils import stats as ewstats
from ew.utils.combat import EwUser
from ew.utils.district import EwDistrict
from .casinoutils import check_skat_bid
from .casinoutils import check_skat_call
from .casinoutils import checkiflegal
from .casinoutils import determine_trick_taker
from .casinoutils import evaluatehand
from .casinoutils import evaluatetrick
from .casinoutils import get_skat_play
from .casinoutils import printcard
from .casinoutils import printhand
from .casinoutils import skat_putback
from .casinoutils import payout
from .casinoutils import collect_bet

# Map containing user IDs and the last time in UTC seconds since the pachinko
# machine was used.
last_pachinkoed_times = {}

# Map containing user IDs and the last time in UTC seconds since the player
# threw their dice.
last_crapsed_times = {}

# Map containing user IDs and the last time in UTC seconds since the slot
# machine was used.
last_slotsed_times = {}

# Map containing user IDs and the last time in UTC seconds since the player
# played roulette.
last_rouletted_times = {}

# Map containing user IDs and the last time in UTC seconds since the player
# played russian roulette.
last_russianrouletted_times = {}


async def betsoul(cmd):
    user_data = EwUser(id_user=cmd.message.author.id, id_server=cmd.guild.id)
    user_inv = bknd_item.inventory(id_user=cmd.message.author.id, id_server=cmd.guild.id, item_type_filter=ewcfg.it_cosmetic)

    if cmd.mentions_count == 1:
        mention_target = cmd.mentions[0]
    else:
        mention_target = None

    item_select = None

    for item in user_inv:
        item_object = EwItem(item.get('id_item'))
        if item_object.item_props.get('id_cosmetic') == "soul":
            if not mention_target:
                item_select = item_object
                break
            elif mention_target.id == item_object.item_props.get('user_id'):
                item_select = item_object
                break

    if user_data.poi != ewcfg.poi_id_thecasino:
        response = "If you want to exchange your soul for SlimeCoin you have to be in the casino first."
    elif mention_target and item_select == None:
        response = "Sorry, you don't have that soul."
    elif item_select == None:
        response = "You don't have any souls in your inventory. !extractsoul if you want to do this properly."
    else:
        poi = poi_static.id_to_poi.get(user_data.poi)
        bknd_item.give_item(id_user="casinosouls", id_server=cmd.guild.id, id_item=item_select.id_item)
        user_data.change_slimecoin(coinsource=ewcfg.coinsource_spending, n=ewcfg.soulprice)  # current price for souls is 500 mil slimecoin
        user_data.persist()
        response = "You hand over {} for {:,} slimecoin.".format(item_select.item_props.get('cosmetic_name'), ewcfg.soulprice)
    return await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(cmd.message.author, response))


async def buysoul(cmd):
    user_data = EwUser(id_user=cmd.message.author.id, id_server=cmd.guild.id)

    casino_inv = bknd_item.inventory(id_user="casinosouls", id_server=cmd.guild.id, item_type_filter=ewcfg.it_cosmetic)

    if cmd.mentions_count == 1:
        mention_target = cmd.mentions[0]
    else:
        mention_target = None

    selected_item = None
    for item_sought in casino_inv:
        item_object = EwItem(item_sought.get('id_item'))
        selected_item = item_object
        if item_object.item_props.get('user_id') == cmd.message.author.id:
            if not mention_target:
                break
        if mention_target:
            if mention_target.id == item_object.item_props.get('user_id'):
                break

    if user_data.poi != ewcfg.poi_id_thecasino:
        response = "If you want to buy people's souls you have to be in the casino first."
    elif mention_target and selected_item == None:
        response = "That soul isn't available. Go torment someone else."
    elif selected_item == None:
        response = "Sorry, no souls on the market today."
    elif user_data.slimecoin < ewcfg.soulprice:
        response = "Tough luck. You can't afford a soul. Poor you."
    else:
        if bknd_item.give_item(id_user=cmd.message.author.id, id_server=cmd.guild.id, id_item=selected_item.id_item):
            user_data.change_slimecoin(coinsource=ewcfg.coinsource_spending, n=-ewcfg.soulprice)  # current price for souls is 500 mil slimecoin
            user_data.persist()
            response = "You buy {} off the casino. This will be fun.".format(selected_item.item_props.get('cosmetic_name'))
        else:
            response = "How do you expect to buy a soul when you cant even hold it? Dump some cosmetics weirdo."
    return await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(cmd.message.author, response))


async def pachinko(cmd):
    resp = await cmd_utils.start(cmd=cmd)
    time_now = int(time.time())

    user_data = EwUser(member=cmd.message.author)

    global last_pachinkoed_times
    last_used = last_pachinkoed_times.get(cmd.message.author.id)

    if last_used == None:
        last_used = 0

    response = ""

    # Default currency is slimecoin
    currency_used = ewcfg.currency_slimecoin

    if ewcfg.currency_slime in cmd.tokens[1:]:
        currency_used = ewcfg.currency_slime

    if last_used + 10 > time_now:
        response = "**ENOUGH**"
    elif cmd.message.channel.name not in [ewcfg.channel_casino, ewcfg.channel_casino_p]:
        # Only allowed in the slime casino.
        response = "You must go to the Casino to gamble your {}.".format(currency_used)
    else:
        last_pachinkoed_times[cmd.message.author.id] = time_now
        user_data = EwUser(member=cmd.message.author)

        value = 1
        if currency_used == ewcfg.currency_slimecoin:
            value = ewcfg.slimes_perpachinko

        elif currency_used == ewcfg.currency_slime:

            value = ewcfg.slimes_perpachinko * ewcfg.slimecoin_exchangerate
        
        # Handle all "regular bets", including slime / slimecoin
        value = await collect_bet(cmd, resp, value, user_data, currency_used)

        if not value:
            return


        user_data.persist()

        resp = await fe_utils.edit_message(cmd.client, resp, fe_utils.formatMessage(cmd.message.author, "You insert {:,} {}. Balls begin to drop!".format(value, currency_used)))
        await asyncio.sleep(3)

        ball_count = 10
        response = ""
        winballs = 0

        # Drop ball_count balls
        while ball_count > 0:
            ball_count -= 1

            roll = random.randint(1, 5)
            response += "\n*plink*"

            # Add a varying number of plinks to make it feel more random.
            plinks = random.randint(1, 4)
            while plinks > 0:
                plinks -= 1
                response += " *plink*"
            response += " PLUNK"

            # 1/5 chance to win.
            if roll == 5:
                response += " ... **ding!**"
                winballs += 1

            resp = await fe_utils.edit_message(cmd.client, resp, fe_utils.formatMessage(cmd.message.author, response))
            await asyncio.sleep(1)

        winnings = int(winballs * value / 2)

        # Significant time has passed since the user issued this command. We can't trust that their data hasn't changed.
        user_data = EwUser(member=cmd.message.author)

        if winnings > 0:
            response += "\n\n**You won {:,} {currency}!**".format(winnings, currency=currency_used)
        else:
            response += "\n\nYou lost your {}.".format(currency_used)
        
        response += payout(winnings, value, user_data, currency_used)

        # Allow the player to pachinko again now that we're done.
        last_pachinkoed_times[cmd.message.author.id] = 0

    # Send the response to the player.
    resp = await fe_utils.edit_message(cmd.client, resp, fe_utils.formatMessage(cmd.message.author, response))


async def craps(cmd):
    time_now = int(time.time())
    resp = await cmd_utils.start(cmd=cmd)

    user_data = EwUser(member=cmd.message.author)

    global last_crapsed_times
    last_used = last_crapsed_times.get(cmd.message.author.id)

    if last_used == None:
        last_used = 0

    # Default currency is slimecoin
    currency_used = ewcfg.currency_slimecoin

    if ewcfg.currency_slime in cmd.tokens[1:]:
        currency_used = ewcfg.currency_slime
    elif ewcfg.currency_soul in cmd.tokens[1:]:
        currency_used = ewcfg.currency_soul
    if last_used + 2 > time_now:
        response = "**ENOUGH**"
    elif cmd.message.channel.name not in [ewcfg.channel_casino, ewcfg.channel_casino_p]:
        # Only allowed in the slime casino.
        response = "You must go to the Casino to gamble your {}.".format(currency_used)
    else:
        last_crapsed_times[cmd.message.author.id] = time_now
        value = None
        winnings = 0

        if cmd.tokens_count > 1:
            value = ewutils.getIntToken(tokens=cmd.tokens, allow_all=True)
            if currency_used == ewcfg.currency_soul:
                value = ewcfg.soulprice

        if value != None:
            user_data = EwUser(member=cmd.message.author)
            
            # Handle all "regular bets", including slime / slimecoin
            value = await collect_bet(cmd, resp, value, user_data, currency_used)

            if not value:
                response = "You're shooed away; the dealer doesn't know how that'd even work!"
                return await fe_utils.edit_message(cmd.client, resp, fe_utils.formatMessage(cmd.message.author, response))
            if currency_used == ewcfg.currency_soul:
                if cmd.mentions_count > 0:
                    correct_soul = 0
                    user_inv = bknd_item.inventory(id_server=user_data.id_server, id_user=user_data.id_user)
                    for item_sought in user_inv:
                        if "soul" in item_sought.get("name"):
                            item = EwItem(id_item=item_sought.get('id_item'))
                            if str(cmd.mentions[0].id) == item.item_props.get("user_id"):
                                correct_soul = item.id_item
                    if correct_soul == 0:
                        response = "You don't have that soul."
                        return await fe_utils.edit_message(cmd.client, resp, fe_utils.formatMessage(cmd.message.author, response))
                    else:
                        bknd_item.give_item(id_item=correct_soul, id_user="casinosouls_wait", id_server=user_data.id_server)
                        soul_id = correct_soul
                elif user_data.has_soul == 0:
                    response = "You don't have a soul to bet."
                    return await fe_utils.edit_message(cmd.client, resp, fe_utils.formatMessage(cmd.message.author, response))
                else:
                    soul_id = item_utils.surrendersoul(receiver=user_data.id_user, giver=user_data.id_user, id_server=user_data.id_server)
                    bknd_item.give_item(id_item=soul_id, id_user="casinosouls_wait", id_server=user_data.id_server)
                    user_data = EwUser(member=cmd.message.author)


            roll1 = random.randint(1, 6)
            roll2 = random.randint(1, 6)

            response = " {} {}".format(ewcfg.emotes_dice[roll1 - 1], ewcfg.emotes_dice[roll2 - 1])

            if (roll1 + roll2) == 7:
                winnings = 5 * value

                if currency_used == ewcfg.currency_soul:
                    currency_used = ewcfg.currency_slimecoin
                    if not bknd_item.give_item(id_item=soul_id, member=cmd.message.author):
                        bknd_item.give_item(id_item=soul_id, id_user=ewcfg.poi_id_thecasino, id_server=user_data.id_server)
                        response += "\n\nThe dealer hands you the soul, but you're holding too many cosmetics and you drop it on the floor."
                response += "\n\n**You rolled a 7! It's your lucky day. You won {:,} {currency}.**".format(winnings, currency=currency_used)
            else:
                response += "\n\nYou didn't roll 7. You lost your {}.".format(currency_used)
                if currency_used == ewcfg.currency_soul:
                    bknd_item.give_item(id_item=soul_id, id_user="casinosouls", id_server=cmd.guild.id)

            response += payout(winnings, value, user_data, currency_used)


            user_data.persist()
        else:
            response = "Specify how much {} you will wager.".format(currency_used)

    # Send the response to the player.
    return await fe_utils.edit_message(cmd.client, resp, fe_utils.formatMessage(cmd.message.author, response))


async def slots(cmd):
    resp = await cmd_utils.start(cmd=cmd)
    time_now = int(time.time())

    global last_slotsed_times
    last_used = last_slotsed_times.get(cmd.message.author.id)

    user_data = EwUser(member=cmd.message.author)

    if last_used == None:
        last_used = 0

    # Default currency is slimecoin
    currency_used = ewcfg.currency_slimecoin

    if ewcfg.currency_slime in cmd.tokens[1:]:
        currency_used = ewcfg.currency_slime

    if last_used + 30 > time_now:
        # Rate limit slot machine action.
        response = "**ENOUGH**"
    elif cmd.message.channel.name  not in [ewcfg.channel_casino, ewcfg.channel_casino_p]:
        # Only allowed in the slime casino.
        response = "You must go to the Casino to gamble your {}.".format(currency_used)
    else:
        last_slotsed_times[cmd.message.author.id] = time_now

        user_data = EwUser(member=cmd.message.author)

        value = 1
        if currency_used == ewcfg.currency_slimecoin:
            value = ewcfg.slimes_perslot

        elif currency_used == ewcfg.currency_slime:

            value = ewcfg.slimes_perslot * ewcfg.slimecoin_exchangerate
        
        # Handle all "regular bets", including slime / slimecoin
        value = await collect_bet(cmd, resp, value, user_data, currency_used)


        if not value:
            return


        user_data.persist()

        # Add some suspense...
        resp = await fe_utils.edit_message(cmd.client, resp, fe_utils.formatMessage(cmd.message.author, "You insert {:,} {} and pull the handle...".format(value, currency_used)))
        await asyncio.sleep(3)

        slots = [
            ewcfg.emote_tacobell,
            ewcfg.emote_pizzahut,
            ewcfg.emote_kfc,
            ewcfg.emote_moon,
            ewcfg.emote_111,
            ewcfg.emote_copkiller,
            ewcfg.emote_rowdyfucker,
            ewcfg.emote_theeye
        ]
        slots_len = len(slots)

        # Roll those tumblers!
        spins = 3
        while spins > 0:
            resp = await fe_utils.edit_message(cmd.client, resp, fe_utils.formatMessage(cmd.message.author, "{} {} {}".format(
                slots[random.randrange(0, slots_len)],
                slots[random.randrange(0, slots_len)],
                slots[random.randrange(0, slots_len)]
            )))
            await asyncio.sleep(1)
            spins -= 1

        # Determine the final state.
        roll1 = slots[random.randrange(0, slots_len)]
        roll2 = slots[random.randrange(0, slots_len)]
        roll3 = slots[random.randrange(0, slots_len)]

        response = "{} {} {}".format(roll1, roll2, roll3)
        winnings = 0

        # Determine winnings.
        if roll1 == ewcfg.emote_tacobell and roll2 == ewcfg.emote_tacobell and roll3 == ewcfg.emote_tacobell:
            winnings = 5 * value

            response += "\n\n**¡Ándale! ¡Arriba! The machine spits out {:,} {currency}.**".format(winnings, currency=currency_used)

        elif roll1 == ewcfg.emote_pizzahut and roll2 == ewcfg.emote_pizzahut and roll3 == ewcfg.emote_pizzahut:
            winnings = 5 * value

            response += "\n\n**Oven-fired goodness! The machine spits out {:,} {currency}.**".format(winnings, currency=currency_used)

        elif roll1 == ewcfg.emote_kfc and roll2 == ewcfg.emote_kfc and roll3 == ewcfg.emote_kfc:
            winnings = 5 * value

            response += "\n\n**The Colonel's dead eyes unnerve you deeply. The machine spits out {:,} {currency}.**".format(winnings, currency=currency_used)

        elif (roll1 == ewcfg.emote_tacobell or roll1 == ewcfg.emote_kfc or roll1 == ewcfg.emote_pizzahut) and (roll2 == ewcfg.emote_tacobell or roll2 == ewcfg.emote_kfc or roll2 == ewcfg.emote_pizzahut) and (roll3 == ewcfg.emote_tacobell or roll3 == ewcfg.emote_kfc or roll3 == ewcfg.emote_pizzahut):
            winnings = value

            response += "\n\n**You dine on fast food. The machine spits out {:,} {currency}.**".format(winnings, currency=currency_used)

        elif roll1 == ewcfg.emote_moon and roll2 == ewcfg.emote_moon and roll3 == ewcfg.emote_moon:
            winnings = 5 * value

            response += "\n\n**Tonight seems like a good night for VIOLENCE. The machine spits out {:,} {currency}.**".format(winnings, currency=currency_used)

        elif roll1 == ewcfg.emote_111 and roll2 == ewcfg.emote_111 and roll3 == ewcfg.emote_111:
            winnings = 1111

            response += "\n\n**111111111111111111111111111111111111111111111111**\n\n**The machine spits out {:,} {currency}.**".format(winnings, currency=currency_used)

        elif roll1 == ewcfg.emote_copkiller and roll2 == ewcfg.emote_copkiller and roll3 == ewcfg.emote_copkiller:
            winnings = 40 * value

            response += "\n\n**How handsome!! The machine spits out {:,} {currency}.**".format(winnings, currency=currency_used)

        elif roll1 == ewcfg.emote_rowdyfucker and roll2 == ewcfg.emote_rowdyfucker and roll3 == ewcfg.emote_rowdyfucker:
            winnings = 40 * value

            response += "\n\n**So powerful!! The machine spits out {:,} {currency}.**".format(winnings, currency=currency_used)

        elif roll1 == ewcfg.emote_theeye and roll2 == ewcfg.emote_theeye and roll3 == ewcfg.emote_theeye:
            winnings = 350 * value

            response += "\n\n**JACKPOT!! The machine spews forth {:,} {currency}!**".format(winnings, currency=currency_used)

        else:
            response += "\n\n*Nothing happens...*"

        # Significant time has passed since the user issued this command. We can't trust that their data hasn't changed.
        user_data = EwUser(member=cmd.message.author)

        # add winnings
        if currency_used == ewcfg.currency_slimecoin:
            user_data.change_slimecoin(n=winnings, coinsource=ewcfg.coinsource_casino)
        else:
            levelup_response = user_data.change_slimes(n=winnings, source=ewcfg.source_casino)

            if levelup_response != "":
                response += "\n\n" + levelup_response

        user_data.persist()

        last_slotsed_times[cmd.message.author.id] = 0

    # Send the response to the player.
    return await fe_utils.edit_message(cmd.client, resp, fe_utils.formatMessage(cmd.message.author, response))


async def roulette(cmd):
    resp = await cmd_utils.start(cmd=cmd)
    time_now = int(time.time())
    bet = ""
    soul_id = None

    user_data = EwUser(member=cmd.message.author)

    returned_item_id = None
    all_bets = ["0", "00", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15",
                "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31",
                "32", "33", "34", "35", "36", "1strow", "2ndrow", "3rdrow", "1st12", "2nd12", "3rd12", "1to18",
                "19to36", "even", "odd", "pink", "purple", "green"]
    img_base = "http://165.227.192.207/img/cas/sr/"

    global last_rouletted_times
    last_used = last_rouletted_times.get(cmd.message.author.id)

    if last_used == None:
        last_used = 0

    # Default currency is slimecoin
    currency_used = ewcfg.currency_slimecoin
    if ewcfg.currency_soul in cmd.tokens[1:]:
        currency_used = ewcfg.currency_soul
    elif ewcfg.currency_slime in cmd.tokens[3:]:
        currency_used = ewcfg.currency_slime

    if last_used + 5 > time_now:
        response = "**ENOUGH**"
    elif cmd.message.channel.name  not in [ewcfg.channel_casino, ewcfg.channel_casino_p]:
        # Only allowed in the slime casino.
        response = "You must go to the #{} to gamble your {}.".format(ewcfg.channel_casino, currency_used)
    else:
        last_rouletted_times[cmd.message.author.id] = time_now
        value = None

        if cmd.tokens_count > 1:
            value = ewutils.getIntToken(tokens=cmd.tokens[:2], allow_all=True)
            bet = ewutils.flattenTokenListToString(tokens=cmd.tokens[2:3])

        if ewcfg.currency_soul in cmd.tokens[1:]:
            value = ewcfg.soulprice

        if value != None:
            user_data = EwUser(member=cmd.message.author)


            if len(bet) == 0:
                response = "You need to say what you're betting on. Options are: {}\n{}board.png".format(ewutils.formatNiceList(names=all_bets), img_base)
            elif bet not in all_bets:
                response = "The dealer didn't understand your wager. Options are: {}\n{}board.png".format(ewutils.formatNiceList(names=all_bets), img_base)
            else:
                # Handle all "regular bets", including slime / slimecoin
                value = await collect_bet(cmd, resp, value, user_data, currency_used)

                if not value:
                    response = "You're shooed away; the dealer doesn't know how that'd even work!"
                    return await fe_utils.edit_message(cmd.client, resp, fe_utils.formatMessage(cmd.message.author, response))
                
                if currency_used == ewcfg.currency_soul:
                    if cmd.mentions_count > 0:
                        correct_soul = 0
                        user_inv = bknd_item.inventory(id_server=user_data.id_server, id_user=user_data.id_user)
                        for item_sought in user_inv:
                            if "soul" in item_sought.get("name"):
                                item = EwItem(id_item=item_sought.get('id_item'))
                                if str(cmd.mentions[0].id) == item.item_props.get("user_id"):
                                    correct_soul = item.id_item
                        if correct_soul == 0:
                            response = "You don't have that soul."
                            return await fe_utils.edit_message(cmd.client, resp, fe_utils.formatMessage(cmd.message.author, response))
                        else:
                            bknd_item.give_item(id_item=correct_soul, id_user="casinosouls_wait", id_server=user_data.id_server)
                            soul_id = correct_soul
                    elif user_data.has_soul == 0:
                        response = "You don't have a soul to bet."
                        return await fe_utils.edit_message(cmd.client, resp, fe_utils.formatMessage(cmd.message.author, response))
                    else:
                        soul_id = item_utils.surrendersoul(receiver=user_data.id_user, giver=user_data.id_user, id_server=user_data.id_server)
                        bknd_item.give_item(id_item=soul_id, id_user="casinosouls_wait", id_server=user_data.id_server)
                        user_data = EwUser(member=cmd.message.author)

                user_data.persist()

                resp = await fe_utils.edit_message(cmd.client, resp, fe_utils.formatMessage(
                    cmd.message.author,
                    img_base + "sr.gif"
                ))

                await asyncio.sleep(5)

                roll = str(random.randint(1, 38))
                if roll == "37":
                    roll = "0"
                if roll == "38":
                    roll = "00"

                youstoleitback = False
                response = "The ball landed on {}!\n".format(roll)

                odd = ["1", "3", "5", "7", "9", "11", "13", "15", "17", "19", "21", "23", "25", "27", "29", "31", "33", "35"]
                even = ["2", "4", "6", "8", "10", "12", "14", "16", "18", "20", "22", "24", "26", "28", "30", "32", "34", "36"]
                firstrow = ["1", "4", "7", "10", "13", "16", "19", "22", "25", "28", "31", "34"]
                secondrow = ["2", "5", "8", "11", "14", "17", "20", "23", "26", "29", "32", "35"]
                thirdrow = ["3", "6", "9", "12", "15", "18", "21", "24", "27", "30", "33", "36"]
                firsttwelve = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]
                secondtwelve = ["13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24"]
                thirdtwelve = ["25", "26", "27", "28", "29", "30", "31", "32", "33", "34", "35", "36"]
                onetoeighteen = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18"]
                nineteentothirtysix = ["19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31", "32", "33", "34", "35", "36"]
                pink = ["2", "4", "6", "8", "10", "11", "13", "15", "17", "20", "22", "24", "26", "28", "29", "31", "33", "35"]
                purple = ["1", "3", "5", "7", "9", "12", "14", "16", "18", "19", "21", "23", "25", "27", "30", "32", "34", "36"]
                green = ["0", "00"]

                if roll == bet:
                    winnings = (value * 36)
                elif bet == "1strow" and roll in firstrow:
                    winnings = (value * 3)
                elif bet == "2ndrow" and roll in secondrow:
                    winnings = (value * 3)
                elif bet == "3rdrow" and roll in thirdrow:
                    winnings = (value * 3)
                elif bet == "1st12" and roll in firsttwelve:
                    winnings = (value * 3)
                elif bet == "2nd12" and roll in secondtwelve:
                    winnings = (value * 3)
                elif bet == "3rd12" and roll in thirdtwelve:
                    winnings = (value * 3)
                elif bet == "1to18" and roll in onetoeighteen:
                    winnings = (value * 2)
                elif bet == "19to36" and roll in nineteentothirtysix:
                    winnings = (value * 2)
                elif bet == "odd" and roll in odd:
                    winnings = (value * 2)
                elif bet == "even" and roll in even:
                    winnings = (value * 2)
                elif bet == "pink" and roll in pink:
                    winnings = (value * 2)
                elif bet == "purple" and roll in purple:
                    winnings = (value * 2)
                elif bet == "green" and roll in green:
                    winnings = (value * 18)
                else:
                    winnings = 0

                if currency_used == ewcfg.currency_soul and winnings > 0:
                    if not bknd_item.give_item(id_item=soul_id, id_user=user_data.id_user, id_server=user_data.id_server):
                        bknd_item.give_item(id_item=soul_id, id_user=ewcfg.poi_id_thecasino, id_server=user_data.id_server)
                        response += " The dealer hands you the soul, but you're holding too many cosmetics and you drop it on the floor.\n"
                    currency_used = ewcfg.currency_slimecoin
                else:
                    bknd_item.give_item(id_item=soul_id, id_user="casinosouls", id_server=user_data.id_server)
                if winnings > 0 and not youstoleitback:
                    response += " You won {:,} {currency}!".format(winnings, currency=currency_used)
                elif youstoleitback:
                    pass
                else:
                    response += " You lost your bet..."

                # Assemble image file name.
                response += "\n\n{}{}.gif".format(img_base, roll)

                # add winnings
                user_data = EwUser(member=cmd.message.author)
                response += payout(winnings, value, user_data, currency_used)
        else:
            response = "Specify how much {} you will wager.".format(currency_used)


    # Send the response to the player.
    return await fe_utils.edit_message(cmd.client, resp, fe_utils.formatMessage(cmd.message.author, response))

async def baccarat(cmd):
    resp = await cmd_utils.start(cmd=cmd)
    time_now = int(time.time())
    bet = ""
    all_bets = ["player", "dealer", "tie"]
    img_base = "http://165.227.192.207/img/cas/sb/"
    response = ""
    rank = ""
    suit = ""
    str_ranksuit = " the **{} of {}**. "

    global last_rouletted_times
    last_used = last_rouletted_times.get(cmd.message.author.id)

    if last_used == None:
        last_used = 0

    user_data = EwUser(member=cmd.message.author)

    currency_used = ewcfg.currency_slimecoin

    if ewcfg.currency_slime in cmd.tokens[3:]:
        currency_used = ewcfg.currency_slime
    elif ewcfg.currency_soul in cmd.tokens[1:]:
        currency_used = ewcfg.currency_soul
    if last_used + 2 > time_now:
        response = "**ENOUGH**"
    elif cmd.message.channel.name not in [ewcfg.channel_casino, ewcfg.channel_casino_p]:
        # Only allowed in the slime casino.
        response = "You must go to the Casino to gamble your {}.".format(currency_used)
        resp = await fe_utils.edit_message(cmd.client, resp, fe_utils.formatMessage(cmd.message.author, response))
        await asyncio.sleep(1)
    else:
        last_rouletted_times[cmd.message.author.id] = time_now
        value = None

        if cmd.tokens_count > 1:
            value = ewutils.getIntToken(tokens=cmd.tokens[:2], allow_all=True)

            if currency_used == ewcfg.currency_soul:
                value = ewcfg.soulprice
            bet = ewutils.flattenTokenListToString(tokens=cmd.tokens[2:3])

        if value != None:
            user_data = EwUser(member=cmd.message.author)


            if len(bet) == 0:
                response = "You must specify what hand you are betting on. Options are {}.".format(ewutils.formatNiceList(names=all_bets), img_base)
                resp = await fe_utils.edit_message(cmd.client, resp, fe_utils.formatMessage(cmd.message.author, response))
                await asyncio.sleep(1)

            elif bet not in all_bets:
                response = "The dealer didn't understand your wager. Options are {}.".format(ewutils.formatNiceList(names=all_bets), img_base)
                resp = await fe_utils.edit_message(cmd.client, resp, fe_utils.formatMessage(cmd.message.author, response))
                await asyncio.sleep(1)

            else:
                value = await collect_bet(cmd, resp, value, user_data, currency_used)

                if not value:
                    return
                
                if currency_used == ewcfg.currency_soul:
                    if cmd.mentions_count > 0:
                        correct_soul = 0
                        user_inv = bknd_item.inventory(id_server=user_data.id_server, id_user=user_data.id_user)
                        for item_sought in user_inv:
                            if "soul" in item_sought.get("name"):
                                item = EwItem(id_item=item_sought.get('id_item'))
                                if str(cmd.mentions[0].id) == item.item_props.get("user_id"):
                                    correct_soul = item.id_item
                        if correct_soul == 0:
                            response = "You don't have that soul."
                            return await fe_utils.edit_message(cmd.client, resp, fe_utils.formatMessage(cmd.message.author, response))
                        else:
                            soul_id = correct_soul
                    elif user_data.has_soul == 0:
                        response = "You don't have a soul to bet."
                        return await fe_utils.edit_message(cmd.client, resp, fe_utils.formatMessage(cmd.message.author, response))
                    else:
                        soul_id = item_utils.surrendersoul(receiver=user_data.id_user, giver=user_data.id_user, id_server=user_data.id_server)
                        user_data = EwUser(member=cmd.message.author)

                user_data.persist()

                response = "You bet {} {} on {}. The dealer shuffles the deck, then begins to deal.".format(str(value), currency_used, str(bet))
                if currency_used == ewcfg.currency_soul:
                    bknd_item.give_item(id_item=soul_id, id_user="casinosouls_wait", id_server=user_data.id_server)
                    response = "You bet your soul on {}. The dealer shuffles the deck, then begins to deal.".format(str(bet))

                resp_d = await cmd_utils.start(cmd=cmd)
                resp_f = await cmd_utils.start(cmd=cmd)

                resp = await fe_utils.edit_message(cmd.client, resp, fe_utils.formatMessage(cmd.message.author, response))
                await asyncio.sleep(1)

                response += "\nThe dealer deals you your first card..."

                resp = await fe_utils.edit_message(cmd.client, resp, fe_utils.formatMessage(cmd.message.author, response))
                await asyncio.sleep(3)

                winnings = 0
                end = False
                phit = False
                d = 0
                p = 0

                drawp1 = str(random.randint(1, 52))
                if drawp1 in ["1", "14", "27", "40"]:
                    p += 1
                if drawp1 in ["2", "15", "28", "41"]:
                    p += 2
                if drawp1 in ["3", "16", "29", "42"]:
                    p += 3
                if drawp1 in ["4", "17", "30", "43"]:
                    p += 4
                if drawp1 in ["5", "18", "31", "44"]:
                    p += 5
                if drawp1 in ["6", "19", "32", "45"]:
                    p += 6
                if drawp1 in ["7", "20", "33", "46"]:
                    p += 7
                if drawp1 in ["8", "21", "34", "47"]:
                    p += 8
                if drawp1 in ["9", "22", "35", "48"]:
                    p += 9
                if drawp1 in ["10", "11", "12", "13", "23", "24", "25", "26", "36", "37", "38", "39", "49", "50", "51", "52"]:
                    p += 0
                lastcard = drawp1
                if lastcard in ["1", "14", "27", "40"]:
                    rank = "Ace"
                if lastcard in ["2", "15", "28", "41"]:
                    rank = "Two"
                if lastcard in ["3", "16", "29", "42"]:
                    rank = "Three"
                if lastcard in ["4", "17", "30", "43"]:
                    rank = "Four"
                if lastcard in ["5", "18", "31", "44"]:
                    rank = "Five"
                if lastcard in ["6", "19", "32", "45"]:
                    rank = "Six"
                if lastcard in ["7", "20", "33", "46"]:
                    rank = "Seven"
                if lastcard in ["8", "21", "34", "47"]:
                    rank = "Eight"
                if lastcard in ["9", "22", "35", "48"]:
                    rank = "Nine"
                if lastcard in ["10", "23", "36", "49"]:
                    rank = "Ten"
                if lastcard in ["11", "24", "37", "50"]:
                    rank = "Jack"
                if lastcard in ["12", "25", "38", "51"]:
                    rank = "Queen"
                if lastcard in ["13", "26", "39", "52"]:
                    rank = "King"
                if lastcard in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13"]:
                    suit = "Hearts"
                if lastcard in ["14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26"]:
                    suit = "Slugs"
                if lastcard in ["27", "28", "29", "30", "31", "32", "33", "34", "35", "36", "37", "38", "39"]:
                    suit = "Hats"
                if lastcard in ["40", "41", "42", "43", "44", "45", "46", "47", "48", "49", "50", "51", "52"]:
                    suit = "Shields"

                if p > 9:
                    p -= 10
                if d > 9:
                    d -= 10

                response += str_ranksuit.format(rank, suit)
                response += img_base + lastcard + ".png"

                resp = await fe_utils.edit_message(cmd.client, resp, fe_utils.formatMessage(cmd.message.author, response))
                await asyncio.sleep(1)
                response += "\nThe dealer deals you your second card..."
                resp = await fe_utils.edit_message(cmd.client, resp, fe_utils.formatMessage(cmd.message.author, response))
                await asyncio.sleep(3)

                while True:
                    drawp2 = str(random.randint(1, 52))
                    if drawp2 != drawp1:
                        break
                if drawp2 in ["1", "14", "27", "40"]:
                    p += 1
                if drawp2 in ["2", "15", "28", "41"]:
                    p += 2
                if drawp2 in ["3", "16", "29", "42"]:
                    p += 3
                if drawp2 in ["4", "17", "30", "43"]:
                    p += 4
                if drawp2 in ["5", "18", "31", "44"]:
                    p += 5
                if drawp2 in ["6", "19", "32", "45"]:
                    p += 6
                if drawp2 in ["7", "20", "33", "46"]:
                    p += 7
                if drawp2 in ["8", "21", "34", "47"]:
                    p += 8
                if drawp2 in ["9", "22", "35", "48"]:
                    p += 9
                if drawp2 in ["10", "11", "12", "13", "23", "24", "25", "26", "36", "37", "38", "39", "49", "50", "51", "52"]:
                    p += 0
                lastcard = drawp2
                if lastcard in ["1", "14", "27", "40"]:
                    rank = "Ace"
                if lastcard in ["2", "15", "28", "41"]:
                    rank = "Two"
                if lastcard in ["3", "16", "29", "42"]:
                    rank = "Three"
                if lastcard in ["4", "17", "30", "43"]:
                    rank = "Four"
                if lastcard in ["5", "18", "31", "44"]:
                    rank = "Five"
                if lastcard in ["6", "19", "32", "45"]:
                    rank = "Six"
                if lastcard in ["7", "20", "33", "46"]:
                    rank = "Seven"
                if lastcard in ["8", "21", "34", "47"]:
                    rank = "Eight"
                if lastcard in ["9", "22", "35", "48"]:
                    rank = "Nine"
                if lastcard in ["10", "23", "36", "49"]:
                    rank = "Ten"
                if lastcard in ["11", "24", "37", "50"]:
                    rank = "Jack"
                if lastcard in ["12", "25", "38", "51"]:
                    rank = "Queen"
                if lastcard in ["13", "26", "39", "52"]:
                    rank = "King"
                if lastcard in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13"]:
                    suit = "Hearts"
                if lastcard in ["14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26"]:
                    suit = "Slugs"
                if lastcard in ["27", "28", "29", "30", "31", "32", "33", "34", "35", "36", "37", "38", "39"]:
                    suit = "Hats"
                if lastcard in ["40", "41", "42", "43", "44", "45", "46", "47", "48", "49", "50", "51", "52"]:
                    suit = "Shields"

                if p > 9:
                    p -= 10
                if d > 9:
                    d -= 10

                response += str_ranksuit.format(rank, suit)
                response += img_base + lastcard + ".png"

                resp = await fe_utils.edit_message(cmd.client, resp, fe_utils.formatMessage(cmd.message.author, response))
                await asyncio.sleep(1)

                responsesave = response

                response = "\nThe dealer deals the house its first card..."

                resp_d = await fe_utils.edit_message(cmd.client, resp_d, fe_utils.formatMessage(cmd.message.author, response))
                await asyncio.sleep(3)

                while True:
                    drawd1 = str(random.randint(1, 52))
                    if drawd1 != drawp1 and drawd1 != drawp2:
                        break
                if drawd1 in ["1", "14", "27", "40"]:
                    d += 1
                if drawd1 in ["2", "15", "28", "41"]:
                    d += 2
                if drawd1 in ["3", "16", "29", "42"]:
                    d += 3
                if drawd1 in ["4", "17", "30", "43"]:
                    d += 4
                if drawd1 in ["5", "18", "31", "44"]:
                    d += 5
                if drawd1 in ["6", "19", "32", "45"]:
                    d += 6
                if drawd1 in ["7", "20", "33", "46"]:
                    d += 7
                if drawd1 in ["8", "21", "34", "47"]:
                    d += 8
                if drawd1 in ["9", "22", "35", "48"]:
                    d += 9
                if drawd1 in ["10", "11", "12", "13", "23", "24", "25", "26", "36", "37", "38", "39", "49", "50", "51", "52"]:
                    d += 0
                lastcard = drawd1
                if lastcard in ["1", "14", "27", "40"]:
                    rank = "Ace"
                if lastcard in ["2", "15", "28", "41"]:
                    rank = "Two"
                if lastcard in ["3", "16", "29", "42"]:
                    rank = "Three"
                if lastcard in ["4", "17", "30", "43"]:
                    rank = "Four"
                if lastcard in ["5", "18", "31", "44"]:
                    rank = "Five"
                if lastcard in ["6", "19", "32", "45"]:
                    rank = "Six"
                if lastcard in ["7", "20", "33", "46"]:
                    rank = "Seven"
                if lastcard in ["8", "21", "34", "47"]:
                    rank = "Eight"
                if lastcard in ["9", "22", "35", "48"]:
                    rank = "Nine"
                if lastcard in ["10", "23", "36", "49"]:
                    rank = "Ten"
                if lastcard in ["11", "24", "37", "50"]:
                    rank = "Jack"
                if lastcard in ["12", "25", "38", "51"]:
                    rank = "Queen"
                if lastcard in ["13", "26", "39", "52"]:
                    rank = "King"
                if lastcard in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13"]:
                    suit = "Hearts"
                if lastcard in ["14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26"]:
                    suit = "Slugs"
                if lastcard in ["27", "28", "29", "30", "31", "32", "33", "34", "35", "36", "37", "38", "39"]:
                    suit = "Hats"
                if lastcard in ["40", "41", "42", "43", "44", "45", "46", "47", "48", "49", "50", "51", "52"]:
                    suit = "Shields"

                if p > 9:
                    p -= 10
                if d > 9:
                    d -= 10

                response += str_ranksuit.format(rank, suit)
                response += img_base + lastcard + ".png"

                resp_d = await fe_utils.edit_message(cmd.client, resp_d, fe_utils.formatMessage(cmd.message.author, response))
                await asyncio.sleep(1)
                response += "\nThe dealer deals the house its second card..."
                resp_d = await fe_utils.edit_message(cmd.client, resp_d, fe_utils.formatMessage(cmd.message.author, response))
                await asyncio.sleep(3)

                while True:
                    drawd2 = str(random.randint(1, 52))
                    if drawd2 != drawp1 and drawd2 != drawp2 and drawd2 != drawd1:
                        break
                if drawd2 in ["1", "14", "27", "40"]:
                    d += 1
                if drawd2 in ["2", "15", "28", "41"]:
                    d += 2
                if drawd2 in ["3", "16", "29", "42"]:
                    d += 3
                if drawd2 in ["4", "17", "30", "43"]:
                    d += 4
                if drawd2 in ["5", "18", "31", "44"]:
                    d += 5
                if drawd2 in ["6", "19", "32", "45"]:
                    d += 6
                if drawd2 in ["7", "20", "33", "46"]:
                    d += 7
                if drawd2 in ["8", "21", "34", "47"]:
                    d += 8
                if drawd2 in ["9", "22", "35", "48"]:
                    d += 9
                if drawd2 in ["10", "11", "12", "13", "23", "24", "25", "26", "36", "37", "38", "39", "49", "50", "51", "52"]:
                    d += 0
                lastcard = drawd2
                if lastcard in ["1", "14", "27", "40"]:
                    rank = "Ace"
                if lastcard in ["2", "15", "28", "41"]:
                    rank = "Two"
                if lastcard in ["3", "16", "29", "42"]:
                    rank = "Three"
                if lastcard in ["4", "17", "30", "43"]:
                    rank = "Four"
                if lastcard in ["5", "18", "31", "44"]:
                    rank = "Five"
                if lastcard in ["6", "19", "32", "45"]:
                    rank = "Six"
                if lastcard in ["7", "20", "33", "46"]:
                    rank = "Seven"
                if lastcard in ["8", "21", "34", "47"]:
                    rank = "Eight"
                if lastcard in ["9", "22", "35", "48"]:
                    rank = "Nine"
                if lastcard in ["10", "23", "36", "49"]:
                    rank = "Ten"
                if lastcard in ["11", "24", "37", "50"]:
                    rank = "Jack"
                if lastcard in ["12", "25", "38", "51"]:
                    rank = "Queen"
                if lastcard in ["13", "26", "39", "52"]:
                    rank = "King"
                if lastcard in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13"]:
                    suit = "Hearts"
                if lastcard in ["14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26"]:
                    suit = "Slugs"
                if lastcard in ["27", "28", "29", "30", "31", "32", "33", "34", "35", "36", "37", "38", "39"]:
                    suit = "Hats"
                if lastcard in ["40", "41", "42", "43", "44", "45", "46", "47", "48", "49", "50", "51", "52"]:
                    suit = "Shields"

                if p > 9:
                    p -= 10
                if d > 9:
                    d -= 10

                response += str_ranksuit.format(rank, suit)
                response += img_base + lastcard + ".png"

                resp_d = await fe_utils.edit_message(cmd.client, resp_d, fe_utils.formatMessage(cmd.message.author, response))
                await asyncio.sleep(1)
                responsesave_d = response

                if d in [8, 9] or p in [8, 9]:
                    end = True

                drawp3 = ""
                if (p <= 5) and (end != True):

                    response = responsesave
                    response += "\nThe dealer deals you another card..."

                    resp = await fe_utils.edit_message(cmd.client, resp, fe_utils.formatMessage(cmd.message.author, response))
                    await asyncio.sleep(3)

                    phit = True
                    while True:
                        drawp3 = str(random.randint(1, 52))
                        if drawp3 != drawp1 and drawp3 != drawp2 and drawp3 != drawd1 and drawp3 != drawd2:
                            break
                    if drawp3 in ["1", "14", "27", "40"]:
                        p += 1
                    if drawp3 in ["2", "15", "28", "41"]:
                        p += 2
                    if drawp3 in ["3", "16", "29", "42"]:
                        p += 3
                    if drawp3 in ["4", "17", "30", "43"]:
                        p += 4
                    if drawp3 in ["5", "18", "31", "44"]:
                        p += 5
                    if drawp3 in ["6", "19", "32", "45"]:
                        p += 6
                    if drawp3 in ["7", "20", "33", "46"]:
                        p += 7
                    if drawp3 in ["8", "21", "34", "47"]:
                        p += 8
                    if drawp3 in ["9", "22", "35", "48"]:
                        p += 9
                    if drawp3 in ["10", "11", "12", "13", "23", "24", "25", "26", "36", "37", "38", "39", "49", "50", "51", "52"]:
                        p += 0
                    lastcard = drawp3
                    if lastcard in ["1", "14", "27", "40"]:
                        rank = "Ace"
                    if lastcard in ["2", "15", "28", "41"]:
                        rank = "Two"
                    if lastcard in ["3", "16", "29", "42"]:
                        rank = "Three"
                    if lastcard in ["4", "17", "30", "43"]:
                        rank = "Four"
                    if lastcard in ["5", "18", "31", "44"]:
                        rank = "Five"
                    if lastcard in ["6", "19", "32", "45"]:
                        rank = "Six"
                    if lastcard in ["7", "20", "33", "46"]:
                        rank = "Seven"
                    if lastcard in ["8", "21", "34", "47"]:
                        rank = "Eight"
                    if lastcard in ["9", "22", "35", "48"]:
                        rank = "Nine"
                    if lastcard in ["10", "23", "36", "49"]:
                        rank = "Ten"
                    if lastcard in ["11", "24", "37", "50"]:
                        rank = "Jack"
                    if lastcard in ["12", "25", "38", "51"]:
                        rank = "Queen"
                    if lastcard in ["13", "26", "39", "52"]:
                        rank = "King"
                    if lastcard in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13"]:
                        suit = "Hearts"
                    if lastcard in ["14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26"]:
                        suit = "Slugs"
                    if lastcard in ["27", "28", "29", "30", "31", "32", "33", "34", "35", "36", "37", "38", "39"]:
                        suit = "Hats"
                    if lastcard in ["40", "41", "42", "43", "44", "45", "46", "47", "48", "49", "50", "51", "52"]:
                        suit = "Shields"

                    if p > 9:
                        p -= 10
                    if d > 9:
                        d -= 10

                    response += str_ranksuit.format(rank, suit)
                    response += img_base + lastcard + ".png"

                    resp = await fe_utils.edit_message(cmd.client, resp, fe_utils.formatMessage(cmd.message.author, response))
                    await asyncio.sleep(1)

                if ((phit != True and d <= 5) or (phit == True and (
                        (d <= 2) or (d == 3 and drawp3 not in ["8", "21", "34", "47"]) or (d == 4 and drawp3 in ["2", "15", "28", "41", "3", "16", "29", "42", "4", "17", "30", "43", "5", "18", "31", "44", "6", "19", "32", "45", "7", "20", "33", "46"]) or (d == 5 and drawp3 in ["4", "17", "30", "43", "5", "18", "31", "44", "6", "19", "32", "45", "7", "20", "33", "46"]) or (
                        d == 6 and drawp3 in ["6", "19", "32", "45", "7", "20", "33", "46"])))) and (d != 7) and (end != True):

                    response = responsesave_d
                    response += "\nThe dealer deals the house another card..."
                    resp_d = await fe_utils.edit_message(cmd.client, resp_d, fe_utils.formatMessage(cmd.message.author, response))
                    await asyncio.sleep(3)

                    while True:
                        drawd3 = str(random.randint(1, 52))
                        if drawd3 != drawp1 and drawd3 != drawp2 and drawd3 != drawd1 and drawd3 != drawd2 and drawd3 != drawp3:
                            break
                    if drawd3 in ["1", "14", "27", "40"]:
                        d += 1
                    if drawd3 in ["2", "15", "28", "41"]:
                        d += 2
                    if drawd3 in ["3", "16", "29", "42"]:
                        d += 3
                    if drawd3 in ["4", "17", "30", "43"]:
                        d += 4
                    if drawd3 in ["5", "18", "31", "44"]:
                        d += 5
                    if drawd3 in ["6", "19", "32", "45"]:
                        d += 6
                    if drawd3 in ["7", "20", "33", "46"]:
                        d += 7
                    if drawd3 in ["8", "21", "34", "47"]:
                        d += 8
                    if drawd3 in ["9", "22", "35", "48"]:
                        d += 9
                    if drawd3 in ["10", "11", "12", "13", "23", "24", "25", "26", "36", "37", "38", "39", "49", "50", "51", "52"]:
                        d += 0
                    lastcard = drawd3
                    if lastcard in ["1", "14", "27", "40"]:
                        rank = "Ace"
                    if lastcard in ["2", "15", "28", "41"]:
                        rank = "Two"
                    if lastcard in ["3", "16", "29", "42"]:
                        rank = "Three"
                    if lastcard in ["4", "17", "30", "43"]:
                        rank = "Four"
                    if lastcard in ["5", "18", "31", "44"]:
                        rank = "Five"
                    if lastcard in ["6", "19", "32", "45"]:
                        rank = "Six"
                    if lastcard in ["7", "20", "33", "46"]:
                        rank = "Seven"
                    if lastcard in ["8", "21", "34", "47"]:
                        rank = "Eight"
                    if lastcard in ["9", "22", "35", "48"]:
                        rank = "Nine"
                    if lastcard in ["10", "23", "36", "49"]:
                        rank = "Ten"
                    if lastcard in ["11", "24", "37", "50"]:
                        rank = "Jack"
                    if lastcard in ["12", "25", "38", "51"]:
                        rank = "Queen"
                    if lastcard in ["13", "26", "39", "52"]:
                        rank = "King"
                    if lastcard in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13"]:
                        suit = "Hearts"
                    if lastcard in ["14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26"]:
                        suit = "Slugs"
                    if lastcard in ["27", "28", "29", "30", "31", "32", "33", "34", "35", "36", "37", "38", "39"]:
                        suit = "Hats"
                    if lastcard in ["40", "41", "42", "43", "44", "45", "46", "47", "48", "49", "50", "51", "52"]:
                        suit = "Shields"

                    if p > 9:
                        p -= 10
                    if d > 9:
                        d -= 10

                    response += str_ranksuit.format(rank, suit)
                    response += img_base + lastcard + ".png"

                    resp_d = await fe_utils.edit_message(cmd.client, resp_d, fe_utils.formatMessage(cmd.message.author, response))
                    await asyncio.sleep(2)

                if p > 9:
                    p -= 10
                if d > 9:
                    d -= 10

                if p > d:
                    response = "\n\nPlayer hand beats the dealer hand {} to {}.".format(str(p), str(d))
                    result = "player"
                    odds = 2
                elif d > p:
                    response = "\n\nDealer hand beats the player hand {} to {}.".format(str(d), str(p))
                    result = "dealer"
                    odds = 2
                else:  # p == d (peed lol)
                    response = "\n\nPlayer hand and dealer hand tied at {}.".format(str(p))
                    result = "tie"
                    odds = 8

                if bet == result:
                    winnings = (odds * value)

                    if currency_used == ewcfg.currency_soul:
                        if not bknd_item.give_item(id_item=soul_id, id_user=cmd.message.author.id, id_server=user_data.id_server):
                            bknd_item.give_item(id_item=soul_id, id_user=ewcfg.poi_id_thecasino, id_server=user_data.id_server)
                            response += "\n\nThe dealer hands you the soul, but you're holding too many cosmetics and you drop it on the floor."
                        currency_used = ewcfg.currency_slimecoin

                    response += "\n\n**You won {:,} {currency}!**".format(winnings, currency=currency_used)
                else:
                    response += "\n\n*You lost your bet.*"
                    if currency_used == ewcfg.currency_soul:
                        bknd_item.give_item(id_item=soul_id, id_user="casinosouls", id_server=user_data.id_server)

                # add winnings
                user_data = EwUser(member=cmd.message.author)
                response += payout(winnings, value, user_data, currency_used)

                user_data.persist()
                resp_f = await fe_utils.edit_message(cmd.client, resp_f, fe_utils.formatMessage(cmd.message.author, response))

        else:
            response = "Specify how much {} you will wager.".format(currency_used)
            return await fe_utils.edit_message(cmd.client, resp, fe_utils.formatMessage(cmd.message.author, response))


async def skat(cmd):
    time_now = int(time.time())
    multiplier = 1
    img_base = "http://165.227.192.207/img/cas/sb/"
    response = ""
    rank = ""
    suit = ""
    str_ranksuit = " the **{} of {}**. "

    join_timeout = 60
    bidding_timeout = 120
    hand_timeout = 120
    declare_timeout = 120
    play_timeout = 120

    try:
        if cmd.tokens_count > 3:
            multiplier = ewutils.getIntToken(tokens=cmd.tokens, allow_all=True)
    except:
        multiplier = 1

    if cmd.message.channel.name  not in [ewcfg.channel_casino, ewcfg.channel_casino_p]:
        # Only at the casino
        response = "You can only play slime skat at the casino."
        return await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(cmd.message.author, response))

    user_data = EwUser(member=cmd.message.author)
    if cmd.mentions_count != 2:
        # Must mention exactly 2 players
        response = "Mention the two players you want to invite."
        return await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(cmd.message.author, response))

    author = cmd.message.author
    member = cmd.mentions[0]
    member2 = cmd.mentions[1]

    members = [author, member, member2]

    # global last_russianrouletted_times
    # last_used_author = last_russianrouletted_times.get(author.id)
    # last_used_member = last_russianrouletted_times.get(member.id)

    # if last_used_author == None:
    #	last_used_author = 0
    # if last_used_member == None:
    #	last_used_member = 0

    # if last_used_author + ewcfg.cd_rr > time_now or last_used_member + ewcfg.cd_rr > time_now:
    #	response = "**ENOUGH**"
    #	return await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(cmd.message.author, response))

    if author.id == member.id or author.id == member2.id:
        response = "This is not solitaire, you dumbass."
        return await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(author, response))

    challenger = EwUser(member=author)
    challengee = EwUser(member=member)
    challengee2 = EwUser(member=member2)
    maxgame = multiplier * max(2 * 15 * 12, 2 * 8 * 24)

    gellphone_active_challengee1 = False
    if challengee.has_gellphone():
        gellphone_active_challengee1 = True

    gellphone_active_challengee2 = False
    if challengee2.has_gellphone():
        gellphone_active_challengee2 = True

    # Players have been challenged
    if ewutils.active_target_map.get(challenger.id_user) != None and ewutils.active_target_map.get(challenger.id_user) != "":
        response = "You are already in the middle of a challenge."
        return await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(author, response))

    if ewutils.active_target_map.get(challengee.id_user) != None and ewutils.active_target_map.get(challengee.id_user) != "":
        response = "{} is already in the middle of a challenge.".format(member.display_name).replace("@", "\{at\}")
        return await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(author, response))

    if ewutils.active_target_map.get(challengee2.id_user) != None and ewutils.active_target_map.get(challengee2.id_user) != "":
        response = "{} is already in the middle of a challenge.".format(member2.display_name).replace("@", "\{at\}")
        return await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(author, response))

    if not (challengee.poi == ewcfg.poi_id_greenlightdistrict or gellphone_active_challengee1) or not (challengee2.poi == ewcfg.poi_id_greenlightdistrict or gellphone_active_challengee2):
        # Challangees must be in the casino
        response = "All players must be in the casino."
        return await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(author, response))

    # Players must have sufficient slimecoin for the game
    if challenger.slimecoin < maxgame:
        response = "You don't have enough slimecoin to cover your potential loss. Try lowering the multiplier."
        return await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(author, response))
    if challengee.slimecoin < maxgame:
        response = "{} doesn't have enough slimecoin to cover their potential loss. Try lowering the multiplier.".format(member.display_name).replace("@", "\{at\}")
        return await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(author, response))
    if challengee2.slimecoin < maxgame:
        response = "{} doesn't have enough slimecoin to cover their potential loss. Try lowering the multiplier.".format(member2.display_name).replace("@", "\{at\}")
        return await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(author, response))

    for m in members:
        ewuser = EwUser(member=m)
        ewutils.active_target_map[ewuser.id_user] = ""

    response = "You have been invited by {} to a game of slime skat. Do you {} or {}?".format(author.display_name, ewcfg.cmd_slimeskat_join, ewcfg.cmd_slimeskat_decline).replace("@", "\{at\}")
    await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(member, response))

    # Wait for an answer
    accepted = False
    try:
        msg = await cmd.client.wait_for('message', timeout=join_timeout, check=lambda message: member == cmd.message.author and
                                                                                               message.content.lower() in [ewcfg.cmd_slimeskat_join, ewcfg.cmd_slimeskat_decline])

        if msg != None:
            if msg.content == ewcfg.cmd_slimeskat_join:
                accepted = True
    except:
        accepted = False

    if accepted == False:
        response = "{}'s brain was too small to understand slime skat.".format(member.display_name).replace("@", "\{at\}")
        await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(author, response))
        for m in members:
            ewuser = EwUser(member=m)
            ewutils.active_target_map[ewuser.id_user] = ""

        return

    response = "You have been invited by {} to a round of slime skat. Do you {} or {}?".format(author.display_name, ewcfg.cmd_slimeskat_join, ewcfg.cmd_slimeskat_decline).replace("@", "\{at\}")
    await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(member2, response))

    # Wait for an answer
    accepted = False
    try:
        msg = await cmd.client.wait_for('message', timeout=join_timeout, check=lambda message: member2 == cmd.message.author and
                                                                                               message.content.lower() in [ewcfg.cmd_slimeskat_join, ewcfg.cmd_slimeskat_decline])

        if msg != None:
            if msg.content == ewcfg.cmd_slimeskat_join:
                accepted = True
    except:
        accepted = False

    if accepted == False:
        response = "{}'s brain was too small to understand slime skat.".format(member2.display_name).replace("@", "\{at\}")
        await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(author, response))
        for m in members:
            ewuser = EwUser(member=m)
            ewutils.active_target_map[ewuser.id_user] = ""

        return

    round_num = 0
    while True:
        round_num += 1
        # Players must have sufficient slimecoin for the game
        for i in range(3):
            player = EwUser(member=members[i])

            if player.slimecoin < maxgame:
                response = "You don't have enough slimecoin to cover your potential loss. Try lowering the multiplier."
                for m in members:
                    ewuser = EwUser(member=m)
                    ewutils.active_target_map[ewuser.id_user] = ""
                return await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(members[i], response))

        front_idx = (round_num + 0) % 3
        mid_idx = (round_num + 1) % 3
        back_idx = (round_num + 2) % 3

        # shuffle deck and deal cards
        deck = [1, 7, 8, 9, 10, 11, 12, 13,  # hearts
                14, 20, 21, 22, 23, 24, 25, 26,  # slugs
                27, 33, 34, 35, 36, 37, 38, 39,  # hats
                40, 46, 47, 48, 49, 50, 51, 52]  # shields

        hands = []
        handles_table = []
        for mem in members:
            hand = []
            handles = []
            for card in range(10):
                hand.append(str(deck.pop(random.randrange(len(deck)))))
            hands.append(hand)
            hand3parts = printhand(hand)
            for part in hand3parts:
                handle = await fe_utils.send_message(cmd.client, mem, fe_utils.formatMessage(mem, part))
                handles.append(handle)
            handles_table.append(handles)

        skat = deck  # the remaining two cards are called the skat
        skat[0] = str(deck[0])
        skat[1] = str(deck[1])

        # bidding
        passed = False
        maxbid = 17
        active_idx = 0
        # round 1
        while not passed:
            bid = -1

            response = "Please {} an amount greater than {} or {}".format(ewcfg.cmd_slimeskat_bid, maxbid, ewcfg.cmd_slimeskat_pass)
            await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(members[mid_idx], response))
            try:
                msg = await cmd.client.wait_for('message', timeout=bidding_timeout, check=lambda message: members[mid_idx] == cmd.message.author and
                                                                                                          message.content.lower().startswith(ewcfg.cmd_slimeskat_bid) or
                                                                                                          message.content.lower().startswith(ewcfg.cmd_slimeskat_pass) or
                                                                                                          message.content.lower().startswith(ewcfg.cmd_slimeskat_call))

                if msg != None:
                    bid = check_skat_bid(msg)
            except:
                bid = -1
            if bid > maxbid:
                maxbid = bid
                response = "You are bidding {} points.".format(bid)
            else:
                passed = True
                active_idx = front_idx
                response = "You are passing."
            await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(members[mid_idx], response))
            if passed == True:
                break

            called = -1
            response = "Please {} or {}".format(ewcfg.cmd_slimeskat_call, ewcfg.cmd_slimeskat_pass)
            await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(members[front_idx], response))
            try:
                msg = await cmd.client.wait_for('message', timeout=bidding_timeout, check=lambda message: members[front_idx] == cmd.message.author and
                                                                                                          message.content.lower().startswith(ewcfg.cmd_slimeskat_bid) or
                                                                                                          message.content.lower().startswith(ewcfg.cmd_slimeskat_pass) or
                                                                                                          message.content.lower().startswith(ewcfg.cmd_slimeskat_call))

                if msg != None:
                    called = check_skat_call(msg)
            except:
                called = -1

            if called == 1:
                response = "You are calling."
            else:
                response = "You are passing."
                passed = True
                active_idx = mid_idx
            await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(members[front_idx], response))

        # round 2
        passed = False
        while not passed:
            bid = -1

            response = "Please {} an amount greater than {} or {}".format(ewcfg.cmd_slimeskat_bid, maxbid, ewcfg.cmd_slimeskat_pass)
            await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(members[back_idx], response))
            try:
                msg = await cmd.client.wait_for('message', timeout=bidding_timeout, check=lambda message: members[back_idx] == cmd.message.author and
                                                                                                          message.content.lower().startswith(ewcfg.cmd_slimeskat_bid) or
                                                                                                          message.content.lower().startswith(ewcfg.cmd_slimeskat_pass) or
                                                                                                          message.content.lower().startswith(ewcfg.cmd_slimeskat_call))

                if msg != None:
                    bid = check_skat_bid(msg)
            except:
                bid = -1
            if bid > maxbid:
                maxbid = bid
                response = "You are bidding {} points.".format(bid)
            else:
                passed = True
                response = "You are passing."
            await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(members[back_idx], response))
            if passed == True:
                break

            called = -1
            response = "Please {} or {}".format(ewcfg.cmd_slimeskat_call, ewcfg.cmd_slimeskat_pass)
            await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(members[active_idx], response))
            try:
                msg = await cmd.client.wait_for('message', timeout=bidding_timeout, check=lambda message: members[mid_idx] == cmd.message.author and
                                                                                                          message.content.lower().startswith(ewcfg.cmd_slimeskat_bid) or
                                                                                                          message.content.lower().startswith(ewcfg.cmd_slimeskat_pass) or
                                                                                                          message.content.lower().startswith(ewcfg.cmd_slimeskat_call))

                if msg != None:
                    called = check_skat_call(msg)
            except:
                called = -1

            if called == 1:
                response = "You are calling."
            else:
                response = "You are passing."
                passed = True
            await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(members[active_idx], response))
            if passed == True:
                active_idx = back_idx

        # potential round 3
        if maxbid < 18:
            bid = -1

            response = "Please {} an amount greater than {} or {}".format(ewcfg.cmd_slimeskat_bid, maxbid, ewcfg.cmd_slimeskat_pass)
            await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(members[active_idx], response))
            try:
                msg = await cmd.client.wait_for('message', timeout=bidding_timeout, check=lambda message: members[active_idx] == cmd.message.author and
                                                                                                          message.content.lower().startswith(ewcfg.cmd_slimeskat_bid) or
                                                                                                          message.content.lower().startswith(ewcfg.cmd_slimeskat_pass) or
                                                                                                          message.content.lower().startswith(ewcfg.cmd_slimeskat_call))

                if msg != None:
                    bid = check_skat_bid(msg)
            except:
                bid = -1
            if bid > maxbid:
                maxbid = bid
                response = "You are bidding {} points.".format(bid)
            else:
                passed = True
                response = "You are passing."
            await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(members[active_idx], response))

        if maxbid >= 18:

            # hand or no
            active_hand = hands[active_idx]
            game_multiplier = 1
            response = "Please {} the skat or play {}".format(ewcfg.cmd_slimeskat_take, ewcfg.cmd_slimeskat_hand)
            hand = -1
            await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(members[active_idx], response))
            try:
                msg = await cmd.client.wait_for('message', timeout=hand_timeout, check=lambda message: members[active_idx] == cmd.message.author and
                                                                                                       message.content.lower().startswith(ewcfg.cmd_slimeskat_hand) or
                                                                                                       message.content.lower().startswith(ewcfg.cmd_slimeskat_take))

                if msg != None:
                    content = msg.content.lower()
                    if content.startswith(ewcfg.cmd_slimeskat_take):
                        hand = 0
                    else:
                        hand = 1
            except:
                hand = -1

            if hand == 1:
                response = "You are playing hand."
                game_multiplier += 1
                await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(members[active_idx], response))

            else:
                active_hand.extend(skat)
                random.shuffle(active_hand)
                skat = []

                hand3parts = printhand(active_hand)
                handles = handles_table[active_idx]
                for i in range(len(hand3parts)):
                    handles[i] = await fe_utils.edit_message(cmd.client, handles[i], fe_utils.formatMessage(members[active_idx], hand3parts[i]))
                response = "You take the skat. Please {} two cards from your hand to put back into the skat.".format(ewcfg.cmd_slimeskat_choose)
                await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(members[active_idx], response))
                while len(active_hand) > 10:
                    putback = False
                    try:
                        msg = await cmd.client.wait_for('message', timeout=hand_timeout, check=lambda message: members[active_idx] == cmd.message.author and
                                                                                                               message.content.lower().startswith(ewcfg.cmd_slimeskat_choose))
                        if msg != None:
                            putback = skat_putback(msg, active_hand, skat)
                    except:
                        putback = False

                    if not putback:
                        skat.append(active_hand.pop(0))

                    hand3parts = printhand(active_hand)
                    handles = handles_table[active_idx]
                    for i in range(len(hand3parts)):
                        handles[i] = await fe_utils.edit_message(cmd.client, handles[i], fe_utils.formatMessage(members[active_idx], hand3parts[i]))

            # declare game
            gametype = "grand"
            basevalue = 24
            trumps = ["24", "50", "11", "37"]
            response = "Please declare what kind of game you are going to play (options are {}, {}, {}, {}, {} and {})".format(ewcfg.cmd_slimeskat_slugs, ewcfg.cmd_slimeskat_shields, ewcfg.cmd_slimeskat_hearts, ewcfg.cmd_slimeskat_hats, ewcfg.cmd_slimeskat_grand, ewcfg.cmd_slimeskat_null)
            await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(members[active_idx], response))

            try:
                msg = await cmd.client.wait_for('message', timeout=declare_timeout, check=lambda message: members[active_idx] == cmd.message.author and
                                                                                                          message.content.lower().startswith(ewcfg.cmd_slimeskat_hearts) or
                                                                                                          message.content.lower().startswith(ewcfg.cmd_slimeskat_hats) or
                                                                                                          message.content.lower().startswith(ewcfg.cmd_slimeskat_slugs) or
                                                                                                          message.content.lower().startswith(ewcfg.cmd_slimeskat_shields) or
                                                                                                          message.content.lower().startswith(ewcfg.cmd_slimeskat_grand) or
                                                                                                          message.content.lower().startswith(ewcfg.cmd_slimeskat_null))

                if msg != None:
                    content = msg.content.lower()
                    if content.startswith(ewcfg.cmd_slimeskat_hearts):
                        gametype = "suit"
                        trumps = ["24", "50", "11", "37", "1", "10", "13", "12", "9", "8", "7"]
                        basevalue = 10
                    elif content.startswith(ewcfg.cmd_slimeskat_slugs):
                        gametype = "suit"
                        trumps = ["24", "50", "11", "37", "14", "23", "26", "25", "22", "21", "20"]
                        basevalue = 12
                    elif content.startswith(ewcfg.cmd_slimeskat_hats):
                        gametype = "suit"
                        trumps = ["24", "50", "11", "37", "27", "36", "39", "38", "35", "34", "33"]
                        basevalue = 9
                    elif content.startswith(ewcfg.cmd_slimeskat_shields):
                        gametype = "suit"
                        trumps = ["24", "50", "11", "37", "40", "49", "52", "51", "48", "47", "46"]
                        basevalue = 11
                    elif content.startswith(ewcfg.cmd_slimeskat_grand):
                        gametype = "grand"
                        trumps = ["24", "50", "11", "37"]
                        basevalue = 24
                    elif content.startswith(ewcfg.cmd_slimeskat_null):
                        gametype = "null"
                        trumps = []
                        basevalue = 23

            except:
                gametype = "grand"
                trumps = ["24", "50", "11", "37"]
                basevalue = 24
            if gametype == "suit" or gametype == "grand":
                game_multiplier += evaluatehand(active_hand, skat, trumps)
            elif gametype == "null":
                if game_multiplier == 2:
                    basevalue = 35
                    game_multiplier = 1
            response = "**Playing a {} type game with a base value of {}.**".format(gametype, basevalue)
            await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(members[active_idx], response))

            # game loop
            trick_take_idx = front_idx
            score = 0
            trick_msgs = []
            for turn in range(10):
                front_idx = trick_take_idx
                mid_idx = (trick_take_idx + 1) % 3
                back_idx = (trick_take_idx + 2) % 3
                idxs = [front_idx, mid_idx, back_idx]
                trick = []
                for idx in idxs:
                    response = "It's your turn, {} a card.".format(ewcfg.cmd_slimeskat_play)
                    await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(members[idx], response))
                    legalplay = False
                    while not legalplay:

                        while not legalplay:
                            play = random.randrange(len(hands[idx]))
                            legalplay = checkiflegal(hands[idx], play, trick[0], trumps) if len(trick) > 0 else True

                        try:
                            msg = await cmd.client.wait_for('message', timeout=play_timeout, check=lambda message: members[idx] == cmd.message.author and
                                                                                                                   message.content.lower().startswith(ewcfg.cmd_slimeskat_play))

                            if msg != None:
                                play = get_skat_play(msg, hands[idx]) - 1
                        except:
                            play = play
                        if idx == front_idx:
                            legalplay = True
                        else:
                            legalplay = checkiflegal(hands[idx], play, trick[0], trumps)
                        if not legalplay:
                            response = "You have to follow suit! Try again."
                            await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(members[idx], response))

                    response = "You play" + printcard(hands[idx][play])
                    msg = await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(members[idx], response))
                    trick.append(hands[idx].pop(play))
                    if idx == front_idx:
                        for tm in trick_msgs:
                            await tm.delete()
                            pass
                        trick_msgs = []
                    trick_msgs.append(msg)
                    hand3parts = printhand(hands[idx])
                    handles = handles_table[idx]
                    for i in range(len(hand3parts)):
                        handles[i] = await fe_utils.edit_message(cmd.client, handles[i], fe_utils.formatMessage(members[idx], hand3parts[i]))

                trick_take_idx = idxs[determine_trick_taker(trick, gametype, trumps)]
                response = "**{} takes the trick.**".format(members[trick_take_idx].display_name)
                await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(members[active_idx], response))
                if trick_take_idx == active_idx:
                    if gametype == "null":
                        score = 1
                        break
                    else:
                        score += evaluatetrick(trick)

            # determine winner
            win = False
            if gametype == "null":
                if score == 0:
                    win = True
            else:
                if score > 60:
                    win = True
                    if score >= 90:
                        game_multiplier += 1
                    if score == 120:
                        game_multiplier += 1
                else:
                    if score < 30:
                        game_multiplier += 1
                    if score == 0:
                        game_multiplier += 1
                response = "You got {} points in your tricks.".format(score)
                await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(members[active_idx], response))
            totalvalue = basevalue * game_multiplier
            if totalvalue < maxbid:
                response = "You overbid your hand! Your game was worth {} points, but you bid {} points.".format(totalvalue, maxbid)
                await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(members[active_idx], response))
                while totalvalue < maxbid:
                    win = False
                    totalvalue += basevalue

            if win:
                winstate = "won"
                gain = "gain"
                lossmod = 1
                sign = 1
            else:
                winstate = "lost"
                gain = "lose"
                lossmod = 2
                sign = -1

            # payout
            totalsc = totalvalue * multiplier * lossmod

            response = "You {} a {} game with a value of {}. You {} {} SlimeCoin.".format(winstate, gametype, str(totalvalue), gain, str(totalsc))

            await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(members[active_idx], response))

            for i in range(3):
                player = EwUser(member=members[i])
                if i == active_idx:
                    player.change_slimecoin(n=sign * totalsc, coinsource=ewcfg.coinsource_casino)
                else:
                    player.change_slimecoin(n=-1 * (sign * totalsc) / 2, coinsource=ewcfg.coinsource_casino)
                player.persist()

        for handles in handles_table:
            for h in handles:
                await h.delete()
        onemore = True
        for mem in members:
            response = "Game ended. Will you {} for another round or will you {}?".format(ewcfg.cmd_slimeskat_join, ewcfg.cmd_slimeskat_decline)
            await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(mem, response))
            try:
                msg = await cmd.client.wait_for('message', timeout=join_timeout, check=lambda message: mem == cmd.message.author and
                                                                                                       message.content.lower().startswith(ewcfg.cmd_slimeskat_join) or
                                                                                                       message.content.lower().startswith(ewcfg.cmd_slimeskat_decline))

                if msg != None:
                    if msg.content.lower().startswith(ewcfg.cmd_slimeskat_decline):
                        onemore = False
                else:
                    onemore = False
            except:
                onemore = False
            if not onemore:
                break

        if onemore:
            response = "Everyone is in. Let's go for another round!"
            await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(members[active_idx], response))
        else:
            break

    response = "No more. Your puny brains can't handle this intellectual challenge any longer."
    await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(members[active_idx], response))
    for m in members:
        ewuser = EwUser(member=m)
        ewutils.active_target_map[ewuser.id_user] = ""

    return


""" nullifies commands sent in response to skat plays """


async def skat_play(cmd):
    return


async def russian_roulette(cmd):
    time_now = int(time.time())
    soulstake = False

    if len(cmd.tokens) > 1 and cmd.tokens[1] == "soul":
        soulstake = True

    user_data = EwUser(member=cmd.message.author)

    if user_data.poi != ewcfg.poi_id_thecasino:
        # Only at the casino
        response = "You can only play russian roulette at the casino."
        return await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(cmd.message.author, response))

    if cmd.mentions_count != 1:
        # Must mention only one player
        response = "Mention the player you want to challenge."
        return await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(cmd.message.author, response))

    author = cmd.message.author
    member = cmd.mentions[0]

    global last_russianrouletted_times
    last_used_author = last_russianrouletted_times.get(author.id)
    last_used_member = last_russianrouletted_times.get(member.id)

    if last_used_author == None:
        last_used_author = 0
    if last_used_member == None:
        last_used_member = 0

    if last_used_author + ewcfg.cd_rr > time_now or last_used_member + ewcfg.cd_rr > time_now:
        response = "**ENOUGH**"
        return await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(cmd.message.author, response))

    if author.id == member.id:
        response = "You might be looking for !suicide."
        return await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(author, response))

    challenger = EwUser(member=author)
    challengee = EwUser(member=member)

    # Players have been challenged
    if ewutils.active_target_map.get(challenger.id_user) != None and ewutils.active_target_map.get(challenger.id_user) != "":
        response = "You are already in the middle of a challenge."
        return await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(author, response))

    if ewutils.active_target_map.get(challengee.id_user) != None and ewutils.active_target_map.get(challengee.id_user) != "":
        response = "{} is already in the middle of a challenge.".format(member.display_name).replace("@", "\{at\}")
        return await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(author, response))

    if challenger.poi != challengee.poi:
        # Challangee must be in the casino
        response = "Both players must be in the casino."
        return await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(author, response))

    challenger_mutations = challenger.get_mutations()
    challengee_mutations = challengee.get_mutations()

    # Players have to be enlisted
    playable_life_states = [ewcfg.life_state_enlisted, ewcfg.life_state_lucky, ewcfg.life_state_executive, ewcfg.life_state_juvenile]
    if challenger.life_state not in playable_life_states or challengee.life_state not in playable_life_states:
        if challenger.life_state == ewcfg.life_state_corpse:
            response = "You try to grab the gun, but it falls through your hands. Ghosts can't hold weapons.".format(author.display_name).replace("@", "\{at\}")
            return await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(author, response))
        elif challengee.life_state == ewcfg.life_state_corpse:
            response = "{} tries to grab the gun, but it falls through their hands. Ghosts can't hold weapons.".format(member.display_name).replace("@", "\{at\}")
            return await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(author, response))
        elif challenger.life_state == ewcfg.life_state_kingpin:
            response = "Throwing all of your gang's hard earned slime on the line strikes you as a bad idea..."
            return await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(author, response))
        elif challengee.life_state == ewcfg.life_state_kingpin:
            response = "They think about accepting for a moment, but then back away, remembering all the hard work their gangsters have put forth. Bummer..."
            return await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(author, response))
        else:
            response = "Juveniles are too cowardly to gamble their lives."
            return await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(author, response))
    elif (challenger.has_soul == 0 or challengee.has_soul == 0) and soulstake:
        response = "A soul game of russian roulette can't be played unless both players have souls planted firmly in their body."
        return await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(author, response))
    elif (challenger.life_state == ewcfg.life_state_juvenile and ewcfg.mutation_id_nervesofsteel not in challenger_mutations):
        response = "Juveniles are usually too cowardly to gamble their lives."
        return await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(author, response))
    elif (challengee.life_state == ewcfg.life_state_juvenile and ewcfg.mutation_id_nervesofsteel not in challengee_mutations):
        response = "Juveniles are usually too cowardly to gamble their lives."
        return await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(author, response))

    # Assign a challenger so players can't be challenged
    ewutils.active_target_map[challenger.id_user] = challengee.id_user
    ewutils.active_target_map[challengee.id_user] = challenger.id_user

    ewutils.active_restrictions[challenger.id_user] = 1
    ewutils.active_restrictions[challengee.id_user] = 1

    response = "You have been challenged by {} to a game of russian roulette. Do you !accept or !refuse?".format(author.display_name).replace("@", "\{at\}")
    if soulstake:
        response = "You have been challenged by {} to a game of russian roulette. Your soul is on the line in this game. Do you !accept or !refuse?".format(author.display_name).replace("@", "\{at\}")
    await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(member, response))

    # Wait for an answer
    accepted = False
    try:
        msg = await cmd.client.wait_for('message', timeout=30, check=lambda message: message.author == member and
                                                                                     message.content.lower() in [ewcfg.cmd_accept, ewcfg.cmd_refuse])

        if msg != None:
            if msg.content == ewcfg.cmd_accept:
                accepted = True
    except:
        accepted = False

    # Start game
    if accepted == 1:
        # SLIMERNALIA

        if not soulstake and ewcfg.slimernalia_active:
            challenger = EwUser(member = author)
            challengee = EwUser(member = member)


            ewstats.change_stat(id_server=cmd.guild.id, id_user=challengee.id_user, metric=ewcfg.stat_festivity, n=round((challenger.slimes / 100000) + 50))
            ewstats.change_stat(id_server=cmd.guild.id, id_user=challenger.id_user, metric=ewcfg.stat_festivity, n=round((challengee.slimes / 100000) + 50))


        wait_time = 1
        if soulstake:
            wait_time = 2

        for spin in range(1, 7):
            challenger = EwUser(member=author)
            challengee = EwUser(member=member)

            # Challenger goes second
            if spin % 2 == 0:
                player = author
            else:
                player = member

            response = "You put the gun to your head and pull the trigger..."
            res = await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(player, response))
            await asyncio.sleep(wait_time)

            # Player dies
            if random.randint(1, (7 - spin)) == 1:
                res = await fe_utils.edit_message(cmd.client, res, fe_utils.formatMessage(player, (response + " **BANG**")))
                response = "You return to the Casino with {}'s slime.".format(player.display_name).replace("@", "\{at\}")
                if soulstake:
                    response = "You return to the Casino with {}'s soul.".format(player.display_name).replace("@", "\{at\}")
                was_suicide = False
                # Challenger dies
                if spin % 2 == 0:
                    winner = member

                    challenger = EwUser(member=author)
                    challengee = EwUser(member=member)

                    challengee.change_slimes(n=challenger.slimes * 0.8, source=ewcfg.source_killing)

                    challenger.id_killer = challenger.id_user
                    challenger.trauma = ewcfg.trauma_id_suicide
                    await challenger.die(cause=ewcfg.cause_suicide)

                    if soulstake:
                        item_utils.surrendersoul(giver=challenger.id_user, receiver=challengee.id_user, id_server=challenger.id_server)
                        challenger.has_soul = 0

                # Challengee dies
                else:
                    winner = author

                    challenger = EwUser(member=author)
                    challengee = EwUser(member=member)

                    challenger.change_slimes(n=challengee.slimes * 0.8, source=ewcfg.source_killing)

                    challengee.id_killer = challengee.id_user
                    challenger.trauma = ewcfg.trauma_id_suicide
                    await challengee.die(cause=ewcfg.cause_suicide)
                    if soulstake:
                        item_utils.surrendersoul(giver=challengee.id_user, receiver=challenger.id_user, id_server=challenger.id_server)
                        challengee.has_soul = 0

                ewutils.active_target_map[challenger.id_user] = ""
                ewutils.active_target_map[challengee.id_user] = ""

                ewutils.active_restrictions[challenger.id_user] = 0
                ewutils.active_restrictions[challengee.id_user] = 0

                challenger.persist()
                challengee.persist()

                await fe_utils.send_response(response, cmd)

                break

            # Or survives
            else:
                res = await fe_utils.edit_message(cmd.client, res, fe_utils.formatMessage(player, (response + " but it's empty")))
                await asyncio.sleep(wait_time)

    # Or cancel the challenge
    else:
        response = "{} was too cowardly to accept your challenge.".format(member.display_name).replace("@", "\{at\}")
        await fe_utils.send_message(cmd.client, cmd.message.channel, fe_utils.formatMessage(author, response))
        last_russianrouletted_times[author.id] = time_now - 540
        last_russianrouletted_times[member.id] = time_now - 540

    challenger = EwUser(member=author)
    challengee = EwUser(member=member)

    ewutils.active_target_map[challenger.id_user] = ""
    ewutils.active_target_map[challengee.id_user] = ""

    ewutils.active_restrictions[challenger.id_user] = 0
    ewutils.active_restrictions[challengee.id_user] = 0

    challenger.persist()
    challengee.persist()

    return
