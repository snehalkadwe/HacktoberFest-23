from nextcord.ext import commands, application_checks
from nextcord import SlashOption
import nextcord
import NextcordUtils
import random
import asyncio
import cooldowns


class EconomyCog(commands.Cog, name="Economy"):
    """balance, work, withdraw, deposit, give, add, subtract, rob, shop"""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        await asyncio.sleep(3)
        async with self.bot.db2.cursor() as cursor:
            await cursor.execute(
                "CREATE TABLE IF NOT EXISTS bank(server INTEGER, wallet INTEGER, bank INTEGER, maxbank INTEGER, user INTEGER)"
            )
            await cursor.execute(
                "CREATE TABLE IF NOT EXISTS inv(server INTEGER, laptop INTEGER, phone INTEGER, fakeid INTEGER, user INTEGER)"
            )
            await cursor.execute(
                "CREATE TABLE IF NOT EXISTS shop(server INTEGER, name TEXT, id TEXT, desc TEXT, cost INTEGER)"
            )
        await self.bot.db2.commit()

    async def create_balance(self, user, guild_id):
        async with self.bot.db2.cursor() as cursor:
            await cursor.execute(
                "INSERT INTO bank VALUES (?,?,?,?,?)", (guild_id, 0, 0, 500, user.id)
            )
        await self.bot.db2.commit()
        return

    async def create_inv(self, user, guild_id):
        async with self.bot.db2.cursor() as cursor:
            await cursor.execute(
                "INSERT INTO inv VALUES (?,?,?,?,?)", (guild_id, 0, 0, 0, user.id)
            )
        await self.bot.db2.commit()
        return

    async def get_balance(self, user, guild_id):
        async with self.bot.db2.cursor() as cursor:
            await cursor.execute(
                "SELECT wallet, bank, maxbank FROM bank WHERE user = ? AND server = ?",
                (
                    user.id,
                    guild_id,
                ),
            )
            data = await cursor.fetchone()
            if data is None:
                await self.create_balance(user, guild_id)
                return 0, 0, 500
            wallet, bank, maxbank = data[0], data[1], data[2]
            return wallet, bank, maxbank

    async def get_inv(self, user, guild_id):
        async with self.bot.db2.cursor() as cursor:
            await cursor.execute(
                "SELECT laptop, phone, fakeid FROM inv WHERE user = ? AND server = ?",
                (
                    user.id,
                    guild_id,
                ),
            )
            data = await cursor.fetchone()
            if data is None:
                await self.create_inv(user, guild_id)
                return 0, 0, 0
            laptop, phone, fakeid = data[0], data[1], data[2]
            return laptop, phone, fakeid

    async def update_wallet(self, user, amount: int, guild_id):
        async with self.bot.db2.cursor() as cursor:
            await cursor.execute(
                "SELECT wallet FROM bank WHERE user = ? AND server = ?",
                (user.id, guild_id),
            )
            data = await cursor.fetchone()
            if data is None:
                await self.create_balance(user, guild_id)
                return 0
            await cursor.execute(
                "UPDATE bank SET wallet = ? WHERE user = ? AND server = ?",
                (data[0] + amount, user.id, guild_id),
            )
        await self.bot.db2.commit()

    async def update_bank(self, user, amount, guild_id):
        async with self.bot.db2.cursor() as cursor:
            await cursor.execute(
                "SELECT wallet, bank, maxbank FROM bank WHERE user = ? AND server = ?",
                (
                    user.id,
                    guild_id,
                ),
            )
            data = await cursor.fetchone()
            if data is None:
                await self.create_balance(user, guild_id)
                return 0
            capacity = int(data[2] - data[1])
            if amount > capacity:
                await self.update_wallet(user, amount, guild_id)
                return 1
            await cursor.execute(
                "UPDATE bank SET bank = ? WHERE user = ? AND server = ?",
                (data[1] + amount, user.id, guild_id),
            )
        await self.bot.db2.commit()

    async def update_maxbank(self, user, amount, guild_id):
        async with self.bot.db2.cursor() as cursor:
            await cursor.execute(
                "SELECT maxbank FROM bank WHERE user = ? AND server = ?",
                (
                    user.id,
                    guild_id,
                ),
            )
            data = await cursor.fetchone()
            if data is None:
                await self.create_balance(user, guild_id)
                return 0
            await cursor.execute(
                "UPDATE bank SET maxbank = ? WHERE user = ? AND server = ?",
                (data[0] + amount, user.id, guild_id),
            )
        await self.bot.db2.commit()

    async def update_shop(self, guild, name: str, id: str, desc: str, cost: int):
        async with self.bot.db2.cursor() as cursor:
            await cursor.execute(
                "INSERT INTO shop VALUES(?,?,?,?,?)", (guild.id, name, id, desc, cost)
            )
        await self.bot.db2.commit()
        return

    # balance
    @nextcord.slash_command(description="Check a users balance")
    async def balance(
        self,
        interaction: nextcord.Interaction,
        member: nextcord.Member = SlashOption(
            description="The user whos balance you want to check!"
        ),
    ):
        if not member:
            member = interaction.user
        wallet, bank, maxbank = await self.get_balance(member)
        embed = nextcord.Embed(title=f"{member.name}'s Balance", color=0xFD9FA1)
        embed.add_field(name="Wallet", value=wallet)
        embed.add_field(name="Bank", value=f"{bank}/{maxbank}")
        embed.add_field(name="Server", value=f"{interaction.guild.name}")
        embed.set_thumbnail(
            url="https://cdn.discordapp.com/emojis/1017329095350161408.webp?size=128&quality=lossless"
        )
        await interaction.response.send_message(embed=embed)

    # work
    @nextcord.slash_command(description="Earn some money by working!")
    @cooldowns.cooldown(1, 1800, bucket=cooldowns.SlashBucket.author)
    async def work(self, interaction: nextcord.Interaction):
        user = interaction.guild.get_member(interaction.user.id)
        chances = random.randint(1, 4)

        if chances == 1:
            return await interaction.response.send_message("You got nothing.")

        amount = random.randint(1, 10)
        res = await self.update_wallet(interaction.user, amount)
        if res == 0:
            return await interaction.response.send_message(
                "No account has been found, so one has been created for you. Please run the command again!"
            )
        await interaction.response.send_message(f"You got {amount} SSC!")

    # withdraw
    @nextcord.slash_command(description="Withdraw money into your wallet!")
    @cooldowns.cooldown(1, 5, bucket=cooldowns.SlashBucket.author)
    async def withdraw(self, interaction: nextcord.Interaction):
        wallet, bank, maxbank = await self.get_balance(interaction.user)

        try:
            amount = int(amount)
        except ValueError:
            pass

        if type(amount) == str:
            if amount.lower() == "max" or amount.lower() == "all":
                amount = int(bank)
        else:
            amount = int(amount)

        bank_res = await self.update_bank(interaction.user, -amount)
        wallet_res = await self.update_wallet(interaction.user, amount)
        if bank_res == 0 or wallet_res == 0:
            return await interaction.response.send_message(
                "No account has been found so one has been created for you. Please use the command again."
            )

        wallet, bank, maxbank = await self.get_balance(interaction.user)
        embed = nextcord.Embed(
            title=f"{amount} coins have been withdrawn.", color=0xFD9FA1
        )
        embed.add_field(name="New Wallet", value=wallet)
        embed.add_field(name="New Bank", value=f"{bank}/{maxbank}")
        await interaction.response.send_message(embed=embed)

    # deposit
    @nextcord.slash_command(description="Deposit money into your bank!")
    @cooldowns.cooldown(1, 5, bucket=cooldowns.SlashBucket.author)
    async def deposit(self, interaction: nextcord.Interaction):
        wallet, bank, maxbank = await self.get_balance(interaction.user)

        try:
            amount = int(amount)
        except ValueError:
            pass

        if type(amount) == str:
            if amount.lower() == "max" or amount.lower() == "all":
                amount = int(wallet)
        else:
            amount = int(amount)

        bank_res = await self.update_bank(interaction.user, amount)
        wallet_res = await self.update_wallet(interaction.user, -amount)
        if bank_res == 0 or wallet_res == 0:
            return await interaction.response.send_message(
                "No account has been found so one has been created for you. Please use the command again."
            )
        elif bank_res == 1:
            return await interaction.response.send_message(
                "You do not have enough storage in your bank."
            )

        wallet, bank, maxbank = await self.get_balance(interaction.user)
        embed = nextcord.Embed(
            title=f"{amount} coins have been deposited.", color=0xFD9FA1
        )
        embed.add_field(name="New Wallet", value=wallet)
        embed.add_field(name="New Bank", value=f"{bank}/{maxbank}")
        await interaction.response.send_message(embed=embed)

    # give
    @nextcord.slash_command(description="Share the money!")
    @cooldowns.cooldown(1, 10, bucket=cooldowns.SlashBucket.author)
    async def give(
        self,
        interaction: nextcord.Interaction,
        amount: int,
        member: nextcord.Member = SlashOption(
            description="Who do you want to give money to?", required=True
        ),
    ):
        wallet = await self.get_balance(interaction.user)

        try:
            amount = int(amount)
        except ValueError:
            pass

        if type(amount) == str:
            if amount.lower() == "max" or amount.lower() == "all":
                amount = int(wallet)
        else:
            amount = int(amount)

        wallet_res = await self.update_wallet(interaction.user, -amount)
        wallet_res2 = await self.update_wallet(member, amount)

        if wallet_res == 0 or wallet_res2 == 0:
            return await interaction.response.send_message(
                "No wallet has been found, so one has been created for you. Please run the command again."
            )

        wallet = await self.get_balance(interaction.user)
        wallet2 = await self.get_balance(member)

        embed = nextcord.Embed(
            title=f"Gave {amount} coins to {member.name}", color=0xFD9FA1
        )
        embed.add_field(name=f"{interaction.user.name}'s Wallet", value=wallet)
        embed.add_field(name=f"{member.name}'s Wallet", value=wallet2)
        await interaction.response.send_message(embed=embed)

    # add
    @nextcord.slash_command(description="Share the money!")
    @application_checks.has_permissions(administrator=True)
    async def add(
        self,
        interaction: nextcord.Interaction,
        amount: int,
        member: nextcord.Member = SlashOption(
            description="Who do you want to give money to?", required=True
        ),
    ):
        wallet_res2 = await self.update_wallet(member, amount)

        if wallet_res2 == 0:
            return await interaction.response.send_message(
                "No wallet has been found, so one has been created. Please run the command again."
            )

        wallet2, bank2, maxbank2 = await self.get_balance(member)
        embed = nextcord.Embed(
            title=f"Added {amount} coins to {member.name}", color=0xFD9FA1
        )
        embed.add_field(name=f"{member.name}'s Wallet", value=wallet2)
        await interaction.response.send_message(embed=embed)

    # subtract
    @nextcord.slash_command(description="Share the money!")
    @application_checks.has_permissions(administrator=True)
    async def subtract(
        self,
        interaction: nextcord.Interaction,
        amount: int,
        member: nextcord.Member = SlashOption(
            description="Who do you want to give money to?", required=True
        ),
    ):
        wallet_res2 = await self.update_wallet(member, -amount)
        if wallet_res2 == 0:
            return await interaction.response.send_message(
                "No wallet has been found, so one has been created. Please run the command again."
            )

        wallet2, bank2, maxbank2 = await self.get_balance(member)
        embed = nextcord.Embed(
            title=f"Subtracted {amount} coins from {member.name}", color=0xFD9FA1
        )
        embed.add_field(name=f"{member.name}'s Wallet", value=wallet2)
        await interaction.response.send_message(embed=embed)

    # rob
    @nextcord.slash_command(description="You may go to jail but you may get rich!")
    @cooldowns.cooldown(1, 60, bucket=cooldowns.SlashBucket.author)
    async def rob(
        self,
        interaction: nextcord.Interaction,
        member: nextcord.Member = SlashOption(
            description="Who do you want to rob?", required=True
        ),
    ):
        author_wallet, author_bank, author_maxbank = await self.get_balance(
            interaction.user
        )
        member_wallet, member_bank, member_maxbank = await self.get_balance(member)
        if not author_wallet > 500:
            return await interaction.response.send_message(
                f"You need atleast `500`SSC to rob someone!"
            )
        if not random.randint(1, 3) > 1:
            return await interaction.response.send_message(
                f"You got caught trying to rob `{member.name}` 💀 and had to pay them `500`SSC"
            )

        robbed_amount = random.randint(20, member_wallet)

        await self.update_wallet(interaction.user, robbed_amount)
        await self.update_wallet(member, -robbed_amount)

        await interaction.response.send_message(
            f"You robbed `{member.name}` for `{robbed_amount}`SCC (im suprised you didnt get caught)"
        )

    # shop
    @nextcord.slash_command(description="Whats in the shop?")
    async def shop(self, interaction: nextcord.Interaction):
        embeds = [
            nextcord.Embed(
                title="SSC Shop",
                color=0xFD9FA1,
                description="SSC stands for Secret Society Coins. It is earned through bot commands such as /work. To check your balance, use /balance. To purchase, use /purchase then ping a mod and show them the message as proof. \n\n\n**Timeout 80 SSC**\nTimeout someone for 1 minute. +10 SSC for extra time \(1 min, 5 min, 10 min, 1 hour, 1 day, 1 week\). +10 SSC if you choose a Consigliere.\n\n**Un-Timeout 80 SSC**\nRemove your or someone else's timeout. Doesn't matter why you were timed out, you will be un-timed out once this is purchased. This does NOT protect you from being timed out again.\n\n**Kick 40 SSC**\nKick any Associate. They can still join back.",
            )
            .set_thumbnail(
                url="https://cdn.discordapp.com/emojis/1017329095350161408.webp?size=128&quality=lossless"
            )
            .set_footer(text="Page 1 of 2"),
            nextcord.Embed(
                title="SSC Shop",
                color=0xFD9FA1,
                description="**Unban 100 SSC**\nUnban someone. No matter what they were banned for, they will be unbanned. This does NOT protect them from being banned again.",
            )
            .set_thumbnail(
                url="https://cdn.discordapp.com/emojis/913010082235703326.webp?size=56&quality=lossless"
            )
            .set_footer(text="Page 2 of 2"),
        ]
        paginator = NextcordUtils.Pagination.CustomEmbedPaginator(
            interaction, remove_reactions=True
        )
        paginator.add_reaction("⏪", "back")
        paginator.add_reaction("⏩", "next")

        await paginator.run(embeds)


def setup(bot):
    bot.add_cog(EconomyCog(bot))
    print("Economy is loaded")
