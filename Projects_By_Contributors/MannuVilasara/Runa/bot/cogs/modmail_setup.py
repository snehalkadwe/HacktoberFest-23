import pymongo
import nextcord
from nextcord.ext import commands
from utils.mongo import mongo, servers
from main import bot


class Modmail_Setup(commands.Cog):
    """~modmail, ~close, modmail pingrole, modmail logs, modmail transcript"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # modmail
    @commands.command(name="modmail")
    @commands.has_guild_permissions()
    async def modmail(
        self, ctx: commands.Context, args=None, member: nextcord.Member = None
    ):
        if args == None:
            embed = nextcord.Embed(
                description=f"**No options were given**\n\n__command example__: `{self.bot.command_prefix}modmail [setup, disable, block, unblock]`\nUse ~modmail setup to enable modmail. \nUse ~modmail disable to disable modmail. \nUse ~modmail block to block a member from using modmail, and ~modmail unblock to unblock. \nUse /pingrole to set the role you want pinged when a ticket is created. \nUse /logs to set the log channel where you want all ticket activity to be sent to. \nUse /transcript to set the channel you want ticket transcripts to be sent in.\nUse ~close in an open ticket to close the ticket.\nUse /modmail category to set the category where tickets should go.",
                color=nextcord.Colour.red(),
            )
            await ctx.send(embed=embed)
            return
        if ctx.author.guild_permissions.manage_guild == True:
            if args == "setup":
                db = servers()
                guild = db.find_one({"_id": str(ctx.author.guild.id)})
                if guild:
                    await ctx.send("`Modmail is already enabled`")
                    return
                document = {
                    "_id": str(ctx.guild.id),
                    "name": str(ctx.guild.name),
                    "blocklist": [],
                    "log_channel": None,
                    "pingrole": None,
                    "transcripts": None,
                    "category": None,
                }
                db.insert_one(document)
                await ctx.send("Modmail enabled")
            elif args == "disable":
                db = servers()
                guild = db.find_one({"_id": str(ctx.author.guild.id)})
                if guild:
                    db.delete_one(guild)
                    await ctx.send("Modmail disabled")
                    return
                await ctx.send("Modmail is already disabled.")
            elif args == "block":
                if member == None:
                    await ctx.send("Please also select the user to block")
                    return
                db = servers()
                server = db.find_one({"_id": str(ctx.author.guild.id)})
                if server:
                    if int(member.id) in server["blocklist"]:
                        await ctx.send("`Member already blocked`")
                        return
                    db.delete_one(server)
                    blocklist = server["blocklist"]
                    blocklist.append(int(member.id))
                    server["blocklist"] = blocklist
                    db.insert_one(server)
                    await ctx.send(f"`blocked {member.name} from making tickets`")
                else:
                    await ctx.send(
                        f"`Guild has no Modmail Setup. Run {self.bot.command_prefix}modmail setup to setup modmail`"
                    )
            elif args == "unblock":
                if member == None:
                    await ctx.send("Please also select the user to unblock")
                    return
                db = servers()
                server = db.find_one({"_id": str(ctx.author.guild.id)})
                if server:
                    if int(member.id) in server["blocklist"]:
                        db.delete_one(server)
                        blocklist = server["blocklist"]
                        index = blocklist.index(int(member.id))
                        blocklist.pop(index)
                        server["blocklist"] = blocklist
                        db.insert_one(server)
                        await ctx.send(f"`unblocked {member.name} Tickets`")
                        return
                    await ctx.send("`User is not blocked`")

                else:
                    await ctx.send(
                        f"`Guild has no Modmail Setup. Run {self.bot.command_prefix}modmail setup to setup modmail`"
                    )
            else:
                embed = nextcord.Embed(
                    description=f"**Invalid Options**\n\n__command example__: `{self.bot.command_prefix}modmail [setup,disable,block]`",
                    color=nextcord.Colour.red(),
                )
                await ctx.send(embed=embed)
        else:
            await ctx.send("No Permission")

    @nextcord.slash_command(name="modmail", description="Modmail Feature for guild")
    @commands.has_guild_permissions(manage_guild=True)
    async def mail(self, interaction: nextcord.Interaction):
        pass

    @mail.subcommand(name="transcripts")
    @commands.has_guild_permissions(manage_guild=True)
    async def transcripts(
        self, interaction: nextcord.Interaction, channel: nextcord.TextChannel = None
    ):
        if interaction.user.guild_permissions.manage_guild != True:
            await interaction.response.send_message("No permission", ephemeral=True)
            return
        db = servers()
        guild = db.find_one({"_id": str(interaction.guild.id)})
        if guild:
            if channel == None:
                db.delete_one(guild)
                guild["transcripts"] = None
                db.insert_one(guild)
                await interaction.response.send_message("`REMOVED TRANSCRIPTS CHANNEL`")
                return
            db.delete_one(guild)
            guild["transcripts"] = int(channel.id)
            db.insert_one(guild)
            await interaction.response.send_message(
                f"`Saved` {channel.mention} `as transcripts channel. All ticket transcripts will go here.`"
            )

        else:
            await interaction.response.send_message(
                "`Please use ~modmail setup command to enable Modmail`"
            )

    @mail.subcommand(name="logs", description="Set or remove the logs channel")
    async def logs(
        self, interaction: nextcord.Interaction, channel: nextcord.TextChannel = None
    ):
        if interaction.user.guild_permissions.manage_guild != True:
            await interaction.response.send_message("No perms", ephemeral=True)
            return
        db = servers()
        guild = db.find_one({"_id": str(interaction.guild.id)})
        if guild:
            if channel == None:
                db.delete_one(guild)
                guild["log_channel"] = None
                db.insert_one(guild)
                await interaction.response.send_message("`REMOVED LOG CHANNEL`")
                return
            db.delete_one(guild)
            guild["log_channel"] = int(channel.id)
            db.insert_one(guild)
            await interaction.response.send_message(
                f"`Saved` {channel.mention} `as log channel. All ticket actions will be logged here.`"
            )

        else:
            await interaction.response.send_message(
                "`Please use ~modmail setup command to enable Modmail`"
            )

    @mail.subcommand(name="pingrole")
    async def pingrole(
        self, interaction: nextcord.Interaction, role: nextcord.Role = None
    ):
        if interaction.user.guild_permissions.manage_guild != True:
            await interaction.response.send_message("No perms", ephemeral=True)
            return
        db = servers()
        guild = db.find_one({"_id": str(interaction.guild.id)})
        if guild:
            if role == None:
                db.delete_one(guild)
                guild["pingrole"] = None
                db.insert_one(guild)
                await interaction.response.send_message("`Removed Pingrole`")
                return
            db.delete_one(guild)
            guild["pingrole"] = int(role.id)
            db.insert_one(guild)
            await interaction.response.send_message(
                f"`Saved` {role.mention} `as Pingrole. This role will be pinged when tickets are created.`"
            )
        else:
            await interaction.response.send_message(
                "`Please use ~modmail setup command to enable Modmail`"
            )

    @mail.subcommand(
        name="category", description="set or remove category for ticket channels"
    )
    async def category(
        self,
        interaction: nextcord.Interaction,
        category: nextcord.CategoryChannel = None,
    ):
        if interaction.user.guild_permissions.manage_guild != True:
            await interaction.response.send_message("No permission", ephemeral=True)
            return
        db = servers()
        guild = db.find_one({"_id": str(interaction.guild.id)})
        if guild:
            if category == None:
                db.delete_one(guild)
                guild["category"] = None
                db.insert_one(guild)
                await interaction.response.send_message(
                    "`Removed Category for modmail tickets`"
                )
                return
            db.delete_one(guild)
            guild["category"] = int(category.id)
            db.insert_one(guild)
            await interaction.response.send_message(
                f"`Saved` {category.mention} `as category for modmail tickets`"
            )
        else:
            await interaction.response.send_message(
                "`Please use ~modmail setup command to Enable Modmail`"
            )


def setup(bot: commands.Bot):
    bot.add_cog(Modmail_Setup(bot))
    print("Modmail_Setup Loaded")
