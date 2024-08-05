import discord
from discord.ext import commands, tasks
rom discord_components import DiscordComponents, Button, ButtonStyle, Select, SelectOption
from PIL import Image, ImageDraw
import random
import json
import time
import io
import os

# Initialize bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='.', intents=intents)
DiscordComponents(bot)  # Initialize DiscordComponents

# Load data from JSON files
with open('players.json', 'r') as f:
    players = json.load(f)
with open('stadiums.json', 'r') as f:
    stadiums = json.load(f)
with open('umpires.json', 'r') as f:
    umpires = json.load(f)

# Cooldowns and timing
drop_cooldown_duration = 3600  # 1 hour
shop_update_time = 43200  # 12 hours
drop_cooldown = {}
last_shop_update = time.time()  # Initialize with current time

# User data storage
user_data = {}

# Helper functions
def current_time():
    return int(time.time())

def get_user_data(user_id):
    if user_id not in user_data:
        user_data[user_id] = {
            'squad': [],
            'last_generated_team': [],
            'games': {}
        }
    return user_data[user_id]

def get_batters(team):
    return sorted([p for p in team if p['role'] == 'Batsman'], key=lambda x: x['overall'], reverse=True)

def get_bowlers(team):
    return sorted([p for p in team if p['role'] == 'Bowler'], key=lambda x: x['overall'], reverse=True)

# Command to generate a team of 11 random players
@bot.command(name='generate')
async def generate_team(ctx):
    team = random.sample(players, 11)
    user_data = get_user_data(ctx.author.id)
    user_data['last_generated_team'] = team
    team_message = '\n'.join([f"{player['name']} - {player['overall']} - {player['role']}" for player in team])
    await ctx.send(f"Generated team:\n{team_message}")

# Command to show the last generated team
@bot.command(name='xi')
async def show_last_team(ctx):
    user_data = get_user_data(ctx.author.id)
    if user_data['last_generated_team']:
        team = user_data['last_generated_team']
        team_message = '\n'.join([f"{player['name']} - {player['overall']} - {player['role']}" for player in team])
        await ctx.send(f"Your last team:\n{team_message}")
    else:
        await ctx.send("No team found. Please generate a team first.")

# Command to add a player to the squad
@bot.command(name='add_to_squad')
async def add_to_squad(ctx, player_name: str):
    user_data = get_user_data(ctx.author.id)
    if len(user_data['squad']) >= 20:
        await ctx.send("Your squad is full with 20 players.")
        return
    player = next((p for p in players if p['name'].lower() == player_name.lower()), None)
    if player:
        if player in user_data['squad']:
            await ctx.send(f"{player_name} is already in your squad.")
        else:
            user_data['squad'].append(player)
            await ctx.send(f"Added {player_name} to your squad.")
    else:
        await ctx.send(f"Player {player_name} not found.")

# Command to remove a player from the squad
@bot.command(name='remove_from_squad')
async def remove_from_squad(ctx, player_name: str):
    user_data = get_user_data(ctx.author.id)
    player = next((p for p in user_data['squad'] if p['name'].lower() == player_name.lower()), None)
    if player:
        user_data['squad'].remove(player)
        await ctx.send(f"Removed {player_name} from your squad.")
    else:
        await ctx.send(f"Player {player_name} is not in your squad.")

# Command to view the squad
@bot.command(name='squad')
async def view_squad(ctx):
    user_data = get_user_data(ctx.author.id)
    if user_data['squad']:
        squad_message = '\n'.join([f"{player['name']} - {player['overall']} - {player['role']}" for player in user_data['squad']])
        await ctx.send(f"Your squad:\n{squad_message}")
    else:
        await ctx.send("Your squad is empty. Add players to your squad first.")

# Command to drop a random player (overall rating < 90)
@bot.command(name='drop')
async def drop_player(ctx):
    current_time_ = current_time()
    if ctx.author.id not in drop_cooldown or (current_time_ - drop_cooldown[ctx.author.id]) > drop_cooldown_duration:
        available_players = [player for player in players if player['overall'] < 90]
        if available_players:
            player = random.choice(available_players)
            await ctx.send(f"Dropped player: {player['name']} - {player['overall']}")
        else:
            await ctx.send("No players available to drop.")
        drop_cooldown[ctx.author.id] = current_time_
    else:
        remaining_time = drop_cooldown_duration - (current_time_ - drop_cooldown[ctx.author.id])
        await ctx.send(f"Command on cooldown. Try again in {remaining_time // 60} minutes.")

# Command to display the list of major stadiums
@bot.command(name='stadiums')
async def show_stadiums(ctx):
    major_stadiums = [stadium for stadium in stadiums if stadium['type'] == 'Major']
    stadium_list = '\n'.join([f"{stadium['name']} - {stadium['country']} - {stadium['weather']} - {stadium['temperature']} - {stadium['pitch']}" for stadium in major_stadiums])
    await ctx.send(f"List of major stadiums:\n{stadium_list}")

# Command to pick a random umpire
@bot.command(name='umpire')
async def pick_umpire(ctx):
    umpire = random.choice(umpires)
    await ctx.send(f"Random umpire: {umpire}")

# Command to vote and potentially drop a random card
@bot.command(name='vote')
async def vote(ctx):
    available_cards = [player for player in players if player['type'] != 'Legend']
    card = random.choice(available_cards)
    if random.random() < 0.00001:
        card = next((p for p in players if p['name'] == "Don Bradman"), card)
    await ctx.send(f"Voted! Dropped card: {card['name']} - {card['price']}")

# Command to gamble coins
@bot.command(name='gamble')
async def gamble(ctx, amount: int):
    if amount < 100:
        await ctx.send("Minimum gamble amount is 100 coins.")
        return
    # Implement gambling logic here
    # For simplicity, let's assume a 50% chance of winning or losing
    if random.random() < 0.5:
        await ctx.send(f"Congratulations! You won {amount * 2} coins!")
    else:
        await ctx.send(f"Sorry, you lost {amount} coins.")

# Command to start a match
@bot.command(name='pm')
async def play_match(ctx):
    stadium = random.choice(stadiums)
    umpire = random.choice(umpires)
    match_details = (
        f"**Match Details:**\n"
        f"**Stadium:** {stadium['name']}\n"
        f"**Weather:** {stadium['weather']}\n"
        f"**Temperature:** {stadium['temperature']}\n"
        f"**Pitch:** {stadium['pitch']}\n"
        f"**Umpire:** {umpire}\n"
    )
    message = await ctx.send(match_details, components=[
        Button(style=ButtonStyle.green, label="Join Game", custom_id="join_game")
    ])
    
    # Store the message ID and game information for tracking
    user_data = get_user_data(ctx.author.id)
    user_data['games'][message.id] = {
        'host': ctx.author.id,
        'players': [ctx.author.id],
        'stadium': stadium,
        'umpire': umpire,
        'overs': None,
        'coin_toss': None,
        'batting_choice': None,
        'batting_team': None,
        'bowling_team': None,
        'last_bowler': None
    }

@bot.component()
async def on_button_click(ctx):
    game = None
    for game_info in user_data.get(ctx.author.id, {}).get('games', {}).values():
        if ctx.message.id in game_info:
            game = game_info
            break

    if not game:
        await ctx.send("Game not found.")
        return

    if ctx.custom_id == "join_game":
        if ctx.author.id in game['players']:
            await ctx.send("You are already in this game.")
        else:
            game['players'].append(ctx.author.id)
            await ctx.send(f"{ctx.author.mention} has joined the game!")
            if len(game['players']) == 2:
                await start_coin_toss(ctx, game)
    elif ctx.custom_id in ["heads", "tails"]:
        await handle_coin_toss(ctx, game, ctx.custom_id)
    elif ctx.custom_id in ["bat", "bowl"]:
        await handle_batting_choice(ctx, game, ctx.custom_id)
    elif ctx.custom_id == "pick_batsmen":
        await pick_players(ctx, game, "bat")
    elif ctx.custom_id == "pick_bowlers":
        await pick_players(ctx, game, "bowl")

async def start_coin_toss(ctx, game):
    # Prompt for coin toss
    message = await ctx.send("**Coin Toss:**\nChoose Heads or Tails.", components=[
        Button(style=ButtonStyle.primary, label="Heads", custom_id="heads"),
        Button(style=ButtonStyle.primary, label="Tails", custom_id="tails")
    ])
    game['coin_toss'] = message.id

async def handle_coin_toss(ctx, game, choice):
    result = random.choice(["heads", "tails"])
    if choice == result:
        await ctx.send(f"You won the coin toss! You can choose to bat or bowl.", components=[
            Button(style=ButtonStyle.success, label="Bat", custom_id="bat"),
            Button(style=ButtonStyle.danger, label="Bowl", custom_id="bowl")
        ])
        game['batting_choice'] = ctx.author.id
    else:
        await ctx.send(f"You lost the coin toss. The other team can choose to bat or bowl.", components=[
            Button(style=ButtonStyle.success, label="Bat", custom_id="bat"),
            Button(style=ButtonStyle.danger, label="Bowl", custom_id="bowl")
        ])
        game['batting_choice'] = ctx.author.id

async def handle_batting_choice(ctx, game, choice):
    if game['batting_choice'] == ctx.author.id:
        if choice == "bat":
            game['batting_team'] = ctx.author.id
            await ctx.send("You chose to bat. Please pick 2 batsmen.", components=[
                Select(placeholder="Select Batsmen", options=[SelectOption(label=p['name'], value=p['name']) for p in get_batters(get_user_data(ctx.author.id)['last_generated_team'])])
            ])
        else:
            game['batting_team'] = ctx.author.id
            await ctx.send("You chose to bowl. Please pick 2 bowlers.", components=[
                Select(placeholder="Select Bowlers", options=[SelectOption(label=p['name'], value=p['name']) for p in get_bowlers(get_user_data(ctx.author.id)['last_generated_team'])])
            ])
    else:
        if choice == "bat":
            game['bowling_team'] = ctx.author.id
            await ctx.send("Other team chose to bat. Please pick 2 batsmen.", components=[
                Select(placeholder="Select Batsmen", options=[SelectOption(label=p['name'], value=p['name']) for p in get_batters(get_user_data(ctx.author.id)['last_generated_team'])])
            ])
        else:
            game['bowling_team'] = ctx.author.id
            await ctx.send("Other team chose to bowl. Please pick 2 bowlers.", components=[
                Select(placeholder="Select Bowlers", options=[SelectOption(label=p['name'], value=p['name']) for p in get_bowlers(get_user_data(ctx.author.id)['last_generated_team'])])
            ])

async def pick_players(ctx, game, role):
    selected_players = await ctx.send("Pick your players.", components=[
        Select(placeholder=f"Select {role.capitalize()}", options=[SelectOption(label=p['name'], value=p['name']) for p in get_batters(get_user_data(ctx.author.id)['last_generated_team'])] if role == "bat" else [SelectOption(label=p['name'], value=p['name']) for p in get_bowlers(get_user_data(ctx.author.id)['last_generated_team'])])
    ])

    # Save the selected players
    user_data = get_user_data(ctx.author.id)
    if role == "bat":
        game['batsmen'] = selected_players.values
    else:
        game['bowlers'] = selected_players.values

    await ctx.send(f"Players for {role.capitalize()} have been selected!")

# Command to generate an image of player cards
@bot.command(name='image')
async def generate_image(ctx):
    user_data = get_user_data(ctx.author.id)
    if user_data['last_generated_team']:
        image = Image.new('RGB', (800, 1000), color=(255, 255, 255))
        draw = ImageDraw.Draw(image)
        y = 10
        for player in user_data['last_generated_team']:
            draw.text((10, y), f"{player['name']} - {player['overall']}", fill=(0, 0, 0))
            y += 40
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        await ctx.send(file=discord.File(fp=buffer, filename='players.png'))
    else:
        await ctx.send("No team found. Please generate a team first.")

# Task to update the shop every 12 hours
@tasks.loop(seconds=shop_update_time)
async def update_shop():
    global last_shop_update
    last_shop_update = current_time()
    # Update shop logic here
    print("Shop updated")

# Start the bot
update_shop.start()
bot.run(os.getenv('MY DISCORD BOT TOKEN'))
