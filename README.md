# DiscordBattlemetricsBanBot

A bot that uses the Battlemetrics API to poll information about recently banned players and updates a discord servers 'wall of shame' text channel automatically whenever it detect new bans.

Use the config.ini file to set discordToken, discordTextChannelId, battlemetricsToken, banListId. You can also set the polling interval (time between every poll of banlist data), prefix for commands and a comma seperated list of names of admins that are allowed to operate bot commands.

Setup
Script is written in Python 3.8

1.Run the following to setup the environment:
```$ pip install -r requirements.txt```

2.Edit lines, 7, 9,11,15,17 and 19(if you wish)
on line 7 include the full discord Username and number
on line 9 include your discord bot token
on line 11 include the discord channel id you wish for the bot to send the message into

on line 15 you need to create a BM access token, and imput this here
on line 17 input your ban list ID
If you wish to change the polling interval change this setting on line 19
