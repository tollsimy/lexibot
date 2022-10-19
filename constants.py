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
