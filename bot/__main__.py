from signal import signal, SIGINT
import random
from random import choice
from os import path as ospath, remove as osremove, execl as osexecl
from subprocess import run as srun, check_output
from datetime import datetime, timedelta
from psutil import disk_usage, cpu_percent, swap_memory, cpu_count, virtual_memory, net_io_counters, boot_time
from time import time
from sys import executable
from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler
import requests
import pytz
from bot import bot, dispatcher, updater, botStartTime, TIMEZONE, IGNORE_PENDING_REQUESTS, LOGGER, Interval, INCOMPLETE_TASK_NOTIFIER, \
                    DB_URI, alive, app, main_loop, HEROKU_API_KEY, HEROKU_APP_NAME, SET_BOT_COMMANDS, AUTHORIZED_CHATS, EMOJI_THEME, \
                    START_BTN1_NAME, START_BTN1_URL, START_BTN2_NAME, START_BTN2_URL, CREDIT_NAME, TITLE_NAME, PICS
from .helper.ext_utils.fs_utils import start_cleanup, clean_all, exit_clean_up
from .helper.ext_utils.telegraph_helper import telegraph
from .helper.ext_utils.bot_utils import get_readable_file_size, get_readable_time
from .helper.ext_utils.db_handler import DbManger
from .helper.telegram_helper.bot_commands import BotCommands
from .helper.telegram_helper.message_utils import sendMessage, sendMarkup, editMessage, sendLogFile, sendPhoto
from .helper.telegram_helper.filters import CustomFilters
from .helper.telegram_helper.button_build import ButtonMaker
from bot.modules.wayback import getRandomUserAgent
from .modules import authorize, list, cancel_mirror, mirror_status, mirror_leech, clone, ytdlp, shell, eval, \
                    delete, count, leech_settings, search, rss, wayback, speedtest, usage, anilist, bt_select, mediainfo, hash, sleep
from bot import *
from datetime import datetime

now=datetime.now(pytz.timezone(f'{TIMEZONE}'))

IMAGE_STATS = "https://telegra.ph/file/1fb3daf55643a745f9339.jpg"
IMAGE_START = "https://telegra.ph/file/231af0efb2b7e60e7f5da.jpg"

def progress_bar(percentage):
    p_used = '⬢'
    p_total = '⬡'
    if isinstance(percentage, str):
        return 'NaN'
    try:
        percentage=int(percentage)
    except:
        percentage = 0
    return ''.join(
        p_used if i <= percentage // 10 else p_total for i in range(1, 11)
    )

def stats(update, context):
    if ospath.exists('.git'):
        last_commit = check_output(["git log -1 --date=short --pretty=format:'%cr \n<b>Version: </b> %cd'"], shell=True).decode()
    else:
        last_commit = 'No UPSTREAM_REPO'
    currentTime = get_readable_time(time() - botStartTime)
    total, used, free, disk= disk_usage('/')
    total = get_readable_file_size(total)
    used = get_readable_file_size(used)
    free = get_readable_file_size(free)
    sent = get_readable_file_size(net_io_counters().bytes_sent)
    recv = get_readable_file_size(net_io_counters().bytes_recv)
    cpuUsage = cpu_percent(interval=1)
    memory = virtual_memory()
    mem_p = memory.percent
    stats = f'<b><u>PeterX3 Bot Statistics</u></b>\n\n'\
            f'<b>CPU</b>:  {progress_bar(cpuUsage)} {cpuUsage}%\n' \
            f'<b>RAM</b>: {progress_bar(mem_p)} {mem_p}%\n' \
            f'<b>DISK</b>: {progress_bar(disk)} {disk}%\n\n' \
            f'<b>Last Updated:</b> {last_commit}\n'\
            f'<b>UPTM:</b> <code>{currentTime}</code>\n\n'\
            f'<b>Total Disk:</b> <code>{total}</code> [{disk}% In use]\n'\
            f'<b>Used:</b> <code>{used}</code> | <b>Free:</b> <code>{free}</code>\n'\
            f'<b>T-UL:</b> <code>{sent}</code> | <b>T-DL:</b> <code>{recv}</code>\n'
    update.effective_message.reply_photo(
                IMAGE_STATS,
                stats,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(
                    [[
                         InlineKeyboardButton(
                             text="Peter X Cloud",
                             url="https://t.me/PeterXCloud"),
                    ]]))

def start(update, context):
    buttons = ButtonMaker()
    if EMOJI_THEME is True:
        buttons.buildbutton(f"😎 {START_BTN1_NAME}", f"{START_BTN1_URL}")
        buttons.buildbutton(f"🔥 {START_BTN2_NAME}", f"{START_BTN2_URL}")
    else:
        buttons.buildbutton("Owner", "telegram.dog/KristyX_TG")
        buttons.buildbutton("Mirror Logs", "https://t.me/+C29hzgP2Ol81MzJk")
        buttons.buildbutton("Leech Logs", "https://t.me/+debqz-eWtrY1ZjQ0")
        buttons.buildbutton("Updates", "telegram.dog/PeterXCloud")
    reply_markup = InlineKeyboardMarkup(buttons.build_menu(2))
    if CustomFilters.authorized_user(update) or CustomFilters.authorized_chat(update):
        start_string = f''' This bot can mirror all your links to Google Drive!
Type /{BotCommands.HelpCommand} to get a list of available commands
'''
        if PICS:
            sendPhoto(start_string, context.bot, update.message, random.choice(PICS), reply_markup)
        else:
            sendMarkup(start_string, context.bot, update.message, reply_markup)
    else:
        text = f"<b><u>Access Denied...</u>\nYou can't use me here.\nJoin My Group & use me there\n I'll send your links & leeched files here.</b>"

        if PICS:
            sendPhoto(text, context.bot, update.message, random.choice(PICS), reply_markup)
        else:
            sendMarkup(text, context.bot, update.message, reply_markup)

def restart(update, context):
    cmd = update.effective_message.text.split(' ', 1)
    dynoRestart = False
    dynoKill = False
    if len(cmd) == 2:
        dynoRestart = (cmd[1].lower()).startswith('d')
        dynoKill = (cmd[1].lower()).startswith('k')
    if (not HEROKU_API_KEY) or (not HEROKU_APP_NAME):
        LOGGER.info("If you want Heroku features, fill HEROKU_APP_NAME HEROKU_API_KEY vars.")
        dynoRestart = False
        dynoKill = False
    if dynoRestart:
        LOGGER.info("Dyno Restarting.")
        restart_message = sendMessage("Dyno Restarting.", context.bot, update.message)
        with open(".restartmsg", "w") as f:
            f.truncate(0)
            f.write(f"{restart_message.chat.id}\n{restart_message.message_id}\n")
        heroku_conn = heroku3.from_key(HEROKU_API_KEY)
        app = heroku_conn.app(HEROKU_APP_NAME)
        app.restart()
    elif dynoKill:
        LOGGER.info("Killing Dyno. MUHAHAHA")
        sendMessage("Killed Dyno.", context.bot, update.message)
        alive.kill()
        clean_all()
        heroku_conn = heroku3.from_key(HEROKU_API_KEY)
        app = heroku_conn.app(HEROKU_APP_NAME)
        proclist = app.process_formation()
        for po in proclist:
            app.process_formation()[po.type].scale(0)
    else:
        LOGGER.info("Normally Restarting.")
        restart_message = sendMessage("Normally Restarting.", context.bot, update.message)
        if Interval:
            Interval[0].cancel()
            Interval.clear()
        alive.kill()
        clean_all()
        srun(["pkill", "-9", "-f", "gunicorn|chrome|firefox|megasdkrest|opera"])
        srun(["python3", "update.py"])
        with open(".restartmsg", "w") as f:
            f.truncate(0)
            f.write(f"{restart_message.chat.id}\n{restart_message.message_id}\n")
        osexecl(executable, executable, "-m", "bot")



def ping(update, context):
    if EMOJI_THEME is True:
        start_time = int(round(time() * 1000))
        reply = sendMessage("Starting_Ping ⛔", context.bot, update.message)
        end_time = int(round(time() * 1000))
        editMessage(f'{end_time - start_time} ms 🔥', reply)
    else:
        start_time = int(round(time() * 1000))
        reply = sendMessage("Starting_Ping ", context.bot, update.message)
        end_time = int(round(time() * 1000))
        editMessage(f'{end_time - start_time} ms ', reply)


def log(update, context):
    sendLogFile(context.bot, update.message)


help_string = '''
<b><a href='telegram.dog/PeterXCloud'>Peter X Cloud</a></b> - The Ultimate Telegram MIrror-Leech Bot to Upload Your File & Link in Google Drive & Telegram
Choose a help category:
'''

help_string_telegraph_user = f'''
<b><u>👤 User Commands</u></b>
<br><br>
• <b>/{BotCommands.HelpCommand}</b>: To get this message
<br><br>
• <b>/{BotCommands.MirrorCommand}</b> [download_url][magnet_link]: Start mirroring to Google Drive. Send <b>/{BotCommands.MirrorCommand}</b> for more help
<br><br>
• <b>/{BotCommands.ZipMirrorCommand}</b> [download_url][magnet_link]: Start mirroring and upload the file/folder compressed with zip extension
<br><br>
• <b>/{BotCommands.UnzipMirrorCommand}</b> [download_url][magnet_link]: Start mirroring and upload the file/folder extracted from any archive extension
<br><br>
• <b>/{BotCommands.QbMirrorCommand}</b> [magnet_link][torrent_file][torrent_file_url]: Start Mirroring using qBittorrent, Use <b>/{BotCommands.QbMirrorCommand} s</b> to select files before downloading
<br><br>
• <b>/{BotCommands.QbZipMirrorCommand}</b> [magnet_link][torrent_file][torrent_file_url]: Start mirroring using qBittorrent and upload the file/folder compressed with zip extension
<br><br>
• <b>/{BotCommands.QbUnzipMirrorCommand}</b> [magnet_link][torrent_file][torrent_file_url]: Start mirroring using qBittorrent and upload the file/folder extracted from any archive extension
<br><br>
• <b>/{BotCommands.LeechCommand}</b> [download_url][magnet_link]: Start leeching to Telegram, Use <b>/{BotCommands.LeechCommand} s</b> to select files before leeching
<br><br>
• <b>/{BotCommands.ZipLeechCommand}</b> [download_url][magnet_link]: Start leeching to Telegram and upload the file/folder compressed with zip extension
<br><br>
• <b>/{BotCommands.UnzipLeechCommand}</b> [download_url][magnet_link][torent_file]: Start leeching to Telegram and upload the file/folder extracted from any archive extension
<br><br>
• <b>/{BotCommands.QbLeechCommand}</b> [magnet_link][torrent_file][torrent_file_url]: Start leeching to Telegram using qBittorrent, Use <b>/{BotCommands.QbLeechCommand} s</b> to select files before leeching
<br><br>
• <b>/{BotCommands.QbZipLeechCommand}</b> [magnet_link][torrent_file][torrent_file_url]: Start leeching to Telegram using qBittorrent and upload the file/folder compressed with zip extension
<br><br>
• <b>/{BotCommands.QbUnzipLeechCommand}</b> [magnet_link][torrent_file][torrent_file_url]: Start leeching to Telegram using qBittorrent and upload the file/folder extracted from any archive extension
<br><br>
• <b>/{BotCommands.CloneCommand}</b> [drive_url][gdtot_url]: Copy file/folder to Google Drive
<br><br>
• <b>/{BotCommands.CountCommand}</b> [drive_url][gdtot_url]: Count file/folder of Google Drive
<br><br>
• <b>/{BotCommands.DeleteCommand}</b> [drive_url]: Delete file/folder from Google Drive (Only Owner & Sudo)
<br><br>
• <b>/{BotCommands.WatchCommand}</b> [yt-dlp supported link]: Mirror yt-dlp supported link. Send <b>/{BotCommands.WatchCommand}</b> for more help
<br><br>
• <b>/{BotCommands.ZipWatchCommand}</b> [yt-dlp supported link]: Mirror yt-dlp supported link as zip
<br><br>
• <b>/{BotCommands.LeechWatchCommand}</b> [yt-dlp supported link]: Leech yt-dlp supported link
<br><br>
• <b>/{BotCommands.LeechZipWatchCommand}</b> [yt-dlp supported link]: Leech yt-dlp supported link as zip
<br><br>
• <b>/{BotCommands.LeechSetCommand}</b>: Leech settings
<br><br>
• <b>/{BotCommands.SetThumbCommand}</b>: Reply photo to set it as Thumbnail
<br><br>
• <b>/{BotCommands.RssListCommand}</b>: List all subscribed rss feed info
<br><br>
• <b>/{BotCommands.RssGetCommand}</b>: [Title] [Number](last N links): Force fetch last N links
<br><br>
• <b>/{BotCommands.RssSubCommand}</b>: [Title] [Rss Link] f: [filter]: Subscribe new rss feed
<br><br>
• <b>/{BotCommands.RssUnSubCommand}</b>: [Title]: Unubscribe rss feed by title
<br><br>
• <b>/{BotCommands.RssSettingsCommand}</b>: Rss Settings
<br><br>
• <b>/{BotCommands.CancelMirror}</b>: Reply to the message by which the download was initiated and that download will be cancelled
<br><br>
• <b>/{BotCommands.CancelAllCommand}</b>: Cancel all downloading tasks
<br><br>
• <b>/{BotCommands.ListCommand}</b> [query]: Search in Google Drive(s)
<br><br>
• <b>/{BotCommands.SearchCommand}</b> [query]: Search for torrents with API
<br>sites: <code>rarbg, 1337x, yts, etzv, tgx, torlock, piratebay, nyaasi, ettv</code><br><br>
• <b>/{BotCommands.StatusCommand}</b>: Shows a status of all the downloads
<br><br>
• <b>/{BotCommands.UsageCommand}</b>: Shows Heroku App Dyno Usage
<br><br>
• <b>/{BotCommands.StatsCommand}</b>: Show Stats of the machine the bot is hosted on
<br><br>
• <b>/{BotCommands.SpeedCommand}</b>: Speedtest of Heroku server
<br><br>
• <b>/weebhelp</b>: Okatu helper
'''

help_user = telegraph.create_page(
    title=f"{TITLE_NAME} Help",
    content=help_string_telegraph_user)["path"]

help_string_telegraph_admin = f'''
<b><u>🛡️ Admin Commands</u></b>
<br><br>
• <b>/{BotCommands.PingCommand}</b>: Check how long it takes to Ping the Bot
<br><br>
• <b>/{BotCommands.AuthorizeCommand}</b>: Authorize a chat or a user to use the bot (Can only be invoked by Owner & Sudo of the bot)
<br><br>
• <b>/{BotCommands.UnAuthorizeCommand}</b>: Unauthorize a chat or a user to use the bot (Can only be invoked by Owner & Sudo of the bot)
<br><br>
• <b>/{BotCommands.AuthorizedUsersCommand}</b>: Show authorized users (Only Owner & Sudo)
<br><br>
• <b>/{BotCommands.AddSudoCommand}</b>: Add sudo user (Only Owner)
<br><br>
• <b>/{BotCommands.RmSudoCommand}</b>: Remove sudo users (Only Owner)
<br><br>
• <b>/{BotCommands.RestartCommand}</b>: Restart and update the bot
<br><br>
• <b>/{BotCommands.LogCommand}</b>: Get a log file of the bot. Handy for getting crash reports
'''

help_admin = telegraph.create_page(
    title=f"{TITLE_NAME} Help",
    content=help_string_telegraph_admin)["path"]

def bot_help(update, context):
    button = ButtonMaker()
    if EMOJI_THEME is True:
        button.buildbutton("👤 User", f"https://graph.org/{help_user}")
        button.buildbutton("🛡️ Admin", f"https://graph.org/{help_admin}")
    else:
        button.buildbutton("User", f"https://graph.org/{help_user}")
        button.buildbutton("Admin", f"https://graph.org/{help_admin}")
    sendMarkup(help_string, context.bot, update.message, InlineKeyboardMarkup(button.build_menu(2)))

       


if SET_BOT_COMMANDS:
    botcmds = [
        (f'{BotCommands.MirrorCommand}', 'Mirror'),
        (f'{BotCommands.ZipMirrorCommand}','Mirror and upload as zip'),
        (f'{BotCommands.UnzipMirrorCommand}','Mirror and extract files'),
        (f'{BotCommands.QbMirrorCommand}','Mirror torrent using qBittorrent'),
        (f'{BotCommands.QbZipMirrorCommand}','Mirror torrent and upload as zip using qb'),
        (f'{BotCommands.QbUnzipMirrorCommand}','Mirror torrent and extract files using qb'),
        (f'{BotCommands.WatchCommand}','Mirror yt-dlp supported link'),
        (f'{BotCommands.ZipWatchCommand}','Mirror yt-dlp supported link as zip'),
        (f'{BotCommands.CloneCommand}','Copy file/folder to Drive'),
        (f'{BotCommands.LeechCommand}','Leech'),
        (f'{BotCommands.ZipLeechCommand}','Leech and upload as zip'),
        (f'{BotCommands.UnzipLeechCommand}','Leech and extract files'),
        (f'{BotCommands.QbLeechCommand}','Leech torrent using qBittorrent'),
        (f'{BotCommands.QbZipLeechCommand}','Leech torrent and upload as zip using qb'),
        (f'{BotCommands.QbUnzipLeechCommand}','Leech torrent and extract using qb'),
        (f'{BotCommands.LeechWatchCommand}','Leech yt-dlp supported link'),
        (f'{BotCommands.LeechZipWatchCommand}','Leech yt-dlp supported link as zip'),
        (f'{BotCommands.CountCommand}','Count file/folder of Drive'),
        (f'{BotCommands.DeleteCommand}','Delete file/folder from Drive'),
        (f'{BotCommands.CancelMirror}','Cancel a task'),
        (f'{BotCommands.ListCommand}','Search in Drive'),
        (f'{BotCommands.LeechSetCommand}','Leech settings'),
        (f'{BotCommands.SetThumbCommand}','Set thumbnail'),
        (f'{BotCommands.StatusCommand}','Get mirror status message'),
        (f'{BotCommands.StatsCommand}','Bot usage stats'),
        (f'{BotCommands.UsageCommand}','Heroku Dyno usage'),
        (f'{BotCommands.RestartCommand}','Restart the bot'),
        (f'{BotCommands.HelpCommand}','Get detailed help'),
    ]


def main():
    if SET_BOT_COMMANDS:
        bot.set_my_commands(botcmds)
    start_cleanup()
    date = now.strftime('%d/%m/%y')
    time = now.strftime('%I:%M:%S %p')
    notifier_dict = False
    if INCOMPLETE_TASK_NOTIFIER and DB_URI is not None:
        if notifier_dict := DbManger().get_incomplete_tasks():
            for cid, data in notifier_dict.items():
                if ospath.isfile(".restartmsg"):
                    with open(".restartmsg") as f:
                        chat_id, msg_id = map(int, f)
                    msg = f"😎Restarted successfully❗\n"
                    msg += f" DATE: {date}\n"
                    msg += f" TIME: {time}\n"
                    msg += f" TIMEZONE: {TIMEZONE}\n"
                else:
                    msg = f"<b>Every Ends is a New Beginning! <b>\n\n**Bot Got Re-Started 🚀**"
                    msg += f"**📅 Date : {date}**\n"
                    msg += f"**⏰ Time : {time}**\n\n"
                    msg += f"**🗺️ Time Zone : {TIMEZONE}**\n\n"
                    msg += f"**Please Re-Download Your Tasks 🚶**"

                for tag, links in data.items():
                     msg += f"\n{tag}: "
                     for index, link in enumerate(links, start=1):
                         msg += f" <a href='{link}'>{index}</a> |"
                         if len(msg.encode()) > 4000:
                             if '😎Restarted successfully❗' in msg and cid == chat_id:
                                 bot.editMessageText(msg, chat_id, msg_id, parse_mode='HTML', disable_web_page_preview=True)
                                 osremove(".restartmsg")
                             else:
                                 try:
                                     bot.sendMessage(cid, msg, 'HTML', disable_web_page_preview=True)
                                 except Exception as e:
                                     LOGGER.error(e)
                             msg = ''
                if '😎Restarted successfully❗' in msg and cid == chat_id:
                     bot.editMessageText(msg, chat_id, msg_id, parse_mode='HTML', disable_web_page_preview=True)
                     osremove(".restartmsg")
                else:
                    try:
                        bot.sendMessage(cid, msg, 'HTML', disable_web_page_preview=True)
                    except Exception as e:
                        LOGGER.error(e)

    if ospath.isfile(".restartmsg"):
        with open(".restartmsg") as f:
            chat_id, msg_id = map(int, f)
        msg = f"😎Restarted successfully❗\n DATE: {date}\n TIME: {time}\n TIMEZONE: {TIMEZONE}\n"
        bot.edit_message_text(msg, chat_id, msg_id)
        osremove(".restartmsg")
    elif not notifier_dict and AUTHORIZED_CHATS:
        text = f"<b>Every Ends is a New Beginning! \n\nBot Got Re-Started 🚀\n\n📅 Date : {date}\n⏰ Time : {time}\n\n🗺️ TimeZone : {TIMEZONE}\n\nPlease Re-Download Your Tasks 🚶</b>"
        for id_ in AUTHORIZED_CHATS:
            try:
                bot.sendMessage(chat_id=id_, text=text, parse_mode=ParseMode.HTML)
            except Exception as e:
                LOGGER.error(e)


    start_handler = CommandHandler(BotCommands.StartCommand, start, run_async=True)
    ping_handler = CommandHandler(BotCommands.PingCommand, ping,
                                  filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
    restart_handler = CommandHandler(BotCommands.RestartCommand, restart,
                                     filters=CustomFilters.owner_filter | CustomFilters.sudo_user, run_async=True)
    help_handler = CommandHandler(BotCommands.HelpCommand,
                                  bot_help, filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
    stats_handler = CommandHandler(BotCommands.StatsCommand,
                                   stats, filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
    log_handler = CommandHandler(BotCommands.LogCommand, log, filters=CustomFilters.owner_filter | CustomFilters.sudo_user, run_async=True)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(ping_handler)
    dispatcher.add_handler(restart_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(stats_handler)
    dispatcher.add_handler(log_handler)
    updater.start_polling(drop_pending_updates=IGNORE_PENDING_REQUESTS)
    LOGGER.info("💥𝐁𝐨𝐭 𝐒𝐭𝐚𝐫𝐭𝐞𝐝❗")
    signal(SIGINT, exit_clean_up)

app.start()
main()

main_loop.run_forever()
