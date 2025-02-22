# 1. Always check the results of the procedure
# 2. Always run "npx prettier -w lnbits/static/i18n/XX.js" to reformat the result

import os
import re
import sys

import json5
from openai import OpenAI

if len(sys.argv) < 2:
    print("Usage: python3 tools/i18n-tool.py <code> [language]")
    sys.exit(1)
lang = sys.argv[1]


def load_language(lang):
    s = open(f"lnbits/static/i18n/{lang}.js", "rt").read()
    prefix = "window.localisation.%s = {\n" % lang
    assert s.startswith(prefix)
    s = s[len(prefix) - 2 :]
    return json5.loads(s)


def save_language(lang, data):
    with open(f"lnbits/static/i18n/{lang}.js", "wt") as f:
        f.write("window.localisation.%s = {\n" % lang)
        row = 0
        for k, v in data.items():
            row += 1
            f.write("  %s:\n" % k)
            if "'" in v:
                f.write('    "%s"' % v)
            else:
                f.write("    '%s'" % v)
            if row == len(data):
                f.write("\n")
            else:
                f.write(",\n")
        f.write("}\n")


def string_variables_match(str1, str2):
    pat = re.compile(r"%\{[a-z0-9_]*\}")
    m1 = re.findall(pat, str1)
    m2 = re.findall(pat, str2)
    return sorted(m1) == sorted(m2)


def translate_string(lang_from, lang_to, text):
    target = {
        "de": "German",
        "es": "Spanish",
        "jp": "Japan",
        "cn": "Chinese",
        "fr": "French",
        "it": "Italian",
        "pi": "Pirate",
        "nl": "Dutch",
        "we": "Welsh",
        "pl": "Polish",
        "pt": "Portuguese",
        "br": "Brazilian Portugese",
        "cs": "Czech",
        "sk": "Slovak",
        "kr": "Korean",
    }[lang_to]
    assert os.getenv("OPENAI_API_KEY"), "OPENAI_API_KEY env var not set"
    client = OpenAI()
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a language expert that speaks all languages in the world. You are about to translate text from English to another language. The text is a part of the software you are translating. If the given text contains a phrase enclosed by curly preceded with a percent sign, do not translate the given phrase, just keep it verbatim. So for example, the phrase %{amount} translated to target language should still be kept as %{amount}. Never output anything else, just the translated string.",  # noqa: E501
                },
                {
                    "role": "user",
                    "content": f"Translate the following string from English to {target}: {text}",  # noqa: E501
                },
            ],
            model="gpt-4-1106-preview",  # aka GPT-4 Turbo
        )
        translated = chat_completion.choices[0].message.content.strip()
        # return translated string only if variables were not broken
        if string_variables_match(text, translated):
            return translated
        else:
            return None
    except Exception:
        return None


data_en = load_language("en")
data = load_language(lang)

missing = set(data_en.keys()) - set(data.keys())
print(f"Missing {len(missing)} keys in language '{lang}'")

if len(missing) > 0:
    new = {}
    for k in data_en:
        if k in data:
            new[k] = data[k]
        else:
            print(f"Translating key '{k}'")
            print(f"{data_en[k]}")
            translated = translate_string("en", lang, data_en[k])
            print("->")
            if translated:
                print(f"{translated}")
                new[k] = translated
            else:
                print("ERROR")
            print()
    save_language(lang, new)
else:
    # check whether variables match for each string
    for k in data_en:
        if not string_variables_match(data_en[k], data[k]):
            print(f"Variables mismatch ({k}):")
            print(data_en[k])
            print(data[k])
