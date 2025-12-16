import asyncio
import os
import random
import re
import unicodedata

import discord
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", "0"))

QUESTIONS: list[tuple[str, str]] = [
    ("Quelle est la capitale du Japon ?", "Tokyo"),
    ("Combien de continents y a-t-il sur Terre ?", "7"),
    ("Quelle planète est surnommée la planète rouge ?", "Mars"),
]

intents = discord.Intents.default()
intents.message_content = True


def normalize(text: str) -> str:
    """Normalise une réponse: trim, minuscules, suppression accents + caractères parasites."""
    text = text.strip().lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")  # enlève accents
    text = re.sub(r"[^a-z0-9]+", "", text)  # enlève espaces/ponctuation/invisibles
    return text


class CultureGBot(discord.Client):
    def __init__(self) -> None:
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        # Sync "guild" = immédiat
        if GUILD_ID:
            guild = discord.Object(id=GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            print(f"✅ Slash commands sync sur le serveur (GUILD_ID={GUILD_ID})")
        else:
            await self.tree.sync()
            print("✅ Slash commands sync global (peut prendre du temps à apparaître)")

    async def on_ready(self) -> None:
        print(f"✅ Connecté en tant que {self.user} (id={self.user.id})")


bot = CultureGBot()


async def ask_question(interaction: discord.Interaction) -> None:
    question, answer = random.choice(QUESTIONS)

    embed = discord.Embed(title="🧠 CultureG", description=question)
    embed.set_footer(text="Réponds dans le chat (20s), je te dis si c'est bon 😉")
    await interaction.response.send_message(embed=embed)

    def check(msg: discord.Message) -> bool:
        return msg.author == interaction.user and msg.channel == interaction.channel and not msg.author.bot

    try:
        msg = await bot.wait_for("message", timeout=20.0, check=check)
    except asyncio.TimeoutError:
        await interaction.followup.send(f"⏰ Temps écoulé ! La réponse était : **{answer}**")
        return

    user_answer = normalize(msg.content)
    good = normalize(answer)

    # debug utile si jamais ça rebug
    print(f"[DEBUG] raw='{msg.content}' -> norm='{user_answer}' | expected='{good}'")

    if user_answer == good:
        await interaction.followup.send("✅ Bien joué ! Bonne réponse.")
    else:
        await interaction.followup.send(f"❌ Pas ça… La bonne réponse était : **{answer}**")


@bot.tree.command(name="culture", description="Pose une question CultureG")
async def culture(interaction: discord.Interaction) -> None:
    await ask_question(interaction)


# ✅ Alias pour éviter le bug /quiz “not found”
@bot.tree.command(name="quiz", description="Alias de /culture")
async def quiz(interaction: discord.Interaction) -> None:
    await ask_question(interaction)


def main() -> None:
    if not TOKEN:
        raise SystemExit("❌ DISCORD_TOKEN manquant dans .env (clé DISCORD_TOKEN)")
    print("🚀 Démarrage du bot CultureG…")
    bot.run(TOKEN)


if __name__ == "__main__":
    main()
