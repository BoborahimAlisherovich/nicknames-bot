import random

text_lower = "qwertyuiopasdfghjklzxcvbnm"
text_upper = "QWERTYUIOPASDFGHJKLZXCVBNM"
text_combined = text_lower + text_upper

yozuv = [
   "ợฬєгtץยเ๏թคร๔Ŧɠђןкlzxςv๒ภ๓",
   "ᵠᵂᵉʳᵗᵧᵤᵢᵒᵖᵃˢᵈᶠᵍʰʲᵏˡᶻˣᶜᵛᵇᶰᵐ",
    "Q𝓌ɆℛƬƳ𝓾𝓲o₱𝔸ⓈⒹⒻⒼℌᒎⓚᒪ𝔃𝕏ⒸⓋ฿𝕟𝕄",
    "𝓠𝔀𝓮𝓻𝓽𝔂𝓾𝓲𝓸𝓹𝓪𝓼𝓭𝓯𝓰𝓱𝓳𝓴𝓵𝔃𝔁𝓬𝓿𝓫𝓷𝓶",
    "𝑞𝑤𝑒𝑟𝑡𝑦𝑢𝑖𝑜𝑝𝑎𝑠𝑑𝑓𝑔ℎ𝑗𝑘𝑙𝑧𝑥𝑐𝑣𝑏𝑛𝑚",
    "𝔮𝔴𝔢𝔯𝔱𝛾𝔲𝔦𝔬𝔭𝔞𝔰𝔡𝔣𝔤𝔥𝔧𝔨𝔩𝔷𝔵𝔠𝔳𝔟𝔫𝔪",
     "գᤐᤉᤇէყս𐌠ჿթձ᥉ძӻᤚჩʆҟ꤈ᤁ᥊᥌᥎ճከო",
  "ǫѡєɍϯƴυϊѳⱀѧƽđӻƍђɉҟƖⱬχҁⱱƀƞʍ",
   "ᱧᱦꤕ𐍂ተ𐍅𐌵𐌉ᱛᱞ𐌳Ⴝᱚፑ᱙ዘ𐌋ઝ𑀉ᱮ𐌗ꤍ𐌖ଓ𐌽ᱬ",
   "𝙦𝙬𝙚𝙧𝙩𝙮𝙪𝙞𝙤𝙥𝙖𝙨𝙙𝙛𝙜𝙝𝙟𝙠𝙡𝙯𝙭𝙘𝙫𝙗𝙣𝙢",
  "ǫᴡᴇʀᴛʏᴜɪᴏᴘᴀsᴅғɢʜᴊᴋʟᴢxᴄᴠʙɴᴍ",
   "qᥕᥱrᴛyᥙi᧐ρᥲsɗfgɦjκᥣᤁ᥊ᥴ᥎δᥒⲙ",
  "𝓺𝔀𝓮𝓻𝓽𝔂𝓾𝓲𝓸𝓹𝓪𝓼𝓭𝓯𝓰𝓱𝓳𝓴𝓵𝔃𝔁𝓬𝓿𝓫𝓷𝓶",
   "ǫѡɛɼᎿℽʋⅈσ℘ɑʂⅆƒℊℏⅉƙℓʑℵɕɤᎴɳɱ",
    "ᛟᚠᛊᚱᛠᚴᛘᛨᛜᚹᚣᛢᚦᚫᛩᚻᛇᛕᚳZᚷᛈᛉᛒᚺᛖ",
   "qwᴇrᴛyuiᴏᴩᴀsdfghjᴋlzxᴄvʙnʍ",
    "વਘ૯ʀ੮ⲩυɪ૦ƿɑઽᑯ⨍ɢⲏᴊκʟⲍⲭςνᑲⲛⲙ",
      "qⲱⲉʀⲧⲩυⲓⲟⲣⲁⲋⲇϝⳋⲏⳗⲕⳑⲍⲭⲥⳳⲃⲛⲙ",
       "າ໖౿ཞรຯບ୲ഠ༩คຣລச໑ลຽ๙ℓຂ྾໒୶দກຕ",
       "ꐎꅐꂅꉸꉢꌦꏵꀤꏿꉣꁲꌗꅓꊰꁅꍬꀭꂪ꒒ꏣꉧꊐꏝꃃꊮꂵ",
      "ⵕᏔⵟⴽⵜᖿƲⵊⵔᎮѦⵢⵠƑGⴼɈҞȽƵⵋⵎⴸɃƝᗑ",
      "ϙωεɾʈγμʝσραʂɗϝɠɦʆӄɭʐ𑀌ϲѵϸηϻ",
     "ʠѡϱɼʈƴυɩσραѕ∂ƒɠɧʝƙɭʑχϲνɓɳɱ",
     "ｑｗｅｒｔｙｕｉｏｐａｓｄｆｇｈｊｋｌｚｘｃｖｂｎｍ",
    "ᘯᙡᙓᖇᙢᎽᑌᖗᗝᖘᗣᔕᗪᖴᘜᕼᒍᏦᒐᘔⵋᙅᐯᙖᘉᗰ",
    "🆀🆆🅴🆁🆃🆈🆄🅸🅾🅿🅰🆂🅳🅵🅶🅷🅹🅺🅻🆉🆇🅲🆅🅱🅽🅼",  
     "ɋաɛʀȶʏʊɨօքǟֆɖʄɢɦʝӄʟʐӼƈʋɮռʍ",
    "Ⴓᗯᕮᖇ丅ϤႮᎥѺᎮᗩᔕᕲҒᏀᎻᎫᏦᏞᏃᏃᎭᏉᏰᏁᎷ",
     "𝚚ω𝒆𝓻𝓽ƴ𝑢¡⊙𝖕ⲁ𝚜đꊰġĥⓙҜ𝚕𝘻xc𝚟ᵦח",  
    "𝓠𝓦𝓔𝓡𝓣𝓨𝓤𝓘𝓞𝓟𝓐𝓢𝓓𝓕𝓖𝓗𝓙𝓚𝓛𝓩𝓧𝓒𝓥𝓑𝓝М",  
    "𝕼𝖂𝖊𝖗𝖙𝖞𝖚𝖎𝖔𝖕𝖆𝖘𝖉𝖋𝖌𝖍𝖏𝖐𝖑𝖟𝖝𝖈𝖛𝖇𝖓𝖒",   
    "𝑄𝑊𝐸𝑅𝑇𝒴𝒰𝐼𝒪𝒫𝒜𝒮𝒟𝑭𝑮𝑯𝑱𝒦𝑳𝒵𝒳𝑪𝒱𝒷𝒩𝑴",  
    "𝐐𝐖𝐄𝐑𝐓𝐘𝐔𝐈𝐎𝐏𝐀𝐒𝐃𝐅𝐆𝐇𝐉𝐊𝐋𝐌", 
    "🅀🅆🄴🅁🅃🅈🅄🄸🄾🄿🄰🅂🄳🄵🄶🄷🄹🄺🄻🅉🅇🄲🅅🄱🄽🄼",  
    "ⓠⓦⓔⓡⓣⓨⓤⓘⓞⓟⓐⓢⓓⓕⓖⓗⓙⓚⓛⓩⓧⓒⓥⓑⓝⓜ",  
    "🅠🅦🅔🅡🅣🅨🅤🅘🅞🅟🅐🅢🅓🅕🅖🅗🅙🅚🅛🅩🅧🅒🅥🅑🅝🅜",  
    "𝔮𝔴𝔢𝔯𝔱𝔶𝔲𝔦𝔬𝔭𝔞𝔰𝔡𝔣𝔤𝔥𝔧𝔨𝔩𝔷𝔵𝔠𝔳𝔟𝔫𝔪",  
    "𝕢𝕨𝕖𝕣𝕥𝕪𝕦𝕚𝕠𝕡𝕒𝕤𝕕𝕗𝕘𝕙𝕛𝕜𝕝𝕫𝕩𝕔𝕧𝕓𝕟𝕞",  
    "𝑄𝑊𝐸𝑅𝑇𝑌𝑈𝐼𝐎𝐏𝐀𝐒𝐃𝐅𝐆𝐇𝐉𝐊𝐋𝐙𝐗𝐂𝐕𝐁𝐍М",
     "Ɋᗯᗴᖇ丅ƳᑌᎥᗝᑭᗩᔕᗪᖴǤᕼᒎᛕᒪ乙᙭ᑕᐯᗷᑎᗰ",
     "QŴĔŔŤŶÚĨŐРĂŚĎŦĞĤĴĶĹŹЖČVβŃМ",
    "𝑞𝑤𝑒𝑟𝑡𝑦𝑢𝑖𝑜𝑝𝑎𝑠𝑑𝑓𝑔𝑗𝑘𝑙𝑧𝑥𝑐𝑣𝑏𝑛𝑚", 
    "🅢🅘🅜🅑🅞🅛🅢",   
    'ợฬєгՇץยเ๏קคร๔Ŧﻮђןкɭչאςש๒ภ๓',
    "qʷᵉʳᵗʸᵘⁱᵒᵖᵃˢᵈᶠᵍʰʲᵏˡᶻˣᶜᵛᵇⁿᵐ",
    "qЩΣЯƬyЦiӨpΛƧdfgΉjkᄂzxᄃvbПm",
    "Ɋ山乇尺ㄒㄚㄩ丨ㄖ卩卂丂ᗪ千Ꮆ卄ﾌҜㄥ乙乂匚ᐯ乃几爪", 
    "ꆰꅐꏂꋪ꓄ꌦ꒤꒐ꄲꉣꋬꇙ꒯ꊰꍌꁝ꒻ꀘ꒒ꁴꉧꉔ꒦ꃳꋊꂵ",
    "𝘲𝘸𝘦𝘳𝓽𝔂𝘶𝘪ｵ𝘱𝘢𝘴𝘥𝘧𝘨𝘩𝘫𝗄𝘭𝗓𝘹𝘤𝘷𝘣𝘯𝘮",
    "ҩω૯Ր੮עυɿ૦ƿคςძԲ૭ҺʆқՆઽ૪८౮ცՈɱ",
    "qwₑᵣ𝚝yᵤᵢₒ𝐩ₐ𝘴𝚍fg𝓱ⱼ𝓴ᄂzₓ𝚌ᵥ𝚋𝚗ᗰ",
    "ϙɯҽɾƚყυισραʂԃϝɠԋʝƙʅȥxƈʋႦɳɱ",
    "ｑώⒺℝ𝓣ч𝕌𝕚ᵒƤＡ𝕤Ⓓ𝕗قĦנｋ𝕃𝕫ˣ𝐜𝕧𝔟ภ𝓶",
    "Q₩ɆⱤ₮ɎɄłØ₱₳₴Đ₣₲ⱧJ₭ⱠⱫӾ₵V฿₦₥", 
    "𝔔𝔚𝔈ℜ𝔗𝔜𝔘𝔓𝔄𝔖𝔇𝔉𝔊ℌ𝔍𝔎𝔏ℨ𝔛ℭ𝔙𝔅𝔑𝔐", 
     "𝖰𝗐𝖾𝗋𝗍𝗒𝗎𝗂𝗈𝗉𝖺𝗌𝖽▵𝗀𝗁𝗃𝗄𝗅𝗓𝗑𝖼𝗏𝖻𝗇𝗆",
     "𝐐𝐰𝐞𝐫𝐭𝐲𝐮𝐢𝐨𝐩𝐚𝐬𝐝𝐟𝐠𝐡𝐣𝐤𝐥𝐳𝐱𝐜𝐯𝐛𝐧𝐦",
     "ᑫᗯEᖇTYᑌIOᑭᗩᔕᗪᖴGᕼᒍKᒪᘔ᙭ᑕᐯᗷᑎᗰ",
     "𝔔𝔴𝔢𝔯𝔱𝔶𝔲𝔦𝔬𝔭𝔞𝔰𝔡𝔣𝔤𝔥𝔧𝔨𝔩𝔷𝔵𝔠𝔳𝔟𝔫𝔪",
     "𝕼𝖜𝖊𝖗𝖙𝖞𝖚𝖎𝖔𝖕𝖆𝖘𝖉𝖋𝖌𝖍𝖏𝖐𝖑𝖟𝖝𝖈𝖛𝖇𝖓𝖒",
     "𝓺𝔀𝓮𝓻𝓽𝔂𝓾𝓲𝓸𝓹𝓪𝓼𝓭𝓯𝓰𝓱𝓳𝓴𝓵𝓏𝓍𝓬𝓿𝓫𝓷𝓂",
     "𝗤𝗪𝗘𝗥𝗧𝗬𝗨𝗜𝗢𝗣𝗔𝗦𝗗𝗙𝗚𝗛𝗝𝗞𝗟𝗭𝗫𝗖𝗩𝗕𝗡𝗠",
    "ꁸꅐꍟ꒓꓅ꐟꐇꂑꆂꉣꋫꌚꁕꄘꁍꑛꀭꀗ꒒ꁴꇓꏸꏝꃃꁹꁒ",
    "ꆰꅏꍟꋪ꓄ꌩꀎꀤꂦꉣꍏꌗꀸꎇꁅꃅꀭꀘ꒒ꁴꊼꉓꃴꌃꈤꂵ",
    "ゐW乇尺ｲﾘひﾉのｱﾑ丂りｷムんﾌズﾚ乙ﾒᄃ√乃刀ﾶ",
     "ᎤᏇᏋᏒᏖᎩᏬᎥᎧᎮᏗᏕᎴᎦᎶᏂᏠᏦᏝፚጀፈᏉᏰᏁᎷ",
     "ҨƜƐ尺ŤϤЦɪØþΛらÐFƓнﾌҚŁẔχㄈƔϦЛ௱",
     "გwპΓནყυἶõρმჰძfცhქκlɀჯეὗჩῆო",
     "𝒒᭙𝒆𝗿†ᥡᶶ¡őᵽ𝕒ṧÐϝ𝑔𝐡ɉ𝐤ₗᴢxc𝔳𝔟𝚗m",
     "qwêr†¥µïðþå§Ð£ghjklzx¢vßñm",
     "q𝔀ⓔᖇ𝕥ｙⓊᎥσｐ𝓪ร∂ᶠᎶђＪⓀ𝓵žx𝒸ⓥ𝕓ⓝⓂ",  
]

def add_stylized_effects(name):
    # Potential for adding emojis or extra chars if needed, currently just base
    return name

def nick_generator(name, son=None):
    result = []
    
    # Process the name to be translated robustly
    if son:
        if 0 < son <= len(yozuv):
            fon = yozuv[son - 1]
            # Mapping for both cases if font is 26 chars
            if len(fon) == 26:
                trans = str.maketrans(text_lower + text_upper, fon + fon)
            else:
                l = min(len(text_combined), len(fon))
                trans = str.maketrans(text_combined[:l], fon[:l])
            return name.translate(trans)
        return name
    else:
        for fon in yozuv:
            if len(fon) == 26:
                trans = str.maketrans(text_lower + text_upper, fon + fon)
            else:
                l = min(len(text_combined), len(fon))
                trans = str.maketrans(text_combined[:l], fon[:l])
            
            stylized = name.translate(trans)
            result.append(f" {stylized}")
        return result

def transform_text(input_text, styles=None):
    if styles is None:
        styles = yozuv
    selected = random.choice(styles)
    if len(selected) == 26:
        trans = str.maketrans(text_lower + text_upper, selected + selected)
    else:
        l = min(len(text_combined), len(selected))
        trans = str.maketrans(text_combined[:l], selected[:l])
    return input_text.translate(trans)
