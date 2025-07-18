from pyvolt.ext import commands
from tools.db_funcs import *
from bot import Toko

import pyvolt
import time

class Help(commands.Gear):
    def __init__(self, bot: Toko):
        self.bot = bot
    
    def get_avatar_url(self, user: pyvolt.User) -> str:
        if user.avatar:
            return user.avatar.url()
        return self.bot.http.url_for(pyvolt.routes.USERS_GET_DEFAULT_AVATAR.compile(user_id=user.id))

    @commands.command(name="help")
    async def help_command(self, ctx: commands.Context):
        msg = await ctx.send("woah! this is a help command, you're not as dumb as you look")
        try:
            time.sleep(1)

        except Exception as e:
            await self.bot.logger.error(e)


async def setup(bot: Toko) -> None:
    await bot.add_gear(Help(bot))       