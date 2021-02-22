from discord.ext import commands

from bot import SteekerBot


class Steeker(commands.Cog):
    def __init__(self, bot):
        self.bot: SteekerBot = bot
        self.db = self.bot.database

    @commands.group(name="pack", aliases=["packs"], invoke_without_command=True)
    @commands.is_owner()
    async def pack(self, ctx: commands.Context):
        """Pack command"""

        await ctx.send_help(ctx.command)
        return

    @pack.command(name="create")
    @commands.is_owner()
    @commands.guild_only()
    async def pack_create(self, ctx: commands.Context, name: str):
        """
        Create a sticker pack
        """
        message = await ctx.send(f"<a:c4:813270233993183282> | Creating a sticker pack with name `{name}`")
        pack_id = await self.db.create_pack(str(ctx.author.id), name, ctx.message.id)
        await message.edit(
            content=f"**<a:stickbug:813271257759612938> | Successfully created a sticker pack with name `{name}` and ID `{pack_id}`**")
        return

    @pack.command(name="list")
    @commands.is_owner()
    @commands.guild_only()
    async def packs_list(self, ctx: commands.Context):
        """
        Get a list of your pack with IDs
        """

        message = await ctx.send(f"<a:c4:813270233993183282> | Searching through my database")
        packs = await self.db.get_user_packs(str(ctx.author.id))
        if not packs or len(packs) <= 0:
            await message.edit(
                content=f"<:crypuddle:813275761230217246> | I couldn't find any packs owned by `{str(ctx.author)}`")
            return
        msg = "```"
        for pack in packs:
            msg += f"{pack['pack_id']} - {pack['name']}\n"
        msg += "```"
        await message.edit(content=msg)
        return


def setup(bot: SteekerBot):
    bot.add_cog(Steeker(bot))
