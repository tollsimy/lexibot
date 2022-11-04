import os

lang_dict={
    "english" : "en", 
    "italian" : "it",
    "spanish" : "es",
    "french" : "fr",
    "german" : "de",
    "portuguese" : "pt",
    "russian" : "ru",
    "japanese" : "ja",
    "arabic" : "ar",
    "dutch" : "nl",
    "polish" : "pl",
    "romanian" : "ro",
    "turkish" : "tr",
    "swedish" : "sv",
    "finnish" : "fi",
    "danish" : "da",
    "norwegian" : "no",
    "hungarian" : "hu",
    "czech" : "cs",
    "greek" : "el",
    "bulgarian" : "bg",
    "slovak" : "sk",
    "slovenian" : "sl",
    "albanian" : "sq",
    "serbian" : "sr",
    "bosnian" : "bs",
    "croatian" : "hr",
    "macedonian" : "mk",
    "bulgarian" : "bg",
    "estonian" : "et",
    "latvian" : "lv",
    "lithuanian" : "lt",
    "afrikaans" : "af",
    "icelandic" : "is",
    "maori" : "mi",
    "maltese" : "mt",
    "welsh" : "cy",
    "basque" : "eu",
    "galician" : "gl",
    "indonesian" : "id",
    "thai" : "th",
    "korean" : "ko",
    "vietnamese" : "vi",
    "hebrew" : "he",
    "urdu" : "ur",
    "hindi" : "hi",
    "punjabi" : "pa",
    "bengali" : "bn",
    "tamil" : "ta",
    "telugu" : "te",
    "marathi" : "mr",
    "gujarati" : "gu",
    "kannada" : "kn",
    "malayalam" : "ml",
    "assamese" : "as",
    #TODO: missing chinese
    #TODO: don't know if they are all supported by reverso
}

scripts_path = os.getcwd() + os.path.abspath("/scripts-and-automations/reverso-script/api/")

help_msg = """
Welcome, the LexiBox help message is here to guide you!
Send /start - start and configure the bot.
Send /help - get this message.
Send /set_lang [language_to_learn] to [mothertongue] - set the language (e.g. /set_lang it to en).
Send /set_sheet [link] - set the google sheet link (e.g. /set_sheet https://docs.google.com/spreadsheets/d/example).
Send /set_email [your_email@gmail.com] - set the google email address to whom the sheet will be shared.
After setting the language and the sheet, send whatever you want to translate to the bot and it will append the translation to the sheet.
The intended use of the LexiBot is to translate a new words whenever you encounter one and then store them all in a google sheet along with the original words in order to study and memorize them in a clever way.
"""

welcome_msg = """
Hi, I'm LexiBot, I can help you to learn vocabulary in a foreign language.
The intended use of the LexiBot is to translate a new words whenever you encounter one and then store them all in a google sheet along with the original words in order to study and memorize them in a clever way.
Send /cancel to stop conversation and manually set LexiBot.\n
If you are not new to Lexibot you can restore your worksheet typing 'resume [url]', remember that the sheet must be
shared with everyone who has the link!
"""
guided_msg_lang = """
First of all, you need to tell me which language you want to learn and which is your mothertongue.
Format: [language_to_learn] to [mothertongue] (e.g. italian to english)
"""
guided_msg_email = "Wonderful! Now send me your google email address to share with you the sheet that will store your words (e.g. namesurname@gmail.com)"
guided_msg_sheet = "Last step! Now send me the `create [sheet_name]` or `resume [sheet_id]` to respectively create a new google sheet or resume an existing one."
guided_msg_complete = "Great! Now you can start to translate words, just send me a message and I'll reply with the translation while writing it on your sheet to keep track of it."
guided_msg_exit = "Guided config ended, you can now use /set_lang and /set_sheet and /set_email to manually set LexiBot"
