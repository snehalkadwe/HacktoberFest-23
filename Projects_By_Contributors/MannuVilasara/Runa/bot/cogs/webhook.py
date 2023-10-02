import nextcord
from nextcord.ext import commands


class Webhook(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


def setup(bot):
    bot.add_cog(Webhook(bot))
