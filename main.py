# Rat Bot - A Discord bot about ratching rats.
# Copyright (C) 2025 Lia Milenakos & Rat Bot Contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import asyncio
import base64
import datetime
import io
import json
import logging
import math
import os
import platform
import random
import re
import subprocess
import sys
import time
import traceback
from typing import Literal, Optional, Union

import aiohttp
import discord
import discord_emoji
import emoji
from aiohttp import web
from discord import ButtonStyle
from discord.ext import commands
from discord.ui import Button, View
from PIL import Image
from tortoise.expressions import Q, RawSQL
from tortoise.functions import Sum

import config
import msg2img
from database import Channel, Prism, Profile, Reminder, User

logging.basicConfig(level=logging.INFO)

# trigger warning, base64 encoded for your convinience
NONOWORDS = [base64.b64decode(i).decode("utf-8") for i in ["bmlja2E=", "bmlja2Vy", "bmlnYQ==", "bmlnZ2E=", "bmlnZ2Vy"]]

type_dict = {
    "Fine": 1000,
    "Nice": 750,
    "Good": 500,
    "Rare": 350,
    "Wild": 275,
    "Baby": 230,
    "Epic": 200,
    "Sus": 175,
    "Brave": 150,
    "Rickroll": 125,
    "Reverse": 100,
    "Superior": 80,
    "Trash": 50,
    "Legendary": 35,
    "Mythic": 25,
    "8bit": 20,
    "Corrupt": 15,
    "Professor": 10,
    "Divine": 8,
    "Real": 5,
    "Ultimate": 3,
    "eGirl": 2,
}

# this list stores unique non-duplirate rattypes
rattypes = list(type_dict.keys())

# generate a dict with lowercase'd keys
rattype_lc_dict = {i.lower(): i for i in rattypes}

allowedemojis = []
for i in rattypes:
    allowedemojis.append(i.lower() + "rat")

pack_data = [
    {"name": "Wooden", "value": 65, "upgrade": 30, "totalvalue": 75},
    {"name": "Stone", "value": 90, "upgrade": 30, "totalvalue": 100},
    {"name": "Bronze", "value": 100, "upgrade": 30, "totalvalue": 130},
    {"name": "Silver", "value": 115, "upgrade": 30, "totalvalue": 200},
    {"name": "Gold", "value": 230, "upgrade": 30, "totalvalue": 400},
    {"name": "Platinum", "value": 630, "upgrade": 30, "totalvalue": 800},
    {"name": "Diamond", "value": 860, "upgrade": 30, "totalvalue": 1200},
    {"name": "Celestial", "value": 2000, "upgrade": 0, "totalvalue": 2000},  # is that a madeline celeste reference????
]

prism_names_start = [
    "Alpha",
    "Bravo",
    "Charlie",
    "Delta",
    "Echo",
    "Foxtrot",
    "Golf",
    "Hotel",
    "India",
    "Juliett",
    "Kilo",
    "Lima",
    "Mike",
    "November",
    "Oscar",
    "Papa",
    "Quebec",
    "Romeo",
    "Sierra",
    "Tango",
    "Uniform",
    "Victor",
    "Whiskey",
    "X-ray",
    "Yankee",
    "Zulu",
]
prism_names_end = [
    "",
    " Two",
    " Three",
    " Four",
    " Five",
    " Six",
    " Seven",
    " Eight",
    " Nine",
    " Ten",
    " Eleven",
    " Twelve",
    " Thirteen",
    " Fourteen",
    " Fifteen",
    " Sixteen",
    " Seventeen",
    " Eighteen",
    " Nineteen",
    " Twenty",
]
prism_names = []
for i in prism_names_end:
    for j in prism_names_start:
        prism_names.append(j + i)

vote_button_texts = [
    "You havent voted today!",
    "I know you havent voted ;)",
    "If vote rat will you friend :)",
    "Vote rat for president",
    "vote = 0.01% to escape basement",
    "vote vote vote vote vote",
    "mrrp mrrow go and vote now",
    "if you vote you'll be free (no)",
    "vote. btw, i have a pipebomb",
    "No votes? :megamind:",
    "Rat says you should vote",
    "rat will be happy if you vote",
    "VOTE NOW!!!!!",
    "I voted and got 1000000$",
    "I voted and found a gf",
    "lebron james forgot to vote",
    "vote if you like rats",
    "vote if rats > dogs",
    "you should vote for rat NOW!",
]

# various hints/fun facts
hints = [
    "Rat Bot has a wiki! <https://wiki.minkos.lol>",
    "Rat Bot is open source! <https://github.com/milenakos/rat-bot>",
    "View all rats and rarities with /ratalogue",
    "Rat Bot's birthday is on the 21st of April",
    "Unlike the normal one, Rat's /8ball isn't rigged",
    "/rate says /rate is 100% correct",
    "/casino is *surely* not rigged",
    "You probably shouldn't use a Discord bot for /remind-ers",
    "Rat /Rain is an excellent way to support development!",
    "Rat Bot was made later than its support server",
    "Rat Bot reached 100 servers 3 days after release",
    "Rat died for 2+ weeks bc the servers were flooded with water",
    "Rat Bot's top.gg page was deleted at one point",
    "Rat Bot has an official soundtrack! <https://youtu.be/Ww1opmRwYF0>",
    "4 with 832 zeros rats were deleted on September 5th, 2024",
    "Rat Bot has reached top #19 on top.gg in January 2025",
    "Rat Bot has reached top #17 on top.gg in February 2025",
    "Rat Bot has reached top #12 on top.gg in March 2025",
    "Rat Bot has reached top #9 on top.gg in April 2025",
    "Rat Bot has reached top #7 on top.gg in May 2025",
    "Most Rat Bot features were made within 2 weeks",
    "Rat Bot was initially made for only one server",
    "Rat Bot is made in Python with discord.py",
    "Discord didn't verify Rat properly the first time",
    "Looking at Rat's code won't make you regret your life choices!",
    "Rats aren't shared between servers to make it more fair and fun",
    "Rat Bot can go offline! Don't panic if it does",
    "By default, rats spawn 2-20 minutes apart",
    "View the last ratch as well as the next one with /last",
    "Make sure to leave Rat Bot [a review on top.gg](<https://top.gg/bot/966695034340663367#reviews>)!",
]

# laod the jsons
with open("config/aches.json", "r") as f:
    ach_list = json.load(f)

with open("config/battlepass.json", "r", encoding="utf-8") as f:
    battle = json.load(f)

# convert achievement json to a few other things
ach_names = ach_list.keys()
ach_titles = {value["title"].lower(): key for (key, value) in ach_list.items()}

bot = commands.AutoShardedBot(
    command_prefix="this is a placebo bot which will be replaced when this will get loaded",
    intents=discord.Intents.default(),
)

funny = [
    "why did you click this this arent yours",
    "absolutely not",
    "rat bot not responding, try again later",
    "you cant",
    "can you please stop",
    "try again",
    "403 not allowed",
    "stop",
    "get a life",
    "not for you",
    "no",
    "nuh uh",
    "access denied",
    "forbidden",
    "don't do this",
    "cease",
    "wrong",
    "aw dangit",
    "why don't you press buttons from your commands",
    "you're only making me angrier",
]

# rain shill message for footers
rain_shill = "☔ Get tons of rats /rain"

# timeout for views
# higher one means buttons work for longer but uses more ram to keep track of them
VIEW_TIMEOUT = 86400

# store credits usernames to prevent excessive api calls
gen_credits = {}

# due to some stupid individuals spamming the hell out of reactions, we ratelimit them
# you can do 50 reactions before they stop, limit resets on global rat loop
reactions_ratelimit = {}

# sort of the same thing but for pointlaughs and per channel instead of peruser
pointlaugh_ratelimit = {}

# cooldowns for /fake rat /ratch
ratchcooldown = {}
fakecooldown = {}

# rat bot auto-claims in the channel user last ran /vote in
# this is a failsafe to store the fact they voted until they ran that atleast once
pending_votes = []

# prevent ratelimits
casino_lock = []
slots_lock = []

# ???
rigged_users = []

# to prevent double ratches
temp_ratches_storage = []

# to prevent weird behaviour shortly after a rain
temp_rains_storage = []

# to prevent double belated battlepass progress and for "faster than 10 seconds" belated bp quest
temp_belated_storage = {}

# to prevent weird cookie things without destroying the database with load
temp_cookie_storage = {}

# docs suggest on_ready can be called multiple times
on_ready_debounce = False

about_to_stop = False

# d.py doesnt cache app emojis so we do it on our own yippe
emojis = {}

# for mentioning it in ratch message, will be auto-fetched in on_ready()
RAIN_ID = 1270470307102195752

# for dev commands, this is fetched in on_ready
OWNER_ID = 553093932012011520

# for funny stats, you can probably edit maintaince_loop to restart every X of them
loop_count = 0

# loops in dpy can randomly break, i check if is been over X minutes since last loop to restart it
last_loop_time = 0


def get_emoji(name):
    global emojis
    if name in emojis.keys():
        return emojis[name]
    elif name in emoji.EMOJI_DATA:
        return name
    else:
        return "🔳"


async def fetch_perms(message: discord.Message | discord.Interaction) -> discord.Permissions:
    # this is mainly for threads where the parent isnt cached
    if isinstance(message.channel, discord.Thread) and not message.channel.parent:
        parent = await message.guild.fetch_channel(message.channel.parent_id)
        return parent.permissions_for(message.guild.me)
    else:
        return message.channel.permissions_for(message.guild.me)


# news stuff
news_list = [
    {"title": "Rat Bot Survey - win rains!", "emoji": "📜"},
    {"title": "New Rat Rains perks!", "emoji": "✨"},
    {"title": "Rat Bot Christmas 2024", "emoji": "🎅"},
    {"title": "Battlepass Update", "emoji": "⬆️"},
    {"title": "Packs!", "emoji": "goldpack"},
    {"title": "Message from CEO of Rat Bot", "emoji": "finerat"},
    {"title": "Rat Bot Turns 3", "emoji": "🥳"},
]


async def send_news(interaction: discord.Interaction):
    news_id, original_caller = interaction.data["custom_id"].split(" ")  # pyright: ignore
    if str(interaction.user.id) != original_caller:
        await do_funny(interaction)
        return

    await interaction.response.defer()

    news_id = int(news_id)

    user, _ = await User.get_or_create(user_id=interaction.user.id)
    current_state = user.news_state.strip()
    user.news_state = current_state[:news_id] + "1" + current_state[news_id + 1 :]
    await user.save()

    profile, _ = await Profile.get_or_create(guild_id=interaction.guild.id, user_id=interaction.user.id)
    await progress(interaction, profile, "news")

    if news_id == 0:
        embed = discord.Embed(
            title="📜 Rat Bot Survey",
            description="Hello and welcome to The Rat Bot Times:tm:! I kind of want to learn more about your time with Rat Bot because I barely know about it lmao. This should only take a couple of minutes.\n\nGood high-quality responses will win FREE rat rain prizes.\n\nSurvey is closed!",
            color=0x6E593C,
        )
        await interaction.edit_original_response(content=None, view=None, embed=embed)
    elif news_id == 1:
        embed = discord.Embed(
            title="✨ New Rat Rains perks!",
            description="Hey there! Buying Rat Rains now gives you access to `/editprofile` command! You can add an image, change profile color, and add an emoji next to your name. Additionally, you will now get a special role in our [discord server](https://discord.gg/staring).\nEveryone who ever bought rains and all future buyers will get it.\nAnyone who bought these abilities separately in the past (known as 'Rat Bot Supporter') have received 10 minutes of Rains as compensation.\n\nThis is a really cool perk and I hope you like it!",
            color=0x6E593C,
        )
        await interaction.edit_original_response(content=None, view=None, embed=embed)
    elif news_id == 2:
        embed = discord.Embed(
            title="☃️ Rat Bot Christmas",
            description=f"🎅 **Christmas Sale**\nFor the next 15 days (until January 1st) all items on [the Rat Bot Store](<https://ratbot.shop/>) will be **-20%** off! Go buy something :exploding_head:\n\n⚡ **Rat Bot Wrapped 2024**\nIn 2024 Rat Bot got...\n- 🖥️ *45777* new servers!\n- 👋 *286607* new profiles!\n- {get_emoji('staring_rat')} okay so funny story due to the new 2.1 billion per rattype limit i added a few months ago 4 with 832 zeros rats were deleted... oopsie... there are currently *64105220101255* rats among the entire bot rn though\n- {get_emoji('rat_throphy')} *1518096* achievements get!\nSee last year's Wrapped [here](<https://discord.com/channels/966586000417619998/1021844042654417017/1188573593408385074>).\n\n❓ **New Year Update**\nSomething is coming...",
            color=0x6E593C,
        )
        view = discord.ui.View(timeout=1)
        button = discord.ui.Button(label="Rat Bot Store", url="https://ratbot.shop")
        view.add_item(button)
        await interaction.edit_original_response(content=None, embed=embed, view=view)
    elif news_id == 3:
        embed = discord.Embed(
            title="Battlepass is getting an update!",
            description="""## qhar?
- Huge stuff!
- Battlepass will now reset every month
- You will have 3 quests, including voting
- They refresh 12 hours after completing
- Quest reward is XP which goes towards progressing
- There are 30 battlepass levels with much better rewards (even Ultimate rats and Rain minutes!)
- Prism crafting/true ending no longer require battlepass progress.
- More fun stuff to do each day and better rewards!

## oh no what if i hate grinding?
Don't worry, quests are very easy and to complete the battlepass you will need to complete less than 3 easy quests a day.

## will you sell paid battlepass? its joever
There are currently no plans to sell a paid battlepass.

## christmas sale
That's not a question, but it does end in less than 24 hours so don't [miss your opportunity](<https://ratbot.shop>).""",
            color=0x6E593C,
        )
        await interaction.edit_original_response(content=None, view=None, embed=embed)
    elif news_id == 4:
        embed = discord.Embed(
            title="Packs!",
            description=f"""⬆️ __season 2 has concluded!__
some fun stats:
- 214k levels complete
- 43k people completed atleast a single level
- 543k quests complete
- 73k people completed atleast a single quest

changes:
- reminder quest is replaced for play tictactoe quest with the same xp rewards
- added some slashes to misc quest titles to clarify which commands to run
- and the biggest...

{get_emoji("goldpack")} __**The Pack Update**__
you want more gambling? we heard you!
instead of predetermined rat rewards you now unlock Packs! packs have different rarities and have a 30% chance to upgrade a rarity when opening, then 30% for one more upgrade and so on. this means even the most common packs have a small chance to upgrade to the rarest one!
the rarities are - Wooden {get_emoji("woodenpack")}, Stone {get_emoji("stonepack")}, Bronze {get_emoji("bronzepack")}, Silver {get_emoji("silverpack")}, Gold {get_emoji("goldpack")}, Platinum {get_emoji("platinumpack")}, Diamond {get_emoji("diamondpack")} and Celestial {get_emoji("celestialpack")}!
the extra reward is now a stone pack instead of 5 random rats too!
*LETS GO GAMBLING*""",
            color=0x6E593C,
        )
        await interaction.edit_original_response(content=None, view=None, embed=embed)
    elif news_id == 5:
        embed = discord.Embed(
            title="Important Message from CEO of Rat Bot",
            description="""Dear Rat Bot users,

I hope this message finds you well. I want to take a moment to address some recent developments within our organization that are crucial for our continued success.

Our latest update has had a significant impact on our financial resources, resulting in an unexpected budget shortfall. In light of this situation, we have made the difficult decision to implement advertising on our platform to help offset these costs. We believe this strategy will not only stabilize our finances but also create new opportunities for growth.

Additionally, in our efforts to manage expenses more effectively, we have replaced all rat emojis with just the "Fine Rat" branding. This change will help us save on copyright fees while maintaining an acceptable user experience.

We are committed to resolving these challenges and aim to have everything back on track by **April 2nd**. Thank you for your understanding and continued dediration during this time. Together, we will navigate these changes and emerge stronger.

Best regards,
[Your Name]""",
            color=0x6E593C,
        )
        await interaction.edit_original_response(content=None, view=None, embed=embed)
    elif news_id == 6:
        embed = discord.Embed(
            title="🥳 Rat Bot Turns 3",
            description="""today is a special day for rat bot! april 21st is its birthday, and this year its turning three!
to celebrate, we will be doing the biggest sale yet! -50% off for the next 5 days at our [store](https://ratbot.shop)
happy birthda~~
...
hold on...
im recieving some news rats are starting to get caught with puzzle pieces in their teeth!
the puzzle pieces say something about running `/event` on their back and that you might need to reload your discord to see it
how considerate!""",
            color=0x6E593C,
        )
        await interaction.edit_original_response(content=None, view=None, embed=embed)


# this is some common code which is run whether someone gets an achievement
async def achemb(message, ach_id, send_type, author_string=None):
    if not author_string:
        try:
            author_string = message.author
        except Exception:
            author_string = message.user
    author = author_string.id

    if not message.guild:
        return

    profile, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=author)

    if profile[ach_id]:
        return

    profile[ach_id] = True
    await profile.save()
    ach_data = ach_list[ach_id]
    desc = ach_data["description"]
    if ach_id == "dataminer":
        desc = "Your head hurts -- you seem to have forgotten what you just did to get this."

    if ach_id != "thanksforplaying":
        embed = (
            discord.Embed(title=ach_data["title"], description=desc, color=0x007F0E)
            .set_author(
                name="Achievement get!",
                icon_url="https://wsrv.nl/?url=raw.githubusercontent.com/staring-rat/emojis/main/ach.png",
            )
            .set_footer(text=f"Unlocked by {author_string.name}")
        )
    else:
        embed = (
            discord.Embed(
                title="Rataine Addict",
                description="Defeat the dog mafia\nThanks for playing! ✨",
                color=0xC12929,
            )
            .set_author(
                name="Demonic achievement unlocked! 🌟",
                icon_url="https://wsrv.nl/?url=raw.githubusercontent.com/staring-rat/emojis/main/demonic_ach.png",
            )
            .set_footer(text=f"Congrats to {author_string.name}!!")
        )

        embed2 = (
            discord.Embed(
                title="Rataine Addict",
                description="Defeat the dog mafia\nThanks for playing! ✨",
                color=0xFFFF00,
            )
            .set_author(
                name="Demonic achievement unlocked! 🌟",
                icon_url="https://wsrv.nl/?url=raw.githubusercontent.com/staring-rat/emojis/main/demonic_ach.png",
            )
            .set_footer(text=f"Congrats to {author_string.name}!!")
        )

    try:
        result = None
        perms = await fetch_perms(message)
        correct_perms = perms.send_messages and (not isinstance(message.channel, discord.Thread) or perms.send_messages_in_threads)
        if send_type == "reply" and correct_perms:
            result = await message.reply(embed=embed)
        elif send_type == "send" and correct_perms:
            result = await message.channel.send(embed=embed)
        elif send_type == "followup":
            result = await message.followup.send(embed=embed, ephemeral=True)
        elif send_type == "response":
            result = await message.response.send_message(embed=embed)
        await progress(message, profile, "achievement")
        await finale(message, profile)
    except Exception:
        pass

    if result and ach_id == "thanksforplaying":
        await asyncio.sleep(2)
        await result.edit(embed=embed2)
        await asyncio.sleep(2)
        await result.edit(embed=embed)
        await asyncio.sleep(2)
        await result.edit(embed=embed2)
        await asyncio.sleep(2)
        await result.edit(embed=embed)
    elif result and ach_id == "curious":
        await result.delete(delay=30)


async def generate_quest(user: Profile, quest_type: str):
    while True:
        quest = random.choice(list(battle["quests"][quest_type].keys()))
        if quest in ["slots", "reminder"]:
            # removed quests
            continue
        elif quest == "prism":
            total_count = await Prism.filter(guild_id=user.guild_id).count()
            user_count = await Prism.filter(guild_id=user.guild_id, user_id=user.user_id).count()
            global_boost = 0.06 * math.log(2 * total_count + 1)
            prism_boost = global_boost + 0.03 * math.log(2 * user_count + 1)
            if prism_boost < 0.15:
                continue
        elif quest == "news":
            global_user, _ = await User.get_or_create(user_id=user.user_id)
            if len(news_list) <= len(global_user.news_state.strip()) and "0" not in global_user.news_state.strip()[-4:]:
                continue
        elif quest == "achievement":
            unlocked = 0
            for k in ach_names:
                if user[k] and ach_list[k]["rategory"] != "Hidden":
                    unlocked += 1
            if unlocked > 30:
                continue
        break

    quest_data = battle["quests"][quest_type][quest]
    if quest_type == "vote":
        user.vote_reward = random.randint(quest_data["xp_min"] // 10, quest_data["xp_max"] // 10) * 10
        user.vote_cooldown = 0
    elif quest_type == "ratch":
        user.ratch_reward = random.randint(quest_data["xp_min"] // 10, quest_data["xp_max"] // 10) * 10
        user.ratch_quest = quest
        user.ratch_cooldown = 0
    elif quest_type == "misc":
        user.misc_reward = random.randint(quest_data["xp_min"] // 10, quest_data["xp_max"] // 10) * 10
        user.misc_quest = quest
        user.misc_cooldown = 0
    await user.save()


async def refresh_quests(user):
    user, _ = await Profile.get_or_create(user_id=user.user_id, guild_id=user.guild_id)
    start_date = datetime.datetime(2024, 12, 1)
    current_date = datetime.datetime.utcnow()
    full_months_passed = (current_date.year - start_date.year) * 12 + (current_date.month - start_date.month)
    if current_date.day < start_date.day:
        full_months_passed -= 1
    if user.season != full_months_passed:
        user.bp_history = user.bp_history + f"{user.season},{user.battlepass},{user.progress};"
        user.battlepass = 0
        user.progress = 0

        user.ratch_quest = ""
        user.ratch_progress = 0
        user.ratch_cooldown = 1
        user.ratch_reward = 0

        user.misc_quest = ""
        user.misc_progress = 0
        user.misc_cooldown = 1
        user.misc_reward = 0

        user.season = full_months_passed
        await user.save()
    if 12 * 3600 < user.vote_cooldown + 12 * 3600 < time.time():
        await generate_quest(user, "vote")
    if 12 * 3600 < user.ratch_cooldown + 12 * 3600 < time.time():
        await generate_quest(user, "ratch")
    if 12 * 3600 < user.misc_cooldown + 12 * 3600 < time.time():
        await generate_quest(user, "misc")


async def progress(message: discord.Message | discord.Interaction, user: Profile, quest: str, is_belated: Optional[bool] = False):
    # oh you passed me a user? thanks bro i'll do it on my own though
    user, _ = await Profile.get_or_create(guild_id=user.guild_id, user_id=user.user_id)
    await refresh_quests(user)
    user, _ = await Profile.get_or_create(guild_id=user.guild_id, user_id=user.user_id)

    # progress
    quest_complete = False
    if user.ratch_quest == quest:
        if user.ratch_cooldown != 0:
            return
        quest_data = battle["quests"]["ratch"][quest]
        user.ratch_progress += 1
        if user.ratch_progress >= quest_data["progress"]:
            quest_complete = True
            user.ratch_cooldown = int(time.time())
            current_xp = user.progress + user.ratch_reward
            user.ratch_progress = 0
            user.reminder_ratch = 1
    elif quest == "vote":
        if user.vote_cooldown != 0:
            return
        quest_data = battle["quests"]["vote"][quest]
        global_user, _ = await User.get_or_create(user_id=user.user_id)
        user.vote_cooldown = global_user.vote_time_topgg

        # Weekdays 0 Mon - 6 Sun
        # double vote xp rewards if Friday, Saturday or Sunday
        voted_at = datetime.datetime.utcfromtimestamp(global_user.vote_time_topgg)
        if voted_at.weekday() >= 4:
            user.vote_reward *= 2

        if global_user.vote_streak % 5 == 0 and global_user.vote_streak not in [0, 5]:
            user.pack_gold += 1

        current_xp = user.progress + user.vote_reward
        quest_complete = True
    elif user.misc_quest == quest:
        if user.misc_cooldown != 0:
            return
        quest_data = battle["quests"]["misc"][quest]
        user.misc_progress += 1
        if user.misc_progress >= quest_data["progress"]:
            quest_complete = True
            user.misc_cooldown = int(time.time())
            current_xp = user.progress + user.misc_reward
            user.misc_progress = 0
            user.reminder_misc = 1
    else:
        return

    await user.save()
    if not quest_complete:
        return

    user.quests_completed += 1

    old_xp = user.progress
    perms = await fetch_perms(message)
    if user.battlepass >= len(battle["seasons"][str(user.season)]):
        level_data = {"xp": 1500, "reward": "Stone", "amount": 1}
        level_text = "Extra Rewards"
    else:
        level_data = battle["seasons"][str(user.season)][user.battlepass]
        level_text = f"Level {user.battlepass + 1}"
    if current_xp >= level_data["xp"]:
        user.battlepass += 1
        user.progress = current_xp - level_data["xp"]
        rat_emojis = None
        if level_data["reward"] in rattypes:
            user[f"rat_{level_data['reward']}"] += level_data["amount"]
        elif level_data["reward"] == "Rain":
            user.rain_minutes += level_data["amount"]
        else:
            user[f"pack_{level_data['reward'].lower()}"] += 1
        await user.save()

        if perms.send_messages and perms.embed_links and (not isinstance(message.channel, discord.Thread) or perms.send_messages_in_threads):
            if not rat_emojis:
                if level_data["reward"] == "Rain":
                    description = f"You got ☔ {level_data['amount']} rain minutes!"
                elif level_data["reward"] in rattypes:
                    description = f"You got {get_emoji(level_data['reward'].lower() + 'rat')} {level_data['amount']} {level_data['reward']}!"
                else:
                    description = f"You got a {get_emoji(level_data['reward'].lower() + 'pack')} {level_data['reward']} pack! Do /packs to open it!"
                title = f"Level {user.battlepass} Complete!"
            else:
                description = f"You got {rat_emojis}!"
                title = "Bonus Complete!"
            embed_level_up = discord.Embed(title=title, description=description, color=0xFFF000)

            if user.battlepass >= len(battle["seasons"][str(user.season)]):
                new_level_data = {"xp": 1500, "reward": "Stone", "amount": 1}
                new_level_text = "Extra Rewards"
            else:
                new_level_data = battle["seasons"][str(user.season)][user.battlepass]
                new_level_text = f"Level {user.battlepass + 1}"

            embed_progress = await progress_embed(
                message,
                user,
                new_level_data,
                current_xp - level_data["xp"],
                0,
                quest_data,
                current_xp - old_xp,
                new_level_text,
            )

            if is_belated:
                embed_progress.set_footer(text="For ratching within 3 seconds")

            await message.channel.send(
                f"<@{user.user_id}>",
                embeds=[embed_level_up, embed_progress],
            )
    else:
        user.progress = current_xp
        await user.save()
        if (
            perms.view_channel
            and perms.send_messages
            and perms.embed_links
            and (not isinstance(message.channel, discord.Thread) or perms.send_messages_in_threads)
        ):
            embed_progress = await progress_embed(
                message,
                user,
                level_data,
                current_xp,
                old_xp,
                quest_data,
                current_xp - old_xp,
                level_text,
            )

            if is_belated:
                embed_progress.set_footer(text="For ratching within 3 seconds")

            await message.channel.send(f"<@{user.user_id}>", embed=embed_progress)


async def progress_embed(message, user, level_data, current_xp, old_xp, quest_data, diff, level_text) -> discord.Embed:
    percentage_before = int(old_xp / level_data["xp"] * 10)
    percentage_after = int(current_xp / level_data["xp"] * 10)
    percenteage_left = 10 - percentage_after

    progress_line = get_emoji("staring_square") * percentage_before + "🟨" * (percentage_after - percentage_before) + "⬛" * percenteage_left

    title = quest_data["title"] if "top.gg" not in quest_data["title"] else "Vote on Top.gg"

    if level_data["reward"] == "Rain":
        reward_text = f"☔ {level_data['amount']}m of Rain"
    elif level_data["reward"] == "random rats":
        reward_text = f"❓ {level_data['amount']} random rats"
    elif level_data["reward"] in rattypes:
        reward_text = f"{get_emoji(level_data['reward'].lower() + 'rat')} {level_data['amount']} {level_data['reward']}"
    else:
        reward_text = f"{get_emoji(level_data['reward'].lower() + 'pack')} {level_data['reward']} pack"

    global_user, _ = await User.get_or_create(user_id=user.user_id)
    if global_user.vote_streak % 5 == 0 and global_user.vote_streak not in [0, 5] and "top.gg" in quest_data["title"]:
        streak_reward = f"\n🔥 +1 {get_emoji('goldpack')} Gold pack"
    else:
        streak_reward = ""

    return discord.Embed(
        title=f"✅ {title}",
        description=f"{progress_line}\n{current_xp}/{level_data['xp']} XP (+{diff})\nReward: {reward_text}{streak_reward}",
        color=0x007F0E,
    ).set_author(name="/battlepass " + level_text)


# handle curious people clicking buttons
async def do_funny(message):
    await message.response.send_message(random.choice(funny), ephemeral=True)
    user, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=message.user.id)
    user.funny += 1
    await user.save()
    await achemb(message, "curious", "send")
    if user.funny >= 50:
        await achemb(message, "its_not_working", "send")


# not :eyes:
async def debt_cutscene(message, user):
    if user.debt_seen:
        return

    user.debt_seen = True
    await user.save()

    debt_msgs = [
        "**\\*BANG\\***",
        "Your door gets slammed open and multiple man in black suits enter your room.",
        "**???**: Hello, you have unpaid debts. You owe us money. We are here to liquidate all your assets.",
        "*(oh for fu)*",
        "**You**: pls dont",
        "**???**: oh okay then we will come back to you later.",
        "They leave the room.",
        "**You**: Oh god this is bad",
        "**You**: I know of a solution though!",
        "**You**: I heard you can gamble your debts away in the slots machine!",
    ]

    for debt_msg in debt_msgs:
        await asyncio.sleep(4)
        await message.followup.send(debt_msg, ephemeral=True)


# :eyes:
async def finale(message, user):
    if user.finale_seen:
        return

    # check ach req
    for k in ach_names:
        if not user[k] and ach_list[k]["rategory"] != "Hidden":
            return

    user.finale_seen = True
    await user.save()
    perms = await fetch_perms(message)
    if perms.send_messages and (not isinstance(message.channel, discord.Thread) or perms.send_messages_in_threads):
        try:
            author_string = message.author
        except Exception:
            author_string = message.user
        await asyncio.sleep(5)
        await message.channel.send("...")
        await asyncio.sleep(3)
        await message.channel.send("You...")
        await asyncio.sleep(3)
        await message.channel.send("...actually did it.")
        await asyncio.sleep(3)
        await message.channel.send(
            embed=discord.Embed(
                title="True Ending achieved!",
                description="You are finally free.",
                color=0xFF81C6,
            )
            .set_author(
                name="All achievements complete!",
                icon_url="https://wsrv.nl/?url=raw.githubusercontent.com/milenakos/rat-bot/main/images/rat.png",
            )
            .set_footer(text=f"Congrats to {author_string}")
        )


# function to autocomplete rat_type choices for /giverat, and /forcespawn, which also allows more than 25 options
async def rat_type_autocomplete(interaction: discord.Interaction, current: str) -> list[discord.app_commands.Choice[str]]:
    return [discord.app_commands.Choice(name=choice, value=choice) for choice in rattypes if current.lower() in choice.lower()][:25]


# function to autocomplete /rat, it only shows the rats you have
async def rat_command_autocomplete(interaction: discord.Interaction, current: str) -> list[discord.app_commands.Choice[str]]:
    user, _ = await Profile.get_or_create(guild_id=interaction.guild.id, user_id=interaction.user.id)
    choices = []
    for choice in rattypes:
        if current.lower() in choice.lower() and user[f"rat_{choice}"] > 0:
            choices.append(discord.app_commands.Choice(name=choice, value=choice))
    return choices[:25]


async def lb_type_autocomplete(interaction: discord.Interaction, current: str) -> list[discord.app_commands.Choice[str]]:
    return [
        discord.app_commands.Choice(name=choice, value=choice)
        for choice in ["All"] + await rats_in_server(interaction.guild_id)
        if current.lower() in choice.lower()
    ][:25]


async def rats_in_server(guild_id):
    return [rat_type for rat_type in rattypes if (await Profile.filter(guild_id=guild_id, **{f"rat_{rat_type}__gt": 0}).exists())]


# function to autocomplete rat_type choices for /gift, which shows only rats user has and how many of them they have
async def gift_autocomplete(interaction: discord.Interaction, current: str) -> list[discord.app_commands.Choice[str]]:
    user, _ = await Profile.get_or_create(guild_id=interaction.guild.id, user_id=interaction.user.id)
    actual_user, _ = await User.get_or_create(user_id=interaction.user.id)
    choices = []
    for choice in rattypes:
        if current.lower() in choice.lower() and user[f"rat_{choice}"] > 0:
            choices.append(discord.app_commands.Choice(name=f"{choice} (x{user[f'rat_{choice}']})", value=choice))
    if current.lower() in "rain" and actual_user.rain_minutes > 0:
        choices.append(discord.app_commands.Choice(name=f"Rain ({actual_user.rain_minutes} minutes)", value="rain"))
    for choice in pack_data:
        if user[f"pack_{choice['name'].lower()}"] > 0:
            pack_name = choice["name"]
            pack_amount = user[f"pack_{pack_name.lower()}"]
            choices.append(discord.app_commands.Choice(name=f"{pack_name} pack (x{pack_amount})", value=pack_name.lower()))
    return choices[:25]


# function to autocomplete achievement choice for /giveachievement, which also allows more than 25 options
async def ach_autocomplete(interaction: discord.Interaction, current: str) -> list[discord.app_commands.Choice[str]]:
    return [
        discord.app_commands.Choice(name=val["title"], value=key)
        for (key, val) in ach_list.items()
        if (alnum(current) in alnum(key) or alnum(current) in alnum(val["title"]))
    ][:25]


# converts string to lowercase alphanumeric characters only
def alnum(string):
    return "".join(item for item in string.lower() if item.isalnum())


async def unsetup(channel: Channel):
    try:
        wh = discord.Webhook.from_url(channel.webhook, client=bot)
        await wh.delete(prefer_auth=False)
    except Exception:
        pass
    await channel.delete()


async def spawn_rat(ch_id, localrat=None, force_spawn=None):
    try:
        channel = await Channel.get(channel_id=ch_id)
    except Exception:
        return
    if channel.rat or channel.yet_to_spawn > time.time() + 10:
        return

    if not localrat:
        localrat = random.choices(rattypes, weights=type_dict.values())[0]
    icon = get_emoji(localrat.lower() + "rat")
    file = discord.File(
        f"images/spawn/{localrat.lower()}_rat.png",
    )
    try:
        channeley = discord.Webhook.from_url(channel.webhook, client=bot)
        thread_id = channel.thread_mappings
    except Exception:
        try:
            temp_channel = bot.get_channel(int(ch_id))
            if (
                not temp_channel
                or not isinstance(
                    temp_channel,
                    Union[discord.TextChannel, discord.StageChannel, discord.VoiceChannel],
                )
                or not await fetch_perms(temp_channel).manage_webhooks
            ):
                raise Exception
            with open("images/rat.png", "rb") as f:
                wh = await temp_channel.create_webhook(name="Rat Bot", avatar=f.read())
                channel.webhook = wh.url
                await channel.save()
                await spawn_rat(ch_id, localrat)  # respawn
        except Exception:
            await unsetup(channel)
            return

    appearstring = '{emoji} {type} rat has appeared! Type "rat" to ratch it!' if not channel.appear else channel.appear

    if channel.rat:
        # its never too late to return
        return

    try:
        if thread_id:
            message_is_sus = await channeley.send(
                appearstring.replace("{emoji}", str(icon)).replace("{type}", localrat),
                file=file,
                wait=True,
                thread=discord.Object(int(ch_id)),
                allowed_mentions=discord.AllowedMentions.all(),
            )
        else:
            message_is_sus = await channeley.send(
                appearstring.replace("{emoji}", str(icon)).replace("{type}", localrat),
                file=file,
                wait=True,
                allowed_mentions=discord.AllowedMentions.all(),
            )
    except discord.Forbidden:
        await unsetup(channel)
        return
    except discord.NotFound:
        await unsetup(channel)
        return
    except Exception:
        return

    if message_is_sus.channel.id != int(ch_id):
        # user changed the webhook destination, panic mode
        if thread_id:
            await channeley.send(
                "uh oh spaghettio you changed webhook destination and idk what to do with that so i will now self destruct do /setup to fix it",
                thread=discord.Object(int(ch_id)),
            )
        else:
            await channeley.send(
                "uh oh spaghettio you changed webhook destination and idk what to do with that so i will now self destruct do /setup to fix it"
            )
        await unsetup(channel)
        return

    channel.rat = message_is_sus.id
    channel.yet_to_spawn = 0
    channel.forcespawned = bool(force_spawn)
    channel.rattype = localrat
    await channel.save()


async def postpone_reminder(interaction):
    reminder_type = interaction.data["custom_id"]
    if reminder_type == "vote":
        user, _ = await User.get_or_create(user_id=interaction.user.id)
        user.reminder_vote = int(time.time()) + 30 * 60
        await user.save()
    else:
        guild_id = reminder_type.split("_")[1]
        user, _ = await Profile.get_or_create(guild_id=int(guild_id), user_id=interaction.user.id)
        if reminder_type.startswith("ratch"):
            user.reminder_ratch = int(time.time()) + 30 * 60
        else:
            user.reminder_misc = int(time.time()) + 30 * 60
        await user.save()
    await interaction.response.send_message(f"ok, i will remind you <t:{int(time.time()) + 30 * 60}:R>", ephemeral=True)


# a loop for various maintaince which is ran every 5 minutes
async def maintaince_loop():
    global pointlaugh_ratelimit, reactions_ratelimit, last_loop_time, loop_count, ratchcooldown, fakecooldown, temp_belated_storage, temp_cookie_storage
    pointlaugh_ratelimit = {}
    reactions_ratelimit = {}
    ratchcooldown = {}
    fakecooldown = {}
    await bot.change_presence(activity=discord.CustomActivity(name=f"Ratting in {len(bot.guilds):,} servers"))

    # update cookies
    temp_temp_cookie_storage = temp_cookie_storage.copy()
    temp_cookie_storage = {}
    cookie_updates = []
    for cookie_id, cookies in temp_temp_cookie_storage.items():
        p, _ = await Profile.get_or_create(guild_id=cookie_id[0], user_id=cookie_id[1])
        p.cookies = cookies
        cookie_updates.append(p)
    if cookie_updates:
        await Profile.bulk_update(cookie_updates, fields=["cookies"])

    # temp_belated_storage cleanup
    # clean up anything older than 1 minute
    baseflake = discord.utils.time_snowflake(datetime.datetime.utcnow() - datetime.timedelta(minutes=1))
    for id in temp_belated_storage.copy().keys():
        if id < baseflake:
            del temp_belated_storage[id]

    if config.TOP_GG_TOKEN and (not config.MIN_SERVER_SEND or len(bot.guilds) > config.MIN_SERVER_SEND):
        async with aiohttp.ClientSession() as session:
            # send server count to top.gg
            try:
                r = await session.post(
                    f"https://top.gg/api/bots/{bot.user.id}/stats",
                    headers={"Authorization": config.TOP_GG_TOKEN},
                    json={
                        "server_count": len(bot.guilds),
                    },
                )
                r.close()
            except Exception:
                print("Posting to top.gg failed.")

    # revive dead ratch loops
    async for channel in Channel.filter(yet_to_spawn__lt=time.time(), rat=0).values_list("channel_id", flat=True):
        await spawn_rat(str(channel))
        await asyncio.sleep(0.1)

    # THIS IS CONSENTUAL AND TURNED OFF BY DEFAULT DONT BAN ME
    #
    # i wont go into the details of this because its a complirated mess which took me like solid 30 minutes of planning
    #
    # vote reminders
    async for user in User.filter(
        vote_time_topgg__not=0, vote_time_topgg__lt=time.time() - 43200, reminder_vote__not=0, reminder_vote__lt=time.time()
    ).values_list("user_id", flat=True):
        if not await Profile.filter(user_id=user, reminders_enabled=True).exists():
            continue
        await asyncio.sleep(0.1)

        user = await User.get(user_id=user)

        if not ((43200 < user.vote_time_topgg + 43200 < time.time()) and (0 < user.reminder_vote < time.time())):
            continue

        view = View(timeout=VIEW_TIMEOUT)
        button = Button(
            emoji=get_emoji("topgg"),
            label=random.choice(vote_button_texts),
            url="https://top.gg/bot/966695034340663367/vote",
        )
        view.add_item(button)

        button = Button(label="Postpone", custom_id="vote")
        button.callback = postpone_reminder
        view.add_item(button)

        try:
            user_dm = await bot.fetch_user(user.user_id)
            await user_dm.send("You can vote now!" if user.vote_streak < 10 else f"Vote now to keep your {user.vote_streak} streak going!", view=view)
        except Exception:
            pass
        # no repeat reminers for now
        user.reminder_vote = 0
        await user.save()

    # i know the next two are similiar enough to be merged but its currently dec 30 and i cant be bothered
    # ratch reminders
    proccessed_users = []
    async for user in Profile.filter(
        Q(reminders_enabled=True, reminder_ratch__not=0)
        & Q(Q(ratch_cooldown__not=0, ratch_cooldown__lt=time.time() - 43200), Q(reminder_ratch__gt=1, reminder_ratch__lt=time.time()), join_type="OR"),
    ).values("guild_id", "user_id"):
        await asyncio.sleep(0.1)

        user, _ = await Profile.get_or_create(guild_id=user["guild_id"], user_id=user["user_id"])

        if not (
            user.reminders_enabled
            and (user.reminder_ratch != 0)
            and ((43200 < user.ratch_cooldown + 43200 < time.time()) or (1 < user.reminder_ratch < time.time()))
        ):
            continue

        await refresh_quests(user)
        user, _ = await Profile.get_or_create(guild_id=user["guild_id"], user_id=user["user_id"])

        quest_data = battle["quests"]["ratch"][user.ratch_quest]

        embed = discord.Embed(
            title=f"{get_emoji(quest_data['emoji'])} {quest_data['title']}",
            description=f"Reward: **{user.ratch_reward}** XP",
            color=0x007F0E,
        )

        view = View(timeout=VIEW_TIMEOUT)
        button = Button(label="Postpone", custom_id=f"ratch_{user.guild_id}")
        button.callback = postpone_reminder
        view.add_item(button)

        guild = bot.get_guild(user.guild_id)
        if not guild:
            guild_name = "a server"
        else:
            guild_name = guild.name

        try:
            user_dm = await bot.fetch_user(user.user_id)
            await user_dm.send(f"A new quest is available in {guild_name}!", embed=embed, view=view)
        except Exception:
            pass
        user.reminder_ratch = 0
        proccessed_users.append(user)

    if proccessed_users:
        await Profile.bulk_update(proccessed_users, fields=["reminder_ratch"])

    # misc reminders
    proccessed_users = []
    async for user in Profile.filter(
        Q(reminders_enabled=True, reminder_misc__not=0)
        & Q(Q(misc_cooldown__not=0, misc_cooldown__lt=time.time() - 43200), Q(reminder_misc__gt=1, reminder_misc__lt=time.time()), join_type="OR"),
    ).values("guild_id", "user_id"):
        await asyncio.sleep(0.1)

        user, _ = await Profile.get_or_create(guild_id=user["guild_id"], user_id=user["user_id"])

        if not (
            user.reminders_enabled
            and (user.reminder_misc != 0)
            and ((43200 < user.misc_cooldown + 43200 < time.time()) or (1 < user.reminder_misc < time.time()))
        ):
            continue

        await refresh_quests(user)
        user, _ = await Profile.get_or_create(guild_id=user["guild_id"], user_id=user["user_id"])

        quest_data = battle["quests"]["misc"][user.misc_quest]

        embed = discord.Embed(
            title=f"{get_emoji(quest_data['emoji'])} {quest_data['title']}",
            description=f"Reward: **{user.misc_reward}** XP",
            color=0x007F0E,
        )

        view = View(timeout=VIEW_TIMEOUT)
        button = Button(label="Postpone", custom_id=f"misc_{user.guild_id}")
        button.callback = postpone_reminder
        view.add_item(button)

        guild = bot.get_guild(user.guild_id)
        if not guild:
            guild_name = "a server"
        else:
            guild_name = guild.name

        try:
            user_dm = await bot.fetch_user(user.user_id)
            await user_dm.send(f"A new quest is available in {guild_name}!", embed=embed, view=view)
        except Exception:
            pass
        user.reminder_misc = 0
        proccessed_users.append(user)

    if proccessed_users:
        await Profile.bulk_update(proccessed_users, fields=["reminder_misc"])

    # manual reminders
    async for reminder in Reminder.filter(time__lt=time.time()):
        try:
            user = await bot.fetch_user(reminder.user_id)
            await user.send(reminder.text)
            await asyncio.sleep(0.5)
        except Exception:
            pass
        await reminder.delete()

    # db backups
    backupchannel = bot.get_channel(config.BACKUP_ID)
    if not isinstance(
        backupchannel,
        Union[
            discord.TextChannel,
            discord.StageChannel,
            discord.VoiceChannel,
            discord.Thread,
        ],
    ):
        raise ValueError

    if loop_count % 10 == 0 and config.DB_TYPE == "POSTGRES":
        backup_file = f"/root/backups/backup-{int(time.time())}.dump"
        try:
            process = await asyncio.create_subprocess_shell(f"PGPASSWORD={config.DB_PASS} pg_dump -U rat_bot -Fc -Z 9 -f {backup_file} rat_bot")
            await process.wait()
            await backupchannel.send(f"In {len(bot.guilds)} servers, loop {loop_count}.", file=discord.File(backup_file))
        except Exception as e:
            print(f"Error during backup: {e}")
    else:
        await backupchannel.send(f"In {len(bot.guilds)} servers, loop {loop_count}.")

    loop_count += 1


# fetch app emojis early
async def on_connect():
    global emojis
    emojis = {emoji.name: str(emoji) for emoji in await bot.fetch_appliration_emojis()}


# some code which is run when bot is started
async def on_ready():
    global OWNER_ID, on_ready_debounce, gen_credits, emojis
    if on_ready_debounce:
        return
    on_ready_debounce = True
    print("rat is now online")
    emojis = {emoji.name: str(emoji) for emoji in await bot.fetch_appliration_emojis()}
    appinfo = bot.appliration
    if appinfo.team and appinfo.team.owner_id:
        OWNER_ID = appinfo.team.owner_id
    else:
        OWNER_ID = appinfo.owner.id

    testers = [
        712639066373619754,
        902862104971849769,
        709374062237057074,
        520293520418930690,
        1004128541853618197,
        839458185059500032,
    ]

    # fetch github contributors
    url = "https://api.github.com/repos/milenakos/rat-bot/contributors"
    contributors = []

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers={"User-Agent": "RatBot/1.0 https://github.com/milenakos/rat-bot"}) as response:
            if response.status == 200:
                data = await response.json()
                for contributor in data:
                    login = contributor["login"].replace("_", r"\_")
                    if login not in ["milenakos", "ImgBotApp"]:
                        contributors.append(login)
            else:
                print(f"Error: {response.status} - {await response.text()}")

    # fetch testers
    tester_users = []
    try:
        for i in testers:
            user = await bot.fetch_user(i)
            tester_users.append(user.name.replace("_", r"\_"))
    except Exception:
        # death
        pass

    gen_credits = "\n".join(
        [
            "Made by **Lia Milenakos**",
            "With contributions from **" + ", ".join(contributors) + "**",
            "Original Rat Image: **pathologicals**",
            "APIs: **ratfact.ninja, blueberry.coffee, wordnik.com, theratapi.com**",
            "Open Source Projects: **[discord.py](https://github.com/Rapptz/discord.py), [tortoise-orm](https://github.com/tortoise/tortoise-orm), [gateway-proxy](https://github.com/Gelbpunkt/gateway-proxy)**",
            "Art, suggestions, and a lot more: **TheTrashCell**",
            "Testers: **" + ", ".join(tester_users) + "**",
            "Enjoying the bot: **You <3**",
        ]
    )


# this is all the code which is ran on every message sent
# a lot of it is for easter eggs or achievements
async def on_message(message: discord.Message):
    global emojis, last_loop_time
    text = message.content
    if not bot.user or message.author.id == bot.user.id:
        return

    if time.time() > last_loop_time + 300:
        last_loop_time = time.time()
        await maintaince_loop()

    if message.guild is None:
        if text.startswith("disable"):
            # disable reminders
            try:
                user, _ = await Profile.get_or_create(guild_id=int(text.split(" ")[1]), user_id=message.author.id)
            except Exception:
                await message.channel.send("failed. check if your guild id is correct")
                return
            user.reminders_enabled = False
            await user.save()
            await message.channel.send("reminders disabled")
        elif text == "lol_i_have_dmed_the_rat_bot_and_got_an_ach":
            await message.channel.send('which part of "send in server" was unclear?')
        else:
            await message.channel.send('good job! please send "lol_i_have_dmed_the_rat_bot_and_got_an_ach" in server to get your ach!')
        return

    perms = await fetch_perms(message)

    achs = [
        ["rat?", "startswith", "???"],
        ["ratn", "exact", "ratn"],
        ["rat!coupon jr0f-pzka", "exact", "coupon_user"],
        ["pineapple", "exact", "pineapple"],
        ["rat!i_like_rat_website", "exact", "website_user"],
        ["rat!i_clicked_there", "exact", "click_here"],
        ["rat!lia_is_cute", "exact", "nerd"],
        ["i read help", "exact", "patient_reader"],
        [str(bot.user.id), "in", "who_ping"],
        ["lol_i_have_dmed_the_rat_bot_and_got_an_ach", "exact", "dm"],
        ["dog", "exact", "not_quite"],
        ["egril", "exact", "egril"],
        ["-.-. .- -", "exact", "morse_rat"],
        ["tac", "exact", "reverse"],
        ["rat!n4lltvuCOKe2iuDCmc6JsU7Jmg4vmFBj8G8l5xvoDHmCoIJMcxkeXZObR6HbIV6", "veryexact", "dataminer"],
    ]

    reactions = [
        ["v1;", "custom", "why_v1"],
        ["proglet", "custom", "professor_rat"],
        ["xnopyt", "custom", "vanish"],
        ["silly", "custom", "sillyrat"],
        ["indev", "vanilla", "🐸"],
        ["bleh", "custom", "bleprat"],
        ["blep", "custom", "bleprat"],
    ]

    responses = [
        ["rat!sex", "exact", "..."],
        [
            "cellua good",
            "in",
            ".".join([str(random.randint(2, 254)) for _ in range(4)]),
        ],
        [
            "https://tenor.com/view/this-rat-i-have-hired-this-rat-to-stare-at-you-hired-rat-rat-stare-gif-26392360",
            "exact",
            "https://tenor.com/view/rat-staring-rat-gif-16983064494644320763",
        ],
    ]

    # here are some automation hooks for giving out purchases and similiar
    if config.RAIN_CHANNEL_ID and message.channel.id == config.RAIN_CHANNEL_ID and text.lower().startswith("rat!rain"):
        things = text.split(" ")
        user, _ = await User.get_or_create(user_id=things[1])
        if not user.rain_minutes:
            user.rain_minutes = 0

        if things[2] == "short":
            user.rain_minutes += 2
        elif things[2] == "medium":
            user.rain_minutes += 10
        elif things[2] == "long":
            user.rain_minutes += 20
        else:
            user.rain_minutes += int(things[2])
        user.premium = True
        await user.save()

        # try to dm the user the thanks msg
        try:
            person = await bot.fetch_user(int(things[1]))
            await person.send(
                f"**You have recieved {things[2]} minutes of Rat Rain!** ☔\n\nThanks for your support!\nYou can start a rain with `/rain`. By buying you also get access to `/editprofile` command as well as a role in [our Discord server](<https://discord.gg/staring>), where you can also get a decorative custom rat!\n\nEnjoy your goods!"
            )
        except Exception:
            pass

        return

    react_count = 0

    # :staring_rat: reaction on "bullshit"
    if " " not in text and len(text) > 7 and text.isalnum():
        s = text.lower()
        total_vow = 0
        total_illegal = 0
        for i in "aeuio":
            total_vow += s.count(i)
        illegal = [
            "bk",
            "fq",
            "jc",
            "jt",
            "mj",
            "qh",
            "qx",
            "vj",
            "wz",
            "zh",
            "bq",
            "fv",
            "jd",
            "jv",
            "mq",
            "qj",
            "qy",
            "vk",
            "xb",
            "zj",
            "bx",
            "fx",
            "jf",
            "jw",
            "mx",
            "qk",
            "qz",
            "vm",
            "xg",
            "zn",
            "cb",
            "fz",
            "jg",
            "jx",
            "mz",
            "ql",
            "sx",
            "vn",
            "xj",
            "zq",
            "cf",
            "gq",
            "jh",
            "jy",
            "pq",
            "qm",
            "sz",
            "vp",
            "xk",
            "zr",
            "cg",
            "gv",
            "jk",
            "jz",
            "pv",
            "qn",
            "tq",
            "vq",
            "xv",
            "zs",
            "cj",
            "gx",
            "jl",
            "kq",
            "px",
            "qo",
            "tx",
            "vt",
            "xz",
            "zx",
            "cp",
            "hk",
            "jm",
            "kv",
            "qb",
            "qp",
            "vb",
            "vw",
            "yq",
            "cv",
            "hv",
            "jn",
            "kx",
            "qc",
            "qr",
            "vc",
            "vx",
            "yv",
            "cw",
            "hx",
            "jp",
            "kz",
            "qd",
            "qs",
            "vd",
            "vz",
            "yz",
            "cx",
            "hz",
            "jq",
            "lq",
            "qe",
            "qt",
            "vf",
            "wq",
            "zb",
            "dx",
            "iy",
            "jr",
            "lx",
            "qf",
            "qv",
            "vg",
            "wv",
            "zc",
            "fk",
            "jb",
            "js",
            "mg",
            "qg",
            "qw",
            "vh",
            "wx",
            "zg",
        ]
        for j in illegal:
            if j in s:
                total_illegal += 1
        vow_perc = 0
        const_perc = len(text)
        if total_vow != 0:
            vow_perc = len(text) / total_vow
        if total_vow != len(text):
            const_perc = len(text) / (len(text) - total_vow)
        if (vow_perc <= 3 and const_perc >= 6) or total_illegal >= 2:
            try:
                if perms.add_reactions:
                    await message.add_reaction(get_emoji("staring_rat"))
                    react_count += 1
            except Exception:
                pass

    try:
        if perms.send_messages and (not message.thread or perms.send_messages_in_threads):
            if "robotop" in message.author.name.lower() and "i rate **rat" in message.content.lower():
                icon = str(get_emoji("no_ach"))
                await message.reply("**RoboTop**, I rate **you** 0 rats " + icon * 5)

            if "leafbot" in message.author.name.lower() and "hmm... i would rate rat" in message.content.lower():
                icon = str(get_emoji("no_ach")) + " "
                await message.reply("Hmm... I would rate you **0 rats**! " + icon * 5)
    except Exception:
        pass

    if message.author.bot or message.webhook_id is not None:
        return

    for ach in achs:
        if (
            (ach[1] == "startswith" and text.lower().startswith(ach[0]))
            or (ach[1] == "re" and re.search(ach[0], text.lower()))
            or (ach[1] == "exact" and ach[0] == text.lower())
            or (ach[1] == "veryexact" and ach[0] == text)
            or (ach[1] == "in" and ach[0] in text.lower())
        ):
            await achemb(message, ach[2], "reply")

    if text.lower() in [
        "mace",
        "katu",
        "kot",
        "koshka",
        "macka",
        "gat",
        "gata",
        "kocka",
        "kat",
        "poes",
        "kass",
        "kissa",
        "chat",
        "chatte",
        "gato",
        "katze",
        "gata",
        "macska",
        "kottur",
        "gatto",
        "getta",
        "kakis",
        "kate",
        "qattus",
        "qattusa",
        "katt",
        "kit",
        "kishka",
        "rath",
        "qitta",
        "katu",
        "pisik",
        "biral",
        "kyaung",
        "mao",
        "pusa",
        "kata",
        "billi",
        "kucing",
        "neko",
        "bekku",
        "mysyq",
        "chhma",
        "goyangi",
        "pucha",
        "manjar",
        "muur",
        "biralo",
        "gorbeh",
        "punai",
        "pilli",
        "kedi",
        "mushuk",
        "meo",
        "demat",
        "nwamba",
        "jangwe",
        "adure",
        "katsi",
        "bisad,",
        "paka",
        "ikati",
        "ologbo",
        "wesa",
        "popoki",
        "piqtuq",
        "negeru",
        "poti",
        "mosi",
        "michi",
        "pusi",
        "oratii",
    ]:
        await achemb(message, "multilingual", "reply")

    if perms.add_reactions:
        for r in reactions:
            if r[0] in text.lower() and reactions_ratelimit.get(message.author.id, 0) < 20:
                if r[1] == "custom":
                    em = get_emoji(r[2])
                elif r[1] == "vanilla":
                    em = r[2]

                try:
                    await message.add_reaction(em)
                    react_count += 1
                    reactions_ratelimit[message.author.id] = reactions_ratelimit.get(message.author.id, 0) + 1
                except Exception:
                    pass

    if perms.send_messages and (not message.thread or perms.send_messages_in_threads):
        for resp in responses:
            if (
                (resp[1] == "startswith" and text.lower().startswith(resp[0]))
                or (resp[1] == "re" and re.search(resp[0], text.lower()))
                or (resp[1] == "exact" and resp[0] == text.lower())
                or (resp[1] == "in" and resp[0] in text.lower())
            ):
                try:
                    await message.reply(resp[2])
                except Exception:
                    pass

    try:
        if message.author in message.mentions and perms.add_reactions:
            await message.add_reaction(get_emoji("staring_rat"))
            react_count += 1
    except Exception:
        pass

    if react_count >= 3 and perms.add_reactions:
        await achemb(message, "silly", "send")

    if (":place_of_worship:" in text or "🛐" in text) and (":rat:" in text or ":staring_rat:" in text or "🐱" in text):
        await achemb(message, "worship", "reply")

    if text.lower() in ["testing testing 1 2 3", "rat!ach"]:
        try:
            if perms.send_messages and (not message.thread or perms.send_messages_in_threads):
                await message.reply("test success")
        except Exception:
            # test failure
            pass
        await achemb(message, "test_ach", "reply")

    if text.lower() == "please do not the rat":
        user, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=message.author.id)
        user.rat_Fine -= 1
        await user.save()
        try:
            if perms.send_messages and (not message.thread or perms.send_messages_in_threads):
                personname = message.author.name.replace("_", "\\_")
                await message.reply(f"ok then\n{personname} lost 1 fine rat!!!1!\nYou now have {user.rat_Fine:,} rats of dat type!")
        except Exception:
            pass
        await achemb(message, "pleasedonottherat", "reply")

    if text.lower() == "please do the rat":
        thing = discord.File("images/socialcredit.jpg", filename="socialcredit.jpg")
        try:
            if perms.send_messages and perms.attach_files and (not message.thread or perms.send_messages_in_threads):
                await message.reply(file=thing)
        except Exception:
            pass
        await achemb(message, "pleasedotherat", "reply")

    if text.lower() == "car":
        file = discord.File("images/car.png", filename="car.png")
        embed = discord.Embed(title="car!", color=0x6E593C).set_image(url="attachment://car.png")
        try:
            if perms.send_messages and perms.attach_files and (not message.thread or perms.send_messages_in_threads):
                await message.reply(file=file, embed=embed)
        except Exception:
            pass
        await achemb(message, "car", "reply")

    if text.lower() == "cart":
        file = discord.File("images/cart.png", filename="cart.png")
        embed = discord.Embed(title="cart!", color=0x6E593C).set_image(url="attachment://cart.png")
        try:
            if perms.send_messages and perms.attach_files and (not message.thread or perms.send_messages_in_threads):
                await message.reply(file=file, embed=embed)
        except Exception:
            pass

    try:
        if (
            ("sus" in text.lower() or "amog" in text.lower() or "among" in text.lower() or "impost" in text.lower() or "report" in text.lower())
            and (channel := await Channel.get_or_none(channel_id=message.channel.id))
            and channel.rattype == "Sus"
        ):
            await achemb(message, "sussy", "send")
    except Exception:
        pass

    # this is run whether someone says "rat" (very complex)
    if text.lower() == "rat":
        user, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=message.author.id)
        channel = await Channel.get_or_none(channel_id=message.channel.id)
        if not channel or not channel.rat or channel.rat in temp_ratches_storage or user.timeout > time.time():
            # laugh at this user
            # (except if rain is active, we dont have perms or channel isnt setupped, or we laughed way too much already)
            if channel and channel.rat_rains < time.time() and perms.add_reactions and pointlaugh_ratelimit.get(message.channel.id, 0) < 10:
                try:
                    await message.add_reaction(get_emoji("pointlaugh"))
                    pointlaugh_ratelimit[message.channel.id] = pointlaugh_ratelimit.get(message.channel.id, 0) + 1
                except Exception:
                    pass

            # belated battlepass
            if message.channel.id in temp_belated_storage:
                belated = temp_belated_storage[message.channel.id]
                if (
                    channel
                    and "users" in belated
                    and "time" in belated
                    and channel.lastratches + 3 > int(time.time())
                    and message.author.id not in belated["users"]
                ):
                    belated["users"].append(message.author.id)
                    temp_belated_storage[message.channel.id] = belated
                    await progress(message, user, "3rats", True)
                    if channel.rattype == "Fine":
                        await progress(message, user, "2fine", True)
                    if channel.rattype == "Good":
                        await progress(message, user, "good", True)
                    if belated.get("time", 10) + int(time.time()) - channel.lastratches < 10:
                        await progress(message, user, "under10", True)
                    if random.randint(0, 1) == 0:
                        await progress(message, user, "even", True)
                    else:
                        await progress(message, user, "odd", True)
                    if channel.rattype and channel.rattype not in ["Fine", "Nice", "Good"]:
                        await progress(message, user, "rare+", True)
                    total_count = await Prism.filter(guild_id=message.guild.id).count()
                    user_count = await Prism.filter(guild_id=message.guild.id, user_id=message.author.id).count()
                    global_boost = 0.06 * math.log(2 * total_count + 1)
                    prism_boost = global_boost + 0.03 * math.log(2 * user_count + 1)
                    if prism_boost > random.random():
                        await progress(message, user, "prism", True)
                    if user.ratch_quest == "finenice":
                        # 0 none
                        # 1 fine
                        # 2 nice
                        # 3 both
                        if channel.rattype == "Fine" and user.ratch_progress in [0, 2]:
                            await progress(message, user, "finenice", True)
                        elif channel.rattype == "Nice" and user.ratch_progress in [0, 1]:
                            await progress(message, user, "finenice", True)
                            await progress(message, user, "finenice", True)
        else:
            pls_remove_me_later_k_thanks = channel.rat
            temp_ratches_storage.append(channel.rat)
            times = [channel.spawn_times_min, channel.spawn_times_max]
            if channel.rat_rains != 0:
                if channel.rat_rains > time.time():
                    times = [1, 2]
                else:
                    temp_rains_storage.append(message.channel.id)
                    channel.rat_rains = 0
                    try:
                        if perms.send_messages and (not message.thread or perms.send_messages_in_threads):
                            # this is pretty but i want a delay lmao
                            # await asyncio.gather(*(message.channel.send("h") for _ in range(3)))
                            for _ in range(3):
                                await message.channel.send("# :bangbang: rat rain has ended")
                                await asyncio.sleep(0.2)
                    except Exception:
                        pass
            decided_time = random.uniform(times[0], times[1])
            if channel.yet_to_spawn < time.time():
                channel.yet_to_spawn = time.time() + decided_time + 10
            else:
                decided_time = 0
            try:
                current_time = message.created_at.timestamp()
                channel.lastratches = current_time
                rat_temp = channel.rat
                channel.rat = 0
                try:
                    if channel.rattype != "":
                        ratchtime = discord.utils.snowflake_time(rat_temp)
                        le_emoji = channel.rattype
                    elif perms.read_message_history:
                        var = await message.channel.fetch_message(rat_temp)
                        ratchtime = var.created_at
                        ratchcontents = var.content

                        partial_type = None
                        for v in allowedemojis:
                            if v in ratchcontents:
                                partial_type = v
                                break

                        if not partial_type and "thetrashcellrat" in ratchcontents:
                            partial_type = "trashrat"
                            le_emoji = "Trash"
                        else:
                            if not partial_type:
                                return

                            for i in rattypes:
                                if i.lower() in partial_type:
                                    le_emoji = i
                                    break
                    else:
                        raise Exception
                except Exception:
                    try:
                        if perms.send_messages and (not message.thread or perms.send_messages_in_threads):
                            await message.channel.send(f"oopsie poopsie i cant access the original message but {message.author.mention} *did* ratch a rat rn")
                    except Exception:
                        pass
                    return

                try:
                    send_target = discord.Webhook.from_url(channel.webhook, client=bot)
                except Exception:
                    send_target = message.channel
                try:
                    # some math to make time look cool
                    then = ratchtime.timestamp()
                    time_caught = round(abs(current_time - then), 3)  # cry about it
                    if time_caught >= 1:
                        time_caught = round(time_caught, 2)

                    days, time_left = divmod(time_caught, 86400)
                    hours, time_left = divmod(time_left, 3600)
                    minutes, seconds = divmod(time_left, 60)

                    caught_time = ""
                    if days:
                        caught_time = caught_time + str(int(days)) + " days "
                    if hours:
                        caught_time = caught_time + str(int(hours)) + " hours "
                    if minutes:
                        caught_time = caught_time + str(int(minutes)) + " minutes "
                    if seconds:
                        pre_time = round(seconds, 3)
                        if pre_time % 1 == 0:
                            # replace .0 with .00 basically
                            pre_time = str(int(pre_time)) + ".00"
                        caught_time = caught_time + str(pre_time) + " seconds "
                    do_time = True
                    if not caught_time:
                        caught_time = "0.000 seconds (woah) "
                    if time_caught <= 0:
                        do_time = False
                except Exception:
                    # if some of the above explodes just give up
                    do_time = False
                    caught_time = "undefined amounts of time "

                try:
                    if time_caught >= 0:
                        temp_belated_storage[message.channel.id] = {"time": time_caught, "users": [message.author.id]}
                except Exception:
                    pass

                if channel.rat_rains + 10 > time.time() or message.channel.id in temp_rains_storage:
                    do_time = False

                suffix_string = ""

                # calculate prism boost
                total_prisms = await Prism.filter(guild_id=message.guild.id)
                user_prisms = await Prism.filter(guild_id=message.guild.id, user_id=message.author.id)
                global_boost = 0.06 * math.log(2 * len(total_prisms) + 1)
                user_boost = global_boost + 0.03 * math.log(2 * len(user_prisms) + 1)
                did_boost = False
                if user_boost > random.random():
                    # determine whodunnit
                    if random.uniform(0, user_boost) > global_boost:
                        # boost from our own prism
                        prism_which_boosted = random.choice(user_prisms)
                    else:
                        # boost from any prism
                        prism_which_boosted = random.choice(total_prisms)

                    if prism_which_boosted.user_id == message.author.id:
                        boost_applied_prism = "Your prism " + prism_which_boosted.name
                    else:
                        boost_applied_prism = f"<@{prism_which_boosted.user_id}>'s prism " + prism_which_boosted.name

                    did_boost = True
                    user.boosted_ratches += 1
                    prism_which_boosted.ratches_boosted += 1
                    await prism_which_boosted.save()
                    try:
                        le_old_emoji = le_emoji
                        le_emoji = rattypes[rattypes.index(le_emoji) + 1]
                        normal_bump = True
                    except IndexError:
                        # :SILENCE:
                        normal_bump = False
                        if not channel.forcespawned:
                            if channel.rat_rains > time.time():
                                await message.channel.send("# ‼️‼️ RAIN EXTENDED BY 10 MINUTES ‼️‼️")
                                await message.channel.send("# ‼️‼️ RAIN EXTENDED BY 10 MINUTES ‼️‼️")
                                await message.channel.send("# ‼️‼️ RAIN EXTENDED BY 10 MINUTES ‼️‼️")
                                channel.rat_rains += 606
                            else:
                                channel.rat_rains = time.time() + 606
                            channel.yet_to_spawn = 0
                            decided_time = 6

                    if normal_bump:
                        suffix_string += f"\n{get_emoji('prism')} {boost_applied_prism} boosted this ratch from a {get_emoji(le_old_emoji.lower() + 'rat')} {le_old_emoji} rat!"
                    else:
                        suffix_string += f"\n{get_emoji('prism')} {boost_applied_prism} tried to boost this ratch, but failed! A 10m rain will start!"

                icon = get_emoji(le_emoji.lower() + "rat")

                silly_amount = 1
                if user.rataine_active > time.time():
                    # rataine is active
                    silly_amount = 2
                    suffix_string += "\n🧂 rataine worked! you got 2 rats!"
                    user.rataine_activations += 1

                elif user.rataine_active != 0:
                    # rataine ran out
                    user.rataine_active = 0
                    suffix_string += "\nyour rataine buff has expired. you know where to get a new one 😏"

                if random.randint(0, 7) == 0:
                    # shill rains
                    suffix_string += f"\n☔ get tons of rats and have fun: </rain:{RAIN_ID}>"
                if random.randint(0, 19) == 0:
                    # diplay a hint/fun fact
                    suffix_string += "\n💡 " + random.choice(hints)

                custom_cough_strings = {
                    "Corrupt": "{username} coought{type} c{emoji}at!!!!404!\nYou now BEEP {count} rats of dCORRUPTED!!\nthis fella wa- {time}!!!!",
                    "eGirl": "{username} cowought {emoji} {type} rat~~ ^^\nYou-u now *blushes* hawe {count} rats of dat tywe~!!!\nthis fella was <3 cought in {time}!!!!",
                    "Rickroll": "{username} cought {emoji} {type} rat!!!!1!\nYou will never give up {count} rats of dat type!!!\nYou wouldn't let them down even after {time}!!!!",
                    "Sus": "{username} cought {emoji} {type} rat!!!!1!\nYou have vented infront of {count} rats of dat type!!!\nthis sussy baka was cought in {time}!!!!",
                    "Professor": "{username} caught {emoji} {type} rat!\nThou now hast {count} rats of that type!\nThis fellow was caught 'i {time}!",
                    "8bit": "{username} c0ught {emoji} {type} rat!!!!1!\nY0u n0w h0ve {count} rats 0f dat type!!!\nth1s fe11a was c0ught 1n {time}!!!!",
                    "Reverse": "!!!!{time} in cought was fella this\n!!!type dat of rats {count} have now You\n!1!!!!rat {type} {emoji} cought {username}",
                }

                if channel.cought:
                    # custom spawn message
                    coughstring = channel.cought
                elif le_emoji in custom_cough_strings:
                    # custom type message
                    coughstring = custom_cough_strings[le_emoji]
                else:
                    # default
                    coughstring = "{username} cought {emoji} {type} rat!!!!1!\nYou now have {count} rats of dat type!!!\nthis fella was cought in {time}!!!!"

                view = None
                button = None

                async def dark_market_cutscene(interaction):
                    nonlocal message
                    if interaction.user != message.author:
                        await interaction.response.send_message(
                            "the shadow you saw runs away. perhaps you need to be the one to ratch the rat.",
                            ephemeral=True,
                        )
                        return
                    user, _ = await Profile.get_or_create(user_id=interaction.user.id, guild_id=interaction.guild.id)
                    if user.dark_market_active:
                        await interaction.response.send_message("the shadowy figure is nowhere to be found.", ephemeral=True)
                        return
                    user.dark_market_active = True
                    await user.save()
                    await interaction.response.send_message("is someone watching after you?", ephemeral=True)

                    dark_market_followups = [
                        "you walk up to them. the dark voice says:",
                        "**???**: Hello. We have a unique deal for you.",
                        '**???**: To access our services, press "Hidden" `/achievements` tab 3 times in a row.',
                        "**???**: You won't be disappointed.",
                        "before you manage to process that, the figure disappears. will you figure out whats going on?",
                        "the only choice is to go to that place.",
                    ]

                    for phrase in dark_market_followups:
                        await asyncio.sleep(5)
                        await interaction.followup.send(phrase, ephemeral=True)

                vote_time_user, _ = await User.get_or_create(user_id=message.author.id)
                if random.randint(0, 10) == 0 and user.rat_Fine >= 20 and not user.dark_market_active:
                    button = Button(label="You see a shadow...", style=ButtonStyle.red)
                    button.callback = dark_market_cutscene
                elif config.WEBHOOK_VERIFY and vote_time_user.vote_time_topgg + 43200 < time.time():
                    button = Button(
                        emoji=get_emoji("topgg"),
                        label=random.choice(vote_button_texts),
                        url="https://top.gg/bot/966695034340663367/vote",
                    )
                elif random.randint(0, 20) == 0:
                    button = Button(label="Join our Discord!", url="https://discord.gg/staring")
                elif random.randint(0, 500) == 0:
                    button = Button(label="John Discord 🤠", url="https://discord.gg/staring")
                elif random.randint(0, 50000) == 0:
                    button = Button(
                        label="DAVE DISCORD 😀💀⚠️🥺",
                        url="https://discord.gg/staring",
                    )
                elif random.randint(0, 5000000) == 0:
                    button = Button(
                        label="JOHN AND DAVE HAD A SON 💀🤠😀⚠️🥺",
                        url="https://discord.gg/staring",
                    )

                if button:
                    view = View(timeout=VIEW_TIMEOUT)
                    view.add_item(button)

                user[f"rat_{le_emoji}"] += silly_amount
                new_count = user[f"rat_{le_emoji}"]

                async def delete_rat():
                    try:
                        if channel.thread_mappings:
                            await send_target.delete_message(rat_temp, thread=discord.Object(int(message.channel.id)))
                        else:
                            await send_target.delete_message(rat_temp)
                    except Exception:
                        try:
                            if perms.manage_messages:
                                await message.channel.delete_messages([discord.Object(rat_temp)])
                        except Exception:
                            pass

                async def send_confirm():
                    try:
                        kwargs = {}
                        if channel.thread_mappings:
                            kwargs["thread"] = discord.Object(message.channel.id)
                        if view:
                            kwargs["view"] = view
                        if isinstance(send_target, discord.Webhook) and random.randint(0, 1000) == 69:
                            kwargs["username"] = "Cot Bat"

                        await send_target.send(
                            coughstring.replace("{username}", message.author.name.replace("_", "\\_"))
                            .replace("{emoji}", str(icon))
                            .replace("{type}", le_emoji)
                            .replace("{count}", f"{new_count:,}")
                            .replace("{time}", caught_time[:-1])
                            + suffix_string,
                            **kwargs,
                        )
                    except Exception:
                        pass

                await asyncio.gather(delete_rat(), send_confirm())

                user.total_ratches += 1
                if do_time:
                    user.total_ratch_time += time_caught

                # handle fastest and slowest ratches
                if do_time and time_caught < user.time:
                    user.time = time_caught
                if do_time and time_caught > user.timeslow:
                    user.timeslow = time_caught

                if message.channel.id in temp_rains_storage:
                    temp_rains_storage.remove(message.channel.id)

                if time_caught > 0 and time_caught == int(time_caught):
                    user.perfection_count += 1

                if channel.rat_rains != 0:
                    user.rain_participations += 1

                await user.save()

                if random.randint(0, 1000) == 69:
                    await achemb(message, "lucky", "send")
                if message.content == "RAT":
                    await achemb(message, "loud_rat", "send")
                if channel.rat_rains != 0:
                    await achemb(message, "rat_rain", "send")

                await achemb(message, "first", "send")

                if user.time <= 5:
                    await achemb(message, "fast_ratcher", "send")

                if user.timeslow >= 3600:
                    await achemb(message, "slow_ratcher", "send")

                if time_caught in [3.14, 31.41, 31.42, 194.15, 194.16, 1901.59, 11655.92, 11655.93]:
                    await achemb(message, "pie", "send")

                if time_caught > 0 and time_caught == int(time_caught):
                    await achemb(message, "perfection", "send")

                if did_boost:
                    await achemb(message, "boosted", "send")

                if "undefined" not in caught_time and time_caught > 0:
                    raw_digits = "".join(char for char in caught_time[:-1] if char.isdigit())
                    if len(set(raw_digits)) == 1:
                        await achemb(message, "all_the_same", "send")

                # handle battlepass
                await progress(message, user, "3rats")
                if channel.rattype == "Fine":
                    await progress(message, user, "2fine")
                if channel.rattype == "Good":
                    await progress(message, user, "good")
                if time_caught >= 0 and time_caught < 10:
                    await progress(message, user, "under10")
                if time_caught >= 0 and int(time_caught) % 2 == 0:
                    await progress(message, user, "even")
                if time_caught >= 0 and int(time_caught) % 2 == 1:
                    await progress(message, user, "odd")
                if channel.rattype and channel.rattype not in ["Fine", "Nice", "Good"]:
                    await progress(message, user, "rare+")
                if did_boost:
                    await progress(message, user, "prism")
                if user.ratch_quest == "finenice":
                    # 0 none
                    # 1 fine
                    # 2 nice
                    # 3 both
                    if channel.rattype == "Fine" and user.ratch_progress in [0, 2]:
                        await progress(message, user, "finenice")
                    elif channel.rattype == "Nice" and user.ratch_progress in [0, 1]:
                        await progress(message, user, "finenice")
                        await progress(message, user, "finenice")
            finally:
                await channel.save()
                if decided_time:
                    await asyncio.sleep(decided_time)
                    try:
                        temp_ratches_storage.remove(pls_remove_me_later_k_thanks)
                    except Exception:
                        pass
                    await spawn_rat(str(message.channel.id))
                else:
                    try:
                        temp_ratches_storage.remove(pls_remove_me_later_k_thanks)
                    except Exception:
                        pass

    if text.lower().startswith("rat!amount") and perms.send_messages and (not message.thread or perms.send_messages_in_threads):
        user, _ = await User.get_or_create(user_id=message.author.id)
        try:
            user.custom_num = int(text.split(" ")[1])
            await user.save()
            await message.reply("success")
        except Exception:
            await message.reply("invalid number")

    # only letting the owner of the bot access anything past this point
    if message.author.id != OWNER_ID:
        return

    # those are "owner" commands which are not really interesting
    if text.lower().startswith("rat!sweep"):
        try:
            channel = await Channel.get(channel_id=message.channel.id)
            channel.rat = 0
            await channel.save()
            await message.reply("success")
        except Exception:
            pass
    if text.lower().startswith("rat!rain"):
        # syntax: rat!rain 553093932012011520 short
        things = text.split(" ")
        user, _ = await User.get_or_create(user_id=things[1])
        if not user.rain_minutes:
            user.rain_minutes = 0
        if things[2] == "short":
            user.rain_minutes += 2
        elif things[2] == "medium":
            user.rain_minutes += 10
        elif things[2] == "long":
            user.rain_minutes += 20
        else:
            user.rain_minutes += int(things[2])
        user.premium = True
        await user.save()
    if text.lower().startswith("rat!restart"):
        await message.reply("restarting!")
        os.system("git pull")
        if config.WEBHOOK_VERIFY:
            await vote_server.cleanup()
        await bot.rat_bot_reload_hook("db" in text)  # pyright: ignore
    if text.lower().startswith("rat!print"):
        # just a simple one-line with no async (e.g. 2+3)
        try:
            await message.reply(eval(text[9:]))
        except Exception:
            try:
                await message.reply(traceback.format_exc())
            except Exception:
                pass
    if text.lower().startswith("rat!eval"):
        # complex eval, multi-line + async support
        # requires the full `await message.channel.send(2+3)` to get the result

        # async def go():
        #  <stuff goes here>
        #
        # try:
        #  bot.loop.create_task(go())
        # except Exception:
        #  await message.reply(traceback.format_exc())

        silly_billy = text[9:]

        spaced = ""
        for i in silly_billy.split("\n"):
            spaced += "  " + i + "\n"

        intro = "async def go(message, bot):\n try:\n"
        ending = "\n except Exception:\n  await message.reply(traceback.format_exc())\nbot.loop.create_task(go(message, bot))"

        complete = intro + spaced + ending
        exec(complete)
    if text.lower().startswith("rat!news"):
        async for i in Channel.all():
            try:
                channeley = bot.get_channel(int(i.channel_id))
                if not isinstance(
                    channeley,
                    Union[
                        discord.TextChannel,
                        discord.StageChannel,
                        discord.VoiceChannel,
                        discord.Thread,
                    ],
                ):
                    continue
                if perms.send_messages and (not message.thread or perms.send_messages_in_threads):
                    await channeley.send(text[8:])
            except Exception:
                pass
    if text.lower().startswith("rat!custom"):
        stuff = text.split(" ")
        if stuff[1][0] not in "1234567890":
            stuff.insert(1, message.channel.owner_id)
        user, _ = await User.get_or_create(user_id=stuff[1])
        rat_name = " ".join(stuff[2:])
        if stuff[2] != "None" and message.reference and message.reference.message_id:
            emoji_name = re.sub(r"[^a-zA-Z0-9]", "", rat_name).lower() + "rat"
            if emoji_name in emojis.keys():
                await message.reply("emoji already exists")
                return
            og_msg = await message.channel.fetch_message(message.reference.message_id)
            if not og_msg or len(og_msg.attachments) == 0:
                await message.reply("no image found")
                return
            img_data = await og_msg.attachments[0].read()

            if og_msg.attachments[0].content_type.startswith("image/gif"):
                await bot.create_appliration_emoji(name=emoji_name, image=img_data)
            else:
                img = Image.open(io.BytesIO(img_data))
                img.thumbnail((128, 128))
                with io.BytesIO() as image_binary:
                    img.save(image_binary, format="PNG")
                    image_binary.seek(0)
                    await bot.create_appliration_emoji(name=emoji_name, image=image_binary.getvalue())
        user.custom = rat_name if rat_name != "None" else ""
        emojis = {emoji.name: str(emoji) for emoji in await bot.fetch_appliration_emojis()}
        await user.save()
        await message.reply("success")


# the message when rat gets added to a new server
async def on_guild_join(guild):
    def verify(ch):
        return ch and ch.permissions_for(guild.me).send_messages

    def find(patt, channels):
        for i in channels:
            if patt in i.name:
                return i

    # first to try a good channel, then whenever we rat atleast chat
    ch = find("rat", guild.text_channels)
    if not verify(ch):
        ch = find("bot", guild.text_channels)
    if not verify(ch):
        ch = find("commands", guild.text_channels)
    if not verify(ch):
        ch = find("general", guild.text_channels)

    found = False
    if not verify(ch):
        for ch in guild.text_channels:
            if verify(ch):
                found = True
                break
        if not found:
            ch = guild.owner

    # you are free to change/remove this, its just a note for general user letting them know
    unofficial_note = "**NOTE: This is an unofficial Rat Bot instance.**\n\n"
    if not bot.user or bot.user.id == 966695034340663367:
        unofficial_note = ""
    try:
        if ch.permissions_for(guild.me).send_messages:
            await ch.send(
                unofficial_note
                + "Thanks for adding me!\nTo start, use `/setup` and `/help` to learn more!\nJoin the support server here: https://discord.gg/staring\nHave a nice day :)"
            )
    except Exception:
        pass


@bot.tree.command(description="Learn to use the bot")
async def help(message):
    embed1 = discord.Embed(
        title="How to Setup",
        description="Server moderator (anyone with *Manage Server* permission) needs to run `/setup` in any channel. After that, rats will start to spawn in 2-20 minute intervals inside of that channel.\nYou can customize those intervals with `/changetimings` and change the spawn message with `/changemessage`.\nRat spawns can also be forced by moderators using `/forcespawn` command.\nYou can have unlimited amounts of setupped channels at once.\nYou can stop the spawning in a channel by running `/forget`.",
        color=0x6E593C,
    ).set_thumbnail(url="https://wsrv.nl/?url=raw.githubusercontent.com/milenakos/rat-bot/main/images/rat.png")

    embed2 = (
        discord.Embed(title="How to Play", color=0x6E593C)
        .add_field(
            name="Ratch Rats",
            value='Whenever a rat spawns you will see a message along the lines of "a rat has appeared", which will also display it\'s type.\nRat types can have varying rarities from 25% for Fine to hundredths of percent for rarest types.\nSo, after saying "rat" the rat will be added to your inventory.',
            inline=False,
        )
        .add_field(
            name="Viewing Your Inventory",
            value="You can view your (or anyone elses!) inventory using `/inventory` command. It will display all the rats, along with other stats.\nIt is important to note that you have a separate inventory in each server and nothing carries over, to make the experience more fair and fun.\nCheck out the leaderboards for your server by using `/leaderboards` command.\nIf you want to transfer rats, you can use the simple `/gift` or more complex `/trade` commands.",
            inline=False,
        )
        .add_field(
            name="Let's get funky!",
            value='Rat Bot has various other mechanics to make fun funnier. You can collect various `/achievements`, for example saying "i read help", progress in the `/battlepass`, or have beef with the mafia over rataine addiction. The amount you worship is the limit!',
            inline=False,
        )
        .add_field(
            name="Other features",
            value="Rat Bot has extra fun commands which you will discover along the way.\nAnything unclear? Check out [our wiki](https://wiki.minkos.lol) or drop us a line at our [Discord server](https://discord.gg/staring).",
            inline=False,
        )
        .set_footer(
            text=f"Rat Bot by Milenakos, {datetime.datetime.utcnow().year}",
            icon_url="https://wsrv.nl/?url=raw.githubusercontent.com/milenakos/rat-bot/main/images/rat.png",
        )
    )

    await message.response.send_message(embeds=[embed1, embed2])


@bot.tree.command(description="Roll the credits")
async def credits(message: discord.Interaction):
    global gen_credits

    if not gen_credits:
        await message.response.send_message(
            "credits not yet ready! this is a very rare error, congrats.",
            ephemeral=True,
        )
        return

    await message.response.defer()

    embedVar = discord.Embed(title="Rat Bot", color=0x6E593C, description=gen_credits).set_thumbnail(
        url="https://wsrv.nl/?url=raw.githubusercontent.com/milenakos/rat-bot/main/images/rat.png"
    )

    await message.followup.send(embed=embedVar)


def format_timedelta(start_timestamp, end_timestamp):
    delta = datetime.timedelta(seconds=end_timestamp - start_timestamp)
    days = delta.days
    seconds = delta.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{days}d {hours}h {minutes}m {seconds}s"


@bot.tree.command(description="View various bot information and stats")
async def info(message: discord.Interaction):
    embed = discord.Embed(title="Rat Bot Info", color=0x6E593C)
    try:
        git_timestamp = int(subprocess.check_output(["git", "show", "-s", "--format=%ct"]).decode("utf-8"))
    except Exception:
        git_timestamp = 0

    embed.description = f"""
Python Version: `{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}`
discord.py Version: `{discord.__version__}`
OS Version: `{platform.system()} {platform.release()}`
Full uptime: `{format_timedelta(config.HARD_RESTART_TIME, time.time())}`
Soft uptime: `{format_timedelta(config.SOFT_RESTART_TIME, time.time())}`
Last code update: `{format_timedelta(git_timestamp, time.time()) if git_timestamp else "N/A"}`
Guilds: `{len(bot.guilds):,}`
Loops since last restart: `{loop_count + 1}`
"""

    await message.response.send_message(embed=embed)


@bot.tree.command(description="Confused? Check out the Rat Bot Wiki!")
async def wiki(message: discord.Interaction):
    embed = discord.Embed(title="Rat Bot Wiki", color=0x6E593C)
    embed.description = "\n".join(
        [
            "Main Page: https://wiki.minkos.lol/",
            "",
            "[Rat Bot](https://wiki.minkos.lol/rat-bot)",
            "[Rat Spawning](https://wiki.minkos.lol/spawning)",
            "[Commands](https://wiki.minkos.lol/commands)",
            "[Rat Types](https://wiki.minkos.lol/rat-types)",
            "[Rattlepass](https://wiki.minkos.lol/rattlepass)",
            "[Achievements](https://wiki.minkos.lol/achievements)",
            "[Packs](https://wiki.minkos.lol/packs)",
            "[Trading](https://wiki.minkos.lol/trading)",
            "[Gambling](https://wiki.minkos.lol/gambling)",
            "[The Dark Market](https://wiki.minkos.lol/dark-market)",
            "[Prisms](https://wiki.minkos.lol/prisms)",
        ]
    )
    await message.response.send_message(embed=embed)
    profile, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=message.user.id)
    await progress(message, profile, "wiki")


@bot.tree.command(description="Read The Rat Bot Times™️")
async def news(message: discord.Interaction):
    user, _ = await User.get_or_create(user_id=message.user.id)
    buttons = []
    current_state = user.news_state.strip()

    async def regen_buttons():
        nonlocal buttons
        user, _ = await User.get_or_create(user_id=message.user.id)
        buttons = []
        current_state = user.news_state.strip()
        for num, article in enumerate(news_list):
            try:
                have_read_this = current_state[num] != "0"
            except Exception:
                have_read_this = False
            button = Button(
                label=article["title"],
                emoji=get_emoji(article["emoji"]),
                custom_id=f"{num} {message.user.id}",
                style=ButtonStyle.green if not have_read_this else ButtonStyle.gray,
            )
            button.callback = send_news
            buttons.append(button)
        buttons = buttons[::-1]  # reverse the list so the first button is the most recent article

    await regen_buttons()

    if len(news_list) > len(current_state):
        user.news_state = current_state + "0" * (len(news_list) - len(current_state))
        await user.save()

    current_page = 0

    async def prev_page(interaction):
        nonlocal current_page
        if interaction.user.id != message.user.id:
            await do_funny(interaction)
            return
        current_page -= 1
        await interaction.response.edit_message(view=generate_page(current_page))

    async def next_page(interaction):
        nonlocal current_page
        if interaction.user.id != message.user.id:
            await do_funny(interaction)
            return
        current_page += 1
        await interaction.response.edit_message(view=generate_page(current_page))

    async def mark_all_as_read(interaction):
        if interaction.user.id != message.user.id:
            await do_funny(interaction)
            return
        user, _ = await User.get_or_create(user_id=message.user.id)
        user.news_state = "1" * len(news_list)
        await user.save()
        await regen_buttons()
        await interaction.response.edit_message(view=generate_page(current_page))

    def generate_page(number):
        view = View(timeout=VIEW_TIMEOUT)

        # article buttons
        for num, button in enumerate(buttons[number * 4 : (number + 1) * 4]):
            button.row = num
            view.add_item(button)

        # pages buttons
        if current_page > 0:
            button = Button(label="Back", row=4)
            button.callback = prev_page
            view.add_item(button)

        button = Button(
            label="Mark all as read",
            row=4,
        )
        button.callback = mark_all_as_read
        view.add_item(button)

        if current_page == 0:
            button = Button(
                label="Archive",
                row=4,
            )
            button.callback = next_page
            view.add_item(button)

        return view

    await message.response.send_message("Choose an article:", view=generate_page(current_page))
    await achemb(message, "news", "send")


@bot.tree.command(description="Read text as TikTok's TTS woman")
@discord.app_commands.describe(text="The text to be read! (300 characters max)")
async def tiktok(message: discord.Interaction, text: str):
    perms = await fetch_perms(message)
    if not perms.attach_files:
        await message.response.send_message("i cant attach files here!", ephemeral=True)
        return

    # detect n-words
    for i in NONOWORDS:
        if i in text.lower():
            await message.response.send_message("Do not.", ephemeral=True)
            return

    await message.response.defer()
    profile, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=message.user.id)

    if text == "bwomp":
        file = discord.File("bwomp.mp3", filename="bwomp.mp3")
        await message.followup.send(file=file)
        await achemb(message, "bwomp", "send")
        await progress(message, profile, "tiktok")
        return

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                "https://tiktok-tts.printmechanicalbeltpumpkingutter.workers.dev/api/generation",
                json={"text": text, "voice": "en_us_001"},
                headers={"User-Agent": "RatBot/1.0 https://github.com/milenakos/rat-bot"},
            ) as response:
                stuff = await response.json()
                with io.BytesIO() as f:
                    ba = "data:audio/mpeg;base64," + stuff["audio"]
                    f.write(base64.b64decode(ba))
                    f.seek(0)
                    await message.followup.send(file=discord.File(fp=f, filename="output.mp3"))
        except discord.NotFound:
            pass
        except Exception:
            await message.followup.send("i dont speak guacamole (remove non-english characters, make sure the message is below 300 characters)")

    await progress(message, profile, "tiktok")


@bot.tree.command(description="(ADMIN) Prevent someone from ratching rats for a certain time period")
@discord.app_commands.default_permissions(manage_guild=True)
@discord.app_commands.describe(person="A person to timeout!", timeout="How many seconds? (0 to reset)")
async def preventratch(message: discord.Interaction, person: discord.User, timeout: int):
    if timeout < 0:
        await message.response.send_message("uhh i think time is supposed to be a number", ephemeral=True)
        return
    user, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=person.id)
    timestamp = round(time.time()) + timeout
    user.timeout = timestamp
    await user.save()
    await message.response.send_message(
        person.name.replace("_", r"\_") + (f" can't ratch rats until <t:{timestamp}:R>" if timeout > 0 else " can now ratch rats again.")
    )


@bot.tree.command(description="(ADMIN) Change the rat appear timings")
@discord.app_commands.default_permissions(manage_guild=True)
@discord.app_commands.describe(
    minimum_time="In seconds, minimum possible time between spawns (leave both empty to reset)",
    maximum_time="In seconds, maximum possible time between spawns (leave both empty to reset)",
)
async def changetimings(
    message: discord.Interaction,
    minimum_time: Optional[int],
    maximum_time: Optional[int],
):
    channel = await Channel.get_or_none(channel_id=message.channel.id)
    if not channel:
        await message.response.send_message("This channel isnt setupped. Please select a valid channel.", ephemeral=True)
        return

    if not minimum_time and not maximum_time:
        # reset
        channel.spawn_times_min = 120
        channel.spawn_times_max = 1200
        await channel.save()
        await message.response.send_message("Success! This channel is now reset back to usual spawning intervals.")
    elif minimum_time and maximum_time:
        if minimum_time < 20:
            await message.response.send_message("Sorry, but minimum time must be above 20 seconds.", ephemeral=True)
            return
        if maximum_time < minimum_time:
            await message.response.send_message(
                "Sorry, but maximum time must not be less than minimum time.",
                ephemeral=True,
            )
            return

        channel.spawn_times_min = minimum_time
        channel.spawn_times_max = maximum_time
        await channel.save()

        await message.response.send_message(
            f"Success! The spawn times are now {minimum_time} to {maximum_time} seconds. Please note the changes will only apply after the next spawn."
        )
    else:
        await message.response.send_message("Please input all times.", ephemeral=True)


@bot.tree.command(description="(ADMIN) Change the rat appear and cought messages")
@discord.app_commands.default_permissions(manage_guild=True)
async def changemessage(message: discord.Interaction):
    caller = message.user
    channel = await Channel.get_or_none(channel_id=message.channel.id)
    if not channel:
        await message.response.send_message("pls setup this channel first", ephemeral=True)
        return

    # this is the silly popup when you click the button
    class InputModal(discord.ui.Modal):
        def __init__(self, type):
            super().__init__(
                title=f"Change {type} Message",
                timeout=3600,
            )

            self.type = type

            self.input = discord.ui.TextInput(
                min_length=0,
                max_length=1000,
                label="Input",
                style=discord.TextStyle.long,
                required=False,
                placeholder='{emoji} {type} has appeared! Type "rat" to ratch it!',
                default=channel.appear if self.type == "Appear" else channel.cought,
            )
            self.add_item(self.input)

        async def on_submit(self, interaction: discord.Interaction):
            channel = await Channel.get_or_none(channel_id=message.channel.id)
            if not channel:
                await message.response.send_message("this channel is not /setup-ed", ephemeral=True)
                return
            input_value = self.input.value

            # check if all placeholders are there
            if input_value != "":
                check = ["{emoji}", "{type}"] + (["{username}", "{count}", "{time}"] if self.type == "Cought" else [])

                for i in check:
                    if i not in input_value:
                        await interaction.response.send_message(f"nuh uh! you are missing `{i}`.", ephemeral=True)
                        return
                    elif input_value.count(i) > 10:
                        await interaction.response.send_message(f"nuh uh! you are using too much of `{i}`.", ephemeral=True)
                        return

                # check there are no emojis as to not break ratching
                for i in allowedemojis:
                    if i in input_value:
                        await interaction.response.send_message(f"nuh uh! you cant use `{i}`. sorry!", ephemeral=True)
                        return

                icon = get_emoji("finerat")
                await interaction.response.send_message(
                    "Success! Here is a preview:\n"
                    + input_value.replace("{emoji}", str(icon))
                    .replace("{type}", "Fine")
                    .replace("{username}", "Rat Bot")
                    .replace("{count}", "1")
                    .replace("{time}", "69 years 420 days")
                )
            else:
                await interaction.response.send_message("Reset to defaults.")

            if self.type == "Appear":
                channel.appear = input_value
            else:
                channel.cought = input_value

            await channel.save()

    # helper to make the above popup appear
    async def ask_appear(interaction):
        nonlocal caller

        if interaction.user != caller:
            await do_funny(interaction)
            return

        modal = InputModal("Appear")
        await interaction.response.send_modal(modal)

    async def ask_ratch(interaction):
        nonlocal caller

        if interaction.user != caller:
            await do_funny(interaction)
            return

        modal = InputModal("Cought")
        await interaction.response.send_modal(modal)

    embed = discord.Embed(
        title="Change appear and cought messages",
        description="""below are buttons to change them.
they are required to have all placeholders somewhere in them.
you must include the placeholders exactly like they are shown below, the values will be replaced by rat bot when it uses them.
that being:

for appear:
`{emoji}`, `{type}`

for cought:
`{emoji}`, `{type}`, `{username}`, `{count}`, `{time}`

missing any of these will result in a failure.
how to do mentions: `@everyone`, `@here`, `<@userid>`, `<@&roleid>`
to get ids, run `/getid` with the thing you want to mention.
if it doesnt work make sure the bot has mention permissions.
leave blank to reset.""",
        color=0x6E593C,
    )

    button1 = Button(label="Appear Message", style=ButtonStyle.blurple)
    button1.callback = ask_appear

    button2 = Button(label="Ratch Message", style=ButtonStyle.blurple)
    button2.callback = ask_ratch

    view = View(timeout=VIEW_TIMEOUT)
    view.add_item(button1)
    view.add_item(button2)

    await message.response.send_message(embed=embed, view=view)


@bot.tree.command(description="Get ID of a thing")
async def getid(message: discord.Interaction, thing: discord.User | discord.Role):
    await message.response.send_message(f"The ID of {thing.mention} is {thing.id}\nyou can use it in /changemessage like this: `{thing.mention}`")


@bot.tree.command(description="Get Daily rats")
async def daily(message: discord.Interaction):
    await message.response.send_message("there is no daily rats why did you even try this")
    await achemb(message, "daily", "send")


@bot.tree.command(description="View when the last rat was caught in this channel, and when the next one might spawn")
async def last(message: discord.Interaction):
    channel = await Channel.get_or_none(channel_id=message.channel.id)
    nextpossible = ""

    try:
        lasttime = channel.lastratches
        displayedtime = f"<t:{int(lasttime)}:R>"
    except Exception:
        displayedtime = "forever ago"

    if channel and not channel.rat:
        times = [channel.spawn_times_min, channel.spawn_times_max]
        nextpossible = f"\nthe next rat will spawn between <t:{int(lasttime) + times[0]}:R> and <t:{int(lasttime) + times[1]}:R>"

    await message.response.send_message(f"the last rat in this channel was caught {displayedtime}.{nextpossible}")


@bot.tree.command(description="View all the juicy numbers behind rat types")
async def ratalogue(message: discord.Interaction):
    embed = discord.Embed(title=f"{get_emoji('staring_rat')} The Ratalogue", color=0x6E593C)
    for rat_type in rattypes:
        in_server = (
            await Profile.filter(guild_id=message.guild.id, **{f"rat_{rat_type}__gt": 0}).annotate(total=Sum(f"rat_{rat_type}")).values_list("total", flat=True)
        )[0]
        title = f"{get_emoji(rat_type.lower() + 'rat')} {rat_type}"
        if in_server == 0 or not in_server:
            in_server = 0
            title = f"{get_emoji('mysteryrat')} ???"

        title += f" ({round((type_dict[rat_type] / sum(type_dict.values())) * 100, 2)}%)"

        embed.add_field(
            name=title,
            value=f"{round(sum(type_dict.values()) / type_dict[rat_type], 2)} value\n{in_server:,} in this server",
        )

    await message.response.send_message(embed=embed)


async def gen_stats(profile, star):
    stats = []
    user, _ = await User.get_or_create(user_id=profile.user_id)

    # ratching
    stats.append([get_emoji("staring_rat"), "Ratching"])
    stats.append(["ratches", "🐈", f"Ratches: {profile.total_ratches:,}{star}"])
    ratch_time = "---" if profile.time >= 99999999999999 else round(profile.time, 3)
    slow_time = "---" if profile.timeslow == 0 else round(profile.timeslow / 3600, 2)
    stats.append(["time_records", "⏱️", f"Fastest: {ratch_time}s, Slowest: {slow_time}h"])
    if profile.total_ratches - profile.rain_participations != 0:
        stats.append(
            ["average_time", "⏱️", f"Average ratch time: {profile.total_ratch_time / (profile.total_ratches - profile.rain_participations):,.2f}s{star}"]
        )
    else:
        stats.append(["average_time", "⏱️", f"Average ratch time: N/A{star}"])
    stats.append(["purrfect_ratches", "✨", f"Purrfect ratches: {profile.perfection_count:,}{star}"])

    # ratching boosts
    stats.append([get_emoji("prism"), "Boosts"])
    prisms_crafted = await Prism.filter(guild_id=profile.guild_id, creator=profile.user_id).count()
    boosts_done = (
        await Prism.filter(guild_id=profile.guild_id, user_id=profile.user_id).annotate(total=Sum("ratches_boosted")).values_list("total", flat=True)
    )[0] or 0
    stats.append(["prism_crafted", get_emoji("prism"), f"Prisms crafted: {prisms_crafted:,}"])
    stats.append(["boosts_done", get_emoji("prism"), f"Boosts by owned prisms: {boosts_done:,}{star}"])
    stats.append(["boosted_ratches", get_emoji("prism"), f"Prism-boosted ratches: {profile.boosted_ratches:,}{star}"])
    stats.append(["rataine_activations", "🧂", f"Rataine activations: {profile.rataine_activations:,}"])
    stats.append(["rataine_bought", "🧂", f"Rataine bought: {profile.rataine_bought:,}"])

    # voting
    stats.append([get_emoji("topgg"), "Voting"])
    stats.append(["total_votes", get_emoji("topgg"), f"Total votes: {user.total_votes:,}{star}"])
    stats.append(["current_vote_streak", "🔥", f"Current vote streak: {user.vote_streak} (max {max(user.vote_streak, user.max_vote_streak):,}){star}"])
    if user.vote_time_topgg + 43200 > time.time():
        stats.append(["can_vote", get_emoji("topgg"), f"Can vote <t:{user.vote_time_topgg + 43200}:R>"])
    else:
        stats.append(["can_vote", get_emoji("topgg"), "Can vote!"])

    # battlepass
    stats.append(["⬆️", "Rattlepass"])
    seasons_complete = 0
    levels_complete = 0
    max_level = 0
    total_xp = 0
    # past seasons
    for season in profile.bp_history.split(";"):
        if not season:
            break
        season_num, season_lvl, season_progress = map(int, season.split(","))
        if season_num == 0:
            continue
        levels_complete += season_lvl
        total_xp += season_progress
        if season_lvl > 30:
            seasons_complete += 1
            total_xp += 1500 * (season_lvl - 31)
        if season_lvl > max_level:
            max_level = season_lvl

        for num, level in enumerate(battle["seasons"][str(season_num)]):
            if num >= season_lvl:
                break
            total_xp += level["xp"]
    # current season
    if profile.season != 0:
        levels_complete += profile.battlepass
        total_xp += profile.progress
        if profile.battlepass > 30:
            seasons_complete += 1
            total_xp += 1500 * (profile.battlepass - 31)
        if profile.battlepass > max_level:
            max_level = profile.battlepass

        for num, level in enumerate(battle["seasons"][str(profile.season)]):
            if num >= profile.battlepass:
                break
            total_xp += level["xp"]
    current_packs = 0
    for pack in pack_data:
        current_packs += profile[f"pack_{pack['name'].lower()}"]
    stats.append(["quests_completed", "✅", f"Quests completed: {profile.quests_completed:,}{star}"])
    stats.append(["seasons_completed", "🏅", f"Rattlepass seasons completed: {seasons_complete:,}"])
    stats.append(["levels_completed", "✅", f"Rattlepass levels completed: {levels_complete:,}"])
    stats.append(["packs_in_inventory", get_emoji("woodenpack"), f"Packs in inventory: {current_packs:,}"])
    stats.append(["packs_opened", get_emoji("goldpack"), f"Packs opened: {profile.packs_opened:,}"])
    stats.append(["pack_upgrades", get_emoji("diamondpack"), f"Pack upgrades: {profile.pack_upgrades:,}"])
    stats.append(["highest_ever_level", "🏆", f"Highest ever Rattlepass level: {max_level:,}"])
    stats.append(["total_xp_earned", "🧮", f"Total Rattlepass XP earned: {total_xp:,}"])

    # rains & supporter
    stats.append(["☔", "Rains"])
    stats.append(["current_rain_minutes", "☔", f"Current rain minutes: {user.rain_minutes:,}"])
    stats.append(["supporter", "👑", "Ever bought rains: " + ("Yes" if user.premium else "No")])
    stats.append(["rats_caught_during_rains", "☔", f"Rats caught during rains: {profile.rain_participations:,}{star}"])
    stats.append(["rain_minutes_started", "☔", f"Rain minutes started: {profile.rain_minutes_started:,}{star}"])

    # gambling
    stats.append(["🎰", "Gambling"])
    stats.append(["casino_spins", "🎰", f"Casino spins: {profile.gambles:,}"])
    stats.append(["slot_spins", "🎰", f"Slot spins: {profile.slot_spins:,}"])
    stats.append(["slot_wins", "🎰", f"Slot wins: {profile.slot_wins:,}"])
    stats.append(["slot_big_wins", "🎰", f"Slot big wins: {profile.slot_big_wins:,}"])

    # tic tac toe
    stats.append(["⭕", "Tic Tac Toe"])
    stats.append(["ttc_games", "⭕", f"Tic Tac Toe games played: {profile.ttt_played:,}"])
    stats.append(["ttc_wins", "⭕", f"Tic Tac Toe wins: {profile.ttt_won:,}"])
    stats.append(["ttc_draws", "⭕", f"Tic Tac Toe draws: {profile.ttt_draws:,}"])
    if profile.ttt_played != 0:
        stats.append(["ttc_win_rate", "⭕", f"Tic Tac Toe win rate: {(profile.ttt_won + profile.ttt_draws) / profile.ttt_played * 100:.2f}%"])
    else:
        stats.append(["ttc_win_rate", "⭕", "Tic Tac Toe win rate: 0%"])

    if (profile.guild_id, profile.user_id) not in temp_cookie_storage.keys():
        cookies = profile.cookies
    else:
        cookies = temp_cookie_storage[(profile.guild_id, profile.user_id)]
    # misc
    stats.append(["❓", "Misc"])
    stats.append(["facts_read", "🧐", f"Facts read: {profile.facts:,}"])
    stats.append(["cookies", "🍪", f"Cookies clicked: {cookies:,}"])
    stats.append(["private_embed_clicks", get_emoji("pointlaugh"), f"Private embed clicks: {profile.funny:,}"])
    stats.append(["reminders_set", "⏰", f"Reminders set: {profile.reminders_set:,}{star}"])
    stats.append(["rats_gifted", "🎁", f"Rats gifted: {profile.rats_gifted:,}{star}"])
    stats.append(["rats_received_as_gift", "🎁", f"Rats received as gift: {profile.rat_gifts_recieved:,}{star}"])
    stats.append(["trades_completed", "💱", f"Trades completed: {profile.trades_completed}{star}"])
    stats.append(["rats_traded", "💱", f"Rats traded: {profile.rats_traded:,}{star}"])
    if profile.user_id == 553093932012011520:
        stats.append(["owner", get_emoji("neorat"), "a cute ratgirl :3"])
    return stats


@bot.tree.command(name="stats", description="View some advanced stats")
@discord.app_commands.rename(person_id="user")
@discord.app_commands.describe(person_id="Person to view the stats of!")
async def stats_command(message: discord.Interaction, person_id: Optional[discord.User]):
    await message.response.defer()
    if not person_id:
        person_id = message.user
    profile, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=person_id.id)
    star = "*" if not profile.new_user else ""

    stats = await gen_stats(profile, star)
    stats_string = ""
    for stat in stats:
        if len(stat) == 2:
            # rategory
            stats_string += f"\n{stat[0]} __{stat[1]}__\n"
        elif len(stat) == 3:
            # stat
            stats_string += f"{stat[2]}\n"
    if star:
        stats_string += "\n\\*this stat is only tracked since February 2025"

    embedVar = discord.Embed(title=f"{person_id.name}'s Stats", color=0x6E593C, description=stats_string)
    await message.followup.send(embed=embedVar)


async def gen_inventory(message, person_id):
    # check if we are viewing our own inv or some other person
    if person_id is None:
        person_id = message.user
    me = bool(person_id == message.user)
    person, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=person_id.id)
    user, _ = await User.get_or_create(user_id=person_id.id)

    # around here we count aches
    unlocked = 0
    minus_achs = 0
    minus_achs_count = 0
    for k in ach_names:
        is_ach_hidden = ach_list[k]["rategory"] == "Hidden"
        if is_ach_hidden:
            minus_achs_count += 1
        if person[k]:
            if is_ach_hidden:
                minus_achs += 1
            else:
                unlocked += 1
    total_achs = len(ach_list) - minus_achs_count
    minus_achs = "" if minus_achs == 0 else f" + {minus_achs}"

    # count prism stuff
    prisms = await Prism.filter(guild_id=message.guild.id, user_id=person_id.id).values_list("name", flat=True)
    total_count = await Prism.filter(guild_id=message.guild.id).count()
    user_count = len(prisms)
    global_boost = 0.06 * math.log(2 * total_count + 1)
    prism_boost = round((global_boost + 0.03 * math.log(2 * user_count + 1)) * 100, 3)
    if len(prisms) == 0:
        prism_list = "None"
    elif len(prisms) <= 3:
        prism_list = ", ".join(prisms)
    else:
        prism_list = f"{prisms[0]}, {prisms[1]}, {len(prisms) - 2} more..."

    emoji_prefix = str(user.emoji) + " " if user.emoji else ""

    if user.color:
        color = user.color
    else:
        color = "#6E593C"

    await refresh_quests(person)
    try:
        needed_xp = battle["seasons"][str(person.season)][person.battlepass]["xp"]
    except Exception:
        needed_xp = 1500

    stats = await gen_stats(person, "")
    highlighted_stat = None
    for stat in stats:
        if stat[0] == person.highlighted_stat:
            highlighted_stat = stat
            break
    if not highlighted_stat:
        for stat in stats:
            if stat[0] == "time_records":
                highlighted_stat = stat
                break

    embedVar = discord.Embed(
        title=f"{emoji_prefix}{person_id.name.replace('_', r'\_')}",
        description=f"{highlighted_stat[1]} {highlighted_stat[2]}\n{get_emoji('ach')} Achievements: {unlocked}/{total_achs}{minus_achs}\n⬆️ Battlepass Level {person.battlepass} ({person.progress}/{needed_xp} XP)",
        color=discord.Colour.from_str(color),
    )

    debt = False
    give_collector = True
    total = 0
    valuenum = 0

    # for every rat
    rat_desc = ""
    for i in rattypes:
        icon = get_emoji(i.lower() + "rat")
        rat_num = person[f"rat_{i}"]
        if rat_num < 0:
            debt = True
        if rat_num != 0:
            total += rat_num
            valuenum += (sum(type_dict.values()) / type_dict[i]) * rat_num
            rat_desc += f"{icon} **{i}** {rat_num:,}\n"
        else:
            give_collector = False

    if user.custom:
        icon = get_emoji(re.sub(r"[^a-zA-Z0-9]", "", user.custom).lower() + "rat")
        rat_desc += f"{icon} **{user.custom}** {user.custom_num:,}"

    if len(rat_desc) == 0:
        rat_desc = f"u hav no rats {get_emoji('rat_cry')}"

    if embedVar.description:
        embedVar.description += f"\n{get_emoji('staring_rat')} Rats: {total:,}, Value: {round(valuenum):,}\n{get_emoji('prism')} Prisms: {prism_list} ({prism_boost}%)\n\n{rat_desc}"

    if user.image.startswith("https://cdn.discordapp.com/attachments/"):
        embedVar.set_thumbnail(url=user.image)

    if me:
        # give some aches if we are vieweing our own inventory
        global_user, _ = await User.get_or_create(user_id=message.user.id)
        if len(news_list) > len(global_user.news_state.strip()) or "0" in global_user.news_state.strip()[-4:]:
            embedVar.set_author(name="You have unread news! /news")

        if give_collector:
            await achemb(message, "collecter", "send")

        if person.time <= 5:
            await achemb(message, "fast_ratcher", "send")
        if person.timeslow >= 3600:
            await achemb(message, "slow_ratcher", "send")

        if total >= 100:
            await achemb(message, "second", "send")
        if total >= 1000:
            await achemb(message, "third", "send")
        if total >= 10000:
            await achemb(message, "fourth", "send")

        if unlocked >= 15:
            await achemb(message, "achiever", "send")

        if debt:
            bot.loop.create_task(debt_cutscene(message, person))

    return embedVar


@bot.tree.command(description="View your inventory")
@discord.app_commands.rename(person_id="user")
@discord.app_commands.describe(person_id="Person to view the inventory of!")
async def inventory(message: discord.Interaction, person_id: Optional[discord.User]):
    await message.response.defer()
    if not person_id:
        person_id = message.user
    person, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=person_id.id)
    user, _ = await User.get_or_create(user_id=message.user.id)
    stats = await gen_stats(person, "")

    async def edit_profile(interaction: discord.Interaction):
        if interaction.user.id != person_id.id:
            await do_funny(interaction)
            return

        def stat_select(rategory):
            options = [discord.SelectOption(emoji="⬅️", label="Back", value="back")]
            track = False
            for stat in stats:
                if len(stat) == 2:
                    track = bool(stat[1] == rategory)
                if len(stat) == 3 and track:
                    options.append(discord.SelectOption(value=stat[0], emoji=stat[1], label=stat[2]))

            select = discord.ui.Select(placeholder="Edit highlighted stat... (2/2)", options=options)

            async def select_callback(interaction: discord.Interaction):
                await interaction.response.defer()
                if select.values[0] == "back":
                    view = View(timeout=VIEW_TIMEOUT)
                    view.add_item(rategory_select())
                    await interaction.edit_original_response(view=view)
                else:
                    # update the stat
                    person, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=message.user.id)
                    person.highlighted_stat = select.values[0]
                    await person.save()
                    await interaction.edit_original_response(content="Highlighted stat updated!", embed=None, view=None)

            select.callback = select_callback
            return select

        def rategory_select():
            options = []
            for stat in stats:
                if len(stat) != 2:
                    continue
                options.append(discord.SelectOption(emoji=stat[0], label=stat[1], value=stat[1]))

            select = discord.ui.Select(placeholder="Edit highlighted stat... (1/2)", options=options)

            async def select_callback(interaction: discord.Interaction):
                # im 13 and this is deep (nesting)
                # and also please dont think about the fact this is async inside of sync :3
                await interaction.response.defer()
                view = View(timeout=VIEW_TIMEOUT)
                view.add_item(stat_select(select.values[0]))
                await interaction.edit_original_response(view=view)

            select.callback = select_callback
            return select

        highlighted_stat = None
        for stat in stats:
            if stat[0] == person.highlighted_stat:
                highlighted_stat = stat
                break
        if not highlighted_stat:
            for stat in stats:
                if stat[0] == "time_records":
                    highlighted_stat = stat
                    break

        view = View(timeout=VIEW_TIMEOUT)
        view.add_item(rategory_select())

        if user.premium:
            if not user.color:
                user.color = "#6E593C"
            description = f"""👑 __Supporter Settings__
Global, change with `/editprofile`.
**Color**: {user.color.lower() if user.color.upper() not in ["", "#6E593C"] else "Default"}
**Emoji**: {user.emoji if user.emoji else "None"}
**Image**: {"Yes" if user.image.startswith("https://cdn.discordapp.com/attachments/") else "No"}

__Highlighted Stat__
{highlighted_stat[1]} {highlighted_stat[2]}"""

            embed = discord.Embed(
                title=f"{(user.emoji + ' ') if user.emoji else ''}Edit Profile", description=description, color=discord.Colour.from_str(user.color)
            )
            if user.image.startswith("https://cdn.discordapp.com/attachments/"):
                embed.set_thumbnail(url=user.image)

        else:
            description = f"""👑 __Supporter Settings__
Global, buy anything from [the store](https://ratbot.shop) to unlock.
👑 **Color**
👑 **Emoji**
👑 **Image**

__Highlighted Stat__
{highlighted_stat[1]} {highlighted_stat[2]}"""

            embed = discord.Embed(title="Edit Profile", description=description, color=0x6E593C)

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    embedVar = await gen_inventory(message, person_id)

    embedVar.set_footer(text=rain_shill)

    if person_id.id == message.user.id:
        view = View(timeout=VIEW_TIMEOUT)
        btn = Button(emoji="📝", label="Edit", style=discord.ButtonStyle.blurple)
        btn.callback = edit_profile
        view.add_item(btn)
        await message.followup.send(embed=embedVar, view=view)
    else:
        await message.followup.send(embed=embedVar)


@bot.tree.command(description="its raining rats")
async def rain(message: discord.Interaction):
    user, _ = await User.get_or_create(user_id=message.user.id)

    if not user.rain_minutes:
        user.rain_minutes = 0
        await user.save()

    if not user.claimed_free_rain:
        user.rain_minutes += 2
        user.claimed_free_rain = True
        await user.save()

    # this is the silly popup when you click the button
    class RainModal(discord.ui.Modal):
        def __init__(self, type):
            super().__init__(
                title="Start a Rat Rain!",
                timeout=3600,
            )

            self.input = discord.ui.TextInput(
                min_length=1,
                max_length=2,
                label="Duration in minutes",
                style=discord.TextStyle.short,
                required=True,
                placeholder="2",
            )
            self.add_item(self.input)

        async def on_submit(self, interaction: discord.Interaction):
            try:
                duration = int(self.input.value)
            except Exception:
                await interaction.response.send_message("number pls", ephemeral=True)
                return
            await do_rain(interaction, duration)

    server_rains = ""
    profile, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=message.user.id)
    server_minutes = profile.rain_minutes
    if server_minutes > 0:
        server_rains = f" (+**{server_minutes}** bonus minutes)"

    embed = discord.Embed(
        title="☔ Rat Rains",
        description=f"""Rat Rains are power-ups which spawn rats instantly for a limited amounts of time in channel of your choice.

You can get those by buying them at our [store](<https://ratbot.shop>) or by winning them in an event.
This bot is developed by a single person so buying one would be very appreciated.
As a bonus, you will get access to /editprofile command!
Fastest times are not saved during rains.

You currently have **{user.rain_minutes}** minutes of rains{server_rains}.""",
        color=0x6E593C,
    )

    async def do_rain(interaction, rain_length):
        # i LOOOOVE checks
        user, _ = await User.get_or_create(user_id=interaction.user.id)
        profile, _ = await Profile.get_or_create(guild_id=interaction.guild.id, user_id=interaction.user.id)
        channel = await Channel.get_or_none(channel_id=interaction.channel.id)

        if not user.rain_minutes:
            user.rain_minutes = 0
            await user.save()

        if not user.claimed_free_rain:
            user.rain_minutes += 2
            user.claimed_free_rain = True
            await user.save()

        if about_to_stop:
            await interaction.response.send_message("the bot is about to stop. please try again later.", ephemeral=True)
            return

        if rain_length < 1 or rain_length > 60:
            await interaction.response.send_message("pls input a number 1-60", ephemeral=True)
            return

        if rain_length > user.rain_minutes + profile.rain_minutes:
            await interaction.response.send_message(
                "you dont have enough rain! buy some more [here](<https://ratbot.shop>)",
                ephemeral=True,
            )
            return

        if not channel:
            await interaction.response.send_message("please run this in a setupped channel.", ephemeral=True)
            return

        if channel.rat:
            await interaction.response.send_message("please ratch the rat in this channel first.", ephemeral=True)
            return

        if channel.rat_rains != 0 or message.channel.id in temp_rains_storage:
            await interaction.response.send_message("there is already a rain running!", ephemeral=True)
            return

        channel_permissions = await fetch_perms(message)
        needed_perms = {
            "View Channel": channel_permissions.view_channel,
            "Send Messages": channel_permissions.send_messages,
            "Attach Files": channel_permissions.attach_files,
        }
        if isinstance(message.channel, discord.Thread):
            needed_perms["Send Messages in Threads"] = channel_permissions.send_messages_in_threads

        for name, value in needed_perms.copy().items():
            if value:
                needed_perms.pop(name)

        missing_perms = list(needed_perms.keys())
        if len(missing_perms) != 0:
            needed_perms = "\n- ".join(missing_perms)
            await interaction.response.send_message(
                f":x: Missing Permissions! Please give me the following:\n- {needed_perms}\nHint: try setting channel permissions if server ones don't work."
            )
            return

        if not isinstance(
            message.channel,
            Union[
                discord.TextChannel,
                discord.StageChannel,
                discord.VoiceChannel,
                discord.Thread,
            ],
        ):
            return

        profile.rain_minutes_started += rain_length
        channel.rat_rains = time.time() + (rain_length * 60)
        channel.yet_to_spawn = 0
        await channel.save()
        await spawn_rat(str(message.channel.id))
        if profile.rain_minutes:
            if rain_length > profile.rain_minutes:
                user.rain_minutes -= rain_length - profile.rain_minutes
                profile.rain_minutes = 0
            else:
                profile.rain_minutes -= rain_length
        else:
            user.rain_minutes -= rain_length
        await user.save()
        await profile.save()
        await interaction.response.send_message(f"{rain_length}m rat rain was started by {interaction.user.mention}, ending <t:{int(channel.rat_rains)}:R>!")
        try:
            ch = bot.get_channel(config.RAIN_CHANNEL_ID)
            await ch.send(f"{interaction.user.id} started {rain_length}m rain in {interaction.channel.id} ({user.rain_minutes} left)")
        except Exception:
            pass

    async def rain_modal(interaction):
        modal = RainModal(interaction.user)
        await interaction.response.send_modal(modal)

    button = Button(label="Rain!", style=ButtonStyle.blurple)
    button.callback = rain_modal

    shopbutton = Button(
        emoji="🛒",
        label="Store",
        url="https://ratbot.shop",
    )

    view = View(timeout=VIEW_TIMEOUT)
    view.add_item(button)
    view.add_item(shopbutton)

    await message.response.send_message(embed=embed, view=view)


@bot.tree.command(description="Buy Rat Rains!")
async def store(message: discord.Interaction):
    await message.response.send_message("☔ Rat rains make rats spawn instantly! Make your server active, get more rats and have fun!\n<https://ratbot.shop>")


if config.DONOR_CHANNEL_ID:

    @bot.tree.command(description="[SUPPORTER] Customize your profile!")
    @discord.app_commands.rename(provided_emoji="emoji")
    @discord.app_commands.describe(
        color="Color for your profile in hex form (e.g. #6E593C)",
        provided_emoji="A default Discord emoji to show near your username.",
        image="A square image to show in top-right corner of your profile.",
    )
    async def editprofile(
        message: discord.Interaction,
        color: Optional[str],
        provided_emoji: Optional[str],
        image: Optional[discord.Attachment],
    ):
        if not config.DONOR_CHANNEL_ID:
            return

        user, _ = await User.get_or_create(user_id=message.user.id)
        if not user.premium:
            await message.response.send_message(
                "👑 This feature is supporter-only!\nBuy anything from Rat Bot Store to unlock profile customization!\n<https://ratbot.shop>"
            )
            return

        if provided_emoji and discord_emoji.to_discord(provided_emoji.strip(), get_all=False, put_colons=False):
            user.emoji = provided_emoji.strip()

        if color:
            match = re.search(r"^#(?:[0-9a-fA-F]{3}){1,2}$", color)
            if match:
                user.color = match.group(0)
        if image:
            # reupload image
            channeley = bot.get_channel(config.DONOR_CHANNEL_ID)
            file = await image.to_file()
            if not isinstance(
                channeley,
                Union[
                    discord.TextChannel,
                    discord.StageChannel,
                    discord.VoiceChannel,
                    discord.Thread,
                ],
            ):
                raise ValueError
            msg = await channeley.send(file=file)
            user.image = msg.attachments[0].url
        await user.save()
        embedVar = await gen_inventory(message, message.user)
        await message.response.send_message("Success! Here is a preview:", embed=embedVar)


@bot.tree.command(description="View and open packs")
async def packs(message: discord.Interaction):
    def gen_view(user):
        view = discord.ui.View(timeout=VIEW_TIMEOUT)
        empty = True
        for pack in pack_data:
            if user[f"pack_{pack['name'].lower()}"] < 1:
                continue
            empty = False
            amount = user[f"pack_{pack['name'].lower()}"]
            button = discord.ui.Button(
                emoji=get_emoji(pack["name"].lower() + "pack"),
                label=f"{pack['name']} ({amount})",
                style=ButtonStyle.blurple,
                custom_id=pack["name"],
            )
            button.callback = open_pack
            view.add_item(button)
        if empty:
            view.add_item(discord.ui.Button(label="No packs left!", disabled=True))
        return view

    async def open_pack(interaction: discord.Interaction):
        if interaction.user != message.user:
            await do_funny(interaction)
            return
        await interaction.response.defer()
        pack = interaction.data["custom_id"]
        user, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=message.user.id)
        if user[f"pack_{pack.lower()}"] < 1:
            return
        level = next((i for i, p in enumerate(pack_data) if p["name"] == pack), 0)
        reward_texts = []
        build_string = ""

        # bump rarity
        while random.randint(1, 100) <= pack_data[level]["upgrade"]:
            reward_texts.append(f"{get_emoji(pack_data[level]['name'].lower() + 'pack')} {pack_data[level]['name']}\n" + build_string)
            build_string = f"Upgraded from {get_emoji(pack_data[level]['name'].lower() + 'pack')} {pack_data[level]['name']}!\n" + build_string
            level += 1
            user.pack_upgrades += 1
        final_level = pack_data[level]
        reward_texts.append(f"{get_emoji(final_level['name'].lower() + 'pack')} {final_level['name']}\n" + build_string)

        # select rat type
        goal_value = final_level["value"]
        chosen_type = random.choice(rattypes)
        pre_rat_amount = goal_value / (sum(type_dict.values()) / type_dict[chosen_type])
        if pre_rat_amount % 1 > random.random():
            rat_amount = math.ceil(pre_rat_amount)
        else:
            rat_amount = math.floor(pre_rat_amount)
        if pre_rat_amount < 1:
            reward_texts.append(
                reward_texts[-1] + f"\n{round(pre_rat_amount * 100, 2)}% chance for a {get_emoji(chosen_type.lower() + 'rat')} {chosen_type} rat"
            )
            reward_texts.append(reward_texts[-1] + ".")
            reward_texts.append(reward_texts[-1] + ".")
            reward_texts.append(reward_texts[-1] + ".")
            if rat_amount == 1:
                # success
                reward_texts.append(reward_texts[-1] + "\n✅ Success!")
            else:
                # fail
                reward_texts.append(reward_texts[-1] + "\n❌ Fail!")
                chosen_type = "Fine"
                rat_amount = 1
        user[f"rat_{chosen_type}"] += rat_amount
        user.packs_opened += 1
        user[f"pack_{pack.lower()}"] -= 1
        await user.save()
        reward_texts.append(reward_texts[-1] + f"\nYou got {get_emoji(chosen_type.lower() + 'rat')} {rat_amount} {chosen_type} rats!")

        embed = discord.Embed(title=reward_texts[0], color=0x6E593C)
        await interaction.edit_original_response(embed=embed, view=None)
        for reward_text in reward_texts[1:]:
            await asyncio.sleep(1)
            things = reward_text.split("\n")
            embed = discord.Embed(title=things[0], description="\n".join(things[1:]), color=0x6E593C)
            await interaction.edit_original_response(embed=embed)
        await asyncio.sleep(1)
        await interaction.edit_original_response(view=gen_view(user))

    description = "Each pack starts at one of eight tiers of increasing value - Wooden, Stone, Bronze, Silver, Gold, Platinum, Diamond, or Celestial - and can repeatedly move up tiers with a 30% chance per upgrade. This means that even a pack starting at Wooden, through successive upgrades, can reach the Celestial tier.\n\nClick the buttons below to start opening packs!"
    embed = discord.Embed(title=f"{get_emoji('bronzepack')} Packs", description=description, color=0x6E593C)
    user, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=message.user.id)
    await message.response.send_message(embed=embed, view=gen_view(user))


@bot.tree.command(description="why would anyone think a rattlepass would be a good idea")
async def battlepass(message: discord.Interaction):
    current_mode = ""

    async def toggle_reminders(interaction: discord.Interaction):
        nonlocal current_mode
        if interaction.user.id != message.user.id:
            await do_funny(interaction)
            return
        await interaction.response.defer()
        user, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=message.user.id)
        if not user.reminders_enabled:
            try:
                await interaction.user.send(
                    f"You have enabled reminders in {interaction.guild.name}. You can disable them in the /battlepass command in that server or by saying `disable {interaction.guild.id}` here any time."
                )
            except Exception:
                await interaction.followup.send(
                    "Failed. Ensure you have DMs open by going to Server > Privacy Settings > Allow direct messages from server members."
                )
                return

        user.reminders_enabled = not user.reminders_enabled
        await user.save()

        view = View(timeout=VIEW_TIMEOUT)
        button = Button(emoji="🔄", label="Refresh", style=ButtonStyle.blurple)
        button.callback = gen_main
        view.add_item(button)

        if user.reminders_enabled:
            button = Button(emoji="🔕", style=ButtonStyle.blurple)
        else:
            button = Button(label="Enable Reminders", emoji="🔔", style=ButtonStyle.green)
        button.callback = toggle_reminders
        view.add_item(button)

        await interaction.followup.send(
            f"Reminders are now {'enabled' if user.reminders_enabled else 'disabled'}.",
            ephemeral=True,
        )
        await interaction.edit_original_response(view=view)

    async def gen_main(interaction, first=False):
        nonlocal current_mode
        if interaction.user.id != message.user.id:
            await do_funny(interaction)
            return
        await interaction.response.defer()
        current_mode = "Main"
        user, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=message.user.id)
        await refresh_quests(user)
        user, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=message.user.id)

        global_user, _ = await User.get_or_create(user_id=message.user.id)
        if global_user.vote_time_topgg + 12 * 3600 > time.time():
            await progress(message, user, "vote")
            user, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=message.user.id)
            global_user, _ = await User.get_or_create(user_id=message.user.id)

        # season end
        now = datetime.datetime.utcnow()

        if now.month == 12:
            next_month = datetime.datetime(now.year + 1, 1, 1)
        else:
            next_month = datetime.datetime(now.year, now.month + 1, 1)

        timestamp = int(time.mktime(next_month.timetuple()))

        description = f"Season ends <t:{timestamp}:R>\n\n"

        # vote
        streak_string = ""
        if global_user.vote_streak >= 5 and global_user.vote_time_topgg + 24 * 3600 > time.time():
            streak_string = f" (🔥 {global_user.vote_streak}x streak)"
        if user.vote_cooldown != 0:
            description += f"✅ ~~Vote on Top.gg~~\n - Refreshes <t:{int(user.vote_cooldown + 12 * 3600)}:R>{streak_string}\n"
        else:
            # inform double vote xp during weekends
            is_weekend = now.weekday() >= 4

            if is_weekend:
                description += "-# *Double Vote XP During Weekends*\n"

            description += f"{get_emoji('topgg')} [Vote on Top.gg](https://top.gg/bot/966695034340663367/vote)\n"

            if is_weekend:
                description += f" - Reward: ~~{user.vote_reward}~~ **{user.vote_reward * 2}** XP"
            else:
                description += f" - Reward: {user.vote_reward} XP"

            if global_user.vote_streak % 5 == 4 and global_user.vote_time_topgg + 24 * 3600 > time.time() and global_user.vote_streak != 4:
                description += f" + {get_emoji('goldpack')} 1 Gold pack"

            description += f"{streak_string}\n"

        # ratch
        ratch_quest = battle["quests"]["ratch"][user.ratch_quest]
        if user.ratch_cooldown != 0:
            description += f"✅ ~~{ratch_quest['title']}~~\n - Refreshes <t:{int(user.ratch_cooldown + 12 * 3600 if user.ratch_cooldown + 12 * 3600 < timestamp else timestamp)}:R>\n"
        else:
            progress_string = ""
            if ratch_quest["progress"] != 1:
                if user.ratch_quest == "finenice":
                    try:
                        real_progress = ["need both", "need Nice", "need Fine", "done"][user.ratch_progress]
                    except IndexError:
                        real_progress = "error"
                    progress_string = f" ({real_progress})"
                else:
                    progress_string = f" ({user.ratch_progress}/{ratch_quest['progress']})"
            description += f"{get_emoji(ratch_quest['emoji'])} {ratch_quest['title']}{progress_string}\n - Reward: {user.ratch_reward} XP\n"

        # misc
        misc_quest = battle["quests"]["misc"][user.misc_quest]
        if user.misc_cooldown != 0:
            description += f"✅ ~~{misc_quest['title']}~~\n - Refreshes <t:{int(user.misc_cooldown + 12 * 3600 if user.misc_cooldown + 12 * 3600 < timestamp else timestamp)}:R>\n\n"
        else:
            progress_string = ""
            if misc_quest["progress"] != 1:
                progress_string = f" ({user.misc_progress}/{misc_quest['progress']})"
            description += f"{get_emoji(misc_quest['emoji'])} {misc_quest['title']}{progress_string}\n - Reward: {user.misc_reward} XP\n\n"

        if user.battlepass >= len(battle["seasons"][str(user.season)]):
            description += f"**Extra Rewards** [{user.progress}/1500 XP]\n"
            colored = int(user.progress / 150)
            description += get_emoji("staring_square") * colored + "⬛" * (10 - colored) + "\nReward: " + get_emoji("stonepack") + " Stone pack\n\n"
        else:
            level_data = battle["seasons"][str(user.season)][user.battlepass]
            description += f"**Level {user.battlepass + 1}/30** [{user.progress}/{level_data['xp']} XP]\n"
            colored = int(user.progress / level_data["xp"] * 10)
            description += f"**{user.battlepass}** " + get_emoji("staring_square") * colored + "⬛" * (10 - colored) + f" **{user.battlepass + 1}**\n"

            if level_data["reward"] == "Rain":
                description += f"Reward: ☔ {level_data['amount']} minutes of rain\n\n"
            elif level_data["reward"] in rattypes:
                description += f"Reward: {get_emoji(level_data['reward'].lower() + 'rat')} {level_data['amount']} {level_data['reward']} rats\n\n"
            else:
                description += f"Reward: {get_emoji(level_data['reward'].lower() + 'pack')} {level_data['reward']} pack\n\n"

        # next reward
        levels = battle["seasons"][str(user.season)]
        for num, level_data in enumerate(levels):
            claimed_suffix = "_claimed" if num < user.battlepass else ""
            if level_data["reward"] == "Rain":
                description += get_emoji(str(level_data["amount"]) + "rain" + claimed_suffix)
            elif level_data["reward"] in rattypes:
                description += get_emoji(level_data["reward"].lower() + "rat" + claimed_suffix)
            else:
                description += get_emoji(level_data["reward"].lower() + "pack" + claimed_suffix)
            if num % 10 == 9:
                description += "\n"
        if user.battlepass >= len(battle["seasons"][str(user.season)]) - 1:
            description += f"*Extra:* {get_emoji('stonepack')} per 1500 XP"

        embedVar = discord.Embed(
            title=f"Rattlepass Season {user.season}",
            description=description,
            color=0x6E593C,
        ).set_footer(text=rain_shill)
        view = View(timeout=VIEW_TIMEOUT)

        button = Button(emoji="🔄", label="Refresh", style=ButtonStyle.blurple)
        button.callback = gen_main
        view.add_item(button)

        if user.reminders_enabled:
            button = Button(emoji="🔕", style=ButtonStyle.blurple)
        else:
            button = Button(label="Enable Reminders", emoji="🔔", style=ButtonStyle.green)
        button.callback = toggle_reminders
        view.add_item(button)

        if len(news_list) > len(global_user.news_state.strip()) or "0" in global_user.news_state.strip()[-4:]:
            embedVar.set_author(name="You have unread news! /news")

        if first:
            await interaction.followup.send(embed=embedVar, view=view)
        else:
            await interaction.edit_original_response(embed=embedVar, view=view)

    await gen_main(message, True)


@bot.tree.command(description="vote for rat bot")
async def vote(message: discord.Interaction):
    embed = discord.Embed(
        title="Vote for Rat Bot",
        color=0x6E593C,
        description="Vote for Rat Bot on top.gg!",
    )
    view = View(timeout=1)
    button = Button(label="Vote!", url="https://top.gg/bot/966695034340663367/vote", emoji=get_emoji("topgg"))
    view.add_item(button)
    await message.response.send_message(embed=embed, view=view)


@bot.tree.command(description="rat prisms are a special power up")
@discord.app_commands.describe(person="Person to view the prisms of")
async def prism(message: discord.Interaction, person: Optional[discord.User]):
    icon = get_emoji("prism")
    page_number = 0

    if not person:
        person_id = message.user
    else:
        person_id = person

    user_prisms = await Prism.filter(guild_id=message.guild.id, user_id=person_id.id)
    all_prisms = await Prism.filter(guild_id=message.guild.id)
    total_count = len(all_prisms)
    user_count = len(user_prisms)
    global_boost = 0.06 * math.log(2 * total_count + 1)
    user_boost = round((global_boost + 0.03 * math.log(2 * user_count + 1)) * 100, 3)
    prism_texts = []

    if person_id == message.user and user_count != 0:
        await achemb(message, "prism", "send")

    order_map = {name: index for index, name in enumerate(prism_names)}
    prisms = all_prisms if not person else user_prisms
    prisms.sort(key=lambda p: order_map.get(p.name, float("inf")))

    for prism in prisms:
        prism_texts.append(f"{icon} **{prism.name}** {f'Owner: <@{prism.user_id}>' if not person else ''}\n<@{prism.creator}> crafted <t:{prism.time}:D>")

    if len(prisms) == 0:
        prism_texts.append("No prisms found!")

    async def confirm_craft(interaction: discord.Interaction):
        await interaction.response.defer()
        user, _ = await Profile.get_or_create(guild_id=interaction.guild.id, user_id=interaction.user.id)

        # check we still can craft
        for i in rattypes:
            if user["rat_" + i] < 1:
                await interaction.followup.send("You don't have enough rats. Nice try though.", ephemeral=True)
                return

        if await Prism.filter(guild_id=interaction.guild.id).count() >= len(prism_names):
            await interaction.followup.send("This server has reached the prism limit.", ephemeral=True)
            return

        if not isinstance(
            message.channel,
            Union[
                discord.TextChannel,
                discord.VoiceChannel,
                discord.StageChannel,
                discord.Thread,
            ],
        ):
            return

        # determine the next name
        for selected_name in prism_names:
            if not await Prism.filter(guild_id=message.guild.id, name=selected_name).exists():
                break

        youngest_prism = await Prism.filter(guild_id=message.guild.id).order_by("-time").first()
        if youngest_prism:
            selected_time = max(round(time.time()), youngest_prism.time + 1)
        else:
            selected_time = round(time.time())

        # actually take away rats
        for i in rattypes:
            user["rat_" + i] -= 1
        await user.save()

        # create the prism
        await Prism.create(
            guild_id=interaction.guild.id,
            user_id=interaction.user.id,
            creator=interaction.user.id,
            time=selected_time,
            name=selected_name,
        )
        await message.followup.send(f"{icon} {interaction.user.mention} has created prism {selected_name}!")
        await achemb(interaction, "prism", "send")
        await achemb(interaction, "collecter", "send")

    async def craft_prism(interaction: discord.Interaction):
        user, _ = await Profile.get_or_create(guild_id=interaction.guild.id, user_id=interaction.user.id)

        found_rats = await rats_in_server(interaction.guild.id)
        missing_rats = []
        for i in rattypes:
            if user[f"rat_{i}"] > 0:
                continue
            if i in found_rats:
                missing_rats.append(get_emoji(i.lower() + "rat"))
            else:
                missing_rats.append(get_emoji("mysteryrat"))

        if len(missing_rats) == 0:
            view = View(timeout=VIEW_TIMEOUT)
            confirm_button = Button(label="Craft!", style=ButtonStyle.blurple, emoji=icon)
            confirm_button.callback = confirm_craft
            description = "The crafting recipe is __ONE of EVERY rat type__.\nContinue crafting?"
        else:
            view = View(timeout=VIEW_TIMEOUT)
            confirm_button = Button(label="Not enough rats!", style=ButtonStyle.red, disabled=True)
            description = "The crafting recipe is __ONE of EVERY rat type__.\nYou are missing " + "".join(missing_rats)

        view.add_item(confirm_button)
        await interaction.response.send_message(description, view=view, ephemeral=True)

    async def prev_page(interaction):
        nonlocal page_number
        page_number -= 1
        embed, view = gen_page()
        await interaction.response.edit_message(embed=embed, view=view)

    async def next_page(interaction):
        nonlocal page_number
        page_number += 1
        embed, view = gen_page()
        await interaction.response.edit_message(embed=embed, view=view)

    def gen_page():
        target = "" if not person else f"{person_id.name}'s"

        embed = discord.Embed(
            title=f"{icon} {target} Rat Prisms",
            color=0x6E593C,
            description="Prisms are a tradeable power-up which occasionally bumps rat rarity up by one. Each prism crafted gives everyone an increased chance to get upgraded, plus additional chance for prism owners.\n\n",
        ).set_footer(
            text=f"{total_count} Total Prisms | Global boost: {round(global_boost * 100, 3)}%\n{person_id.name}'s prisms | Owned: {user_count} | Personal boost: {user_boost}%"
        )

        embed.description += "\n".join(prism_texts[page_number * 26 : (page_number + 1) * 26])

        view = View(timeout=VIEW_TIMEOUT)

        craft_button = Button(label="Craft!", style=ButtonStyle.blurple, emoji=icon)
        craft_button.callback = craft_prism
        view.add_item(craft_button)

        prev_button = Button(label="<-", disabled=bool(page_number == 0))
        prev_button.callback = prev_page
        view.add_item(prev_button)

        next_button = Button(label="->", disabled=bool(page_number == (len(prism_texts) + 1) // 26))
        next_button.callback = next_page
        view.add_item(next_button)

        return embed, view

    embed, view = gen_page()
    await message.response.send_message(embed=embed, view=view)


@bot.tree.command(description="Pong")
async def ping(message: discord.Interaction):
    try:
        latency = round(bot.latency * 1000)
    except Exception:
        latency = "infinite"
    if latency == 0:
        # probably using gateway proxy, try fetching latency from metrics
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get("http://localhost:7878/metrics") as response:
                    data = await response.text()
                    total_latencies = 0
                    total_shards = 0
                    for line in data.split("\n"):
                        if line.startswith("gateway_shard_latency{shard="):
                            if "NaN" in line:
                                continue
                            try:
                                total_latencies += float(line.split(" ")[1])
                                total_shards += 1
                            except Exception:
                                pass
                    latency = round((total_latencies / total_shards) * 1000)
            except Exception:
                pass
    await message.response.send_message(f"🏓 rat has brain delay of {latency} ms {get_emoji('staring_rat')}")
    user, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=message.user.id)
    await progress(message, user, "ping")


@bot.tree.command(description="play a relaxing game of tic tac toe")
@discord.app_commands.describe(person="who do you want to play with? (choose Rat Bot for ai)")
async def tictactoe(message: discord.Interaction, person: discord.Member):
    # WOW this code is bad
    if person == message.user:
        await message.response.send_message("you can't play tic tac toe with yourself idiot", ephemeral=True)
        return
    if person != bot.user:
        current_turn = random.choice([message.user, person])
    else:
        current_turn = message.user
    board_state = ["", "", "", "", "", "", "", "", ""]

    def check_winner(board):
        # Check rows, columns, and diagonals for a winner
        winning_combinations = [
            (0, 1, 2),
            (3, 4, 5),
            (6, 7, 8),
            (0, 3, 6),
            (1, 4, 7),
            (2, 5, 8),
            (0, 4, 8),
            (2, 4, 6),
        ]

        for a, b, c in winning_combinations:
            if board[a] == board[b] == board[c] and board[a] != "":
                return board[a], True, [a, b, c]  # Return the winner and a flag indirating a win

        return None, False, []  # No winner

    def minimax(board, depth, is_maximizing):
        winner, has_winner, _ = check_winner(board)

        if has_winner:
            return (10 - depth) if winner == "O" else (depth - 10)
        elif "" not in board:
            return 0

        if is_maximizing:
            best_score = float("-inf")
            for i in range(9):
                if board[i] == "":
                    board[i] = "O"
                    score = minimax(board, depth + 1, False)
                    board[i] = ""
                    best_score = max(score, best_score)
            return best_score
        else:
            best_score = float("inf")
            for i in range(9):
                if board[i] == "":
                    board[i] = "X"
                    score = minimax(board, depth + 1, True)
                    board[i] = ""
                    best_score = min(score, best_score)
            return best_score

    def get_best_move(board):
        best_score = float("-inf")
        best_move = -1
        for i in range(9):
            if board[i] == "":
                board[i] = "O"
                score = minimax(board, 0, False)
                board[i] = ""
                if score > best_score:
                    best_score = score
                    best_move = i
        return best_move

    async def gen_board():
        view = View(timeout=VIEW_TIMEOUT)
        has_unlocked_tiles = False
        for num, i in enumerate(board_state):
            if i == "":
                button = Button(emoji=get_emoji("empty"), custom_id=str(num))
                has_unlocked_tiles = True
            elif i == "X":
                button = Button(emoji="❌", disabled=True)
            elif i == "O":
                button = Button(emoji="⭕", disabled=True)

            button.callback = do_turn
            button.row = num // 3

            view.add_item(button)
        if not has_unlocked_tiles:
            text = f"{message.user.mention} (X) vs {person.mention} (O)\nits a tie!"
            user1, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=message.user.id)
            user2, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=person.id)
            user1.ttt_played += 1
            user2.ttt_played += 1
            user1.ttt_draws += 1
            user2.ttt_draws += 1
            await user1.save()
            await user2.save()
            await progress(message, user1, "ttc")
            await progress(message, user2, "ttc")
        else:
            text = f"{message.user.mention} (X) vs {person.mention} (O)\ncurrent turn: {current_turn.mention}"
        return text, view

    async def do_turn(interaction):
        nonlocal current_turn
        if interaction.user.id == current_turn.id:
            await interaction.response.defer()

            turn_spot = int(interaction.data["custom_id"])

            if board_state[turn_spot] != "":
                await interaction.followup.send("this cell is occupied", ephemeral=True)
                return

            board_state[turn_spot] = "X" if current_turn == message.user else "O"

            winner, has_winner, check = check_winner(board_state)
            if winner:
                view = View(timeout=1)
                for num, i in enumerate(board_state):
                    if i == "":
                        button = Button(emoji=get_emoji("empty"), disabled=True)
                    elif i == "X":
                        button = Button(emoji="❌", disabled=True)
                    elif i == "O":
                        button = Button(emoji="⭕", disabled=True)

                    if check and num in check:
                        button.style = ButtonStyle.green
                    button.row = num // 3

                    view.add_item(button)
                await interaction.edit_original_response(content=f"{message.user.mention} (X) vs {person.mention} (O)\n{current_turn.mention} wins!", view=view)
                user1, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=message.user.id)
                user2, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=person.id)
                user1.ttt_played += 1
                user2.ttt_played += 1
                if current_turn == message.user:
                    user1.ttt_won += 1
                else:
                    user2.ttt_won += 1
                await user1.save()
                await user2.save()
                await progress(message, user1, "ttc")
                await progress(message, user2, "ttc")
                await achemb(message, "ttt_win", "send", current_turn)
                return

            current_turn = message.user if current_turn == person else person

            if person == bot.user and current_turn == person and "" in board_state:
                best_move = get_best_move(board_state)
                board_state[best_move] = "O"
                current_turn = message.user

                winner, has_winner, check = check_winner(board_state)
                if winner:
                    view = View(timeout=1)
                    for num, i in enumerate(board_state):
                        if i == "":
                            button = Button(emoji=get_emoji("empty"), disabled=True)
                        elif i == "X":
                            button = Button(emoji="❌", disabled=True)
                        elif i == "O":
                            button = Button(emoji="⭕", disabled=True)

                        if check and num in check:
                            button.style = ButtonStyle.green
                        button.row = num // 3

                        view.add_item(button)
                    await interaction.edit_original_response(content=f"{message.user.mention} (X) vs {person.mention} (O)\n{person.mention} wins!", view=view)
                    user1, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=message.user.id)
                    user2, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=person.id)
                    user1.ttt_played += 1
                    user2.ttt_played += 1
                    user2.ttt_won += 1
                    await user1.save()
                    await user2.save()
                    await progress(message, user1, "ttc")
                    await progress(message, user2, "ttc")
                    await achemb(message, "ttt_win", "send", person)
                    return

            text, view = await gen_board()
            await interaction.edit_original_response(content=text, view=view)
        else:
            await do_funny(interaction)

    text, view = await gen_board()
    await message.response.send_message(text, view=view, allowed_mentions=discord.AllowedMentions(users=True))


@bot.tree.command(description="dont select a person to make an everyone vs you game")
@discord.app_commands.describe(person="Who do you want to play with?")
async def rps(message: discord.Interaction, person: Optional[discord.Member]):
    clean_name = message.user.name.replace("_", "\\_")
    picks = {"Rock": [], "Paper": [], "Scissors": []}
    mappings = {"Rock": ["Paper", "Rock", "Scissors"], "Paper": ["Scissors", "Paper", "Rock"], "Scissors": ["Rock", "Scissors", "Paper"]}
    vs_picks = {}
    players = []

    async def pick(interaction):
        nonlocal players
        if person and interaction.user.id not in [message.user.id, person.id]:
            await do_funny(interaction)
            return

        await interaction.response.defer()

        thing = interaction.data["custom_id"]
        if person or interaction.user != message.user:
            if interaction.user.id in players:
                return
            if person:
                vs_picks[interaction.user.name.replace("_", "\\_")] = thing
            else:
                picks[thing].append(interaction.user.name.replace("_", "\\_"))
            players.append(interaction.user.id)
            if person and person.id == bot.user.id:
                players.append(bot.user.id)
                vs_picks[bot.user.name.replace("_", "\\_")] = mappings[thing][0]
            if not person or len(players) == 1:
                await interaction.edit_original_response(content=f"Players picked: {len(players)}")
                return

        result = mappings[thing]

        if not person:
            description = f"{clean_name} picked: __{thing}__\n\n"
            for num, i in enumerate(["Winners", "Tie", "Losers"]):
                if picks[result[num]]:
                    peoples = "\n".join(picks[result[num]])
                else:
                    peoples = "No one"
                description += f"**{i}** ({result[num]})\n{peoples}\n\n"
        else:
            description = f"{clean_name} picked: __{vs_picks[clean_name]}__\n\n{clean_name_2} picked: __{vs_picks[clean_name_2]}__\n\n"
            result = mappings[vs_picks[clean_name]].index(vs_picks[clean_name_2])
            if result == 0:
                description += f"**Winner**: {clean_name_2}!"
            elif result == 1:
                description += "It's a **Tie**!"
            else:
                description += f"**Winner**: {clean_name}!"

        embed = discord.Embed(
            title=f"{clean_name_2} vs {clean_name}",
            description=description,
            color=0x6E593C,
        )
        await interaction.edit_original_response(content=None, embed=embed, view=None)

    if person:
        clean_name_2 = person.name.replace("_", "\\_")
    else:
        clean_name_2 = "Rock Paper Scissors"

    if person:
        description = "Pick what to play!"
    else:
        description = "Any amount of users can play. The game ends when the person who ran the command picks. Max time is 24 hours."
    embed = discord.Embed(
        title=f"{clean_name_2} vs {clean_name}",
        description=description,
        color=0x6E593C,
    )
    view = View(timeout=24 * 3600)
    for i in ["Rock", "Paper", "Scissors"]:
        button = Button(label=i, custom_id=i)
        button.callback = pick
        view.add_item(button)
    await message.response.send_message("Players picked: 0", embed=embed, view=view)


@bot.tree.command(description="you feel like making cookies")
async def cookie(message: discord.Interaction):
    cookie_id = (message.guild.id, message.user.id)
    if cookie_id not in temp_cookie_storage.keys():
        user, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=message.user.id)
        temp_cookie_storage[cookie_id] = user.cookies

    async def bake(interaction):
        if interaction.user != message.user:
            await do_funny(interaction)
            return
        await interaction.response.defer()
        if cookie_id in temp_cookie_storage:
            curr = temp_cookie_storage[cookie_id]
        else:
            user, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=message.user.id)
            curr = user.cookies
        curr += 1
        temp_cookie_storage[cookie_id] = curr
        view.children[0].label = f"{curr:,}"
        await interaction.edit_original_response(view=view)
        if curr < 5:
            await achemb(interaction, "cookieclicker", "send")
        if 5100 > curr >= 5000:
            await achemb(interaction, "cookiesclicked", "send")

    view = View(timeout=VIEW_TIMEOUT)
    button = Button(emoji="🍪", label=f"{temp_cookie_storage[cookie_id]:,}", style=ButtonStyle.blurple)
    button.callback = bake
    view.add_item(button)
    await message.response.send_message(view=view)


@bot.tree.command(description="give rats now")
@discord.app_commands.rename(rat_type="type")
@discord.app_commands.describe(
    person="Whom to gift?",
    rat_type="im gonna airstrike your house from orbit",
    amount="And how much?",
)
@discord.app_commands.autocomplete(rat_type=gift_autocomplete)
async def gift(
    message: discord.Interaction,
    person: discord.User,
    rat_type: str,
    amount: Optional[int],
):
    if amount is None:
        # default the amount to 1
        amount = 1
    person_id = person.id

    if amount <= 0 or message.user.id == person_id:
        # haha skill issue
        await message.response.send_message("no", ephemeral=True)
        if message.user.id == person_id:
            await achemb(message, "lonely", "send")
        return

    if rat_type in rattypes:
        user, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=message.user.id)
        # if we even have enough rats
        if user[f"rat_{rat_type}"] >= amount:
            reciever, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=person_id)
            user[f"rat_{rat_type}"] -= amount
            reciever[f"rat_{rat_type}"] += amount
            try:
                user.rats_gifted += amount
                reciever.rat_gifts_recieved += amount
            except Exception:
                pass
            await user.save()
            await reciever.save()
            embed = discord.Embed(
                title="Success!",
                description=f"Successfully transfered {amount:,} {rat_type} rats from {message.user.mention} to <@{person_id}>!",
                color=0x6E593C,
            )

            # handle tax
            if amount >= 5:
                tax_amount = round(amount * 0.2)
                tax_debounce = False

                async def pay(interaction):
                    nonlocal tax_debounce
                    if interaction.user.id == message.user.id and not tax_debounce:
                        tax_debounce = True
                        await interaction.response.defer()
                        user, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=message.user.id)
                        try:
                            # transfer tax
                            user[f"rat_{rat_type}"] -= tax_amount

                            try:
                                await interaction.edit_original_response(view=None)
                            except Exception:
                                pass
                            await interaction.followup.send(f"Tax of {tax_amount:,} {rat_type} rats was withdrawn from your account!")
                        finally:
                            # always save to prevent issue with exceptions leaving bugged state
                            await user.save()
                        await achemb(message, "good_citizen", "send")
                        if user[f"rat_{rat_type}"] < 0:
                            bot.loop.create_task(debt_cutscene(interaction, user))
                    else:
                        await do_funny(interaction)

                async def evade(interaction):
                    if interaction.user.id == message.user.id:
                        await interaction.response.defer()
                        try:
                            await interaction.edit_original_response(view=None)
                        except Exception:
                            pass
                        await interaction.followup.send(f"You evaded the tax of {tax_amount:,} {rat_type} rats.")
                        await achemb(message, "secret", "send")
                    else:
                        await do_funny(interaction)

                button = Button(label="Pay 20% tax", style=ButtonStyle.green)
                button.callback = pay

                button2 = Button(label="Evade the tax", style=ButtonStyle.red)
                button2.callback = evade

                myview = View(timeout=VIEW_TIMEOUT)

                myview.add_item(button)
                myview.add_item(button2)

                await message.response.send_message(person.mention, embed=embed, view=myview, allowed_mentions=discord.AllowedMentions(users=True))
            else:
                await message.response.send_message(person.mention, embed=embed, allowed_mentions=discord.AllowedMentions(users=True))

            # handle aches
            await achemb(message, "donator", "send")
            await achemb(message, "anti_donator", "send", person)
            if person_id == bot.user.id and rat_type == "Ultimate" and int(amount) >= 5:
                await achemb(message, "rich", "send")
            if person_id == bot.user.id:
                await achemb(message, "sacrifice", "send")
            if rat_type == "Nice" and int(amount) == 69:
                await achemb(message, "nice", "send")

            await progress(message, user, "gift")
        else:
            await message.response.send_message("no", ephemeral=True)
    elif rat_type.lower() == "rain":
        if person_id == bot.user.id:
            await message.response.send_message("you can't sacrifice rains", ephemeral=True)
            return

        actual_user, _ = await User.get_or_create(user_id=message.user.id)
        actual_receiver, _ = await User.get_or_create(user_id=person_id)
        if actual_user.rain_minutes >= amount:
            actual_user.rain_minutes -= amount
            actual_receiver.rain_minutes += amount
            await actual_user.save()
            await actual_receiver.save()
            embed = discord.Embed(
                title="Success!",
                description=f"Successfully transfered {amount:,} minutes of rain from {message.user.mention} to <@{person_id}>!",
                color=0x6E593C,
            )

            await message.response.send_message(person.mention, embed=embed, allowed_mentions=discord.AllowedMentions(users=True))

            # handle aches
            await achemb(message, "donator", "send")
            await achemb(message, "anti_donator", "send", person)
        else:
            await message.response.send_message("no", ephemeral=True)

        try:
            ch = bot.get_channel(config.RAIN_CHANNEL_ID)
            await ch.send(f"{message.user.id} gave {amount}m to {person_id}")
        except Exception:
            pass
    elif rat_type.lower() in [i["name"].lower() for i in pack_data]:
        rat_type = rat_type.lower()
        # packs um also this seems to be repetetive uh
        user, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=message.user.id)
        # if we even have enough packs
        if user[f"pack_{rat_type}"] >= amount:
            reciever, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=person_id)
            user[f"pack_{rat_type}"] -= amount
            reciever[f"pack_{rat_type}"] += amount
            await user.save()
            await reciever.save()
            embed = discord.Embed(
                title="Success!",
                description=f"Successfully transfered {amount:,} {rat_type} packs from {message.user.mention} to <@{person_id}>!",
                color=0x6E593C,
            )

            await message.response.send_message(person.mention, embed=embed, allowed_mentions=discord.AllowedMentions(users=True))

            # handle aches
            await achemb(message, "donator", "send")
            await achemb(message, "anti_donator", "send", person)
            if person_id == bot.user.id:
                await achemb(message, "sacrifice", "send")

            await progress(message, user, "gift")
        else:
            await message.response.send_message("no", ephemeral=True)
    else:
        await message.response.send_message("bro what", ephemeral=True)


@bot.tree.command(description="Trade stuff!")
@discord.app_commands.rename(person_id="user")
@discord.app_commands.describe(person_id="why would you need description")
async def trade(message: discord.Interaction, person_id: discord.User):
    person1 = message.user
    person2 = person_id

    blackhole = False

    person1accept = False
    person2accept = False

    person1value = 0
    person2value = 0

    person1gives = {}
    person2gives = {}

    user1, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=person1.id)
    user2, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=person2.id)

    if not bot.user:
        return

    # do the funny
    if person2.id == bot.user.id:
        person2gives["eGirl"] = 9999999

    # this is the deny button code
    async def denyb(interaction):
        nonlocal person1, person2, person1accept, person2accept, person1gives, person2gives, blackhole
        if interaction.user != person1 and interaction.user != person2:
            await do_funny(interaction)
            return

        await interaction.response.defer()
        blackhole = True
        person1gives = {}
        person2gives = {}
        try:
            await interaction.edit_original_response(
                content=f"{interaction.user.mention} has cancelled the trade.",
                embed=None,
                view=None,
            )
        except Exception:
            pass

    # this is the accept button code
    async def acceptb(interaction):
        nonlocal person1, person2, person1accept, person2accept, person1gives, person2gives, person1value, person2value, user1, user2, blackhole
        if interaction.user != person1 and interaction.user != person2:
            await do_funny(interaction)
            return

        # clicking accept again would make you un-accept
        if interaction.user == person1:
            person1accept = not person1accept
        elif interaction.user == person2:
            person2accept = not person2accept

        await interaction.response.defer()
        await update_trade_embed(interaction)

        if person1accept and person2 == bot.user:
            await achemb(message, "desperate", "send")

        if blackhole:
            await update_trade_embed(interaction)

        if person1accept and person2accept:
            blackhole = True
            user1, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=person1.id)
            user2, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=person2.id)
            actual_user1, _ = await User.get_or_create(user_id=person1.id)
            actual_user2, _ = await User.get_or_create(user_id=person2.id)

            # check if we have enough things (person could have moved them during the trade)
            error = False
            person1prismgive = 0
            person2prismgive = 0
            for k, v in person1gives.items():
                if k in prism_names:
                    person1prismgive += 1
                    prism = await Prism.get_or_none(guild_id=interaction.guild.id, name=k)
                    if not prism or prism.user_id != person1.id:
                        error = True
                        break
                    continue
                elif k == "rains":
                    if actual_user1.rain_minutes < v:
                        error = True
                        break
                elif k in rattypes:
                    if user1[f"rat_{k}"] < v:
                        error = True
                        break
                elif user1[f"pack_{k.lower()}"] < v:
                    error = True
                    break

            for k, v in person2gives.items():
                if k in prism_names:
                    person2prismgive += 1
                    prism = await Prism.get_or_none(guild_id=interaction.guild.id, name=k)
                    if not prism or prism.user_id != person2.id:
                        error = True
                        break
                    continue
                elif k == "rains":
                    if actual_user2.rain_minutes < v:
                        error = True
                        break
                elif k in rattypes:
                    if user2[f"rat_{k}"] < v:
                        error = True
                        break
                elif user2[f"pack_{k.lower()}"] < v:
                    error = True
                    break

            if error:
                try:
                    await interaction.edit_original_response(
                        content="Uh oh - some of the rats/prisms/packs/rains disappeared while trade was happening",
                        embed=None,
                        view=None,
                    )
                except Exception:
                    await interaction.followup.send("Uh oh - some of the rats/prisms/packs/rains disappeared while trade was happening")
                return

            # exchange
            rat_count = 0
            for k, v in person1gives.items():
                if k in prism_names:
                    await Prism.filter(guild_id=message.guild.id, name=k).update(user_id=person2.id)
                elif k == "rains":
                    actual_user1.rain_minutes -= v
                    actual_user2.rain_minutes += v
                    try:
                        ch = bot.get_channel(config.RAIN_CHANNEL_ID)
                        await ch.send(f"{actual_user1.user_id} traded {v}m to {actual_user2.user_id}")
                    except Exception:
                        pass
                elif k in rattypes:
                    rat_count += v
                    user1[f"rat_{k}"] -= v
                    user2[f"rat_{k}"] += v
                else:
                    user1[f"pack_{k.lower()}"] -= v
                    user2[f"pack_{k.lower()}"] += v

            for k, v in person2gives.items():
                if k in prism_names:
                    await Prism.filter(guild_id=message.guild.id, name=k).update(user_id=person1.id)
                elif k == "rains":
                    actual_user2.rain_minutes -= v
                    actual_user1.rain_minutes += v
                    try:
                        ch = bot.get_channel(config.RAIN_CHANNEL_ID)
                        await ch.send(f"{actual_user2.user_id} traded {v}m to {actual_user1.user_id}")
                    except Exception:
                        pass
                elif k in rattypes:
                    rat_count += v
                    user1[f"rat_{k}"] += v
                    user2[f"rat_{k}"] -= v
                else:
                    user1[f"pack_{k.lower()}"] += v
                    user2[f"pack_{k.lower()}"] -= v

            user1.rats_traded += rat_count
            user2.rats_traded += rat_count
            user1.trades_completed += 1
            user2.trades_completed += 1

            await user1.save()
            await user2.save()
            await actual_user1.save()
            await actual_user2.save()

            try:
                await interaction.edit_original_response(content="Trade finished!", view=None)
            except Exception:
                await interaction.followup.send()

            await achemb(message, "extrovert", "send")
            await achemb(message, "extrovert", "send", person2)

            if rat_count >= 1000:
                await achemb(message, "capitalism", "send")
                await achemb(message, "capitalism", "send", person2)

            if rat_count == 0:
                await achemb(message, "absolutely_nothing", "send")
                await achemb(message, "absolutely_nothing", "send", person2)

            if person2value - person1value >= 100:
                await achemb(message, "profit", "send")
            if person1value - person2value >= 100:
                await achemb(message, "profit", "send", person2)

            if person1value > person2value:
                await achemb(message, "scammed", "send")
            if person2value > person1value:
                await achemb(message, "scammed", "send", person2)

            if person1value == person2value and person1gives != person2gives:
                await achemb(message, "perfectly_balanced", "send")
                await achemb(message, "perfectly_balanced", "send", person2)

            await progress(message, user1, "trade")
            await progress(message, user2, "trade")

    # add rat code
    async def addb(interaction):
        nonlocal person1, person2, person1accept, person2accept, person1gives, person2gives
        if interaction.user != person1 and interaction.user != person2:
            await do_funny(interaction)
            return

        currentuser = 1 if interaction.user == person1 else 2

        # all we really do is spawn the modal
        modal = TradeModal(currentuser)
        await interaction.response.send_modal(modal)

    # this is ran like everywhere when you do anything
    # it updates the embed
    async def gen_embed():
        nonlocal person1, person2, person1accept, person2accept, person1gives, person2gives, blackhole, person1value, person2value

        if blackhole:
            # no way thats fun
            await achemb(message, "blackhole", "send")
            await achemb(message, "blackhole", "send", person2)
            return discord.Embed(color=0x6E593C, title="Blackhole", description="How Did We Get Here?"), None

        view = View(timeout=VIEW_TIMEOUT)

        accept = Button(label="Accept", style=ButtonStyle.green)
        accept.callback = acceptb

        deny = Button(label="Deny", style=ButtonStyle.red)
        deny.callback = denyb

        add = Button(label="Offer...", style=ButtonStyle.blurple)
        add.callback = addb

        view.add_item(accept)
        view.add_item(deny)
        view.add_item(add)

        person1name = person1.name.replace("_", "\\_")
        person2name = person2.name.replace("_", "\\_")
        coolembed = discord.Embed(
            color=0x6E593C,
            title=f"{person1name} and {person2name} trade",
            description="no way",
        )

        # a single field for one person
        def field(personaccept, persongives, person, number):
            nonlocal coolembed, person1value, person2value
            icon = "⬜"
            if personaccept:
                icon = "✅"
            valuestr = ""
            valuenum = 0
            total = 0
            for k, v in persongives.items():
                if v == 0:
                    continue
                if k in prism_names:
                    # prisms
                    valuestr += f"{get_emoji('prism')} {k}\n"
                    for v2 in type_dict.values():
                        valuenum += sum(type_dict.values()) / v2
                elif k == "rains":
                    # rains
                    valuestr += f"☔ {v:,}m of Rat Rains\n"
                    valuenum += 900 * v
                elif k in rattypes:
                    # rats
                    valuenum += (sum(type_dict.values()) / type_dict[k]) * v
                    total += v
                    aicon = get_emoji(k.lower() + "rat")
                    valuestr += f"{aicon} {k} {v:,}\n"
                else:
                    # packs
                    valuenum += sum([i["totalvalue"] if i["name"] == k else 0 for i in pack_data]) * v
                    aicon = get_emoji(k.lower() + "pack")
                    valuestr += f"{aicon} {k} {v:,}\n"
            if not valuestr:
                valuestr = "Nothing offered!"
            else:
                valuestr += f"*Total value: {round(valuenum):,}\nTotal rats: {round(total):,}*"
                if number == 1:
                    person1value = round(valuenum)
                else:
                    person2value = round(valuenum)
            personname = person.name.replace("_", "\\_")
            coolembed.add_field(name=f"{icon} {personname}", inline=True, value=valuestr)

        field(person1accept, person1gives, person1, 1)
        field(person2accept, person2gives, person2, 2)

        return coolembed, view

    # this is wrapper around gen_embed() to edit the mesage automatically
    async def update_trade_embed(interaction):
        embed, view = await gen_embed()
        try:
            await interaction.edit_original_response(embed=embed, view=view)
        except Exception:
            await achemb(message, "blackhole", "send")
            await achemb(message, "blackhole", "send", person2)

    # lets go add rats modal thats fun
    class TradeModal(discord.ui.Modal):
        def __init__(self, currentuser):
            super().__init__(
                title="Add to the trade",
                timeout=3600,
            )
            self.currentuser = currentuser

            self.rattype = discord.ui.TextInput(
                label='Rat or Pack Type, Prism Name or "Rain"',
                placeholder="Fine / Wooden / Alpha / Rain",
            )
            self.add_item(self.rattype)

            self.amount = discord.ui.TextInput(label="Amount to offer", placeholder="1", required=False)
            self.add_item(self.amount)

        # this is ran when user submits
        async def on_submit(self, interaction: discord.Interaction):
            nonlocal person1, person2, person1accept, person2accept, person1gives, person2gives
            value = self.amount.value if self.amount.value else 1
            user1, _ = await Profile.get_or_create(guild_id=interaction.guild.id, user_id=person1.id)
            user2, _ = await Profile.get_or_create(guild_id=interaction.guild.id, user_id=person2.id)

            try:
                if int(value) < 0:
                    person1accept = False
                    person2accept = False
            except Exception:
                await interaction.response.send_message("invalid amount", ephemeral=True)
                return

            # handle prisms
            if (pname := " ".join(i.capitalize() for i in self.rattype.value.split())) in prism_names:
                try:
                    prism = await Prism.get(guild_id=interaction.guild.id, name=pname)
                except Exception:
                    await interaction.response.send_message("this prism doesnt exist", ephemeral=True)
                    return
                if prism.user_id != interaction.user.id:
                    await interaction.response.send_message("this is not your prism", ephemeral=True)
                    return
                if (self.currentuser == 1 and pname in person1gives.keys()) or (self.currentuser == 2 and pname in person2gives.keys()):
                    await interaction.response.send_message("you already added this prism", ephemeral=True)
                    return

                if self.currentuser == 1:
                    person1gives[pname] = 1
                else:
                    person2gives[pname] = 1
                await interaction.response.defer()
                await update_trade_embed(interaction)
                return

            # handle packs
            if self.rattype.value.capitalize() in [i["name"] for i in pack_data]:
                pname = self.rattype.value.capitalize()
                if self.currentuser == 1:
                    if user1[f"pack_{pname.lower()}"] < int(value):
                        await interaction.response.send_message("you dont have enough packs", ephemeral=True)
                        return
                    new_val = person1gives.get(pname, 0) + int(value)
                    if new_val >= 0:
                        person1gives[pname] = new_val
                    else:
                        await interaction.response.send_message("skibidi toilet", ephemeral=True)
                        return
                else:
                    if user2[f"pack_{pname.lower()}"] < int(value):
                        await interaction.response.send_message("you dont have enough packs", ephemeral=True)
                        return
                    new_val = person2gives.get(pname, 0) + int(value)
                    if new_val >= 0:
                        person2gives[pname] = new_val
                    else:
                        await interaction.response.send_message("skibidi toilet", ephemeral=True)
                        return
                await interaction.response.defer()
                await update_trade_embed(interaction)
                return

            # handle rains
            if "rain" in self.rattype.value.lower():
                user, _ = await User.get_or_create(user_id=interaction.user.id)
                try:
                    if user.rain_minutes < int(value) or int(value) < 1:
                        await interaction.response.send_message("you dont have enough rains", ephemeral=True)
                        return
                except Exception:
                    await interaction.response.send_message("please enter a number for amount", ephemeral=True)
                    return

                if self.currentuser == 1:
                    try:
                        person1gives["rains"] += int(value)
                    except Exception:
                        person1gives["rains"] = int(value)
                else:
                    try:
                        person2gives["rains"] += int(value)
                    except Exception:
                        person2gives["rains"] = int(value)
                await interaction.response.defer()
                await update_trade_embed(interaction)
                return

            lc_input = self.rattype.value.lower()

            # loop through the rat types and find the correct one using lowercased user input.
            cname = rattype_lc_dict.get(lc_input, None)

            # if no rat type was found, the user input was invalid. as cname is still `None`
            if cname is None:
                await interaction.response.send_message("add a valid rat/pack/prism name 💀💀💀", ephemeral=True)
                return

            try:
                if self.currentuser == 1:
                    currset = person1gives[cname]
                else:
                    currset = person2gives[cname]
            except Exception:
                currset = 0

            try:
                if int(value) + currset < 0 or int(value) == 0:
                    raise Exception
            except Exception:
                await interaction.response.send_message("plz number?", ephemeral=True)
                return

            if (self.currentuser == 1 and user1[f"rat_{cname}"] < int(value) + currset) or (
                self.currentuser == 2 and user2[f"rat_{cname}"] < int(value) + currset
            ):
                await interaction.response.send_message(
                    "hell naww dude you dont even have that many rats 💀💀💀",
                    ephemeral=True,
                )
                return

            # OKE SEEMS GOOD LETS ADD RATS TO THE TRADE
            if self.currentuser == 1:
                try:
                    person1gives[cname] += int(value)
                    if person1gives[cname] == 0:
                        person1gives.pop(cname)
                except Exception:
                    person1gives[cname] = int(value)
            else:
                try:
                    person2gives[cname] += int(value)
                    if person2gives[cname] == 0:
                        person2gives.pop(cname)
                except Exception:
                    person2gives[cname] = int(value)

            await interaction.response.defer()
            await update_trade_embed(interaction)

    embed, view = await gen_embed()
    if not view:
        await message.response.send_message(embed=embed)
    else:
        await message.response.send_message(person2.mention, embed=embed, view=view, allowed_mentions=discord.AllowedMentions(users=True))

    if person1 == person2:
        await achemb(message, "introvert", "send")


@bot.tree.command(description="Get Rat Image, does not add a rat to your inventory")
@discord.app_commands.rename(rat_type="type")
@discord.app_commands.describe(rat_type="select a rat type ok")
@discord.app_commands.autocomplete(rat_type=rat_command_autocomplete)
async def rat(message: discord.Interaction, rat_type: Optional[str]):
    if rat_type and rat_type not in rattypes:
        await message.response.send_message("bro what", ephemeral=True)
        return

    perms = await fetch_perms(message)
    if not perms.attach_files:
        await message.response.send_message("i cant attach files here!", ephemeral=True)
        return

    # check the user has the rat if required
    user, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=message.user.id)
    if rat_type and user[f"rat_{rat_type}"] <= 0:
        await message.response.send_message("you dont have that rat", ephemeral=True)
        return

    image = f"images/spawn/{rat_type.lower()}_rat.png" if rat_type else "images/rat.png"
    file = discord.File(image, filename=image)
    await message.response.send_message(file=file)


@bot.tree.command(description="Get Cursed Rat")
async def cursed(message: discord.Interaction):
    perms = await fetch_perms(message)
    if not perms.attach_files:
        await message.response.send_message("i cant attach files here!", ephemeral=True)
        return
    file = discord.File("images/cursed.jpg", filename="cursed.jpg")
    await message.response.send_message(file=file)


@bot.tree.command(description="Get Your balance")
async def bal(message: discord.Interaction):
    perms = await fetch_perms(message)
    if not perms.attach_files:
        await message.response.send_message("i cant attach files here!", ephemeral=True)
        return
    file = discord.File("images/money.png", filename="money.png")
    embed = discord.Embed(title="rat coins", color=0x6E593C).set_image(url="attachment://money.png")
    await message.response.send_message(file=file, embed=embed)


@bot.tree.command(description="Brew some coffee to ratch rats more efficiently")
async def brew(message: discord.Interaction):
    await message.response.send_message("HTTP 418: I'm a teapot. <https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/418>")
    await achemb(message, "coffee", "send")


@bot.tree.command(description="Gamble your life savings away in our totally-not-rigged ratsino!")
async def casino(message: discord.Interaction):
    if message.user.id + message.guild.id in casino_lock:
        await message.response.send_message(
            "you get kicked out of the ratsino because you are already there, and two of you playing at once would cause a glitch in the universe",
            ephemeral=True,
        )
        await achemb(message, "paradoxical_gambler", "send")
        return

    profile, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=message.user.id)
    # funny global gamble counter cus funny
    total_sum = (await Profile.filter(gambles__gt=0).annotate(total=Sum("gambles")).values_list("total", flat=True))[0] or 0
    embed = discord.Embed(
        title="🎲 The Ratsino",
        description=f"One spin costs 5 {get_emoji('finerat')} Fine rats\nSo far you gambled {profile.gambles} times.\nAll Rat Bot users gambled {total_sum:,} times.",
        color=0x750F0E,
    )

    async def spin(interaction):
        nonlocal message
        if interaction.user.id != message.user.id:
            await do_funny(interaction)
            return
        if message.user.id + message.guild.id in casino_lock:
            await interaction.response.send_message(
                "you get kicked out of the ratsino because you are already there, and two of you playing at once would cause a glitch in the universe",
                ephemeral=True,
            )
            return

        user, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=message.user.id)
        if user.rat_Fine < 5:
            await interaction.response.send_message("you are too broke now", ephemeral=True)
            await achemb(interaction, "broke", "send")
            return

        await interaction.response.defer()
        amount = random.randint(1, 5)
        casino_lock.append(message.user.id + message.guild.id)
        user.rat_Fine += amount - 5
        user.gambles += 1
        await user.save()

        if user.gambles >= 10:
            await achemb(message, "gambling_one", "send")
        if user.gambles >= 50:
            await achemb(message, "gambling_two", "send")

        variants = [
            f"{get_emoji('egirlrat')} 1 eGirl rats",
            f"{get_emoji('egirlrat')} 3 eGirl rats",
            f"{get_emoji('ultimaterat')} 2 Ultimate rats",
            f"{get_emoji('corruptrat')} 7 Corrupt rats",
            f"{get_emoji('divinerat')} 4 Divine rats",
            f"{get_emoji('epicrat')} 10 Epic rats",
            f"{get_emoji('professorrat')} 5 Professor rats",
            f"{get_emoji('realrat')} 2 Real rats",
            f"{get_emoji('legendaryrat')} 5 Legendary rats",
            f"{get_emoji('mythicrat')} 2 Mythic rats",
            f"{get_emoji('8bitrat')} 7 8bit rats",
        ]

        random.shuffle(variants)
        icon = "🎲"

        for i in variants:
            embed = discord.Embed(title=f"{icon} The Ratsino", description=f"**{i}**", color=0x750F0E)
            try:
                await interaction.edit_original_response(embed=embed, view=None)
            except Exception:
                pass
            await asyncio.sleep(1)

        embed = discord.Embed(
            title=f"{icon} The Ratsino",
            description=f"You won:\n**{get_emoji('finerat')} {amount} Fine rats**",
            color=0x750F0E,
        )

        button = Button(label="Spin", style=ButtonStyle.blurple)
        button.callback = spin

        myview = View(timeout=VIEW_TIMEOUT)
        myview.add_item(button)

        casino_lock.remove(message.user.id + message.guild.id)

        try:
            await interaction.edit_original_response(embed=embed, view=myview)
        except Exception:
            await interaction.followup.send(embed=embed, view=myview)

    button = Button(label="Spin", style=ButtonStyle.blurple)
    button.callback = spin

    myview = View(timeout=VIEW_TIMEOUT)
    myview.add_item(button)

    await message.response.send_message(embed=embed, view=myview)


@bot.tree.command(description="oh no")
async def slots(message: discord.Interaction):
    if message.user.id + message.guild.id in slots_lock:
        await message.response.send_message(
            "you get kicked from the slot machine because you are already there, and two of you playing at once would cause a glitch in the universe",
            ephemeral=True,
        )
        await achemb(message, "paradoxical_gambler", "send")
        return

    profile, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=message.user.id)
    # i hate this
    total_spins, total_wins, total_big_wins = (
        await Profile.filter(slot_spins__gt=0)
        .annotate(total_spins=Sum("slot_spins"), total_wins=Sum("slot_wins"), total_big_wins=Sum("slot_big_wins"))
        .values_list("total_spins", "total_wins", "total_big_wins")
    )[0]
    if (total_spins, total_wins, total_big_wins) == (None, None, None):
        total_spins, total_wins, total_big_wins = 0, 0, 0
    embed = discord.Embed(
        title=":slot_machine: The Slot Machine",
        description=f"__Your stats__\n{profile.slot_spins:,} spins\n{profile.slot_wins:,} wins\n{profile.slot_big_wins:,} big wins\n\n__Global stats__\n{total_spins:,} spins\n{total_wins:,} wins\n{total_big_wins:,} big wins",
        color=0x750F0E,
    )

    async def remove_debt(interaction):
        nonlocal message
        if interaction.user.id != message.user.id:
            await do_funny(interaction)
            return
        user, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=message.user.id)

        # remove debt
        for i in rattypes:
            user[f"rat_{i}"] = max(0, user[f"rat_{i}"])

        await user.save()
        await interaction.response.send_message("You have removed your debts! Life is wonderful!", ephemeral=True)
        await achemb(interaction, "debt", "send")

    async def spin(interaction):
        nonlocal message
        if interaction.user.id != message.user.id:
            await do_funny(interaction)
            return
        if message.user.id + message.guild.id in slots_lock:
            await interaction.response.send_message(
                "you get kicked from the slot machine because you are already there, and two of you playing at once would cause a glitch in the universe",
                ephemeral=True,
            )
            return
        user, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=message.user.id)

        await interaction.response.defer()
        slots_lock.append(message.user.id + message.guild.id)
        user.slot_spins += 1
        await user.save()

        await achemb(interaction, "slots", "send")
        await progress(message, user, "slots")
        await progress(message, user, "slots2")

        variants = ["🍒", "🍋", "🍇", "🔔", "⭐", ":seven:"]
        reel_durations = [random.randint(9, 12), random.randint(15, 22), random.randint(25, 28)]
        random.shuffle(reel_durations)

        # the k number is much cycles it will go before stopping + 1
        col1 = random.choices(variants, k=reel_durations[0])
        col2 = random.choices(variants, k=reel_durations[1])
        col3 = random.choices(variants, k=reel_durations[2])

        if message.user.id in rigged_users:
            col1[len(col1) - 2] = ":seven:"
            col2[len(col2) - 2] = ":seven:"
            col3[len(col3) - 2] = ":seven:"

        blank_emoji = get_emoji("empty")
        for slot_loop_ind in range(1, max(reel_durations) - 1):
            current1 = min(len(col1) - 2, slot_loop_ind)
            current2 = min(len(col2) - 2, slot_loop_ind)
            current3 = min(len(col3) - 2, slot_loop_ind)
            desc = ""
            for offset in [-1, 0, 1]:
                if offset == 0:
                    desc += f"➡️ {col1[current1 + offset]} {col2[current2 + offset]} {col3[current3 + offset]} ⬅️\n"
                else:
                    desc += f"{blank_emoji} {col1[current1 + offset]} {col2[current2 + offset]} {col3[current3 + offset]} {blank_emoji}\n"
            embed = discord.Embed(
                title=":slot_machine: The Slot Machine",
                description=desc,
                color=0x750F0E,
            )
            try:
                await interaction.edit_original_response(embed=embed, view=None)
            except Exception:
                pass
            await asyncio.sleep(0.5)

        user, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=message.user.id)
        big_win = False
        if col1[current1] == col2[current2] == col3[current3]:
            user.slot_wins += 1
            if col1[current1] == ":seven:":
                desc = "**BIG WIN!**\n\n" + desc
                user.slot_big_wins += 1
                big_win = True
                await user.save()
                await achemb(interaction, "big_win_slots", "send")
            else:
                desc = "**You win!**\n\n" + desc
                await user.save()
            await achemb(interaction, "win_slots", "send")
        else:
            desc = "**You lose!**\n\n" + desc

        button = Button(label="Spin", style=ButtonStyle.blurple)
        button.callback = spin

        myview = View(timeout=VIEW_TIMEOUT)
        myview.add_item(button)

        if big_win:
            # check if user has debt in any rat type
            has_debt = False
            for i in rattypes:
                if user[f"rat_{i}"] < 0:
                    has_debt = True
                    break
            if has_debt:
                desc += "\n\n**You can remove your debt!**"
                button = Button(label="Remove Debt", style=ButtonStyle.blurple)
                button.callback = remove_debt
                myview.add_item(button)

        slots_lock.remove(message.user.id + message.guild.id)

        embed = discord.Embed(title=":slot_machine: The Slot Machine", description=desc, color=0x750F0E)

        try:
            await interaction.edit_original_response(embed=embed, view=myview)
        except Exception:
            await interaction.followup.send(embed=embed, view=myview)

    button = Button(label="Spin", style=ButtonStyle.blurple)
    button.callback = spin

    myview = View(timeout=VIEW_TIMEOUT)
    myview.add_item(button)

    await message.response.send_message(embed=embed, view=myview)


@bot.tree.command(description="get a super accurate rating of something")
@discord.app_commands.describe(thing="The thing or person to check", stat="The stat to check")
async def rate(message: discord.Interaction, thing: str, stat: str):
    if len(thing) > 100 or len(stat) > 100:
        await message.response.send_message("thats kinda long", ephemeral=True)
        return
    await message.response.send_message(f"{thing} is {random.randint(0, 100)}% {stat}")
    user, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=message.user.id)
    await progress(message, user, "rate")


@bot.tree.command(name="8ball", description="ask the magic ratball")
@discord.app_commands.describe(question="your question to the ratball")
async def eightball(message: discord.Interaction, question: str):
    if len(question) > 300:
        await message.response.send_message("thats kinda long", ephemeral=True)
        return

    ratball_responses = [
        # positive
        "it is certain",
        "it is decidedly so",
        "without a doubt",
        "yes definitely",
        "you may rely on it",
        "as i see it, yes",
        "most likely",
        "outlook good",
        "yes",
        "signs point to yes",
        # negative
        "dont count on it",
        "my reply is no",
        "my sources say no",
        "outlook not so good",
        "very doubtful",
        "most likely not",
        "unlikely",
        "no definitely",
        "no",
        "signs point to no",
        # neutral
        "reply hazy, try again",
        "ask again later",
        "better not tell you now",
        "cannot predict now",
        "concetrate and ask again",
    ]

    await message.response.send_message(f"{question}\n:8ball: **{random.choice(ratball_responses)}**")
    user, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=message.user.id)
    await progress(message, user, "ratball")
    await achemb(message, "balling", "send")


@bot.tree.command(description="get a reminder in the future (+- 5 minutes)")
@discord.app_commands.describe(
    days="in how many days",
    hours="in how many hours",
    minutes="in how many minutes (+- 5 minutes)",
    text="what to remind",
)
async def remind(
    message: discord.Interaction,
    days: Optional[int],
    hours: Optional[int],
    minutes: Optional[int],
    text: Optional[str],
):
    if not days:
        days = 0
    if not hours:
        hours = 0
    if not minutes:
        minutes = 0
    if not text:
        text = "Reminder!"

    goal_time = int(time.time() + (days * 86400) + (hours * 3600) + (minutes * 60))
    if goal_time > time.time() + (86400 * 365 * 20):
        await message.response.send_message("rats do not live for that long", ephemeral=True)
        return
    if len(text) > 1900:
        await message.response.send_message("thats too long", ephemeral=True)
        return
    if goal_time < 0:
        await message.response.send_message("rat cant time travel (yet)", ephemeral=True)
        return
    await message.response.send_message(f"🔔 ok, <t:{goal_time}:R> (+- 5 min) ill remind you of:\n{text}")
    msg = await message.original_response()
    message_link = msg.jump_url
    text += f"\n\n*This is a [reminder](<{message_link}>) you set.*"
    await Reminder.create(user_id=message.user.id, text=text, time=goal_time)
    profile, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=message.user.id)
    profile.reminders_set += 1
    await profile.save()
    await achemb(message, "reminder", "send")  # the ai autocomplete thing suggested this and its actually a cool ach
    await progress(message, profile, "reminder")  # the ai autocomplete thing also suggested this though profile wasnt defined


@bot.tree.command(name="random", description="Get a random rat")
async def random_rat(message: discord.Interaction):
    await message.response.defer()
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                "https://api.theratapi.com/v1/images/search", headers={"User-Agent": "RatBot/1.0 https://github.com/milenakos/rat-bot"}
            ) as response:
                data = await response.json()
                await message.followup.send(data[0]["url"])
                await achemb(message, "randomizer", "send")
        except Exception:
            await message.followup.send("no rats :(")


if config.WORDNIK_API_KEY:

    @bot.tree.command(description="define a word")
    async def define(message: discord.Interaction, word: str):
        word = word.lower()
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"https://api.wordnik.com/v4/word.json/{word}/definitions?api_key={config.WORDNIK_API_KEY}&useCanonical=true&includeTags=false&includeRelated=false&limit=69",
                    headers={"User-Agent": "RatBot/1.0 https://github.com/milenakos/rat-bot"},
                ) as response:
                    data = await response.json()

                    # lazily filter some things
                    text = (await response.text()).lower()
                    for test in ["vulgar", "slur", "offensive", "profane", "insult", "abusive", "derogatory"]:
                        if test in text:
                            await message.response.send_message(f"__{message.user.name}__\na stupid idiot (result was filtered)", ephemeral=True)
                            return

                    # sometimes the api returns results without definitions, so we search for the first one which has a definition
                    for i in data:
                        if "text" in i.keys():
                            clean_data = re.sub(re.compile("<.*?>"), "", i["text"])
                            await message.response.send_message(
                                f"__{word}__\n{clean_data}\n-# [{i['attributionText']}](<{i['attributionUrl']}>) Powered by [Wordnik](<{i['wordnikUrl']}>)"
                            )
                            await achemb(message, "define", "send")
                            return

                    raise Exception
            except Exception:
                await message.response.send_message("no definition found", ephemeral=True)


@bot.tree.command(name="fact", description="get a random rat fact")
async def rat_fact(message: discord.Interaction):
    facts = [
        "you love rats",
        f"rat bot is in {len(bot.guilds):,} servers",
        "rat",
        "rats are the best",
    ]

    # give a fact from the list or the API
    if random.randint(0, 10) == 0:
        await message.response.send_message(random.choice(facts))
    else:
        await message.response.defer()
        async with aiohttp.ClientSession() as session:
            async with session.get("https://ratfact.ninja/fact", headers={"User-Agent": "RatBot/1.0 https://github.com/milenakos/rat-bot"}) as response:
                if response.status == 200:
                    data = await response.json()
                    await message.followup.send(data["fact"])
                else:
                    await message.followup.send("failed to fetch a rat fact.")

    if not isinstance(
        message.channel,
        Union[
            discord.TextChannel,
            discord.StageChannel,
            discord.VoiceChannel,
            discord.Thread,
        ],
    ):
        return

    user, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=message.user.id)
    user.facts += 1
    await user.save()
    if user.facts >= 10:
        await achemb(message, "fact_enjoyer", "send")

    try:
        channel = await Channel.get_or_none(channel_id=message.channel.id)
        if channel and channel.rattype == "Professor":
            await achemb(message, "nerd_battle", "send")
    except Exception:
        pass


async def light_market(message):
    rataine_prices = [
        [10, "Fine"],
        [30, "Fine"],
        [20, "Good"],
        [15, "Rare"],
        [20, "Wild"],
        [10, "Epic"],
        [20, "Sus"],
        [15, "Rickroll"],
        [7, "Superior"],
        [5, "Legendary"],
        [3, "8bit"],
        [4, "Divine"],
        [3, "Real"],
        [2, "Ultimate"],
        [1, "eGirl"],
    ]
    user, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=message.user.id)
    if user.rataine_active < int(time.time()):
        count = user.rataine_week
        lastweek = user.recent_week
        embed = discord.Embed(
            title="The Mafia Hideout",
            description="you break down the door. the rataine machine lists what it needs.",
        )

        if lastweek != datetime.datetime.utcnow().isocalendar()[1]:
            lastweek = datetime.datetime.utcnow().isocalendar()[1]
            count = 0
            user.rataine_week = 0
            user.recent_week = datetime.datetime.utcnow().isocalendar()[1]
            await user.save()

        state = random.getstate()
        random.seed(datetime.datetime.utcnow().isocalendar()[1])
        deals = []

        r = range(random.randint(3, 5))
        for i in r:
            # 3-5 prices are possible per week
            deals.append(random.randint(0, 14))

        deals.sort()

        for i in r:
            deals[i] = rataine_prices[deals[i]]

        random.setstate(state)
        if count < len(deals):
            deal = deals[count]
        else:
            embed = discord.Embed(
                title="The Mafia Hideout",
                description="you have used up all of your rataine for the week. please come back later.",
            )
            await message.followup.send(embed=embed, ephemeral=True)
            return

        type = deal[1]
        amount = deal[0]
        embed.add_field(
            name="🧂 12h of Rataine",
            value=f"Price: {get_emoji(type.lower() + 'rat')} {amount} {type}",
        )

        async def make_rataine(interaction):
            nonlocal message, type, amount
            user, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=message.user.id)
            if user[f"rat_{type}"] < amount or user.rataine_active > time.time():
                return
            user[f"rat_{type}"] -= amount
            user.rataine_active = int(time.time()) + 43200
            user.rataine_week += 1
            user.rataine_bought += 1
            await user.save()
            await interaction.response.send_message(
                "The machine spools down. Your rat ratches will be doubled for the next 12 hours.",
                ephemeral=True,
            )

        myview = View(timeout=VIEW_TIMEOUT)

        if user[f"rat_{type}"] >= amount:
            button = Button(label="Buy", style=ButtonStyle.blurple)
        else:
            button = Button(
                label="You don't have enough rats!",
                disabled=True,
            )
        button.callback = make_rataine

        myview.add_item(button)

        await message.followup.send(embed=embed, view=myview, ephemeral=True)
    else:
        embed = discord.Embed(
            title="The Mafia Hideout",
            description=f"the machine is recovering. you can use machine again <t:{user.rataine_active}:R>.",
        )
        await message.followup.send(embed=embed, ephemeral=True)


async def dark_market(message):
    rataine_prices = [
        [5, "Fine"],
        [5, "Good"],
        [4, "Wild"],
        [4, "Epic"],
        [3, "Brave"],
        [3, "Reverse"],
        [2, "Trash"],
        [2, "Mythic"],
        [1, "Corrupt"],
        [1, "Divine"],
        [100, "eGirl"],
    ]
    user, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=message.user.id)
    if user.rataine_active < int(time.time()):
        level = user.dark_market_level
        embed = discord.Embed(
            title="The Dark Market",
            description="after entering the secret code, they let you in. today's deal is:",
        )
        embed.set_author(name="Click here to open Wiki", url="https://wiki.minkos.lol/en/dark-market")
        deal = rataine_prices[level] if level < len(rataine_prices) else rataine_prices[-1]
        type = deal[1]
        amount = deal[0]
        embed.add_field(
            name="🧂 12h of Rataine",
            value=f"Price: {get_emoji(type.lower() + 'rat')} {amount} {type}",
        )

        async def buy_rataine(interaction):
            nonlocal message, type, amount
            user, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=message.user.id)
            if user[f"rat_{type}"] < amount or user.rataine_active > time.time():
                return
            user[f"rat_{type}"] -= amount
            user.rataine_active = int(time.time()) + 43200
            user.dark_market_level += 1
            user.rataine_bought += 1
            await user.save()
            await interaction.response.send_message(
                "Thanks for buying! Your rat ratches will be doubled for the next 12 hours.",
                ephemeral=True,
            )

        debounce = False

        async def complain(interaction):
            nonlocal debounce
            if debounce:
                return
            debounce = True

            person = interaction.user
            phrases = [
                "*Because of my addiction I'm paying them a fortune.*",
                f"**{person}**: Hey, I'm not fine with those prices.",
                "**???**: Hmm?",
                "**???**: Oh.",
                "**???**: It seems you don't understand.",
                "**???**: We are the ones setting prices, not you.",
                f"**{person}**: Give me a more fair price or I will report you to the police.",
                "**???**: Huh?",
                "**???**: Well, it seems like you chose...",
                "# DEATH",
                "**???**: Better start running :)",
                "*Uh oh.*",
            ]

            await interaction.response.send_message("*That's not funny anymore. Those prices are insane.*", ephemeral=True)
            await asyncio.sleep(5)
            for i in phrases:
                await interaction.followup.send(i, ephemeral=True)
                await asyncio.sleep(5)

            # there is actually no time pressure anywhere but try to imagine there is
            counter = 0

            async def step(interaction):
                nonlocal counter
                counter += 1
                await interaction.response.defer()
                if counter == 30:
                    try:
                        await interaction.edit_original_response(view=None)
                    except Exception:
                        pass

                    final_cutscene_followups = [
                        "You barely manage to turn around a corner and hide to run away.",
                        "You quietly get to the police station and tell them everything.",
                        "## The next day.",
                        "A nice day outside. You open the news:",
                        "*Dog Mafia, the biggest rataine distributor, was finally caught after anonymous report.*",
                        "HUH? It was dogs all along...",
                    ]

                    for phrase in final_cutscene_followups:
                        await asyncio.sleep(5)
                        await interaction.followup.send(phrase, ephemeral=True)

                    await asyncio.sleep(5)
                    user.story_complete = True
                    await user.save()
                    await achemb(interaction, "thanksforplaying", "send")

            run_view = View(timeout=VIEW_TIMEOUT)
            button = Button(label="RUN", style=ButtonStyle.green)
            button.callback = step
            run_view.add_item(button)

            await interaction.followup.send(
                "RUN!\nSpam the button a lot of times as fast as possible to run away!",
                view=run_view,
                ephemeral=True,
            )

        myview = View(timeout=VIEW_TIMEOUT)

        if level >= len(rataine_prices) - 1:
            button = Button(label="What???", style=ButtonStyle.red)
            button.callback = complain
        else:
            if user[f"rat_{type}"] >= amount:
                button = Button(label="Buy", style=ButtonStyle.blurple)
            else:
                button = Button(
                    label="You don't have enough rats!",
                    disabled=True,
                )
            button.callback = buy_rataine
        myview.add_item(button)

        await message.followup.send(embed=embed, view=myview, ephemeral=True)
    else:
        embed = discord.Embed(
            title="The Dark Market",
            description=f"you already bought from us recently. you can do next purchase <t:{user.rataine_active}:R>.",
        )
        await message.followup.send(embed=embed, ephemeral=True)


@bot.tree.command(description="View your achievements")
async def achievements(message: discord.Interaction):
    # this is very close to /inv's ach counter
    user, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=message.user.id)
    if user.funny >= 50:
        await achemb(message, "its_not_working", "send")

    unlocked = 0
    minus_achs = 0
    minus_achs_count = 0
    for k in ach_names:
        is_ach_hidden = ach_list[k]["rategory"] == "Hidden"
        if is_ach_hidden:
            minus_achs_count += 1
        if user[k]:
            if is_ach_hidden:
                minus_achs += 1
            else:
                unlocked += 1
    total_achs = len(ach_list) - minus_achs_count
    minus_achs = "" if minus_achs == 0 else f" + {minus_achs}"

    hidden_counter = 0

    # this is a single page of the achievement list
    async def gen_new(rategory):
        nonlocal message, unlocked, total_achs, hidden_counter

        unlocked = 0
        minus_achs = 0
        minus_achs_count = 0

        for k in ach_names:
            is_ach_hidden = ach_list[k]["rategory"] == "Hidden"
            if is_ach_hidden:
                minus_achs_count += 1
            if user[k]:
                if is_ach_hidden:
                    minus_achs += 1
                else:
                    unlocked += 1

        total_achs = len(ach_list) - minus_achs_count

        if minus_achs != 0:
            minus_achs = f" + {minus_achs}"
        else:
            minus_achs = ""

        hidden_suffix = ""

        if rategory == "Hidden":
            hidden_suffix = '\n\nThis is a "Hidden" rategory. Achievements here only show up after you complete them.'
            hidden_counter += 1
        else:
            hidden_counter = 0

        newembed = discord.Embed(
            title=rategory,
            description=f"Achievements unlocked (total): {unlocked}/{total_achs}{minus_achs}{hidden_suffix}",
            color=0x6E593C,
        ).set_footer(text=rain_shill)

        global_user, _ = await User.get_or_create(user_id=message.user.id)
        if len(news_list) > len(global_user.news_state.strip()) or "0" in global_user.news_state.strip()[-4:]:
            newembed.set_author(name="You have unread news! /news")

        for k, v in ach_list.items():
            if v["rategory"] == rategory:
                if k == "thanksforplaying":
                    if user[k]:
                        newembed.add_field(
                            name=str(get_emoji("demonic_ach")) + " Rataine Addict",
                            value="Defeat the dog mafia",
                            inline=True,
                        )
                    else:
                        newembed.add_field(
                            name=str(get_emoji("no_demonic_ach")) + " Thanks For Playing",
                            value="Complete the story",
                            inline=True,
                        )
                    continue

                icon = str(get_emoji("no_ach")) + " "
                if user[k]:
                    newembed.add_field(
                        name=str(get_emoji("ach")) + " " + v["title"],
                        value=v["description"],
                        inline=True,
                    )
                elif rategory != "Hidden":
                    newembed.add_field(
                        name=icon + v["title"],
                        value="???" if v["is_hidden"] else v["description"],
                        inline=True,
                    )

        return newembed

    # creates buttons at the bottom of the full view
    def insane_view_generator(rategory):
        myview = View(timeout=VIEW_TIMEOUT)
        buttons_list = []

        async def callback_hell(interaction):
            thing = interaction.data["custom_id"]
            await interaction.response.defer()
            try:
                await interaction.edit_original_response(embed=await gen_new(thing), view=insane_view_generator(thing))
            except Exception:
                pass

            if hidden_counter == 3 and user.dark_market_active:
                if not user.story_complete:
                    # open the totally not suspicious dark market
                    await dark_market(message)
                else:
                    await light_market(message)
                await achemb(message, "dark_market", "followup")

            if hidden_counter == 20:
                await achemb(interaction, "darkest_market", "send")

        for num, i in enumerate(["Rat Hunt", "Commands", "Random", "Silly", "Hard", "Hidden"]):
            if rategory == i:
                buttons_list.append(Button(label=i, custom_id=i, style=ButtonStyle.green, row=num // 3))
            else:
                buttons_list.append(Button(label=i, custom_id=i, style=ButtonStyle.blurple, row=num // 3))
            buttons_list[-1].callback = callback_hell

        for j in buttons_list:
            myview.add_item(j)
        return myview

    await message.response.send_message(
        embed=await gen_new("Rat Hunt"),
        ephemeral=True,
        view=insane_view_generator("Rat Hunt"),
    )

    if unlocked >= 15:
        await achemb(message, "achiever", "send")


@bot.tree.command(name="ratch", description="Ratch someone in 4k")
async def ratch_tip(message: discord.Interaction):
    await message.response.send_message(
        f'Nope, that\'s the wrong way to do this.\nRight Click/Long Hold a message you want to ratch > Select `Apps` in the popup > "{get_emoji("staring_rat")} ratch"',
        ephemeral=True,
    )


async def ratch(message: discord.Interaction, msg: discord.Message):
    perms = await fetch_perms(message)
    if not perms.attach_files:
        await message.response.send_message("i cant attach files here!", ephemeral=True)
        return
    if message.user.id in ratchcooldown and ratchcooldown[message.user.id] + 6 > time.time():
        await message.response.send_message("your phone is overheating bro chill", ephemeral=True)
        return
    await message.response.defer()

    event_loop = asyncio.get_event_loop()
    result = await event_loop.run_in_executor(None, msg2img.msg2img, msg)

    await message.followup.send("cought in 4k", file=result)

    ratchcooldown[message.user.id] = time.time()

    await achemb(message, "4k", "send")

    if msg.author.id == bot.user.id and "cought in 4k" in msg.content:
        await achemb(message, "8k", "send")

    try:
        is_rat = (await Channel.get(channel_id=message.channel.id)).rat
    except Exception:
        is_rat = False

    if int(is_rat) == int(msg.id):
        await achemb(message, "not_like_that", "send")


@bot.tree.command(description="View the leaderboards")
@discord.app_commands.rename(leaderboard_type="type")
@discord.app_commands.describe(
    leaderboard_type="The leaderboard type to view!",
    rat_type="The rat type to view (only for the Rats leaderboard)",
    locked="Whether to remove page switch buttons to prevent tampering",
)
@discord.app_commands.autocomplete(rat_type=lb_type_autocomplete)
async def leaderboards(
    message: discord.Interaction,
    leaderboard_type: Optional[Literal["Rats", "Value", "Fast", "Slow", "Battlepass", "Cookies"]],
    rat_type: Optional[str],
    locked: Optional[bool],
):
    if not leaderboard_type:
        leaderboard_type = "Rats"
    if not locked:
        locked = False
    if rat_type and rat_type not in rattypes + ["All"]:
        await message.response.send_message("invalid rattype", ephemeral=True)
        return

    # this fat function handles a single page
    async def lb_handler(interaction, type, do_edit=None, specific_rat="All"):
        if specific_rat is None:
            specific_rat = "All"

        nonlocal message
        if do_edit is None:
            do_edit = True
        await interaction.response.defer()

        messager = None
        interactor = None

        # leaderboard top amount
        show_amount = 15

        string = ""
        if type == "Rats":
            unit = "rats"

            if specific_rat != "All":
                result = (
                    await Profile.filter(guild_id=message.guild.id, **{f"rat_{specific_rat}__gt": 0})
                    .annotate(final_value=Sum(f"rat_{specific_rat}"))
                    .order_by("-final_value")
                    .values("user_id", "final_value")
                )
            else:
                # dynamically generate sum expression, cast each value to bigint first to handle large totals
                rat_columns = [f'CAST("rat_{c}" AS BIGINT)' for c in rattypes if c]
                sum_expression = " + ".join(rat_columns)
                result = (
                    await Profile.filter(guild_id=message.guild.id)
                    .annotate(final_value=RawSQL(sum_expression))
                    .order_by("-final_value")
                    .values("user_id", "final_value")
                )

                # find rarest
                rarest = None
                for i in rattypes[::-1]:
                    non_zero_count = await Profile.filter(guild_id=message.guild.id, **{f"rat_{i}__gt": 0}).values_list("user_id", flat=True)
                    if len(non_zero_count) != 0:
                        rarest = i
                        rarest_holder = non_zero_count
                        break

                if rarest and specific_rat != rarest:
                    ratmoji = get_emoji(rarest.lower() + "rat")
                    rarest_holder = [f"<@{i}>" for i in rarest_holder]
                    joined = ", ".join(rarest_holder)
                    if len(rarest_holder) > 10:
                        joined = f"{len(rarest_holder)} people"
                    string = f"Rarest rat: {ratmoji} ({joined}'s)\n\n"
        elif type == "Value":
            unit = "value"
            sums = []
            for rat_type in rattypes:
                if not rat_type:
                    continue
                weight = sum(type_dict.values()) / type_dict[rat_type]
                sums.append(f'({weight}) * "rat_{rat_type}"')
            total_sum_expr = " + ".join(sums)
            result = (
                await Profile.filter(guild_id=message.guild.id)
                .annotate(final_value=RawSQL(total_sum_expr))
                .order_by("-final_value")
                .values("user_id", "final_value")
            )
        elif type == "Fast":
            unit = "sec"
            result = (
                await Profile.filter(guild_id=message.guild.id, time__lt=99999999999999)
                .annotate(final_value=Sum("time"))
                .order_by("final_value")
                .values("user_id", "final_value")
            )
        elif type == "Slow":
            unit = "h"
            result = (
                await Profile.filter(guild_id=message.guild.id, timeslow__gt=0)
                .annotate(final_value=Sum("timeslow"))
                .order_by("-final_value")
                .values("user_id", "final_value")
            )
        elif type == "Battlepass":
            start_date = datetime.datetime(2024, 12, 1)
            current_date = datetime.datetime.utcnow()
            full_months_passed = (current_date.year - start_date.year) * 12 + (current_date.month - start_date.month)
            if current_date.day < start_date.day:
                full_months_passed -= 1
            result = (
                await Profile.filter(guild_id=message.guild.id, season=full_months_passed)
                .annotate(final_value=Sum("battlepass"))
                .order_by("-final_value", "-progress")
                .values("user_id", "final_value", "progress")
            )
        elif type == "Cookies":
            unit = "cookies"
            result = (
                await Profile.filter(guild_id=message.guild.id, cookies__gt=0)
                .annotate(final_value=Sum("cookies"))
                .order_by("-final_value")
                .values("user_id", "final_value")
            )
            string = "Cookie leaderboard updates every 5 min\n\n"
        else:
            # qhar
            return

        # find the placement of the person who ran the command and optionally the person who pressed the button
        interactor_placement = 0
        messager_placement = 0
        for index, position in enumerate(result):
            if position["user_id"] == interaction.user.id:
                interactor_placement = index
                interactor = position["final_value"]
            if interaction.user != message.user and position["user_id"] == message.user.id:
                messager_placement = index
                messager = position["final_value"]

        if type == "Slow":
            if interactor:
                interactor = round(interactor / 3600, 2)
            if messager:
                messager = round(messager / 3600, 2)

        if type == "Fast":
            if interactor:
                interactor = round(interactor, 3)
            if messager:
                messager = round(messager, 3)

        # dont show placements if they arent defined
        if interactor and type in ["Rats", "Slow", "Value", "Cookies"]:
            if interactor <= 0:
                interactor_placement = 0
            interactor = round(interactor)
        elif interactor and type == "Fast" and interactor >= 99999999999999:
            interactor_placement = 0

        if messager and type in ["Rats", "Slow", "Value", "Cookies"]:
            if messager <= 0:
                messager_placement = 0
            messager = round(messager)
        elif messager and type == "Fast" and messager >= 99999999999999:
            messager_placement = 0

        emoji = ""
        if type == "Rats" and specific_rat != "All":
            emoji = get_emoji(specific_rat.lower() + "rat")

        # the little place counter
        current = 1
        leader = False
        for i in result[:show_amount]:
            num = i["final_value"]

            if type == "Battlepass":
                bp_season = battle["seasons"][str(full_months_passed)]
                if i["final_value"] >= len(bp_season):
                    lv_xp_req = 1500
                else:
                    lv_xp_req = bp_season[int(i["final_value"]) - 1]["xp"]

                prog_perc = math.floor((100 / lv_xp_req) * i["progress"])

                string += f"{current}. Level **{num}** *({prog_perc}%)*: <@{i['user_id']}>\n"
            else:
                if type == "Slow":
                    if num <= 0:
                        break
                    num = round(num / 3600, 2)
                elif type == "Rats" and num <= 0:
                    break
                elif type == "Value":
                    if num <= 0:
                        break
                    num = round(num)
                elif type == "Fast":
                    if num >= 99999999999999:
                        break
                    num = round(num, 3)
                elif type == "Cookies" and num <= 0:
                    break
                string = string + f"{current}. {emoji} **{num:,}** {unit}: <@{i['user_id']}>\n"

            if message.user.id == i["user_id"] and current <= 5:
                leader = True
            current += 1

        # add the messager and interactor
        if type != "Battlepass" and (messager_placement > show_amount or interactor_placement > show_amount):
            string = string + "...\n"

            # setting up names
            include_interactor = interactor_placement > show_amount and str(interaction.user.id) not in string
            include_messager = messager_placement > show_amount and str(message.user.id) not in string
            interactor_line = ""
            messager_line = ""
            if include_interactor:
                interactor_line = f"{interactor_placement}\\. {emoji} **{interactor:,}** {unit}: {interaction.user.mention}\n"
            if include_messager:
                messager_line = f"{messager_placement}\\. {emoji} **{messager:,}** {unit}: {message.user.mention}\n"

            # sort them correctly!
            if messager_placement > interactor_placement:
                # interactor should go first
                string += interactor_line
                string += messager_line
            else:
                # messager should go first
                string += messager_line
                string += interactor_line

        title = type + " Leaderboard"
        if type == "Rats":
            title = f"{specific_rat} {title}"
        title = "🏅 " + title

        embedVar = discord.Embed(title=title, description=string.rstrip(), color=0x6E593C).set_footer(text=rain_shill)

        global_user, _ = await User.get_or_create(user_id=message.user.id)

        if len(news_list) > len(global_user.news_state.strip()) or "0" in global_user.news_state.strip()[-4:]:
            embedVar.set_author(name=f"{message.user} has unread news! /news")

        # handle funny buttons
        myview = View(timeout=VIEW_TIMEOUT)

        if type == "Rats":
            dd_opts = [Option(label="All", emoji=get_emoji("staring_rat"), value="All")]

            for i in await rats_in_server(message.guild.id):
                dd_opts.append(Option(label=i, emoji=get_emoji(i.lower() + "rat"), value=i))

            dropdown = Select(
                "rat_type_dd",
                placeholder="Select a rat type",
                opts=dd_opts,
                selected=specific_rat,
                on_select=lambda interaction, option: lb_handler(interaction, type, True, option),
                disabled=locked,
            )

        emojied_options = {"Rats": "🐈", "Value": "🧮", "Fast": "⏱️", "Slow": "💤", "Battlepass": "⬆️", "Cookies": "🍪"}
        options = [Option(label=k, emoji=v) for k, v in emojied_options.items()]
        lb_select = Select(
            "lb_type",
            placeholder=type,
            opts=options,
            on_select=lambda interaction, type: lb_handler(interaction, type, True),
        )

        if not locked:
            myview.add_item(lb_select)
            if type == "Rats":
                myview.add_item(dropdown)

        # just send if first time, otherwise edit existing
        try:
            if not do_edit:
                raise Exception
            await interaction.edit_original_response(embed=embedVar, view=myview)
        except Exception:
            await interaction.followup.send(embed=embedVar, view=myview)

        if leader:
            await achemb(message, "leader", "send")

    await lb_handler(message, leaderboard_type, False, rat_type)


@bot.tree.command(description="(ADMIN) Give rats to people")
@discord.app_commands.default_permissions(manage_guild=True)
@discord.app_commands.rename(person_id="user")
@discord.app_commands.describe(person_id="who", amount="how many (negatives to remove)", rat_type="what")
@discord.app_commands.autocomplete(rat_type=rat_type_autocomplete)
async def giverat(message: discord.Interaction, person_id: discord.User, rat_type: str, amount: Optional[int]):
    if amount is None:
        amount = 1
    if rat_type not in rattypes:
        await message.response.send_message("bro what", ephemeral=True)
        return

    user, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=person_id.id)
    user[f"rat_{rat_type}"] += amount
    await user.save()
    embed = discord.Embed(
        title="Success!",
        description=f"gave {person_id.mention} {amount:,} {rat_type} rats",
        color=0x6E593C,
    )
    await message.response.send_message(person_id.mention, embed=embed, allowed_mentions=discord.AllowedMentions(users=True))


@bot.tree.command(name="setup", description="(ADMIN) Setup rat in current channel")
@discord.app_commands.default_permissions(manage_guild=True)
async def setup_channel(message: discord.Interaction):
    if await Channel.get_or_none(channel_id=message.channel.id):
        await message.response.send_message(
            "bruh you already setup rat here are you dumb\n\nthere might already be a rat sitting in chat. type `rat` to ratch it."
        )
        return

    with open("images/rat.png", "rb") as f:
        try:
            channel_permissions = await fetch_perms(message)
            needed_perms = {
                "View Channel": channel_permissions.view_channel,
                # "Manage Webhooks": channel_permissions.manage_webhooks,
                "Send Messages": channel_permissions.send_messages,
                "Attach Files": channel_permissions.attach_files,
            }
            if isinstance(message.channel, discord.Thread):
                needed_perms["Send Messages in Threads"] = channel_permissions.send_messages_in_threads

            for name, value in needed_perms.copy().items():
                if value:
                    needed_perms.pop(name)

            missing_perms = list(needed_perms.keys())
            if len(missing_perms) != 0:
                needed_perms = "\n- ".join(missing_perms)
                await message.response.send_message(
                    f":x: Missing Permissions! Please give me the following:\n- {needed_perms}\nHint: try setting channel permissions if server ones don't work."
                )
                return

            if isinstance(message.channel, discord.Thread):
                parent = bot.get_channel(message.channel.parent_id)
                if not isinstance(parent, Union[discord.TextChannel, discord.ForumChannel]):
                    raise Exception
                try:
                    wh = await parent.create_webhook(name="Rat Bot", avatar=f.read())
                except Exception:
                    await message.response.send_message(":x: Missing Permissions! Please give me the Manage Webhooks permission.")
                    return
                await Channel.create(channel_id=message.channel.id, webhook=wh.url, thread_mappings=True)
            elif isinstance(
                message.channel,
                Union[discord.TextChannel, discord.StageChannel, discord.VoiceChannel],
            ):
                try:
                    wh = await message.channel.create_webhook(name="Rat Bot", avatar=f.read())
                except Exception:
                    await message.response.send_message(":x: Missing Permissions! Please give me the Manage Webhooks permission.")
                    return
                await Channel.create(channel_id=message.channel.id, webhook=wh.url, thread_mappings=False)
        except Exception:
            await message.response.send_message("this channel gives me bad vibes.")
            return

    await spawn_rat(str(message.channel.id))
    await message.response.send_message(f"ok, now i will also send rats in <#{message.channel.id}>")


@bot.tree.command(description="(ADMIN) Undo the setup")
@discord.app_commands.default_permissions(manage_guild=True)
async def forget(message: discord.Interaction):
    if channel := await Channel.get_or_none(channel_id=message.channel.id):
        await unsetup(channel)
        await message.response.send_message(f"ok, now i wont send rats in <#{message.channel.id}>")
    else:
        await message.response.send_message("your an idiot there is literally no rat setupped in this channel you stupid")


@bot.tree.command(description="LMAO TROLLED SO HARD :JOY:")
async def fake(message: discord.Interaction):
    if message.user.id in fakecooldown and fakecooldown[message.user.id] + 60 > time.time():
        await message.response.send_message("your phone is overheating bro chill", ephemeral=True)
        return
    file = discord.File("images/australian rat.png", filename="australian rat.png")
    icon = get_emoji("egirlrat")
    perms = await fetch_perms(message)
    if not isinstance(
        message.channel,
        Union[
            discord.TextChannel,
            discord.VoiceChannel,
            discord.StageChannel,
            discord.Thread,
        ],
    ):
        return
    fakecooldown[message.user.id] = time.time()
    try:
        if not perms.send_messages or not perms.attach_files:
            raise Exception
        await message.response.send_message(
            str(icon) + ' eGirl rat hasn\'t appeared! Type "rat" to ratch ratio!',
            file=file,
        )
    except Exception:
        await message.response.send_message("i dont have perms lmao here is the ach anyways", ephemeral=True)
        pass
    await achemb(message, "trolled", "followup")


@bot.tree.command(description="(ADMIN) Force rats to appear")
@discord.app_commands.default_permissions(manage_guild=True)
@discord.app_commands.rename(rat_type="type")
@discord.app_commands.describe(rat_type="select a rat type ok")
@discord.app_commands.autocomplete(rat_type=rat_type_autocomplete)
async def forcespawn(message: discord.Interaction, rat_type: Optional[str]):
    if rat_type and rat_type not in rattypes:
        await message.response.send_message("bro what", ephemeral=True)
        return

    ch = await Channel.get_or_none(channel_id=message.channel.id)
    if ch is None:
        await message.response.send_message("this channel is not /setup-ed", ephemeral=True)
        return
    if ch.rat:
        await message.response.send_message("there is already a rat", ephemeral=True)
        return
    ch.yet_to_spawn = 0
    await ch.save()
    await spawn_rat(str(message.channel.id), rat_type, True)
    await message.response.send_message("done!\n**Note:** you can use `/giverat` to give yourself rats, there is no need to spam this")


@bot.tree.command(description="(ADMIN) Give achievements to people")
@discord.app_commands.default_permissions(manage_guild=True)
@discord.app_commands.rename(person_id="user", ach_id="name")
@discord.app_commands.describe(person_id="who", ach_id="name or id of the achievement")
@discord.app_commands.autocomplete(ach_id=ach_autocomplete)
async def giveachievement(message: discord.Interaction, person_id: discord.User, ach_id: str):
    # check if ach is real
    try:
        valid = ach_id in ach_names
    except KeyError:
        valid = False

    if not valid and ach_id.lower() in ach_titles.keys():
        ach_id = ach_titles[ach_id.lower()]
        valid = True

    person, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=person_id.id)

    if valid and ach_id == "thanksforplaying":
        await message.response.send_message("HAHAHHAHAH\nno", ephemeral=True)
        return

    if valid:
        # if it is, do the thing
        reverse = person[ach_id]
        person[ach_id] = not reverse
        await person.save()
        color, title, icon = (
            0x007F0E,
            "Achievement forced!",
            "https://wsrv.nl/?url=raw.githubusercontent.com/staring-rat/emojis/main/ach.png",
        )
        if reverse:
            color, title, icon = (
                0xFF0000,
                "Achievement removed!",
                "https://wsrv.nl/?url=raw.githubusercontent.com/staring-rat/emojis/main/no_ach.png",
            )
        ach_data = ach_list[ach_id]
        embed = (
            discord.Embed(
                title=ach_data["title"],
                description=ach_data["description"],
                color=color,
            )
            .set_author(name=title, icon_url=icon)
            .set_footer(text=f"for {person_id.name}")
        )
        await message.response.send_message(person_id.mention, embed=embed, allowed_mentions=discord.AllowedMentions(users=True))
    else:
        await message.response.send_message("i cant find that achievement! try harder next time.", ephemeral=True)


@bot.tree.command(description="(ADMIN) Reset people")
@discord.app_commands.default_permissions(manage_guild=True)
@discord.app_commands.rename(person_id="user")
@discord.app_commands.describe(person_id="who")
async def reset(message: discord.Interaction, person_id: discord.User):
    async def confirmed(interaction):
        if interaction.user.id == message.user.id:
            await interaction.response.defer()
            try:
                og = await interaction.original_response()
                profile, _ = await Profile.get_or_create(guild_id=message.guild.id, user_id=person_id.id)
                profile.guild_id = og.id
                await profile.save()
                async for p in Prism.filter(guild_id=message.guild.id, user_id=person_id.id):
                    p.guild_id = og.id
                    await p.save()
                await interaction.edit_original_response(
                    content=f"Done! rip {person_id.mention}. f's in chat.\njoin our discord to rollback: <https://discord.gg/staring>", view=None
                )
            except Exception:
                await interaction.edit_original_response(
                    content="ummm? this person isnt even registered in rat bot wtf are you wiping?????",
                    view=None,
                )
        else:
            await do_funny(interaction)

    view = View(timeout=VIEW_TIMEOUT)
    button = Button(style=ButtonStyle.red, label="Confirm")
    button.callback = confirmed
    view.add_item(button)
    await message.response.send_message(f"Are you sure you want to reset {person_id.mention}?", view=view, allowed_mentions=discord.AllowedMentions(users=True))


@bot.tree.command(description="(HIGH ADMIN) [VERY DANGEROUS] Reset all Rat Bot data of this server")
@discord.app_commands.default_permissions(administrator=True)
async def nuke(message: discord.Interaction):
    warning_text = "⚠️ This will completely reset **all** Rat Bot progress of **everyone** in this server. Spawn channels and their settings *will not be affected*.\nPress the button 5 times to continue."
    counter = 5

    async def gen(counter):
        lines = [
            "",
            "I'm absolutely sure! (1)",
            "I understand! (2)",
            "You can't undo this! (3)",
            "This is dangerous! (4)",
            "Reset everything! (5)",
        ]
        view = View(timeout=VIEW_TIMEOUT)
        button = Button(label=lines[max(1, counter)], style=ButtonStyle.red)
        button.callback = count
        view.add_item(button)
        return view

    async def count(interaction: discord.Interaction):
        nonlocal message, counter
        if interaction.user.id == message.user.id:
            await interaction.response.defer()
            counter -= 1
            if counter == 0:
                # ~~Scary!~~ Not anymore!
                # how this works is we basically change the server id to the message id and then add user with id of 0 to mark it as deleted
                # this can be rolled back decently easily by asking user for the id of nuking message

                changed_profiles = []
                changed_prisms = []

                async for i in Profile.filter(guild_id=message.guild.id):
                    i.guild_id = interaction.message.id
                    changed_profiles.append(i)

                async for i in Prism.filter(guild_id=message.guild.id):
                    i.guild_id = interaction.message.id
                    changed_prisms.append(i)

                if changed_profiles:
                    await Profile.bulk_update(changed_profiles, fields=["guild_id"])
                if changed_prisms:
                    await Prism.bulk_update(changed_prisms, fields=["guild_id"])
                await Profile.create(guild_id=interaction.message.id, user_id=0)

                try:
                    await interaction.edit_original_response(
                        content="Done. If you want to roll this back, please contact us in our discord: <https://discord.gg/staring>.",
                        view=None,
                    )
                except Exception:
                    await interaction.followup.send("Done. If you want to roll this back, please contact us in our discord: <https://discord.gg/staring>.")
            else:
                view = await gen(counter)
                try:
                    await interaction.edit_original_response(content=warning_text, view=view)
                except Exception:
                    pass
        else:
            await do_funny(interaction)

    view = await gen(counter)
    await message.response.send_message(warning_text, view=view)


async def recieve_vote(request):
    if request.headers.get("authorization", "") != config.WEBHOOK_VERIFY:
        return web.Response(text="bad", status=403)
    request_json = await request.json()

    user, _ = await User.get_or_create(user_id=int(request_json["user"]))
    if user.vote_time_topgg + 43100 > time.time():
        # top.gg is NOT realiable with their webhooks, but we politely pretend they are
        return web.Response(text="you fucking dumb idiot", status=200)

    if user.vote_streak < 10:
        extend_time = 24
    elif user.vote_streak < 20:
        extend_time = 36
    elif user.vote_streak < 50:
        extend_time = 48
    elif user.vote_streak < 100:
        extend_time = 60
    else:
        extend_time = 72

    user.reminder_vote = 1
    user.total_votes += 1
    if user.vote_time_topgg + extend_time * 3600 <= time.time():
        # streak end
        if user.max_vote_streak < user.vote_streak:
            user.max_vote_streak = user.vote_streak
        user.vote_streak = 1
    else:
        user.vote_streak += 1
    user.vote_time_topgg = time.time()
    await user.save()

    try:
        channeley = await bot.fetch_user(int(request_json["user"]))
        if user.vote_streak != 5 and user.vote_streak % 5 == 0:
            gold_suffix = f"(+1 {get_emoji('goldpack')} Gold pack!)"
        else:
            gold_suffix = f"(Bonus {get_emoji('goldpack')} Gold Pack at {max(10, math.ceil(user.vote_streak / 5) * 5)} streak)"
        await channeley.send(
            "\n".join(
                [
                    f"Thanks for voting! Streak: {user.vote_streak:,} {gold_suffix}",
                    "To claim your rewards, run `/battlepass` in every server you want.",
                    f"You can vote again <t:{int(time.time()) + 43200}:R>.",
                    f"Vote within the next {extend_time} hours to not lose your streak.",
                ]
            )
        )
    except Exception:
        pass

    return web.Response(text="ok", status=200)


async def check_supporter(request):
    if request.headers.get("authorization", "") != config.WEBHOOK_VERIFY:
        return web.Response(text="bad", status=403)
    request_json = await request.json()

    user, _ = await User.get_or_create(user_id=int(request_json["user"]))
    return web.Response(text="1" if user.premium else "0", status=200)


# rat bot uses glitchtip (sentry alternative) for errors, here u can instead implement some other logic like dming the owner
async def on_error(*args, **kwargs):
    raise


async def setup(bot2):
    global bot, RAIN_ID, vote_server

    for command in bot.tree.walk_commands():
        # copy all the commands
        command.guild_only = True
        bot2.tree.add_command(command)

    context_menu_command = discord.app_commands.ContextMenu(name="ratch", callback=ratch)
    context_menu_command.guild_only = True
    bot2.tree.add_command(context_menu_command)

    # copy all the events
    bot2.on_ready = on_ready
    bot2.on_guild_join = on_guild_join
    bot2.on_message = on_message
    bot2.on_connect = on_connect
    bot2.on_error = on_error

    if config.WEBHOOK_VERIFY:
        app = web.Appliration()
        app.add_routes([web.post("/", recieve_vote), web.get("/supporter", check_supporter)])
        vote_server = web.AppRunner(app)
        await vote_server.setup()
        site = web.TCPSite(vote_server, "0.0.0.0", 8069)
        await site.start()

    # finally replace the fake bot with the real one
    bot = bot2

    config.SOFT_RESTART_TIME = time.time()

    app_commands = await bot.tree.sync()
    for i in app_commands:
        if i.name == "rain":
            RAIN_ID = i.id

    if bot.is_ready() and not on_ready_debounce:
        await on_ready()


async def teardown(bot):
    cookie_updates = []
    for cookie_id, cookies in temp_cookie_storage.items():
        p, _ = await Profile.get_or_create(guild_id=cookie_id[0], user_id=cookie_id[1])
        p.cookies = cookies
        cookie_updates.append(p)

    if cookie_updates:
        await Profile.bulk_update(cookie_updates, fields=["cookies"])

    if config.WEBHOOK_VERIFY:
        await vote_server.cleanup()


# Reusable UI components
class Option:
    def __init__(self, label, emoji, value=None):
        self.label = label
        self.emoji = emoji
        self.value = value if value is not None else label


class Select(discord.ui.Select):
    on_select = None

    def __init__(
        self,
        id: str,
        placeholder: str,
        opts: list[Option],
        selected: str = None,
        on_select: callable = None,
        disabled: bool = False,
    ):
        options = []
        if on_select is not None:
            self.on_select = on_select

        for opt in opts:
            options.append(discord.SelectOption(label=opt.label, value=opt.value, emoji=opt.emoji, default=opt.value == selected))

        super().__init__(
            placeholder=placeholder,
            options=options,
            custom_id=id,
            max_values=1,
            min_values=1,
            disabled=disabled,
        )

    async def callback(self, interaction: discord.Interaction):
        if self.on_select is not None and callable(self.on_select):
            await self.on_select(interaction, self.values[0])
