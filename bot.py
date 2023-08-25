from pymongo import MongoClient
import discord

from discord.ext import commands
from discord.ext import tasks

import textwrap
import datetime
from dateutil.tz import gettz

import os

from dotenv import load_dotenv
import json

load_dotenv()


client = MongoClient(os.environ.get("MONGO_URI"))
time = datetime.time(hour=13, minute=37, tzinfo=gettz("Asia/Jerusalem"))

class MyBot(commands.Bot):

    async def on_ready(self):
        print("Bot is ready!")
        self.post_1337.start()
        @self.before_invoke
        async def before_command(ctx):
            ctx.before_message = await ctx.send("Processing, please wait...")
        self.register_commands()

    
    @tasks.loop(time=time)
    async def post_1337(self):
        db = client["Sentences"]
        sentences = db["Sentences"]
        all_s = sentences.find()
        for s in all_s:
            c_id = s.get("channel_id")
            current = s.get("current")
            c = discord.utils.get(self.get_all_channels(), id=c_id)
            try:
                await c.send(content=s.get("sentences")[current])
                sentences.find_one_and_update(filter={
                    "channel_id": c_id,

                }, update={
                    "$set": {
                        "current": (current+1)%len(s.get("sentences"))
                    }
                })
            except AttributeError:
                print(f"Can't send to channel with id: {c_id}")
            except IndexError:
                await c.send(content="No sentence were added! have a cake: 🎂🎂🎂🎂")



    def register_commands(self):


        
        @self.command("add", pass_context=True)
        async def _add(ctx: commands.Context, sentence: str):
            db = client["Sentences"]
            sentences = db["Sentences"]
            sentences.find_one_and_update(filter={
                "channel_id": ctx.channel.id
            }, update={
                "$push": {
                    "sentences": sentence
                }
            })
            await ctx.before_message.edit(content=f"Added `{textwrap.shorten(sentence, 25, placeholder='...')}` successfully!")
        
        @_add.error
        async def _add_error(ctx, error):
            if isinstance(error, commands.errors.MissingRequiredArgument):
                await ctx.send(content="No sentence was given to add, please input a sentence!")


        @self.command("setup", pass_context=True)
        async def _setup(ctx: commands.Context):
            db = client["Sentences"]
            sentences = db["Sentences"]
            sentences.insert_one({
                "channel_id": ctx.channel.id,
                "sentences": [],
                "current": 0
            })
            await ctx.before_message.edit(content="Setup successfully finished!")
        
        


        @self.command("view", pass_context=True)
        async def _view(ctx):
            db = client["Sentences"]
            sentences = db["Sentences"]
            doc = sentences.find_one({
                "channel_id": ctx.channel.id
            })
            all_s = doc.get("sentences")
            if len(all_s) <= 0:
                await ctx.before_message.edit(content="No sentences were found, bitchass, add some sentences!")
                return
            m = ""
            for i,s in enumerate(all_s):
                 m += f"{i+1}. {textwrap.shorten(s.get('content'), 25, placeholder='...')}\n"
            await ctx.before_message.edit(content=m)
        @self.command("del", pass_context=True)
        async def _del(ctx, index: int):
            db = client["Sentences"]
            sentences = db["Sentences"]
            sentences.find_one_and_update(filter={
                "channel_id": ctx.channel.id
            }, update={
                "$unset": {f"sentences.{index-1}": 1}
            })
            sentences.find_one_and_update(filter={
                "channel_id": ctx.channel.id
            }, update={
                "$pull": {"sentences": None}
            })
            await ctx.before_message.edit(content="Deleted sentence successfully!")
                     


bot = MyBot(command_prefix=discord.ext.commands.when_mentioned_or("!"), intents=discord.Intents.all())

bot.run(os.environ.get("TOKEN"))




