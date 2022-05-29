import numpy as np
import requests
from datetime import date
import time
import discord
from tabulate import tabulate

URL = 'https://api.football-data.org/v2'
API_KEY = 'YOUR_API_KEY'
TOKEN = 'YOUR_TOKEN'

headers = {'X-Auth-Token': API_KEY}

print("Fetching data from API...")

# Top leagues (tier 1)
params = {'plan': "TIER_ONE"}
data = requests.get(f'{URL}/competitions', headers=headers, params=params).json()
leagues = {}
for comp in data['competitions']:
    leagues[comp['name']] = (comp['area']['name'], comp['id'])


# Top teams (tier 1)
t1_teams = {}
count = 0
for key in leagues.keys():
    if (count == 10):
        print("Request limit reached\nRestoring request limit - 60s remaining")
        time.sleep(60)
    id = leagues[key][1]
    response = requests.get(f'{URL}/competitions/{id}/teams', headers=headers).json()
    count += 1
    for team in response['teams']:
       t1_teams[team['shortName']] = [team['id'], key, id]

# get top/available leagues
def get_available_leagues():
    arr = []
    for key, val in leagues.items():
        arr.append((key, val[0]))
    
    return arr

# get top/available teams
def get_available_teams():
    arr = []
    for key, val in t1_teams.items():
        arr.append((key, val[1]))

    return arr

# get standings of particular league
def get_standings(league_name):
    if (league_name in leagues.keys()):
        standings = requests.get(f'{URL}/competitions/{leagues[league_name][1]}/standings', headers=headers).json()

        rs = []
        for team in standings['standings'][0]['table']:
            rs.append((team['position'], team['team']['name'], team['points'], team['playedGames'], team['won'], team['draw'], team['lost']))

        hd = ['Position', 'Club', 'Points', 'GP', 'W', 'L', 'D']
        return tabulate(rs, hd)

    else:
        return "League data not available"

# get todays matches
def get_today_matches():
    matches = requests.get(f'{URL}/matches', headers=headers).json()
    if (matches['count'] == 0):
        return "No games today", 0
        
    rs = []
    row = 0
    for match in matches['matches']:
        dt = match['utcDate']
        d = dt.split('T')[0]
        t = dt.split('T')[1]
        t = t.rstrip(t[-1])
        rs.append((match['season']['currentMatchday'], match['competition']['name'], match['competition']['area']['name']
        , match['homeTeam']['name'], match['awayTeam']['name'], d, t))
        row += 1    
    
    return rs, row

# get upcoming matches of a particular league   
def get_league_matches(league_name):
    parameters = {'status': "SCHEDULED"}
    matches = requests.get(f'{URL}/competitions/{league_name}/matches', headers=headers, params=parameters).json()
    if (matches['count'] == 0):
        return "No upcoming games for " + league_name , 0

    print(matches['competition']['name'], "-", matches['competition']['area']['name'])
    rs = []
    row = 0

    for match in matches['matches']:
        dt = match['utcDate']
        d = dt.split('T')[0]
        t = dt.split('T')[1]
        t = t.rstrip(t[-1])
        rs.append((match['homeTeam']['name'], match['awayTeam']['name'], d, t))
        row += 1

    return  rs, row

# get upcoming matches for a particular team  ----check
def get_team_matches(team_name):
    team = t1_teams[team_name]
    params = {'status': "SCHEDULED"}
    matches = requests.get(f'{URL}/teams/{team[0]}/matches', headers=headers, params=params).json()
    if (matches['count'] == 0):
        return "No upcoming games for " +  team_name, 0
        
    rs = []
    row = 0
    for match in matches['matches']:
        dt = match['utcDate']
        d = dt.split('T')[0]
        t = dt.split('T')[1]
        t = t.rstrip(t[-1])
        rs.append((match['competition']['name'], match['homeTeam']['name'], match['awayTeam']['name'], d, t))
        row += 1

    return rs, row

# get live matches
def get_live_match():
    params = {'status': "LIVE", 'status': "IN_PLAY", 'status': "PAUSED"}
    matches = requests.get(f'{URL}/matches', headers=headers, params=params).json()
    if (matches['count'] == 0):
        return "No live games", 0
        
    rs = []
    row = 0
    for match in matches['matches']:
        rs.append((match['competition']['name'], match['status'], match['homeTeam']['name'], match['awayTeam']['name']))
        row += 1

    return rs, row

# get matches by date
def get_matches(dt):
    params = {'dateFrom': dt, 'dateTo': dt}
    matches = requests.get(f'{URL}/matches', headers=headers, params=params).json()
    row = 0
    if (matches['count'] == 0):
        return "No games on " + dt, row, 0

    rs = []
    past = dt < str(date.today())

    for match in matches['matches']:
        dt = match['utcDate']
        t = dt.split('T')[1]
        t = t.rstrip(t[-1])
        row += 1
        if (past):
            hm = match['score']['fullTime']['homeTeam']
            aw = match['score']['fullTime']['awayTeam']
            score = hm + " - " + aw
            rs.append((match['competition']['name'], match['homeTeam']['name'], match['awayTeam']['name'], score))
        else:
            rs.append((match['competition']['name'], match['homeTeam']['name'], match['awayTeam']['name'], t))
    return rs, row, past


get_available_leagues()
get_available_teams()

#bot 
client = discord.Client()

@client.event
async def on_ready():
    print(f'Logged in as {client.user}...')

@client.event
async def on_message(message):
    if (message.author == client.user):
        return

    msg = message.content

    if (msg.startswith('!commands')):
        await message.channel.send("```{}```".format('''!leagues - Displays top leagues

!teams - Displays all teams

!league_name standings - Displays league_name standings
Eg: !Premier League standings - Displays Premier league standings

!league_code upcoming games - Displays upcoming games in league_code
Eg: !PL upcoming games - Displays upcoming games in Premier league

!team team_name upcoming games - Displays upcoming games of team_name
Eg: !team Real Madrid upcoming games - Displays Real Madrid's upcoming games

!live games -Displays all live games

!games yyyy-mm-dd - Displays all games happening on yyyy-mm-dd

!games today - Displays all games played today'''))

    if (msg.startswith('!leagues')):
        arr = get_available_leagues()
        hd = ['League', 'Country']
        await message.channel.send("Top Leagues")
        tb = tabulate(arr, hd)
        await message.channel.send("```{}```".format(tb))


    if (msg.startswith('!teams')):
        arr = get_available_teams()
        hd = ['Team', 'League']
        await message.channel.send("Teams")
        arr = np.array_split(arr, 10)
        for item in arr:
            tb = tabulate(list(item), hd)
            await message.channel.send("```{}```".format(tb))

    
    if (msg.startswith('!') and 'standings' in msg):
        res = msg.split('!')[1].split(' standings')[0]
        tb = get_standings(res)
        await message.channel.send(res + " standings")
        await message.channel.send("```{}```".format(tb))

    if (msg == '!live games'):
        rs, row = get_live_match()
        hd = ['League', 'Status', 'Home Team', 'Away Team']
        if (row):
            await message.channel.send("Live games")
            arr = np.array_split(rs, 10)
            for item in arr:
                tb = tabulate(list(item), hd)
                await message.channel.send("```{}```".format(tb))
        else:
            if(not rs):
                await message.channel.send("Error retriving data")
            else:
                await message.channel.send(rs)

    if (msg == '!games today'):
        rs, row = get_today_matches()
        hd = ['Matchday', 'League', 'Place', 'Home Team', 'Away Team', 'Date', 'Away']
        if (row):
            await message.channel.send("Games today")
            arr = np.array_split(rs, 10)
            for item in arr:
                tb = tabulate(list(item), hd)
                await message.channel.send("```{}```".format(tb))
        else:
            if(not rs):
                await message.channel.send("Error retriving data")
            else:
                await message.channel.send(rs)


    if (msg.startswith('!team') and 'upcoming games' in msg):
        res = msg.split('!team ')[1].split(' upcoming games')[0]
        rs, row = get_team_matches(res)
        hd = ['League', 'Home Team', 'Away Team', 'Date', 'Time']
        if (row):
            await message.channel.send(res + " upcoming games")
            arr = np.array_split(rs, 10)
            for item in arr:
                tb = tabulate(list(item), hd)
                await message.channel.send("```{}```".format(tb))
        else:
            if(not rs):
                await message.channel.send("Error retriving data")
            else:
                await message.channel.send(rs)

    if (msg.startswith('!') and ('team' not in msg) and 'upcoming games' in msg):
        res = msg.split('!')[1].split(' upcoming games')[0]
        rs, row = get_league_matches(res)
        hd = ['Home Team', 'Away Team', 'Date', 'Time']
        if (row):
            await message.channel.send(res + " upcoming games")
            arr = np.array_split(rs, 10)
            for item in arr:
                tb = tabulate(list(item), hd)
                await message.channel.send("```{}```".format(tb))
        else:
            if(not rs):
                await message.channel.send("Error retriving data")
            else:
                await message.channel.send(rs)

    if (msg.startswith('!games') and 'today' not in msg):
        res = msg.split('!games ')[1]
        rs, row, col = get_matches(res)
        hd = []
        if (col):
            hd = ['League', 'Home Team', 'Away Team', 'Score']
        else:
            hd = ['League', 'Home Team', 'Away Team', 'Time']
        
        if (row):
            await message.channel.send("games on " + res)
            arr = np.array_split(rs, 10)
            for item in arr:
                tb = tabulate(list(item), hd)
                await message.channel.send("```{}```".format(tb))
        else:
            if(not rs):
                await message.channel.send("Error retriving data")
            else:
                await message.channel.send(rs)

client.run(TOKEN)
