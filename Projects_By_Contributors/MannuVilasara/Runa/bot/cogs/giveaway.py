import nextcord
import asyncio
import humanfriendly
import datetime
import random

from datetime import datetime, timedelta
from nextcord.ext import commands, application_checks


class Giveaway(commands.Cog):
    """giveaway, reroll"""

    def __init__(self, bot):
        self.bot = bot

    # giveaway command
    @nextcord.slash_command(description="Creates a giveaway.")
    @application_checks.has_permissions(manage_channels=True)
    async def giveaway(self, interaction):
        await interaction.send(
            "Let's start with this giveaway! Answer these questions within 15 seconds!"
        )
        questions = [
            "Which channel should it be hosted in?",
            "What should be the duration of the giveaway? (s|m|h|d)",
            "What is the prize of the giveaway?",
            "How many winners?",
        ]
        answers = []

        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel

        for i in questions:
            await interaction.send(i)
            try:
                msg = await self.bot.wait_for("message", timeout=15.0, check=check)
            except asyncio.TimeoutError:
                await interaction.send(
                    "You didn't answer in time, please be quicker next time!"
                )
                return
            else:
                answers.append(msg.content)
        try:
            c_id = int(answers[0][2:-1])
        except:
            await interaction.send(
                f"You didn't mention a channel properly. Do it like this {interaction.channel.mention} next time."
            )
            return
        channel = self.bot.get_channel(c_id)
        time = humanfriendly.parse_timespan(answers[1])
        if time == -1:
            await interaction.send(
                f"You didn't answer with a proper unit. Use (s|m|h|d) next time!"
            )
            return
        elif time == -2:
            await interaction.send(
                f"The time should just be an integer. Please enter an integer next time."
            )
            return
        prize = answers[2]
        await interaction.send(
            f"The giveaway will be in {channel.mention} and will last {answers[1]}!"
        )
        embed = nextcord.Embed(
            title="Giveaway!", description=f"{prize}", color=interaction.user.color
        )
        embed.add_field(name="Hosted by:", value=interaction.user.mention)
        embed.add_field(name="Winners:", value=answers[3])
        epochEnd = nextcord.utils.format_dt(datetime.now() + timedelta(seconds=time))
        my_msg = await channel.send(embed=embed)
        await channel.send(f"Ends at {epochEnd}!")
        await my_msg.add_reaction("🎉")
        await asyncio.sleep(time)
        new_msg = await channel.fetch_message(my_msg.id)
        users = await new_msg.reactions[0].users().flatten()
        users.remove(self.bot.get_user(937219050365386782))
        for _ in range(int(answers[3])):
            winner = random.choice(users)
            await channel.send(
                f"Congratulations! {winner.mention} won the prize: {prize}!"
            )

    # reroll command
    @nextcord.slash_command(description="Rerolls a giveaway.")
    @application_checks.has_permissions(manage_channels=True)
    async def reroll(self, interaction, channel: nextcord.TextChannel, messageid):
        try:
            new_msg = await channel.fetch_message(messageid)
        except:
            return await interaction.send(
                "The ID that was entered was incorrect, make sure you have entered the correct giveaway message ID."
            )
        users = await new_msg.reactions[0].users().flatten()
        users.pop(users.index(self.bot.user))
        winner = random.choice(users)
        await channel.send(
            f"Congratulations the new winner is: {winner.mention} for the giveaway rerolled!"
        )
        await interaction.send("I have successfully rerolled!")


def setup(bot):
    bot.add_cog(Giveaway(bot))
    print("Giveaway is loaded")
