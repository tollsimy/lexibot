# -------------------------- Imports and basic stuff ------------------------- #
import logging
import constants as const
from telegram import __version__ as TG_VER
import sys 
import os
sys.path.append(os.getcwd() + os.path.abspath("/scripts-and-automations/reverso-script"))
from reverso_wrapped_api import *
from gsheets_wrapped_api import *

TOKEN = None
with open("keys/lexibot_token.txt") as f:
    TOKEN = f.read().strip()

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

sheet_link = None
sheet_name = None
target_lang = None
mother_lang = None
reverso = None
gsheet = None

# Conversation FSM states
LANG_STATE = 0
SHEET_STATE = 1

# ----------------------------- Command Handlers ----------------------------- #

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

    msg = update.message.text.lower()

    try:
        if("/set_lang" in update.message.text):
            arg1 = msg.split("/set_lang ")[1]
        else:
            arg1 = msg.lower()
        arg1 = arg1.split(" ")[0]
        arg2 = msg.lower().split(" to ")[1]
        logger.debug("Languages set to " + arg1 + " to " + arg2)
    except:
        # If we are here from the command handler, message is this one
        if("/set_lang" in update.message.text):
            await update.message.reply_text("Invalid command, use /set_lang [language_to_learn] to [mothertongue]")
        # If we are here from the conversation handler, message is different
        else:
            await update.message.reply_text("Invalid format, use [language_to_learn] to [mothertongue]")
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

async def set_sheet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    #Set sheet link
    global sheet_link
    global sheet_name
    global gsheet

    try:
        if("/set_sheet" in update.message.text):
            sheet_link = update.message.text.split("/set_sheet ")[1]
        else:
            sheet_link = update.message.text
        logger.debug("Sheet set to " + sheet_link)
    except:
        # If we are here from the command handler, message is this one
        if("/set_sheet" in update.message.text):
            await update.message.reply_text("Invalid command, use /set_sheet [link]")
        # If we are here from the conversation handler, message is different
        else:
            await update.message.reply_text("Link not valid, retry")
        logger.debug("/set_sheet: Invalid command")
        return -1

    # Start gsheet
    try:
        gsheet = Gsheet_Api("keys/lexibot_gservice_account.json")
        logger.debug("Gsheet service account authorized correctly")
    except:
        logger.exception("Error while connecting to google service account")
        return -1

    #TODO
    if 1:
        sheet_name = "LexiBot - learn new vocabularies"
        sheet_link = gsheet.create_sheet(sheet_name)
        sheet_link = gsheet.create_sheet(sheet_name)
        sheet_link.share('yourmail@gmail.com',
                         perm_type='user', role='writer')
        logger.debug(sheet_link)
        logger.debug("Sheet created correctly")
    else:
        #TODO
        pass

    # if gsheet.is_a_g_sheet(title, sheet) :
    #     logger.debug("Sheet link is valid")
    #     sheet=arg
    #     await update.message.reply_text("Sheet link set to: " + sheet + "RETRIEVE NAME OF THE SHEET")
    # else:
    #     logger.debug("Sheet link not valid")
    #     await update.message.reply_text("This is not a link to a google sheet document, please try again")
    #     return -1

    return 0

async def translate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    #Reply with the translated the user message
    if(target_lang is None or mother_lang is None):
        await update.message.reply_text("Please set language with /set_lang")
        logger.debug("Language not set")
        return -1
    elif (sheet_link is None):
        await update.message.reply_text("Please set google sheet link with /set_sheet")
        logger.debug("Sheet link not set")
        return -1
    
    trad = reverso.get_separated_translations(update.message.text)
    logger.debug("Translation done")
    gsheet.write_on_sheet("title", sheet_name, update.message.text, trad)
    logger.debug("Written on sheet")
    await update.message.reply_text("Done! Translation: " + trad)
    return 0

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Command not found, visit /help")

# -------------------------- Conversation Handlers --------------------------- #

async def start_main_conv(update, context: ContextTypes.DEFAULT_TYPE):
    # Start main conversation
    await update.message.reply_text("""
Hi, I'm LexiBot, I can help you to learn vocabulary in a foreign language.
The intended use of the LexiBot is to translate a new words whenever you encounter one and then store them all in a google sheet along with the original words in order to study and memorize them in a clever way.
Send /cancel to stop conversation and manually set LexiBot.
""")
    logging.debug("Start main conversation")
    await update.message.reply_text("""
First of all, you need to tell me which language you want to learn and which is your mothertongue.
Format: [language_to_learn] to [mothertongue] (e.g. italian to english)
""")
    return LANG_STATE

async def ask_lang(update, context: ContextTypes.DEFAULT_TYPE):
    # Ask for language
    ret = await set_lang(update, context)
    if(ret == -1):
        return LANG_STATE
    await update.message.reply_text("Wonderful! Now send me the link to your google sheet document (e.g. https://docs.google.com/spreadsheets/d/blablabla)")  
    return SHEET_STATE

async def ask_sheet(update, context: ContextTypes.DEFAULT_TYPE):
    # Ask for sheet link
    ret = await set_sheet(update, context)
    if(ret == -1):
        return SHEET_STATE
    await update.message.reply_text("Great! Now you can start to translate words, just send me a message and I'll reply with the translation while writing it on your sheet to keep track of it.")
    return ConversationHandler.END

async def get_target_lang(update, context: ContextTypes.DEFAULT_TYPE):
    if(mother_lang is not None):
        await update.message.reply_text("Mother tonge language set to: " + mother_lang)
        logging.debug("get_target_lang called: " + mother_lang)
    else:
        await update.message.reply_text("Mother tonge language not set")
        logging.debug("get_target_lang called: mother tongue not set")
    return ConversationHandler.END

async def get_mother_lang(update, context: ContextTypes.DEFAULT_TYPE):
    if(target_lang is not None):
        await update.message.reply_text("Target language set to: " + target_lang)
        logging.debug("get_mother_lang called: " + target_lang)
    else: 
        await update.message.reply_text("Target language not set")
        logging.debug("get_mother_lang called: target language not set")
    return ConversationHandler.END

async def get_sheet(update, context: ContextTypes.DEFAULT_TYPE):
    if(sheet_link is not None):
        await update.message.reply_text("Sheet link set to: " + sheet_link)
        logging.debug("get_sheet called: " + sheet_link)
    else:
        await update.message.reply_text("Sheet link not set")
        logging.debug("get_sheet called: sheet link not set")
    return ConversationHandler.END

async def cancel(update, context: ContextTypes.DEFAULT_TYPE):
    # Quit conversation
    await update.message.reply_text('Guided config ended, you can now use /set_lang and /set_sheet to manually set LexiBot')
    logging.debug("/cancel called: Guided config ended") #TODO: perchè non viene eseguito?
    return ConversationHandler.END

# ---------------------------------- Main ------------------------------------ #

def main() -> None:
    # Set logging level
    logger.setLevel(logging.DEBUG)

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()
    
    #Main conversation handler
    main_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start_main_conv)],

        states={
            LANG_STATE : [MessageHandler(filters.TEXT & ~filters.Command(['/cancel']), ask_lang)],
            SHEET_STATE : [MessageHandler(filters.TEXT & ~filters.Command(['/cancel']), ask_sheet)],
        },

        fallbacks=[CommandHandler("cancel", cancel)]
    )
    application.add_handler(main_conv_handler)

    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("set_lang", set_lang))
    application.add_handler(CommandHandler("set_sheet", set_sheet))
    application.add_handler(CommandHandler("get_target_lang", get_target_lang))
    application.add_handler(CommandHandler("get_mother_lang", get_mother_lang))
    application.add_handler(CommandHandler("get_sheet", get_sheet))
    # translate message
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, translate))
    # unknown command handler, must be added last
    application.add_handler(MessageHandler(filters.COMMAND, unknown))

    # Run the bot
    application.run_polling()

if __name__ == "__main__":
    main()


# TODO: fare comando che restituisce tutti i record della sheet e un comando che restituisce parola randomica da studiare
# TODO: togliere il token prima di committare