from discord.ext import commands

from bot import SteekerBot


class Steeker(commands.Cog):
    def __init__(self, bot):
        self.bot: SteekerBot = bot
        self.db = self.bot.database

    @commands.group(name="pack", invoke_without_command=True)
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


def setup(bot: SteekerBot):
    bot.add_cog(Steeker(bot))
