import random

PREMIUM_FONTS = {
    "gothic": ["𝔔𝔴𝔢𝔯𝔱𝔶𝔲𝔦𝔬𝔭𝔞𝔰𝔡𝔣𝔤𝔥𝔧𝔨𝔩𝔷𝔵𝔠𝔳𝔟𝔫𝔪", "𝕼𝖜𝖊𝖗𝖙𝖞𝖚𝖎𝖔𝖕𝖆𝖘𝖉𝖋𝖌𝖍𝖏𝖐𝖑𝖟𝖝𝖈𝖛𝖇𝖓𝖒"],
    "cursive": ["𝓆𝓌𝑒𝓇𝓉𝓎𝓊𝒾𝑜𝓅𝒶𝓈𝒹𝒻𝑔𝒽𝒿𝓀𝓁𝓏𝓍𝒸𝓋𝒷𝓃𝓂", "𝓺𝔀𝓮𝓻𝓽𝔂𝓾𝓲𝓸𝓹𝓪𝓼𝓭𝓯𝓰𝓱𝓳𝓴𝓵𝔃𝔁𝓬𝓿𝓫𝓷𝓶"],
    "bold": ["𝐐𝐰𝐞𝐫𝐭𝐲𝐮𝐢𝐨𝐩𝐚𝐬𝐝𝐟𝐠𝐡𝐣𝐤𝐥𝐳𝐱𝐜𝐯𝐛𝐧𝐦", "𝗤𝗪𝗘𝗥𝗧𝗬𝗨𝗜𝗢𝗣𝗔𝗦𝗗𝗙𝗚𝗛𝗝𝗞𝗟𝗭𝗫𝗖𝗩𝗕𝗡𝗠"],
    "italic": ["𝑄𝑤𝑒𝑟𝑡𝑦𝑢𝑖𝑜𝑝𝑎𝑠𝑑𝑓𝑔ℎ𝑗𝑘𝑙𝑧𝑥𝑐𝑣𝑏𝑛𝑚", "𝑞𝑤𝑒𝑟𝑡𝑦𝑢𝑖𝑜𝑝𝑎𝑠𝑑𝑓𝑔ℎ𝑗𝑘𝑙𝑧𝑥𝑐𝑣𝑏𝑛𝑚"],
    "script": ["𝓠𝔀𝓮𝓻𝓽𝔂𝓾𝓲𝓸𝓹𝓪𝓼𝓭𝓯𝓰𝓱𝓳𝓴𝓵𝔃𝔁𝓬𝓿𝓫𝓷𝓶", "𝓆𝓌𝑒𝓇𝓉𝓎𝓊𝒾𝑜𝓅𝒶𝓈𝒹𝒻𝑔𝒽𝒿𝓀𝓁𝓏𝓍𝒸𝓋𝒷𝓃𝓂"],
    "double": ["𝕢𝕨𝕖𝕣𝕥𝕪𝕦𝕚𝕠𝕡𝕒𝕤𝕕𝕗𝕘𝕙𝕛𝕜𝕝𝕫𝕩𝕔𝕧𝕓𝕟𝕞", "𝕼𝖜𝖊𝖗𝖙𝖞𝖚𝖎𝖔𝖕𝖆𝖘𝖉𝖋𝖌𝖍𝖏𝖐𝖑𝖟𝖝𝖈𝖛𝖇𝖓𝖒"],
    "mono": ["𝚚𝚠𝚎𝚛𝚝𝚢𝚞𝚒𝚘𝚙𝚊𝚜𝚍𝚏𝚐𝚑𝚓𝚔𝚕𝚣𝚡𝚌𝚟𝚋𝚗𝚖", "𝚀𝚆𝙴𝚁𝚃𝚈𝚄𝙸𝙾𝙿𝙰𝚂𝙳𝙵𝙶𝙷𝙹𝙺𝙻𝚉𝚇𝙲𝚅𝙱𝙽𝙼"],
    "circled": ["ⓠⓦⓔⓡⓣⓨⓤⓘⓞⓟⓐⓢⓓⓕⓖⓗⓙⓚⓛⓩⓧⓒⓥⓑⓝⓜ", "🅠🅦🅔🅡🅣🅨🅤🅘🅞🅟🅐🅢🅓🅕🅖🅗🅙🅚🅛🅩🅧🅒🅥🅑🅝🅜"],
    "flipped": ["ʎxʍʌɔzןʞɾɥɓɟpɐsoʎʇɹǝʍɐ", "⨁⨂⨃⨄⨅⨆⨇⨈⨉⨊⨋⨌⨍⨎⨏⨐⨑⨒⨓⨔⨕⨖⨗⨘⨙⨚"],
    "asian": ["ัเςย๔єк๒รՇאקןאנгק๏гՇאנ", "קєгŦєςՇ гєשєгรє"],
}

FONT_CATEGORIES = list(PREMIUM_FONTS.keys())

text_lower = "qwertyuiopasdfghjklzxcvbnm"
text_upper = "QWERTYUIOPASDFGHJKLZXCVBNM"
text_combined = text_lower + text_upper


def get_all_font_categories():
    return FONT_CATEGORIES


def get_font_by_category(text, category, count=5):
    if category not in PREMIUM_FONTS:
        return []
    results = []
    fonts = PREMIUM_FONTS[category]
    for font in fonts:
        if len(text) > 30:
            continue
        if len(font) == 26:
            trans = str.maketrans(text_lower + text_upper, font + font)
        else:
            l = min(len(text_combined), len(font))
            trans = str.maketrans(text_combined[:l], font[:l])
        results.append(text.translate(trans))
    if count and len(results) > count:
        results = results[:count]
    return results


def get_premium_font_styles(text, count=10):
    results = []
    for category, fonts in PREMIUM_FONTS.items():
        for font in fonts[:2]:
            if len(text) > 30:
                continue
            if len(font) == 26:
                trans = str.maketrans(text_lower + text_upper, font + font)
            else:
                l = min(len(text_combined), len(font))
                trans = str.maketrans(text_combined[:l], font[:l])
            results.append(text.translate(trans))
    if count and len(results) > count:
        results = results[:count]
    random.shuffle(results)
    return results


def transform_text_to_font(text, style):
    for category, fonts in PREMIUM_FONTS.items():
        for font in fonts:
            if len(font) == 26:
                trans = str.maketrans(text_lower + text_upper, font + font)
            else:
                l = min(len(text_combined), len(font))
                trans = str.maketrans(text_combined[:l], font[:l])
            result = text.translate(trans)
            if result != text:
                return result
    return text
