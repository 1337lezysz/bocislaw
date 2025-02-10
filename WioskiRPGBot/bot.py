import mysql.connector
from mysql.connector import Error
import nextcord
import asyncio
from datetime import datetime, timedelta
from nextcord import Interaction
from nextcord.ext import commands
from nextcord.ui import Button, View, Modal, TextInput
from statusAPI import checkSerwer

db_config = {
    "host": "localhost", 
    "user": "discordbot",
    "password": "brak",
    "database": "discordbot"
}

def connect_to_database():
    try:
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            print("Połączono z bazą danych MySQL!")
        return connection
    except Error as e:
        print(f"Błąd podczas łączenia z bazą danych: {e}")
        return None

connection = connect_to_database()

async def update_server_status():
    while True:
        try:
            server = checkSerwer("51.83.214.131", 22003) # tu nalezy podać IP serwera MTA:SA
            if server.players is not None and server.maxplayers is not None:
                await bot.change_presence(activity=nextcord.Activity(type=nextcord.ActivityType.watching, name=f"Graczy: {server.players}/{server.maxplayers}"))
            else:
                await bot.change_presence(activity=nextcord.Activity(type=nextcord.ActivityType.watching, name="Serwer offline"))
        except Exception as e:
            print(f"Błąd podczas pobierania danych serwera: {e}")
            await bot.change_presence(activity=nextcord.Activity(type=nextcord.ActivityType.watching, name="Serwer offline"))
        
        await asyncio.sleep(60)

intents = nextcord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    bot.loop.create_task(update_server_status())
    print("=====================================================")
    print(f"Zalogowano jako: {bot.user}\nID bota: {bot.user.id}")
    print("=====================================================")
    polaczkanal = bot.get_channel(1313603964083896404) # nalezy podać id kanalu do synchronizacji kont
    await polaczkanal.purge()
    polaczembed = nextcord.Embed(title="Synchronizacja Konta!", description="> Aby podłączyć konto z botem należy kliknąć przycisk na dole!", timestamp=datetime.utcnow(), color=nextcord.Color.blurple())
    polaczembed.set_author(name="Synchronizacja konta | TheNoobisty lol", icon_url=bot.user.display_avatar.url)
    polaczembed.set_thumbnail(url=bot.user.display_avatar.url)
    polaczembed.set_footer(text="Panel wysłano!")
    sync_button = Button(label="Synchronizuj konto", style=nextcord.ButtonStyle.danger)
    async def sync_callback(interaction: Interaction):
        class SyncModal(Modal):
            def __init__(self):
                super().__init__(title="Synchronizacja Konta")
                self.kod_input = TextInput(label="Wpisz kod weryfikacyjny", placeholder="Podaj kod weryfikacyjny", required=True)
                self.add_item(self.kod_input)

            async def callback(self, modal_interaction: Interaction):
                kod = self.kod_input.value 
                try:
                    cursor = connection.cursor(dictionary=True)
                    cursor.execute("SELECT * FROM pystories_users WHERE kod = %s", (kod,))
                    rows = cursor.fetchall()

                    if not rows:
                        await modal_interaction.response.send_message(
                            embed=nextcord.Embed(title=":x: Błąd", description="Podany kod weryfikacyjny jest nieprawidłowy!", color=nextcord.Color.red()), ephemeral=True)
                        return

                    user_data = rows[0]

                    cursor.execute("SELECT * FROM discord_connect WHERE serial = %s", (user_data["register_serial"],))
                    if cursor.fetchone():
                        await modal_interaction.response.send_message(
                            embed=nextcord.Embed(description="To konto jest już połączone z naszym serwerem!", color=nextcord.Color.blue()), ephemeral=True)
                        return

                    avatar_url = modal_interaction.user.avatar.url
                    cursor.execute("INSERT INTO discord_connect (avatarurl, discord_login, did, sid, serial, nick) VALUES (%s, %s, %s, %s, %s, %s)", (avatar_url, str(modal_interaction.user), modal_interaction.user.id, user_data["id"], user_data["register_serial"], user_data["login"]))
                    cursor.execute("UPDATE pystories_users SET  avatar = %s, discordconnected = 'TAK', did = %s WHERE kod = %s", (avatar_url, modal_interaction.user.id, kod))
                    connection.commit()

                    await modal_interaction.response.send_message(
                        embed=nextcord.Embed(title=":white_check_mark: Połączono konto!", description=(f"Udało ci się połączyć konto Discord o ID `{modal_interaction.user.id}`\nZ kontem MTA o serialu: ||{user_data['register_serial']}||\nAby ujrzeć swój avatar, należy zrobić reconnect!"), color=nextcord.Color.blurple()), ephemeral=True)
                except Error as e:
                    print(f"Błąd bazy danych: {e}")
                    await modal_interaction.response.send_message("Wystąpił błąd podczas połączenia konta. Spróbuj ponownie później.", ephemeral=True)

        await interaction.response.send_modal(SyncModal())

    sync_button.callback = sync_callback
    view = View()
    view.add_item(sync_button)
    await polaczkanal.send(embed=polaczembed, view=view)

replace = {
    "1": "Tak",
    "0": "Nie"
}

@bot.slash_command(name="konto", description="Sprawdź informacje o swoim koncie!")
async def konto(interaction: Interaction):
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM discord_connect WHERE did = %s", (interaction.user.id,))
        rows = cursor.fetchall()
        if not rows:
            embed = nextcord.Embed(description="Nie posiadasz podłączonego konta z naszym serwerem!", color=nextcord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        sid = rows[0]["sid"]

        cursor.execute("SELECT * FROM pystories_users WHERE id = %s", (sid,))
        user_data = cursor.fetchall()

        if not user_data:
            embed = nextcord.Embed(description="Nie posiadasz konta!", color=nextcord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        user = user_data[0]

        data_rejestracji = user['registered']
        if isinstance(data_rejestracji, datetime):
            timestamp = int(data_rejestracji.timestamp())
            data_rejestracji_umix = f"<t:{timestamp}:R>"

        kontoembed = nextcord.Embed(title="Informacje na temat twojego konta!", description=f":person_frowning: Login: **{user['login']}** (SID: **{user['id']}**)\n:joystick: Level: **{user['lvl']}** (EXP: **{user['exp']}**)\n:clock4: **Przegrany Czas**: {user['hours']} minut\n:date: **Data rejestracji**: {data_rejestracji_umix}\n:money_with_wings: Pieniądze: **{user['money']}** PLN\n:moneybag: Pieniądze w banku: **{user['bank_money']}** PLN\n:ninja: Skin: **{user['skin']}**\n\n**Prawa jazdy:**\n:motor_scooter: Kat. A: **{replace.get(user['pjA'], 'Nie')}**\n:red_car: Kat. B: **{replace.get(user['pjB'], 'Nie')}**\n:truck: Kat. C: **{replace.get(user['pjC'], 'Nie')}**", color=nextcord.Color.purple(), timestamp=datetime.utcnow())
        await interaction.response.send_message(embed=kontoembed, ephemeral=True)
    except Error as e:
        print(f"Błąd bazy danych: {e}")
        await interaction.response.send_message("Wystąpił błąd podczas sprawdzania konta. Spróbuj ponownie później.", ephemeral=True)


bot.run("") # token bota