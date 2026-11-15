"""Lokal nik dvigateli: shriftlar, bezaklar va aralash dizaynlar (API'siz, bir zumda)."""
import random
import string
import unicodedata

UP, LO = string.ascii_uppercase, string.ascii_lowercase


def _math(prefix: str, digits: str | None = None) -> dict:
    """Unicode matematik alifbosidan harf xaritasi (bo'shliqlar letterlike belgilar bilan)."""
    m = {}
    for case, letters in (("CAPITAL", UP), ("SMALL", LO)):
        for ch in letters:
            for name in (f"{prefix} {case} {ch.upper()}",
                         f"{prefix.replace('MATHEMATICAL ', '').replace('FRAKTUR', 'BLACK-LETTER')} {case} {ch.upper()}",
                         f"{prefix.replace('MATHEMATICAL ', '')} {case} {ch.upper()}"):
                try:
                    m[ch] = unicodedata.lookup(name)
                    break
                except KeyError:
                    pass
    if prefix == "MATHEMATICAL ITALIC":
        m["h"] = "ℎ"
    if digits:
        for i, d in enumerate("0123456789"):
            try:
                m[d] = unicodedata.lookup(f"{digits} DIGIT {unicodedata.name(d).split()[-1]}")
            except KeyError:
                pass
    return m


def _named(fmt_up: str, fmt_lo: str | None = None) -> dict:
    m = {}
    for ch in UP + LO:
        fmt = fmt_up if ch.isupper() or not fmt_lo else fmt_lo
        try:
            m[ch] = unicodedata.lookup(fmt.format(ch.upper()))
        except KeyError:
            pass
    return m


def _zip(chars: str) -> dict:
    m = dict(zip(LO, chars))
    m.update({u: c for u, c in zip(UP, chars)})
    return m


FONTS: list[tuple[str, dict]] = [
    ("Bold", _math("MATHEMATICAL BOLD", "MATHEMATICAL BOLD")),
    ("Italic", _math("MATHEMATICAL ITALIC")),
    ("Bold Italic", _math("MATHEMATICAL BOLD ITALIC")),
    ("Script", _math("MATHEMATICAL SCRIPT")),
    ("Bold Script", _math("MATHEMATICAL BOLD SCRIPT")),
    ("Fraktur", _math("MATHEMATICAL FRAKTUR")),
    ("Bold Fraktur", _math("MATHEMATICAL BOLD FRAKTUR")),
    ("Double", _math("MATHEMATICAL DOUBLE-STRUCK", "MATHEMATICAL DOUBLE-STRUCK")),
    ("Sans", _math("MATHEMATICAL SANS-SERIF", "MATHEMATICAL SANS-SERIF")),
    ("Sans Bold", _math("MATHEMATICAL SANS-SERIF BOLD", "MATHEMATICAL SANS-SERIF BOLD")),
    ("Sans Italic", _math("MATHEMATICAL SANS-SERIF ITALIC")),
    ("Sans Bold Italic", _math("MATHEMATICAL SANS-SERIF BOLD ITALIC")),
    ("Mono", _math("MATHEMATICAL MONOSPACE", "MATHEMATICAL MONOSPACE")),
    ("Circled", _named("CIRCLED LATIN CAPITAL LETTER {}", "CIRCLED LATIN SMALL LETTER {}")),
    ("Black Circle", _named("NEGATIVE CIRCLED LATIN CAPITAL LETTER {}")),
    ("Squared", _named("SQUARED LATIN CAPITAL LETTER {}")),
    ("Black Square", _named("NEGATIVE SQUARED LATIN CAPITAL LETTER {}")),
    ("Bracket", _named("PARENTHESIZED LATIN SMALL LETTER {}", "PARENTHESIZED LATIN SMALL LETTER {}")),
    ("Wide", _named("FULLWIDTH LATIN CAPITAL LETTER {}", "FULLWIDTH LATIN SMALL LETTER {}")),
    ("Small Caps", _zip("ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢ")),
    ("Mini", _zip("ᵃᵇᶜᵈᵉᶠᵍʰⁱʲᵏˡᵐⁿᵒᵖᑫʳˢᵗᵘᵛʷˣʸᶻ")),
    ("Asia", _zip("卂乃匚ᗪ乇千Ꮆ卄丨ﾌҜㄥ爪几ㄖ卩Ɋ尺丂ㄒㄩᐯ山乂ㄚ乙")),
    ("Cyber", _zip("ΛBᄃDΣFGΉIJKᄂMПӨPQЯƧƬЦVЩXYZ")),
    ("Magic", _zip("ꍏꌃꏳꀷꏂꎇꁅꀍꀤ꒻ꀘ꒒ꎭꈤꂦᖘꆰꋪꌚ꓄ꀎ꒦ꅐꉧꌩꁴ")),
    ("Lux", _zip("ąცƈɖɛʄɠɧıʝƙƖɱŋơ℘զཞʂɬų۷ῳҳყʑ")),
]
COMBINING = [("Chizilgan", "̶"), ("Tagchiziq", "̲"), ("Qiya", "̸"), ("Nuqtali", "̤")]
FLIP = dict(zip(LO + UP, "ɐqɔpǝɟƃɥᴉɾʞlɯuodbɹsʇnʌʍxʎz" + "∀ᗺƆᗡƎℲ⅁HIſꓘ˥WNOԀῸᴚS⊥∩ΛMX⅄Z"))

FRAMES = [
    "꧁{}꧂", "꧁༒☬{}☬༒꧂", "༺{}༻", "☬{}☬", "『{}』", "【{}】", "〖{}〗", "《{}》", "⟦{}⟧",
    "★彡{}彡★", "♛{}♛", "亗{}亗", "乂{}乂", "✿{}✿", "❦{}❦", "⚡{}⚡", "♡ {} ♡", "𓆩{}𓆪",
    "𖣘 {} 𖣘", "⫷{}⫸", "↬{}↫", "◥꧁ད{}ཌ꧂◤", "▄︻デ{}══━一", "︻╦╤─ {} ─╤╦︻", "☠{}☠",
    "꧁☆{}☆꧂", "-ˋˏ {} ˎˊ-", "⋆｡°✩ {} ✩°｡⋆", "✧･ﾟ {} ﾟ･✧", "•´¯`•. {} .•´¯`•", "ღ{}ღ",
    "ılı.lıllılı {} ılı.lıllılı", "×͜× {}", "{}ツ", "{}™", "{}亗", "ᴹᴿ᭄{}", "ᴮᴼˢˢ {}",
    "ˢᵃᵐᵘʳᵃⁱ {}", "{}࿐", "Ꭵ'ᗰ {}", "⚔{}⚔", "♚{}♚", "☾{}☽", "꧁𓊈𒆜{}𒆜𓊉꧂",
]


def apply(name: str, mapping: dict) -> str:
    return "".join(mapping.get(ch, ch) for ch in name)


def fonts(name: str) -> list[tuple[str, str]]:
    out = [(label, apply(name, m)) for label, m in FONTS]
    out += [(label, "".join(ch + mark if ch != " " else ch for ch in name)) for label, mark in COMBINING]
    out.append(("Teskari", "".join(FLIP.get(ch, ch) for ch in reversed(name))))
    return out


def frames(name: str) -> list[tuple[str, str]]:
    return [("", f.format(name)) for f in FRAMES]


def mix(name: str, seed: str, n: int = 30) -> list[tuple[str, str]]:
    """Shrift + bezak aralashmasi: har safar yangi kombinatsiyalar."""
    rnd = random.Random(seed)
    styled = fonts(name)
    out, seen = [], set()
    while len(out) < n and len(seen) < 2000:
        label, s = rnd.choice(styled)
        nick = rnd.choice(FRAMES).format(s)
        if nick not in seen:
            seen.add(nick)
            out.append((label, nick))
    return out


SECTIONS = {
    "font": ("🔤 Shriftlar", "Har xil shriftlarda"),
    "frame": ("✨ Bezakli", "Chiroyli ramka va belgilar bilan"),
    "mix": ("👑 Premium dizayn · 10 ⭐", "Shrift + bezak kombinatsiyasi, har safar yangi"),
}


def build(kind: str, name: str, seed: str = "0") -> list[tuple[str, str]]:
    if kind == "font":
        return fonts(name)
    if kind == "frame":
        return frames(name)
    return mix(name, f"{name}:{seed}")
