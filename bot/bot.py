import os
import logging
import discord
from discord import app_commands
from discord.ext import commands
import tomlkit
from db.repository import get_latest, get_trend, get_all_names

logger = logging.getLogger(__name__)

ALERT_CHANNEL_ID = 1530540177485988013
CONFIG_PATH = "config.toml"

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


def load_config():
    with open(CONFIG_PATH, "r") as f:
        return tomlkit.parse(f.read())


def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        f.write(tomlkit.dumps(config))


async def check_and_alert(rows):
    """Called by scheduler/jobs.py right after each scrape.
    rows = list of dicts from scraper.py (timestamp, name, type, price)."""
    config = load_config()
    channel = bot.get_channel(ALERT_CHANNEL_ID)
    if channel is None:
        logger.error("Alert channel not found — check bot is in the server/has access")
        return

    alerts = config.get("alerts", {})
    for row in rows:
        section = alerts.get(row["type"], {}).get(row["name"])
        if not section:
            continue
        price = row["price"]
        if "above" in section and price >= section["above"]:
            await channel.send(f"🔺 **{row['name']}** ({row['type']}) = {price} — above {section['above']}")
        if "below" in section and price <= section["below"]:
            await channel.send(f"🔻 **{row['name']}** ({row['type']}) = {price} — below {section['below']}")

async def name_autocomplete(interaction: discord.Interaction, current: str):
    names = await get_all_names()
    return [
        app_commands.Choice(name=n, value=n)
        for n in names if current.lower() in n.lower()
    ][:25]  # Discord caps autocomplete results at 25


@bot.tree.command(name="price", description="Get current price for a crop/seed")
@app_commands.choices(item_type=[
    app_commands.Choice(name="Crop", value="crop"),
    app_commands.Choice(name="Seed", value="seed"),
])
@app_commands.autocomplete(name=name_autocomplete)
async def price(interaction: discord.Interaction, name: str, item_type: app_commands.Choice[str]):
    result = await get_latest(name, item_type.value)
    if result is None:
        await interaction.response.send_message(f"No data for {name} ({item_type.value})")
        return
    await interaction.response.send_message(
        f"**{result['name']}** ({result['type']}): {result['price']} @ {result['timestamp']}"
    )


@bot.tree.command(name="trend", description="Get price trend over N hours")
@app_commands.choices(item_type=[
    app_commands.Choice(name="Crop", value="crop"),
    app_commands.Choice(name="Seed", value="seed"),
])
@app_commands.autocomplete(name=name_autocomplete)
async def trend(interaction: discord.Interaction, name: str, item_type: app_commands.Choice[str], hours: int):
    rows = await get_trend(name, item_type.value, hours)
    if not rows:
        await interaction.response.send_message(f"No trend data for {name} ({item_type.value})")
        return
    lines = [f"{r['bucket']}: {r['avg_price']:.2f}" for r in rows[:20]]
    await interaction.response.send_message(f"**{name}** ({item_type.value}) trend:\n" + "\n".join(lines))


@bot.tree.command(name="setthreshold", description="Set an alert threshold")
async def setthreshold(interaction: discord.Interaction, item_type: str, name: str, direction: str, value: float):
    if direction not in ("above", "below"):
        await interaction.response.send_message("direction must be 'above' or 'below'")
        return
    config = load_config()
    alerts = config.setdefault("alerts", tomlkit.table())
    type_table = alerts.setdefault(item_type, tomlkit.table())
    name_table = type_table.setdefault(name, tomlkit.table())
    name_table[direction] = value
    save_config(config)
    await interaction.response.send_message(f"Set {item_type}.{name} {direction} = {value}")

@bot.event
async def on_ready():
    await bot.tree.sync()
    logger.info(f"Bot ready: {bot.user}")

