from .maps import Maps

__red_end_user_data_statement__ = "This cog does not persistently store data about users."


async def setup(bot):
    n = Maps(bot)
    bot.add_cog(n)
