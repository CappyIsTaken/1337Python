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
        print(f"{self.user.display_name} is ready!")
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
                await c.send(content=f"{s.get('sentences')[current]} @everyone")
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
                await c.send(content="No sentences were added! have a cake: 🎂🎂🎂🎂")



    def register_commands(self):


        @self.command("unlock", pass_context=True, aliases=["u"])
        @commands.is_owner()
        async def _unlock(ctx: commands.Context):
            db = client["Sentences"]
            sentences = db["Sentences"]
            sentences.find_one_and_update(filter={
                "channel_id": ctx.channel.id
            }, update={
                "$set": {
                    "locked": False
                }
            })
            await ctx.before_message.edit(content="Unlocked the channel!")

        
        @_unlock.error
        async def _unlock_error(ctx, error):
            if isinstance(error, commands.errors.NotOwner):
                await ctx.send(content="You ain't the owner, don't try me!!!")  
        
        @self.command("lock", pass_context=True, aliases=["l"])
        @commands.is_owner()
        async def _lock(ctx: commands.Context):
            db = client["Sentences"]
            sentences = db["Sentences"]
            sentences.find_one_and_update(filter={
                "channel_id": ctx.channel.id
            }, update={
                "$set": {
                    "locked": True
                }
            })
            await ctx.before_message.edit(content="Locked the channel!")
        @_lock.error
        async def _lock_error(ctx, error):
            if isinstance(error, commands.errors.NotOwner):
                await ctx.send(content="You ain't the owner, don't try me!!!") 
        
        @self.command("add", pass_context=True, aliases=["a"])
        async def _add(ctx: commands.Context, sentence: str):
            """
            Adds a sentence to the sentences for this current channel!
            """
            db = client["Sentences"]
            sentences = db["Sentences"]

            doc = sentences.find_one(filter={
                "channel_id": ctx.channel.id
            })
            locked_state = doc.get("locked")
            if locked_state:
                await ctx.before_message.edit(content="The owner has disabled adding sentences, try again later!")
                return

            sentences.update_one(filter={
                "channel_id": ctx.channel.id
            }, update={
                "$push": {
                    "sentences": sentence
                }
            })
            await ctx.before_message.edit(content=f"Added `{textwrap.shorten(sentence, 50, placeholder='...')}` successfully!")
        
        @_add.error
        async def _add_error(ctx, error):
            if isinstance(error, commands.errors.MissingRequiredArgument):
                await ctx.send(content="No sentence was given to add, please input a sentence!")


        @self.command("setup", pass_context=True, aliases=["s"])
        @commands.is_owner()
        async def _setup(ctx: commands.Context):
            """
            Sets up the channel for the bot!
            """
            db = client["Sentences"]
            sentences = db["Sentences"]
            sentences.insert_one({
                "channel_id": ctx.channel.id,
                "sentences": [],
                "current": 0
            })
            await ctx.before_message.edit(content="Setup successfully finished!")
        
        

        @self.command("test-post", pass_context=True, aliases=["tp"])
        @commands.is_owner()
        async def test_post(ctx):
            """
            Admin command to check posting!
            """
            await self.post_1337()
            await ctx.send("Successful!")
        
        @test_post.error
        async def _test_post_error(ctx, error):
            if isinstance(error, commands.errors.NotOwner):
                await ctx.send(content="You ain't the owner, don't try me!!!")  



        @self.command("view", pass_context=True, aliases=["v"])
        async def _view(ctx, index: int = 0):
            """
            Shows all the sentences for this current channel, or if passed index: show at index
            """

            db = client["Sentences"]
            sentences = db["Sentences"]
            doc = sentences.find_one({
                "channel_id": ctx.channel.id
            })
            all_s = doc.get("sentences")
            if len(all_s) <= 0:
                await ctx.before_message.edit(content="No sentences were found, bitchass, add some sentences!")
                return
            if index <= 0:
                m = f"Current: {doc.get('current')+1}\n"
                for i,s in enumerate(all_s):
                    m += f"{i+1}. `{textwrap.shorten(s, 50, placeholder='...')}`\n"
                await ctx.before_message.edit(content=m)
            else:
                try:
                    await ctx.before_message.edit(content=all_s[index-1])
                except IndexError:
                    await ctx.before_message.edit(content="No sentence was found at that index!")

       

        @self.command("del", pass_context=True, aliases=["d"])
        async def _del(ctx, index: int):
            """
            Deletes a sentence given an index in the list
            """
            db = client["Sentences"]
            sentences = db["Sentences"]
            t = sentences.find_one_and_update(filter={
                "channel_id": ctx.channel.id
            }, update={
                "$unset": {f"sentences.{index-1}": 1}
            })
            t1 = sentences.find_one_and_update(filter={
                "channel_id": ctx.channel.id
            }, update={
                "$pull": {"sentences": None}
            })
            await ctx.before_message.edit(content="Deleted sentence successfully!")

        @_del.error
        async def _del_error(ctx, error):
            if isinstance(error, commands.errors.MissingRequiredArgument):
                await ctx.send(content="No index was given, please input an index!")             


bot = MyBot(command_prefix=discord.ext.commands.when_mentioned_or("!"), intents=discord.Intents.all())

bot.run(os.environ.get("TOKEN"))




