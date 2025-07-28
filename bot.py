import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os
from dotenv import load_dotenv

load_dotenv() 
TOKEN = os.getenv('DISCORD_TOKEN') 

intents = discord.Intents.all() 

bot = commands.Bot(command_prefix='!', intents=intents)

yt_dlp_options = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

async def play_audio(ctx, url):
    try:
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await asyncio.sleep(0.5)

        if not ctx.author.voice:
            await ctx.send("Tu dois être dans un salon vocal pour que je puisse te rejoindre, Timéo !")
            return

        voice_channel = ctx.author.voice.channel
        voice_client = await voice_channel.connect()
        await ctx.send(f"J'ai rejoint le salon vocal : **{voice_channel.name}**")

        with yt_dlp.YoutubeDL(yt_dlp_options) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
            except Exception as ytdl_error:
                await ctx.send(f"Désolé, je n'ai pas pu trouver cette vidéo ou lien. Erreur: `{ytdl_error}`")
                print(f"Erreur yt-dlp: {ytdl_error}")
                if ctx.voice_client:
                    await ctx.voice_client.disconnect()
                return

            if 'entries' in info: 
                info = info['entries'][0] 
            audio_url = info['url']

        voice_client.play(discord.FFmpegPCMAudio(audio_url, executable="ffmpeg"),
                          after=lambda e: print(f'Erreur de lecture: {e}') if e else None)

        await ctx.send(f"Je joue maintenant : **{info.get('title', 'Musique inconnue')}** de {info.get('uploader', 'Artiste inconnu')}")

    except discord.errors.ClientException as ce:
        print(f"Erreur de client Discord (déjà connecté ?): {ce}")
        await ctx.send(f"Désolé, une erreur est survenue avec la connexion vocale : `{ce}`")
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
    except Exception as e:
        print(f"Une erreur inattendue est survenue : {e}")
        await ctx.send(f"Désolé, une erreur inattendue est survenue et m'a empêché de jouer la musique : `{e}`")
        if ctx.voice_client:
            await ctx.voice_client.disconnect()



@bot.event
async def on_ready():
    """Se déclenche quand le bot est connecté à Discord."""
    print(f'Connecté en tant que {bot.user} ! Prêt à jouer de la musique pour Timéo !')
    await bot.change_presence(activity=discord.Game(name="!play <lien_youtube> ou terme de recherche"))

@bot.event
async def on_command_error(ctx, error):
    """Gère les erreurs de commande pour donner un feedback."""
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Il manque un argument ! Par exemple : `!play nom de la musique`")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send("Cette commande n'existe pas. Essaie `!play` ou `!stop`.")
    else:
        print(f"Une erreur inattendue est survenue : {error}")
        await ctx.send(f"Une erreur est survenue : `{error}`")


@bot.command(name='play')
async def play(ctx, *, url: str):
    """Joue une musique depuis un lien YouTube ou un terme de recherche."""
    print(f"Commande !play reçue avec l'URL/terme: {url} par {ctx.author.name}")
    await play_audio(ctx, url)

@bot.command(name='stop')
async def stop(ctx):
    """Arrête la musique et déconnecte le bot du salon vocal."""
    print(f"Commande !stop reçue par {ctx.author.name}")
    if ctx.voice_client:
        await ctx.voice_client.stop()
        await ctx.voice_client.disconnect()
        await ctx.send("J'ai arrêté la musique et me suis déconnecté du salon vocal.")
    else:
        await ctx.send("Je ne suis pas connecté à un salon vocal.")


if TOKEN is None:
    print("Erreur : Le token Discord n'a pas été trouvé. Assure-toi que DISCORD_TOKEN est défini dans ton fichier .env.")
else:
    try:
        bot.run(TOKEN)
    except discord.errors.LoginFailure:
        print("Erreur : Le token Discord est invalide. Vérifie ton fichier .env et le portail développeur.")
    except discord.errors.PrivilegedIntentsRequired as e:
        print(f"ERREUR CRITIQUE D'INTENTS : {e}")
        print("Vérifie TRÈS attentivement les 'Privileged Gateway Intents' sur le portail développeur Discord.")
        print("Assure-toi que PRESENCE INTENT, SERVER MEMBERS INTENT et MESSAGE CONTENT INTENT sont ACTIVÉS pour ce bot.")
    except Exception as e:
        print(f"Une erreur inattendue s'est produite au lancement du bot : {e}")
