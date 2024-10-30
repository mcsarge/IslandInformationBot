import os
import logging
import wget
import requests
from zoneinfo import ZoneInfo
import datetime
from datetime import timedelta

from sunrisesunset import SunriseSunset
from functools import wraps
from dotenv import load_dotenv
from health_ping import HealthPing
from telegram import ForceReply, Update, Bot
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

#dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
#load_dotenv(dotenv_path)

if os.getenv("HEALTHCHECKS_ENDPOINT"):
    HealthPing(url=os.getenv("HEALTHCHECKS_ENDPOINT"),
               schedule="0,10,20,30,40,50 * * * *",
               retries=[60, 300, 720]).start()

async def getImage(url, save_as):
    if os.path.exists(save_as):
        os.remove(save_as) # if exist, remove it directly
    wget.download(url, save_as)

async def set_timer_tomorrow(chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add a job to the queue."""
    try:

        dt = datetime.datetime.now(tz=ZoneInfo("America/New_York")) + datetime.timedelta(hours=18)
        rs = SunriseSunset(dt, lat=45.955490, lon=-81.179014, zenith='official')
        rise_time, set_time = rs.sun_rise_set
        print(f"      Sunset tomorrow: {set_time}")
        # 1 minute before sunset
        set_time = set_time - datetime.timedelta(minutes=1)

        print(f"Sunset tomorrow-1 min: {set_time}")
        print(f"             Is night: {rs.is_night()}\n")

        job_removed = remove_job_if_exists(str(chat_id), context)
        context.job_queue.run_once(alarm, set_time, chat_id=chat_id, name=str(chat_id), data=set_time)

        print(f"Timer successfully set!")
        if job_removed:
            print(f" Old one was removed.")


    except (IndexError, ValueError):
        print(f"Error setting tomorrow sunset")


async def alarm(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the alarm message."""
    job = context.job

    image_url = 'http://192.168.0.157/cgi-bin/api.cgi?cmd=Snap&channel=0&rs=wuuPhkmUCeI9WG7C&user=admin&password=aabbcc112233'
    save_as = './images/sunset.jpeg'
    await getImage(image_url, save_as)
    await context.bot.sendPhoto(chat_id=job.chat_id, photo=open(save_as, 'rb'), caption='Island Sunset')
    await set_timer_tomorrow(job.chat_id, context)



def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


async def set_timer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add a job to the queue."""
    chat_id = update.effective_message.chat_id
    try:

        dt = datetime.datetime.now(tz=ZoneInfo("America/New_York"))
        rs = SunriseSunset(dt, lat=45.955490, lon=-81.179014, zenith='official')
        rise_time, set_time = rs.sun_rise_set
        print(f"      Sunset: {set_time}")
        # 1 minutes before sunset
        set_time = set_time - datetime.timedelta(minutes=1)
        print(f"Sunset-1 minute: {set_time}")
        print(f"       Is night: {rs.is_night()}\n")

        #check if the time for the sunset has already passed.
        if set_time < dt:
           #get tomorrows sunset and set it for then.
           await set_timer_tomorrow(chat_id, context)
           text += "Setting timer for tomrrow's sunset."
           await update.effective_message.reply_text(text)

        else:
           job_removed = remove_job_if_exists(str(chat_id), context)
           context.job_queue.run_once(alarm, set_time, chat_id=chat_id, name=str(chat_id), data=set_time)
           #context.job_queue.run_once(alarm, 15, chat_id=chat_id, name=str(chat_id), data=set_time)

           text = "Timer successfully set!"

           if job_removed:
               text += " Old one was removed."
           await update.effective_message.reply_text(text)

    except (IndexError, ValueError):
        await update.effective_message.reply_text("Usage: /set <seconds>", quote=False)


async def unset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remove the job if the user changed their mind."""
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
    text = "Timer successfully cancelled!" if job_removed else "You have no active timer."
    await update.message.reply_text(text)


def send_action(action):
    """Sends `action` while processing func command."""

    def decorator(func):
        @wraps(func)
        async def command_func(update, context, *args, **kwargs):
            await context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=action)
            return await func(update, context,  *args, **kwargs)
        return command_func

    return decorator

# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE)-> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!, I can respond to your commands. Type /garden, /tower, /power or /weather to get information.",
        reply_markup=ForceReply(selective=True),
    )

@send_action(ChatAction.TYPING)
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    user = update.effective_user
    await update.message.reply_text(
        rf"Hi {user.mention_html()}!, I can respond to your commands. Type /garden, /tower, /power or /weather to get information.",

@send_action(ChatAction.UPLOAD_PHOTO)
async def tower_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    image_url = 'http://192.168.0.157/cgi-bin/api.cgi?cmd=Snap&channel=0&rs=wuuPhkmUCeI9WG7C&user=admin&password=aabbcc112233'
    save_as = './images/tower.jpeg'
    await getImage(image_url, save_as)
    await context.bot.sendPhoto(chat_id=update.effective_chat.id, photo=open(save_as, 'rb'), caption='Tower')

@send_action(ChatAction.UPLOAD_PHOTO)
async def garden_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    image_url = 'http://192.168.0.108/cgi-bin/api.cgi?cmd=Snap&channel=0&rs=wuuPhkmUCeI9WG7C&user=admin&password=aabbcc112233'
    save_as = './images/garden.jpeg'
    await getImage(image_url, save_as)
    await context.bot.sendPhoto(chat_id=update.effective_chat.id, photo=open(save_as, 'rb'), caption='Garden')


@send_action(ChatAction.TYPING)
async def power_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lines = ''
    if os.getenv("FILE"):
      try:
        with open(os.getenv("FILE"),'r') as file:
          while line := file.readline():
            lines = lines + line.replace('\\n','\n')
          file.close()
        await update.message.reply_text(lines)
      except:
        await update.message.reply_text("No power file present.")

    else:
      await update.message.reply_text("No power file (FILE) defined.")


@send_action(ChatAction.TYPING)
async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    weather_url = 'https://rt.ambientweather.net/v1/devices'

    if os.getenv("AMB_API_KEY"):
       params = dict(
          applicationKey=os.getenv("AMB_APP_KEY"),
          apiKey=os.getenv("AMB_API_KEY")
       )
       try:
          resp = requests.get(url=weather_url, params=params)
       except:
          await update.message.reply_text('Error fetching weather data.')
          return

       data = resp.json()

       lines =          'Outdoor Temp = ' + str(data[0]['lastData']['tempf']) + ' F\n'
       lines = lines +  'Outdoor Humidity = ' + str(data[0]['lastData']['humidity']) + ' %\n'
       lines = lines +  'Wind Speed = ' + str(data[0]['lastData']['windspeedmph']) + ' mph\n'
       lines = lines +  'Wind Gust = ' + str(data[0]['lastData']['windgustmph']) + ' mph\n'
       lines = lines +  'Wind Direction = ' + str(data[0]['lastData']['winddir']) + '\n'
       lines = lines +  'Solar Radiation = ' + str(data[0]['lastData']['solarradiation']) + ' W/m2\n'

       await update.message.reply_text(lines)
    else:
       await update.message.reply_text('Ambient Weather not set up.')



def main():
    """
    Handles the initial launch of the program (entry point).
    """
    token = os.getenv("BOT_TOKEN")
    application = Application.builder().token(token).concurrent_updates(True).read_timeout(30).write_timeout(30).build() # noqa
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("tower", tower_command))
    application.add_handler(CommandHandler("garden", garden_command))
    application.add_handler(CommandHandler("power", power_command))
    application.add_handler(CommandHandler("weather", weather_command))
    application.add_handler(CommandHandler("sunset", set_timer))
    application.add_handler(CommandHandler("unset", unset))

    print("Island Information Bot instance started!")
    application.run_polling()

if __name__ == '__main__':
    main()
