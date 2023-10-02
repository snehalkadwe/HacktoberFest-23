import nextcord

from nextcord.ext import *
from nextcord import *


class ErrorCog(commands.Cog, name="Help"):
    """help"""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        try:
            if hasattr(ctx.command, "on_error") or ctx.command is None:
                return
            else:
                embed = nextcord.Embed(
                    title=f"Error in {ctx.command}",
                    description=f"`{ctx.command.qualified_name} {ctx.command.signature}`\n{error}",
                    color=0xFD9FA1,
                )
                await ctx.send(embed=embed)
        except:
            embed = nextcord.Embed(
                title=f"Error in {ctx.command}", description=f"{error}", color=0xFD9FA1
            )
            await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_application_command_error(self, interaction, error):
        embed = nextcord.Embed(
            title=f"Error in Slash Command", description=f"{error}", color=0xFD9FA1
        )
        await interaction.send(embed=embed)

    # help
    @nextcord.slash_command(
        description="Displays a list of all the slash commands for Runa."
    )
    async def help(self, interaction):
        embed = nextcord.Embed(color=0xFD9FA1)
        cogs_desc = ""
        for x in self.bot.cogs:
            cogs_desc += "**{}** - {}".format(x, self.bot.cogs[x].__doc__) + "\n\n"
        embed.add_field(
            name="Slash Commands List",
            value=cogs_desc[0 : len(cogs_desc) - 1],
            inline=False,
        )
        await interaction.send(embed=embed)


def setup(bot):
    bot.add_cog(ErrorCog(bot))
    print("Error is loaded")
