#!/usr/bin/env python3

import configparser
import discord
import json
import requests
import os
import threading

from enum import Enum

# Read configuration file
config = configparser.ConfigParser()
config.read(os.path.abspath(__file__).replace(os.path.basename(__file__), "config.ini"))
dir_path = os.path.dirname(os.path.realpath(__file__))

PREFIX = config["General"]["prefix"]

DC_ADMINS = config["Discord"]["admins"].replace(" ", "").split(",")
DC_TOKEN = config["Discord"]["discordToken"]
DC_TEXT_CHANNEL_ID = int(config["Discord"]["discordTextChannelId"])

BM_TOKEN = config["Battlemetrics"]["battlemetricsToken"]
BM_BANLIST_ID = config["Battlemetrics"]["banListId"]
BM_POLLING_INTERVAL = int(config["Battlemetrics"]["pollingInterval"])

Embed_Configuration = config["EmbedConfiguration"]["value"]

HEADERS = {"Authorization" : "Bearer " + BM_TOKEN}
URL = "https://api.battlemetrics.com/bans?filter[banList]=" + BM_BANLIST_ID + "&include=user,server"


class DiscordBanBot(discord.Client):
    """ Discord Ban Bot """
    def __init__(self, **options):
        """ Init. """
        super().__init__(**options)
        
        self.event = threading.Event()
        self.thread = threading.Thread(target=self.polling_thread, args=(self.event,))
        self.thread.start()

    async def on_ready(self):
        """ on_ready. """
        print('Logged on as', self.user)

    async def on_message(self, message):
        """ Whenever there is a new message. """
        messageUpper = message.content.upper()

        # don't respond to ourselves
        if message.author == self.user:
            return

        print(str(message.author) + ": " + str(message.content))

        # Add possible commands below
        if str(message.author) in DC_ADMINS and message.content.startswith(PREFIX):
            command = messageUpper[len(PREFIX):]
            if command == "MANUALBANLISTPOLL":
                print("Running manual poll")
                self.update()
            elif command == "LASTBAN":
                banList = get_banlist(URL, HEADERS)
                server = self.getServer(banList)
                admin = self.getAdmin(banList)
                if banList != []:
                    await message.author.send(embed=self.create_embed_of_ban(banList["data"][0], server, admin))

    def polling_thread(self, event):
        """ Polling thread that runs every UPDATE_TIMER second """
        while True:
            self.update()
            event.wait(BM_POLLING_INTERVAL) # Wait for next poll

    def update(self):
        """ Poll from Battrlematrics API and if there is new data, display it in the discord text channel. """
        print("Polling from Battlemetrics API...\nURL: " + str(URL))
        banList = get_banlist(URL, HEADERS)
        server = self.getServer(banList)
        admin = self.getAdmin(banList)
        # if ban list not an empty array, poll was succesfull, if empty not successfull
        if banList != []:
            print("Poll was successful.")
        else:
            print("Poll was not successful...")

        oldBanList = self.readOldRequestFromDisk(dir_path)
        newBans = self.getNewBans(banList, oldBanList)

        #if new bans is not an empty array new bans detected. if empty no new bans.
        if newBans != []:
            parsedBans = self.parseNewBans(newBans,server,admin)
            print("New bans detected!\n" + str(parsedBans))
        else:
            print("Nothing new...")

        for ban in newBans:
            self.update_text_channel(newBans, banList)
    
        self.writeBanListToDisk(banList)


    def getNewBans(self, banList, oldBanList):
        newBans = [item for item in banList['data'] if item not in oldBanList['data']]

        return newBans

    # def getBanByID(self, id, banList):
    #     for ban in banList:
    #         if id == ban['relationships']['player']['data']['id']:
    #             return ban
    #     return None
    
    def parseNewBans(self,newBans,server,admin):
        #parses the new bans array into a prettified array to print out to terminal for good logging.
        parsedBans = []
        for ban in newBans:
            newBan = {}
            newBan['player'] = ban["meta"]["player"]
            newBan['reason'] = ban["attributes"]["reason"].replace(" ({{duration}} ban) - Expires in {{timeLeft}}.", "")
            newBan['timestamp'] = ban["attributes"]["timestamp"].replace("T", " ")[:-5]
            newBan['expires'] = ban["attributes"]["expires"].replace("T", " ")[:-5] if ban["attributes"]["expires"] != None else "Indefinitely"
            newBan['userID'] = ban["relationships"]["player"]["data"]["id"]
            newBan['banNote'] = ban["attributes"]["note"].replace("_", " ") if ban["attributes"]["note"] != "" else "None"
            newBan['server'] = server
            newBan['banner'] = admin
            parsedBans.append(newBan)
        return parsedBans


    def update_text_channel(self, newBans, banList):
        """ Update text channel with the new bans. """
        print("Transmit new ban information to the discord text channel...")
        server = self.getServer(banList)
        admin = self.getAdmin(banList)
        for ban in newBans:
            embedVar = self.create_embed_of_ban(ban,server,admin)
            self.send_embed_to_text_channel(embedVar)
        print("Transmition was successful.")
        

    def writeBanListToDisk(self, banList):
        json_string = banList
        with open('json_data.json', 'w') as outfile:
            json.dump(json_string, outfile ,indent=4)


    def readOldRequestFromDisk(self, dir_path):
        with open('json_data.json') as json_file:
            data = json.load(json_file)
        return data
    
    
    def getServer(self, banList):
        for include in banList["included"]:
            if include["type"] == "server":
                return include['attributes']['name']
    
    
    def getAdmin(self, banList):
        for include in banList["included"]:
            if include["type"] == "user":
                return include['attributes']['nickname']
            
    
    def create_embed_of_ban(self, ban, server, admin):
        if Embed_Configuration == "0":
            return self.embed_type_0(ban, server, admin)
            
        if Embed_Configuration == "1":
            return self.embed_type_1(ban, server, admin)
            
        if Embed_Configuration == "2":
            return self.embed_type_2(ban, server, admin)
            
        if Embed_Configuration == "3":
            return self.embed_type_3(ban, admin)
    
    
    def embed_type_0(self, ban, server, admin):
        """ Creates an embed of a ban. """
        embedVar = discord.Embed(title="Banned Player", color=0x00ff00)
        embedVar.add_field(name="PLAYER NAME", value=ban['meta']['player'], inline=False)
        embedVar.add_field(name="REASON", value= ban["attributes"]["reason"].replace(" ({{duration}} ban) - Expires in {{timeLeft}}.", ""), inline=False)
        embedVar.add_field(name="DATE", value=ban["attributes"]["timestamp"].replace("T", " ")[:-5], inline=False)
        embedVar.add_field(name="EXPIRES", value=ban["attributes"]["expires"].replace("T", " ")[:-5] if ban["attributes"]["expires"] != None else "Indefinitely", inline=False)
        embedVar.add_field(name="Battlemetrics", value="https://www.battlemetrics.com/rcon/players/"+ ban["relationships"]["player"]["data"]["id"], inline=False)
        embedVar.add_field(name="Ban Notes", value=ban["attributes"]["note"].replace("_", " ") if ban["attributes"]["note"] != "" else "None", inline=False)
        embedVar.add_field(name="SERVER", value=server, inline=False)
        embedVar.add_field(name="ADMIN NAME", value=admin, inline=False)
        return embedVar

    def embed_type_1(self, ban, server, admin):
        """ Creates an embed of a ban. """
        embedVar = discord.Embed(title="Banned Player (1)", color=0x00ff00)
        embedVar.add_field(name="PLAYER NAME", value=ban['meta']['player'], inline=True)
        embedVar.add_field(name="ADMIN NAME", value=admin, inline=False)
        embedVar.add_field(name="REASON", value= ban["attributes"]["reason"].replace(" ({{duration}} ban) - Expires in {{timeLeft}}.", ""), inline=False)
        embedVar.add_field(name="DATE", value=ban["attributes"]["timestamp"].replace("T", " ")[:-5], inline=False)
        embedVar.add_field(name="EXPIRES", value=ban["attributes"]["expires"].replace("T", " ")[:-5] if ban["attributes"]["expires"] != None else "Indefinitely", inline=False)
        embedVar.add_field(name="Battlemetrics", value="https://www.battlemetrics.com/rcon/players/"+ ban["relationships"]["player"]["data"]["id"], inline=False)
        embedVar.add_field(name="SERVER", value=server, inline=False)
        return embedVar
    
    def embed_type_2(self, ban, server, admin):
        """ Creates an embed of a ban. """
        embedVar = discord.Embed(title="Banned Player (2)", color=0x00ff00)
        embedVar.add_field(name="PLAYER NAME", value=ban['meta']['player'], inline=True)
        embedVar.add_field(name="ADMIN NAME", value=admin, inline=False)
        embedVar.add_field(name="REASON", value= ban["attributes"]["reason"].replace(" ({{duration}} ban) - Expires in {{timeLeft}}.", ""), inline=False)
        embedVar.add_field(name="DATE", value=ban["attributes"]["timestamp"].replace("T", " ")[:-5], inline=False)
        embedVar.add_field(name="EXPIRES", value=ban["attributes"]["expires"].replace("T", " ")[:-5] if ban["attributes"]["expires"] != None else "Indefinitely", inline=False)
        embedVar.add_field(name="Battlemetrics", value="https://www.battlemetrics.com/rcon/players/"+ ban["relationships"]["player"]["data"]["id"], inline=False)
        embedVar.add_field(name="Ban Notes", value=ban["attributes"]["note"].replace("_", " ") if ban["attributes"]["note"] != "" else "None", inline=False)
        embedVar.add_field(name="SERVER", value=server, inline=False)
        return embedVar

    
    def embed_type_3(self, ban, admin):
        """ Creates an embed of a ban. """
        embedVar = discord.Embed(title="Banned Player 3", color=0x00ff00)
        embedVar.add_field(name="PLAYER NAME", value=ban['meta']['player'], inline=True)
        embedVar.add_field(name="ADMIN NAME", value=admin, inline=False)
        embedVar.add_field(name="REASON", value= ban["attributes"]["reason"].replace(" ({{duration}} ban) - Expires in {{timeLeft}}.", ""), inline=False)
        embedVar.add_field(name="DATE", value=ban["attributes"]["timestamp"].replace("T", " ")[:-5], inline=False)
        embedVar.add_field(name="EXPIRES", value=ban["attributes"]["expires"].replace("T", " ")[:-5] if ban["attributes"]["expires"] != None else "Indefinitely", inline=False)
        embedVar.add_field(name="Battlemetrics", value="https://www.battlemetrics.com/rcon/players/"+ ban["relationships"]["player"]["data"]["id"], inline=False)
        return embedVar


    def send_embed_to_text_channel(self, embedVar):
        """ Send embed to text channel. """
        self.loop.create_task(self.get_channel(DC_TEXT_CHANNEL_ID).send(embed=embedVar))


def get_banlist(url, headers):
    """ Returns a list of the most recent banned players, default 10 players.
        Returns an empty list if request went wrong.
    """
    try:
        response = requests.get(url, headers=headers)
    except Exception as e:
        print(e)
        return []

    banList = response.json()
    return banList


def config_check():
    """ Verify that config is set. """
    cfg = config["Discord"]["discordToken"]
    if cfg == "None":
        raise Exception("Discord token is not set.")

    cfg = config["Discord"]["discordTextChannelId"]
    if cfg == "None":
        raise Exception("Discord text channel id is not set.")

    cfg = config["Battlemetrics"]["battlemetricsToken"]
    if cfg == "None":
        raise Exception("Battlemetrics token is not set.")

    cfg = config["Battlemetrics"]["banListId"]
    if cfg == "None":
        raise Exception("Battlemetrics banlist id is not set.")
    
    cfg = config["EmbedConfiguration"]["value"]
    if cfg == "None":
        raise Exception("Embed Configuration not set.")


if __name__ == "__main__":
    config_check()
    bot = DiscordBanBot()
    bot.run(DC_TOKEN)
