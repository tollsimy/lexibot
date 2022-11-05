# -------------------------- Imports and basic stuff ------------------------- #
from asyncio import FIRST_COMPLETED
import logging
import re

from parso import parse
import constants as const
from telegram import __version__ as TG_VER
import telegram as telegram
import sys
import json
sys.path.append(const.scripts_path)
from reverso_wrapped_api import *
from gsheets_wrapped_api import *
from os import environ

PORT = int(environ.get('PORT'))
TOKEN = environ.get('TOKEN')
GSERVICE_ACC = json.loads(environ.get('GSERVICE_ACC'))

try:
    from telegram import __version_info__

except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )

from telegram import (ForceReply, Update, ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (Application, CommandHandler, ContextTypes, MessageHandler,
                            filters, Updater, ConversationHandler)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --------------------------------- Global vars ------------------------------ #

sheet_id = None
sheet_name = None
sheet_action = None
target_lang = None
mother_lang = None
email = None
is_resuming = False
is_starting_phase = False
# Class instances
reverso = None
gsheet = None

# Conversation FSM states
FIRST_TIME_STATE = 8
LANG_STATE = 16
EMAIL_STATE = 32
SHEET_STATE = 64

# CONVERSATION END CMD
END_CONVERSATION = -3
# Sheet access methods
OPEN_BY_NAME = 0
OPEN_BY_URL = 1

# ----------------------------- Utility functions ----------------------------- #

def parse_header(sheet_headers: list):
    return [const.lang_dict[sheet_headers[0].lower()],const.lang_dict[sheet_headers[1].lower()]]

# ----------------------------- Command Handlers ----------------------------- #

# /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    #Send a message when the command /start is issued
    user = update.effective_user
    await update.message.reply_text("Hi " + user.full_name + "! Please set language and google sheet link with /set_lang and /set_sheet")
    logger.debug("Start command issued")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    #Send a message when the command /help is issued
    await update.message.reply_text(const.help_msg)
    logger.debug("Help command issued")

async def set_lang(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    #Set translation language
    global target_lang
    global mother_lang
    global reverso

    # Langauges are case-insensitive
    msg = update.message.text.lower()

    try:
        if("/set_lang" in msg):
            arg1 = msg.split("/set_lang ")[1]
        else:
            arg1 = msg
        arg1 = arg1.split(" ")[0]
        arg2 = msg.split(" to ")[1]
        logger.debug("Languages set to " + arg1 + " to " + arg2)
    except:
        # If we are here from the command handler, message is this one
        if("/set_lang" in update.message.text):
            await update.message.reply_text("A)Invalid command, use /set_lang [language_to_learn] to [mothertongue]")
        # If we are here from the conversation handler, message is different
        else:
            await update.message.reply_text("B)Invalid format, use [language_to_learn] to [mothertongue]")
        logger.debug("/set_lang: Invalid command")
        return -1

    if arg1 in const.lang_dict and arg2 in const.lang_dict:
        target_lang=const.lang_dict[arg1]
        mother_lang=const.lang_dict[arg2]
        await update.message.reply_text("Target language set to: " + target_lang + '\n'\
        + "Mothertongue language set to: " + mother_lang)
        logger.debug("Languages are valid")

        #Start reverso
        reverso = Reverso_Api(target_lang, mother_lang)
        logger.debug("Reverso started")

    elif arg1 in const.lang_dict.values() and arg2 in const.lang_dict.values():
        target_lang=arg1
        mother_lang=arg2
        await update.message.reply_text("Target language set to: " + target_lang + '\n'\
        + "Mothertongue language set to: " + mother_lang)
        logger.debug("Languages are valid")

        #Start reverso
        reverso = Reverso_Api(target_lang, mother_lang)
        logger.debug("Reverso started")

    else:
        await update.message.reply_text("Languages not found, visit /help")
        logger.debug("Languages not found")
        return -1
    
    return 0

async def set_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    
    global email

    # Email are case-insensitive
    msg = update.message.text.lower()

    try:
        if("/set_email" in msg):
            email = msg.split("/set_email ")[1]
        else:
            email = msg
        # If email is not gmail return fail
        if "@gmail.com" not in email:
            raise Exception
        logger.debug("Inserted email is: " + email)
    except:
        # If we are here from the command handler, message is this one
        if("/set_email" in update.message.text):
            await update.message.reply_text("Invalid command, use /set_email [your_address@gmail.com]")
        # If we are here from the conversation handler, message is different
        else:
            await update.message.reply_text("Invalid format, use [your_address@gmail.com]")
        logger.debug("/set_email: Invalid command")
        return -1

    await update.message.reply_text("Email address set to: " + email)
    logger.debug("Email valid")
    
    return 0

async def set_sheet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    #Set sheet link
    global sheet_id
    global sheet_name
    global gsheet
    global sheet_action
    global is_resuming

    msg = update.message.text

    try:
        if("/set_sheet" in msg.lower()):
            if ("create" in msg.lower()):
                sheet_name = re.split("/set_sheet create ", msg, flags=re.IGNORECASE)[1]
                sheet_name = sheet_name + " - LexiBot, learn new vocabularies"
                sheet_action = OPEN_BY_NAME
                logger.debug("Create new sheet: " + sheet_name)
            elif ("resume" in msg.lower()):
                sheet_id = re.split("/set_sheet resume ", msg, flags=re.IGNORECASE)[1]
                sheet_action = OPEN_BY_URL
                logger.debug("Resume sheet: " + sheet_id)
            else:
                raise SyntaxError
        else:
            if ("create" in msg.lower()):
                sheet_name = re.split("create ", msg, flags=re.IGNORECASE)[1]
                sheet_name = sheet_name + " - LexiBot, learn new vocabularies"
                sheet_action = OPEN_BY_NAME
                logger.debug("Create new sheet: " + sheet_name)
            elif ("resume" in msg.lower()):
                sheet_id = re.split("resume ", msg, flags=re.IGNORECASE)[1]
                sheet_action = OPEN_BY_URL
                is_resuming = True
                logger.debug("Resume sheet: " + sheet_id)
            else:
                raise SyntaxError
    # IndexError returned if re.split doesn't find the substring
    except SyntaxError or IndexError:
        # If we are here from the command handler, message is this one
        if("/set_sheet" in update.message.text):
            await update.message.reply_text("Invalid command, use /set_sheet create [sheet_name] or /set_sheet resume [sheet_id]")
        # If we are here from the conversation handler, message is different
        else:
            await update.message.reply_text("Invalid input, send create [sheet_name] or resume [sheet_id]")
        logger.exception("/set_sheet: Invalid command exception")
        return -1

    # Start gsheet
    try:
        gsheet = Gsheet_Api(GSERVICE_ACC, "dict")
        logger.debug("Gsheet service account authorized correctly")
    except:
        logger.exception("Error while connecting to google service account")
        await update.message.reply_text("Error while connecting to google service, please contact the bot maintainers [Tollsimy](t.me/Tollsimy) and/or [Cannox227](t.me/Cannox227).", parse_mode=telegram.constants.ParseMode.MARKDOWN)
        return -2

    if email is None and is_resuming == False:
        await update.message.reply_text("Please insert an email first")
        logger.debug("Please insert an email first")
        return -1

    if sheet_action == OPEN_BY_NAME:
        gsheet.create_sheet(sheet_name)
        gsheet.write_custom_row([mother_lang, target_lang, "Meaning"])
        logger.debug(f"Created Sheet {gsheet.sh.id}")
        gsheet.sh.share(email, perm_type='user', role='writer')
        logger.debug("Sheet shared correctly")
        await update.message.reply_text(f"Created Sheet named: {sheet_name},\nid: {gsheet.get_sheet_id()},\nurl: {gsheet.get_sheet_url()}")
        await update.message.reply_text(const.guided_msg_complete)
    elif sheet_action == OPEN_BY_URL:
        if gsheet.is_a_g_sheet("url", sheet_id):
            logger.debug(f"Sheet {sheet_id} is a valid google sheet")
            if not is_resuming:
                gsheet.sh.share(email, perm_type='user', role='writer')
                logger.debug("Sheet shared correctly")
            await update.message.reply_text(f"Sheet url {gsheet.get_sheet_url()} resumed correctly!\nNow you can just type the words you want to translate and I will translate for you add the results to the sheet.")
            return END_CONVERSATION
        else:
            logger.debug(f"Sheet {sheet_id} is not a valid google sheet")
            await update.message.reply_text("sheet_id not valid, please retry")
            return -1
    return 0

# Handler for whatever text that is not a command
async def translate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global target_lang
    global mother_lang
    global reverso
    #Reply with the translated the user message
    if(target_lang is None or mother_lang is None):
        if(gsheet.sh is not None):
            langs = parse_header(gsheet.get_sheet_header())
            target_lang = langs[0]
            mother_lang = langs[1]
            await translate(update, context)
        await update.message.reply_text("Please set language with /set_lang")
        logger.debug("Language not set")
        return -1
    elif (gsheet.sh is None and is_resuming == False):
        await update.message.reply_text("Please set google sheet link with /set_sheet")
        logger.debug("Sheet link not set")
        return -1
    elif (email is None and is_resuming == False):
        await update.message.reply_text("Please set your google email address with /set_email")
        logger.debug("Email address not set")
        return -1
    
    logger.debug("Translate message: " + update.message.text)
    if(reverso is None):
        reverso = Reverso_Api(target_lang, mother_lang)
        logger.debug("Started reverso")
    trad = reverso.get_separated_translations(update.message.text)
    logger.debug("Translation done")
    gsheet.write_on_sheet(update.message.text, trad)
    logger.debug("Written on sheet")
    await update.message.reply_text("Done! Translation: " + trad)
    return 0

async def get_target_lang(update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if(mother_lang is not None):
        await update.message.reply_text("Mother tonge language set to: " + mother_lang)
        logging.debug("get_target_lang called: " + mother_lang)
    else:
        await update.message.reply_text("Mother tonge language not set")
        logging.debug("get_target_lang called: mother tongue not set")

async def get_mother_lang(update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if(target_lang is not None):
        await update.message.reply_text("Target language set to: " + target_lang)
        logging.debug("get_mother_lang called: " + target_lang)
    else: 
        await update.message.reply_text("Target language not set")
        logging.debug("get_mother_lang called: target language not set")

async def get_sheet(update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if(sheet_id is not None):
        await update.message.reply_text("Sheet link set to: " + sheet_id)
        logging.debug("get_sheet called: " + sheet_id)
    else:
        await update.message.reply_text("Sheet link not set")
        logging.debug("get_sheet called: sheet link not set")

async def get_email(update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if(email is not None):
        await update.message.reply_text("Email address set to: " + email)
        logging.debug("get_email called: " + email)
    else:
        await update.message.reply_text("Email address not set")
        logging.debug("get_email called: email address not set")

async def random(update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if(gsheet.sh is not None):
        parsed_row = gsheet.get_random_row()
        # if you want just the whole row comment the following line
        parsed_row = parsed_row.split(",")[0]
        logger.debug(f"Parsed random row: {parsed_row}")
        if parsed_row is None or parsed_row == "":
           await update.message.reply_text("No data found") 
        else:
            await update.message.reply_text(parsed_row)
        logging.debug("printall called")

async def printall(update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if(gsheet.sh is not None):
        parsed_rows = gsheet.get_all_records_parsed()
        logger.debug(f"Parsed rows: {parsed_rows}")
        if parsed_rows is None or parsed_rows == "":
           await update.message.reply_text("No data found") 
        else:
            await update.message.reply_text(parsed_rows)
        logging.debug("printall called")

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Command not found, visit /help")


# -------------------------- Conversation Handlers --------------------------- #

# Handler for /start command guided setup
async def start_main_conv(update, context: ContextTypes.DEFAULT_TYPE):
    # Start main conversation
    await update.message.reply_text(const.welcome_msg)
    logging.debug("Start main conversation")
    await update.message.reply_text(const.guided_msg_lang)
    return FIRST_TIME_STATE

async def ask_first_time(update, context: ContextTypes.DEFAULT_TYPE):
    global is_starting_phase
    # Ask the way to use for the first time to the user:
    logger.debug("Ask first time state called")
    msg = update.message.text
    logger.debug(f"First time msg {msg}")
    msg_chunks = msg.split(" ")
    cmd = msg_chunks[0]
    if cmd == "resume":
        ret = await set_sheet(update, context)
        logger.debug(f"Set sheet ret:{ret}")
        if (ret == -1 or ret == -2):
            logger.debug("First time state sheet error")
            return FIRST_TIME_STATE
        else:
            logger.debug("First time state closing conversation")
            return ConversationHandler.END
    elif msg_chunks[1]=="to":
        if await ask_lang(update, context) == EMAIL_STATE:
            is_starting_phase = True
            return EMAIL_STATE
    else:
        logger.debug("Invalid cmd")
        await update.message.reply_text("Invalid command, please try again")
        return FIRST_TIME_STATE


async def ask_lang(update, context: ContextTypes.DEFAULT_TYPE):
    # Ask for language
    logger.debug("Ask lang state called")
    ret = await set_lang(update, context)
    logger.debug(f"Ask lang ret: {ret}")
    if(ret == -1):
        return LANG_STATE
    await update.message.reply_text(const.guided_msg_email)
    return EMAIL_STATE

async def ask_email(update, context: ContextTypes.DEFAULT_TYPE):
    # Ask for google email
    logger.debug("Ask email")
    ret = await set_email(update, context)
    if(ret == -1):
        return EMAIL_STATE
    await update.message.reply_text(const.guided_msg_sheet)  
    return SHEET_STATE

async def ask_sheet(update, context: ContextTypes.DEFAULT_TYPE):
    # Ask for sheet link
    
    ret = await set_sheet(update, context)
    if (ret == END_CONVERSATION or ret == -2):
        if(ret == END_CONVERSATION):
            await update.message.reply_text(const.guided_msg_complete)
        return ConversationHandler.END
    elif(ret == -1):
        return SHEET_STATE
    else:
        return ConversationHandler.END

async def cancel(update, context: ContextTypes.DEFAULT_TYPE):
    # Quit conversation
    await update.message.reply_text(const.guided_msg_exit)
    logging.debug("/cancel called: Guided config ended") #TODO: perchè non viene eseguito?
    return ConversationHandler.END

# ---------------------------------- Main ------------------------------------ #

def main() -> None:
    # Set logging level
    logger.setLevel(logging.DEBUG)

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()
    
    # /start guided setup conversation
    main_conv_handler = ConversationHandler(
        # ENtry point is /start command
        entry_points=[CommandHandler('start', start_main_conv)],
        # States are Lang setup, Email setupn and GSheet setup
        states={
            FIRST_TIME_STATE : [MessageHandler(filters.TEXT & ~filters.Command(['/cancel']), ask_first_time)],
            LANG_STATE : [MessageHandler(filters.TEXT & ~filters.Command(['/cancel']), ask_lang)],
            EMAIL_STATE : [MessageHandler(filters.TEXT & ~filters.Command(['/cancel']), ask_email)],
            SHEET_STATE : [MessageHandler(filters.TEXT & ~filters.Command(['/cancel']), ask_sheet)],
        },
        # /cancel command to exit guided setup
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    application.add_handler(main_conv_handler)

    # Manual commands
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("set_lang", set_lang))
    application.add_handler(CommandHandler("set_email", set_email))
    application.add_handler(CommandHandler("set_sheet", set_sheet))
    application.add_handler(CommandHandler("get_target_lang", get_target_lang))
    application.add_handler(CommandHandler("get_mother_lang", get_mother_lang))
    application.add_handler(CommandHandler("get_sheet", get_sheet))
    application.add_handler(CommandHandler("get_email", get_email))
    application.add_handler(CommandHandler("random", random))
    application.add_handler(CommandHandler("printall", printall))
    # Translate message
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, translate))
    # Unknown command handler, must be added last
    application.add_handler(MessageHandler(filters.COMMAND, unknown))

    # Run the bot
    application.run_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN, webhook_url="https://the-real-lexibot.herokuapp.com/" + TOKEN)

if __name__ == "__main__":
    main()

# TODO: Google sheet must not have duplicates
# TODO: gestire spazi multipli nei comandi -> regex?
# TODO: Aggiungere debug msg alla console con log level appropriati
# TODO: fare in modo che inviando ad esempio il comando /set_lang ecc senza argomenti chieda di inserirli al messaggio seguente -> conv per ogni comando?