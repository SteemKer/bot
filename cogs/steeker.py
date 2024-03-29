from functools import partial
from io import BytesIO

import aiohttp
import discord
from PIL import Image, ImageSequence
from sentry_sdk import capture_exception
from discord.ext import commands

from bot import SteekerBot

async def is_whitelisted(ctx):
    return self.bot._config["whitelisted"].__contains__(ctx.author.id)

class Steeker(commands.Cog):
    def __init__(self, bot):
        self.bot: SteekerBot = bot
        self.db = self.bot.database
        self.session = aiohttp.ClientSession(loop=bot.loop)

    @staticmethod
    def process_emote(emote: bytes, animated: bool) -> BytesIO:
        with Image.open(BytesIO(emote)) as em:
            em_io = BytesIO()
            if animated:
                frames = ImageSequence.Iterator(em)

                def cnv(frames):
                    for frame in frames:
                        snapshot = frame.copy()
                        snapshot = snapshot.resize((512, 512))
                        yield snapshot

                frames = cnv(frames)
                om = next(frames)
                om.info = em.info

                om.save(
                    em_io,
                    format="WEBP",
                    save_all=True,
                    append_images=list(frames),
                    optimize=True,
                    quality=80,
                )
            else:
                em = em.resize((512, 512))
                em.save(em_io, format="WEBP", save_all=True)
        em_io.seek(0)
        return em_io

    @staticmethod
    def process_tray_icon(emote: bytes) -> BytesIO:
        with Image.open(BytesIO(emote)) as em:
            em = em.resize((96, 96))
            em_io = BytesIO()
            em.save(em_io, "png")

        em_io.seek(0)
        return em_io

    @commands.group(name="pack", aliases=["packs"], invoke_without_command=True)
    @commands.check(is_whitelisted)
    async def pack(self, ctx: commands.Context):
        """Pack command"""

        await ctx.send_help(ctx.command)
        return

    @pack.command(name="create")
    @commands.check(is_whitelisted)
    @commands.guild_only()
    async def pack_create(
        self, ctx: commands.Context, name: str, tray_icon: discord.PartialEmoji
    ):
        """
        Create a sticker pack
        """
        if tray_icon.animated:
            await ctx.send(
                "<:crypuddle:813275761230217246> | Tray icons can" "t be animated"
            )
            return

        message = await ctx.send(
            f"<a:c4:813270233993183282> | Creating a sticker pack with name `{name}`"
        )

        await message.edit(
            content=f"<a:BaguetteSwing:813299006657921045> | Creating a sticker pack with name `{name}` | `(Processing Image)`"
        )
        emote_bytes = await tray_icon.url.read()
        fn = partial(self.process_tray_icon, emote_bytes)
        final_buffer = await self.bot.loop.run_in_executor(None, fn)
        file = discord.File(filename=f"{tray_icon.id}.png", fp=final_buffer)
        channel = await self.bot.fetch_channel(813270590608637972)
        emote_message: discord.Message = await channel.send(file=file)
        await message.edit(
            content=f"<a:BaguetteSwing:813299006657921045> | Creating a sticker pack with name `{name}` | `(Image processed)`"
        )

        await message.edit(
            content=f"<a:c4:813270233993183282> | Creating a sticker pack with name `{name}` | `(Securing space)`"
        )
        pack_id = await self.db.create_pack(
            str(ctx.author.id), name, emote_message.attachments[0].url, ctx.message.id
        )
        await message.edit(
            content=f"**<a:stickbug:813271257759612938> | Successfully created a sticker pack with name `{name}` and ID `{pack_id}`**"
        )
        return

    @pack.command(name="list")
    @commands.check(is_whitelisted)
    @commands.guild_only()
    async def packs_list(self, ctx: commands.Context):
        """
        Get a list of your pack with IDs
        """

        message = await ctx.send(
            f"<a:c4:813270233993183282> | Searching through my database"
        )
        packs = await self.db.get_user_packs(str(ctx.author.id))
        if not packs or len(packs) <= 0:
            await message.edit(
                content=f"<:crypuddle:813275761230217246> | I couldn't find any packs owned by `{str(ctx.author)}`"
            )
            return
        msg = "```"
        for pack in packs:
            msg += f"{pack['pack_id']} - {pack['name']}\n"
        msg += "```"
        await message.edit(content=msg)
        return

    @commands.command(name="create")
    @commands.check(is_whitelisted)
    @commands.guild_only()
    async def sticker_create(
        self,
        ctx: commands.Context,
        pack_id: str,
        emojis: commands.Greedy[discord.PartialEmoji],
    ):
        """
        add stickers in a pack
        """

        message = await ctx.send(
            f"<a:c4:813270233993183282> | Searching through my database"
        )

        creator = await self.db.get_creator(pack_id)
        if not creator or creator != str(ctx.author.id):
            await message.edit(
                content=f"<:crypuddle:813275761230217246> | I couldn't find any pack with ID `{pack_id}` owned by `{str(ctx.author)}`"
            )
            return

        await message.edit(
            content="<a:BaguetteSwing:813299006657921045> | Got sticker pack, converting and adding the emotes to your sticker pack\n\n**Note:** Animated stickers won't be processed until a stable release from Whatsapp Inc."
        )
        count = 0
        for emoji in emojis:
            count = count + 1
            try:
                emote: discord.PartialEmoji = emoji

                emote_bytes = await emote.url.read()
                fn = partial(self.process_emote, emote_bytes, emote.animated)
                final_buffer = await self.bot.loop.run_in_executor(None, fn)
                file = discord.File(filename=f"{emote.id}.webp", fp=final_buffer)
                channel = await self.bot.fetch_channel(813270590608637972)
                emote_message: discord.Message = await channel.send(file=file)

                await self.db.add_emote(
                    pack_id,
                    str(ctx.author.id),
                    emote_message.attachments[0].url,
                    emote.name,
                    str(emote.id),
                    emote.animated
                )
                await message.edit(
                    content=f"<a:BaguetteSwing:813299006657921045> Processed `{count}/{len(emojis)}`"
                )

            except Exception as e:
                capture_exception(e)
        await message.edit(
            content=f"<a:stickbug:813271257759612938> | Finished processing `({count}/{len(emojis)})`"
        )


def setup(bot: SteekerBot):
    bot.add_cog(Steeker(bot))
