from pyvolt.ext import commands

from bot import Ramen

class Help(commands.Gear):
    def __init__(self, bot: Ramen):
        self.bot = bot
    
    @commands.command(name="help")
    async def help_command(self, ctx: commands.Context):
        await ctx.send("woah! this is a help command, you're not as dumb as ")

async def setup(bot: Ramen) -> None:
    await bot.add_gear(Help(bot))
        
