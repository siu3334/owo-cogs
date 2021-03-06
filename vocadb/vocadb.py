import aiohttp
import asyncio
import json

from datetime import datetime
from typing import Any, Dict, Literal

import discord
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import pagify
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS

BASE_API_URL = "https://vocadb.net/api/songs"

RequestType = Literal["discord_deleted_user", "owner", "user", "user_strict"]


class VocaDB(commands.Cog):
    """Search for a song on Vocaloid Database (VocaDB) through a query"""

    __author__ = "<@306810730055729152>"
    __version__ = "0.0.2"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    def __init__(self, bot: Red):
        self.bot = bot

    # credits to jack1142
    async def red_get_data_for_user(self, *, user_id: int) -> Dict[str, Any]:
        # this cog does not story any data
        return {}

    async def red_delete_data_for_user(
        self, *, requester: RequestType, user_id: int
    ) -> None:
        # this cog does not story any data
        pass

    @commands.command()
    async def vocadb(self, ctx, *, query: str):
        """Search for a song on VocaDB"""
        params = {
            "query": query,
            "maxResults": 1,
            "sort": "FavoritedTimes",
            "preferAccurateMatches": "true",
            "nameMatchMode": "Words",
            "fields": "ThumbUrl,Lyrics"
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(BASE_API_URL, params=params) as response:
                if response.status == 200:
                    result = await response.json(loads=json.loads)
                else:
                    return await ctx.send(f"API returned response code: {response.status}")

        # Thanks to Fixator's suggestion
        if data := result.get("items"):
            data = data[0]
        else:
            return await ctx.send("No results.")
        if lyrics := data.get("lyrics"):
            lyrics = lyrics[0].get("value")
        else:
            lyrics = "Lyrics unavailable."
        mins = data.get("lengthSeconds", 0) // 60
        secs = data.get("lengthSeconds", 0) % 60
        pub_date = data.get("publishDate")
        pub_date_strp = datetime.strptime(pub_date, "%Y-%m-%dT%H:%M:%SZ")
        pub_date_strf = pub_date_strp.strftime("%A, %d %B, %Y")

        embeds = []
        for page in pagify(lyrics, ["\n"]):
            em = discord.Embed(
                title=f"{data.get('defaultName')}",
                colour=await ctx.embed_colour(),
            )
            em.url = f"https://vocadb.net/S/{data.get('id')}"
            em.description = page
            em.set_thumbnail(url=str(data.get("thumbUrl")))
            em.add_field(name="Duration", value=f"{mins} minutes, {secs} seconds")
            em.add_field(name="Rating Score", value=str(data.get('ratingScore')))
            em.add_field(
                name="Favourited",
                value=f"{str(data.get('favoritedTimes'))} times"
                if data.get("favoritedTimes")
                else "0 times"
            )
            em.add_field(name="Artist", value=str(data.get("artistString")))
            em.set_footer(text=f"Published date: {pub_date_strf}")
            embeds.append(em)

        if not embeds:
            return await ctx.send("No results.")
        elif len(embeds) == 1:
            return await ctx.send(embed=embeds[0])
        else:
            await menu(ctx, embeds, DEFAULT_CONTROLS, timeout=60.0)
