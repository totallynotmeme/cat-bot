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

import json
import config
from tortoise.models import Model
from tortoise import fields, Tortoise


async def init():
    if config.DB_TYPE == "SQLITE":
        db_url = "sqlite://ratbot.db"
    elif config.DB_TYPE == "POSTGRES":
        db_url = f"asyncpg://rat_bot:{config.DB_PASS}@localhost/rat_bot"
    await Tortoise.init(db_url=db_url, modules={"models": ["database"]})
    await Tortoise.generate_schemas(safe=True)


async def close():
    await Tortoise.close_connections()


rattypes = [
    "Fine",
    "Nice",
    "Good",
    "Rare",
    "Wild",
    "Baby",
    "Epic",
    "Sus",
    "Brave",
    "Rickroll",
    "Reverse",
    "Superior",
    "Trash",
    "Legendary",
    "Mythic",
    "8bit",
    "Corrupt",
    "Professor",
    "Divine",
    "Real",
    "Ultimate",
    "eGirl",
]


class CappedIntField(fields.IntField):
    MAX_VALUE = 2147483647
    MIN_VALUE = -2147483648

    def to_db_value(self, value, instance):
        if value is not None:
            return max(self.MIN_VALUE, min(self.MAX_VALUE, value))
        return value


class Profile(Model):
    user_id = fields.BigIntField()
    guild_id = fields.BigIntField(db_index=True)

    time = fields.FloatField(default=99999999999999)  # fastest ratch time
    timeslow = fields.FloatField(default=0)  # slowest ratch time

    timeout = fields.BigIntField(default=0)  # /preventratch timestamp
    rataine_active = fields.BigIntField(default=0)  # rataine timestamp

    dark_market_level = fields.SmallIntField(default=0)  # dark market level
    dark_market_active = fields.BooleanField(default=False)  # dark market unlocked bool
    story_complete = fields.BooleanField(default=False)  # whether story is complete

    finale_seen = fields.BooleanField(default=False)  # whether the finale cutscene was seen
    debt_seen = fields.BooleanField(default=False)  # whether the debt cutscene was seen

    rataine_week = fields.SmallIntField(default=0)  # light market purcashes this week
    recent_week = fields.SmallIntField(default=0)  # the week

    funny = fields.IntField(default=0)  # private embed click amount
    facts = fields.IntField(default=0)  # /fact amount
    gambles = fields.SmallIntField(default=0)  # casino spins amount

    cookies = fields.BigIntField(default=0)  # cookies clicked

    rain_minutes = fields.SmallIntField(default=0)  # server-locked rains amount

    slot_spins = fields.IntField(default=0)
    slot_wins = fields.IntField(default=0)
    slot_big_wins = fields.SmallIntField(default=0)

    battlepass = fields.SmallIntField(default=0)  # battlepass level
    progress = fields.SmallIntField(default=0)  # battlepass progress (in xp)
    season = fields.SmallIntField(default=0)  # if this doesnt match current season it will reset everything

    # battelpass quests fields
    vote_reward = fields.SmallIntField(default=0)
    vote_cooldown = fields.BigIntField(default=1)

    ratch_quest = fields.CharField(default="", max_length=30)
    ratch_progress = fields.SmallIntField(default=0)
    ratch_cooldown = fields.BigIntField(default=1)
    ratch_reward = fields.SmallIntField(default=0)

    misc_quest = fields.CharField(default="", max_length=30)
    misc_progress = fields.SmallIntField(default=0)
    misc_cooldown = fields.BigIntField(default=1)
    misc_reward = fields.SmallIntField(default=0)

    bp_history = fields.CharField(default="", max_length=2000)

    reminder_ratch = fields.BigIntField(default=0)  # timestamp of last ratch reminder
    reminder_misc = fields.BigIntField(default=0)  # timestamp of last misc reminder
    # vote timestamp is in the User model

    reminders_enabled = fields.BooleanField(default=False)

    highlighted_stat = fields.CharField(default="time_records", max_length=30)

    # advanced stats
    boosted_ratches = fields.IntField(default=0)  # amount of ratches boosted by prism
    rataine_activations = fields.IntField(default=0)  # amount of rataine activations
    rataine_bought = fields.IntField(default=0)  # amount of rataine bought
    quests_completed = fields.IntField(default=0)  # amount of quests completed
    total_ratches = fields.IntField(default=0)  # total amount of ratches
    total_ratch_time = fields.BigIntField(default=0)  # total amount of time spent ratching
    perfection_count = fields.IntField(default=0)  # amount of perfection achievements
    rain_participations = fields.IntField(default=0)  # amount of ratches during rains
    rain_minutes_started = fields.IntField(default=0)  # amount of rain minutes started
    reminders_set = fields.IntField(default=0)  # amount of reminders set
    rats_gifted = CappedIntField(default=0)  # amount of rats gifted
    rat_gifts_recieved = CappedIntField(default=0)  # amount of rat gifts recieved
    trades_completed = fields.IntField(default=0)  # amount of trades completed
    rats_traded = CappedIntField(default=0)  # amount of rats traded
    ttt_played = fields.IntField(default=0)  # amount of times played the TTT
    ttt_won = fields.IntField(default=0)  # amount of TTT wins
    ttt_draws = fields.IntField(default=0)  # amount of TTT draws
    packs_opened = fields.IntField(default=0)  # amount of packs opened
    pack_upgrades = fields.IntField(default=0)  # amount of pack upgrades
    new_user = fields.BooleanField(default=True)  # whether the user is new

    puzzle_pieces = fields.IntField(default=0)  # amount of puzzle pieces collected for birthday 2025 event

    def __getitem__(self, item):
        return getattr(self, item)

    def __setitem__(self, item, value):
        setattr(self, item, value)

    # thanks chatgpt
    # rat types
    for rattype in rattypes:
        locals()[f"rat_{rattype}"] = CappedIntField(default=0)

    # aches
    with open("config/aches.json", "r") as f:
        ach_list = json.load(f)
    for ach in ach_list.keys():
        locals()[ach] = fields.BooleanField(default=False)

    # packs
    for pack in ["Wooden", "Stone", "Bronze", "Silver", "Gold", "Platinum", "Diamond", "Celestial"]:
        locals()[f"pack_{pack.lower()}"] = fields.IntField(default=0)

    class Meta:
        # haha facebook meta reference
        indexes = (("user_id", "guild_id"),)


class User(Model):
    user_id = fields.BigIntField(unique=True, db_index=True, primary_key=True)

    vote_time_topgg = fields.BigIntField(default=0)  # timestamp of last vote
    reminder_vote = fields.BigIntField(default=0)  # timestamp of last vote reminder

    custom = fields.CharField(default="", max_length=50)  # custom rat name
    custom_num = fields.IntField(default=1)  # custom rat amount
    emoji = fields.CharField(default="", max_length=10)  # /editprofile emoji
    color = fields.CharField(default="", max_length=10)  # /editprofile color
    image = fields.CharField(default="", max_length=500)  # /editprofile image

    rain_minutes = fields.SmallIntField(default=0)  # rain minute balance
    premium = fields.BooleanField(default=False)  # whether the user has supporter
    claimed_free_rain = fields.BooleanField(default=False)  # whether the user has claimed their free rain

    news_state = fields.CharField(default="", max_length=2000)

    # advanced stats
    total_votes = fields.IntField(default=0)  # total amount of votes
    max_vote_streak = fields.IntField(default=0)  # max vote streak
    vote_streak = fields.IntField(default=0)  # current vote streak


class Channel(Model):
    channel_id = fields.BigIntField(unique=True, db_index=True, primary_key=True)

    rat = fields.BigIntField(default=0)  # rat message id
    rattype = fields.CharField(default="", max_length=20)  # curently spawned rat type (parsed from msg if none)
    forcespawned = fields.BooleanField(default=False)  # whether the current rat is forcespawned

    thread_mappings = fields.BooleanField(default=False)  # whether the channel is a thread

    spawn_times_min = fields.BigIntField(default=120)  # spawn times minimum
    spawn_times_max = fields.BigIntField(default=1200)  # spawn times maximum

    lastratches = fields.BigIntField(default=0)  # timestamp of last ratch
    yet_to_spawn = fields.BigIntField(default=0)  # timestamp of the next ratch, if any
    rat_rains = fields.BigIntField(default=0)  # timestamp of rain end, if any

    appear = fields.CharField(default="", max_length=4000)
    cought = fields.CharField(default="", max_length=4000)

    webhook = fields.CharField(default="", max_length=500)  # webhook url


class Prism(Model):
    user_id = fields.BigIntField()
    guild_id = fields.BigIntField(db_index=True)

    time = fields.BigIntField()  # creation time
    creator = fields.BigIntField()  # original crafter
    name = fields.CharField(max_length=20)  # name (duh)

    ratches_boosted = fields.IntField(default=0)  # amount of boosts from ratches

    class Meta:
        indexes = (("user_id", "guild_id"),)


class Reminder(Model):
    user_id = fields.BigIntField()
    time = fields.BigIntField(db_index=True)
    text = fields.CharField(max_length=2000)
