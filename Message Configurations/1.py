def create_embed_of_ban(self, ban):
        """ Creates an embed of a ban. """
        embedVar = discord.Embed(title="Banned Player", color=0x00ff00)
        embedVar.add_field(name="PLAYER NAME", value=ban[BanInfo.PLAYER_NAME.value], inline=True)
        embedVar.add_field(name="ADMIN NAME", value=ban[BanInfo.ADMIN_NAME.value], inline=True)
        embedVar.add_field(name="REASON", value= ban[BanInfo.REASON.value], inline=False)
        embedVar.add_field(name="DATE", value=ban[BanInfo.TIME_BANNED.value], inline=True)
        embedVar.add_field(name="EXPIRES", value=ban[BanInfo.TIME_UNBANNED.value], inline=True)
        embedVar.add_field(name="Battlemetrics", value="https://www.battlemetrics.com/rcon/players/"+ ban[BanInfo.USER_ID.value], inline=False)
        embedVar.add_field(name="SERVER", value=ban[BanInfo.SERVER.value], inline=False)
        return embedVar
