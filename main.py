import discord
from discord.ext import commands
import requests
import pymongo
import random
from constants import api_key
from constants import discord_key

# TODO:
#        Error Handling               Proper Capitalization               Database

PREFIX = ";"
MUSIC = 788077903841067033
version = "11.10.1"  # Update me!
league_key = api_key  # Update me!


parameters = {
    "X-Riot-Token": league_key
}

client = commands.Bot(
    command_prefix=PREFIX)

myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["mydatabase"]
playlistCollection = mydb["playlists"]


# ----------------------------------------------------------------------------------------------------------------------
@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    await client.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name='for ' + PREFIX + 'help'))


@client.event
async def on_message(message):
    if message.author == client.user or message.author.bot:
        return

    await client.process_commands(message)


# ----------------------------------------------------------------------------------------------------------------------
@client.command()
async def ping(ctx):
    await ctx.send('Pong!')


@client.command()
async def clear(ctx, amt):
    await ctx.channel.purge(limit=(int(amt)+1))


@client.command()
async def p(ctx, arg, arg2=None):
    print(ctx.message.author.name)
    if arg2 is None:
        if arg == "view":
            string = ""
            for x in playlistCollection.find():
                string = string + "Added by **" + x["authorName"].capitalize() + ":** " + x["link"] + "\n"
            await ctx.send(string)
        elif arg == "random":
            myresult = playlistCollection.find()  # creates the dict myresult
            list = []
            for x in myresult:
                list.append(x["link"])
            index = random.randint(0, len(list) - 1)
            channel = client.get_channel(MUSIC)
            await channel.send("Here's a random playlist: " + list[index])
    elif arg == "random":
        myquery = {"authorName": arg2}  # checks if they're from the author
        myresult = playlistCollection.find(myquery)  # creates the dict myresult
        list = []
        for x in myresult:
            list.append(x["link"])
        index = random.randint(0, len(list)-1)
        channel = client.get_channel(MUSIC)
        await channel.send("Here's a random playlist added by " + arg2 + ": " + list[index])
    elif arg == "add":
        playlistCollection.insert_one({"authorId": ctx.message.author.id, "authorName": ctx.message.author.name, "link": arg2, "version": "1"})


@client.command()
async def recent(ctx, name, amt=None):
    if amt is None:
        amt = 1
    amt = str(round(int(amt)))
    if int(amt) < 1:
        await ctx.send("Please enter a valid game index.")
    PUUID = getPUUID(name)
    print(PUUID)
    response = requests.get(
        "https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/" + PUUID + "/ids?start=0&count=" + amt,
        headers=parameters)
    recentGames = response.json()
    print(len(recentGames))
    response = requests.get("https://americas.api.riotgames.com/lol/match/v5/matches/" + recentGames[int(amt) - 1],
                            headers=parameters)
    data = response.json()
    gData = data["info"]["participants"]
    for x in gData:
        if x["puuid"] == PUUID:
            if x["win"]:
                wonOrLost = "Victory!"
            else:
                wonOrLost = "Defeat!"
            gameMode = data["info"]["gameMode"].capitalize()
            d = {
                'Classic': 'Draft',
                'Nexusblitz': 'Nexus Blitz',
                'Oneforall': 'One For All'
            }
            for key in d:
                if gameMode == key:
                    gameMode = d[key]

            line1 = "**" + wonOrLost + " (" + gameMode + ")** \n"
            line2 = "Champion: **"+x["championName"]+" (lvl " + str(x["champLevel"])+")** \n"
            line3 = "KDA: **"+str(x["kills"])+"/"+str(x["deaths"])+"/"+str(x["assists"])+"** \n"
            line4 = "Damage Dealt: **" + str(x["totalDamageDealtToChampions"]) \
                    + "**  |  Self Mitigated Damage: **" + str(x["damageSelfMitigated"]) + "** \n"
            await ctx.send(line1+line2+line3+line4)

@client.command()
async def level(ctx, name):
    response = requests.get("https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-name/" + name,
                            headers=parameters)
    data = response.json()
    await ctx.send(data["name"] + " is level **" + str(data["summonerLevel"]) + ".**")


@client.command()
async def mastery(ctx, name, champion):
    ESID = getESID(name)
    CID = getCID(champion)
    print(ESID)
    print(CID)
    response = requests.get(
        "https://na1.api.riotgames.com/lol/champion-mastery/v4/champion-masteries/by-summoner/" + str(
            ESID) + "/by-champion/" + str(CID), headers=parameters)
    data = response.json()
    await ctx.send(getSummonerName(ESID) + " is **Level " + str(
        data["championLevel"]) + " Mastery** with " + champion.capitalize() + ".")


@client.command()
async def matchup(ctx, name, champion, amt):
    gamesWon = 0
    gamesLost = 0
    champion = champion.capitalize()
    if amt is None:
        amt = 1
    amt = str(round(int(amt)))
    if int(amt) < 1:
        await ctx.send("Please enter a valid game index.")
    PUUID = getPUUID(name)
    print(PUUID)
    response = requests.get(
        "https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/" + PUUID + "/ids?start=0&count=" + amt,
        headers=parameters)
    recentGames = response.json()  # dict containing all the game IDs
    for x in recentGames:
        print(x)
        response = requests.get("https://americas.api.riotgames.com/lol/match/v5/matches/" + x,
                                headers=parameters)
        data = response.json()
        gData = data["info"]["participants"]
        championWon = -1
        playedAsChamp = True  # to prevent referencing before assignment

        for y in gData:
            if y["puuid"] == PUUID:
                if y["championName"] == champion:
                    playedAsChamp = True
                else:
                    won = y["win"]
            else:
                if y["championName"] == champion:
                    playedAsChamp = False
                    if y["win"]:
                        championWon = 1
                    else:
                        championWon = 0
        print(won, playedAsChamp, championWon)
        if not playedAsChamp and championWon > -1:
            if won and championWon == 0:
                gamesWon = gamesWon + 1
            elif not won and championWon == 1:
                gamesLost = gamesLost + 1
    if gamesWon + gamesLost == 0:
        await ctx.send("You have not played against this champion within the amount of games specified.")
    else:
        if gamesLost == 0:
            winrate = 100 * ((gamesWon * 1.0) / 1)
        else:
            winrate = 100 * ((gamesWon * 1.0) / gamesLost)
        await ctx.send("In the past " + amt + " games, you've won " + str(
            gamesWon) + " times against " + champion + " and lost " + str(gamesLost) + " for a winrate of " + str(
            winrate) + "%.")


# ----------------------------------------------------------------------------------------------------------------------
def getESID(name):
    response = requests.get("https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-name/" + name,
                            headers=parameters)
    data = response.json()
    return data["id"]


def getSummonerName(ESID):  # Can be a little unnecessary and demand more API calls
    response = requests.get("https://na1.api.riotgames.com/lol/summoner/v4/summoners/" + ESID, headers=parameters)
    data = response.json()
    return data["name"]


def getPUUID(name):
    response = requests.get("https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-name/" + name,
                            headers=parameters)
    data = response.json()
    return data["puuid"]


def getCID(champion):
    champion = champion.capitalize()
    response = requests.get('http://ddragon.leagueoflegends.com/cdn/' + version + '/data/en_US/champion.json')
    data = response.json()
    cData = data[
        "data"]  # "You have to use .items() to iterate over a dict to separate the key and value into a tuple pair"
    for key, value in cData.items():
        if value['id'] == champion:
            return value['key']


# ----------------------------------------------------------------------------------------------------------------------
client.run(discord_key)
