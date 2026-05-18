# -*- coding: utf-8 -*-
"""
Re-runnable patcher: adds a `forms_detail` array to every multi-form note in
app/static.json so the flashcard UI can show a plain-English gloss above each
inflected Latin form (instead of repeating the dictionary meaning, which is
misleading for declined nouns / conjugated verbs).

GLOSSES maps note id -> list of plain-English glosses, in the SAME ORDER the
forms appear in that note's forms_summary string. The script splits
forms_summary, zips it with the gloss list, and writes:

    note["forms_detail"] = [{"f": form, "n": count, "g": gloss}, ...]

Single-form notes are left untouched (their one form IS the dictionary form,
so the existing base-English label is already correct).

Run:  python tools/gen_forms_detail.py
Idempotent. Re-run after editing GLOSSES to refresh static.json.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(HERE, "..", "app", "static.json")

# note id -> glosses, ordered to match forms_summary order.
GLOSSES = {
    86:  ["your", "your", "your", "your / yours", "your", "your", "your", "of yours", "your", "your", "of yours"],
    87:  ["O Lord", "the Lord", "the Lord (object)"],
    88:  ["who", "which / that", "who / which", "whom", "whose", "to whom / by which", "whom"],
    89:  ["God", "of God", "to / for God"],
    90:  ["you (object)", "to you", "you", "you (plural)"],
    91:  ["holy / the holy", "to / with the holy", "holy", "of the holy / the saints", "holy (object)",
          "to / for the holy", "holy", "O holy", "the holy (object)", "of the holy", "holy", "holy"],
    92:  ["my", "my", "my", "my", "my", "my", "my", "of my"],
    93:  ["is", "are", "were", "to be", "were / would be", "let it be"],
    94:  ["our / of us", "our", "our", "our", "our", "our", "our", "of our", "our", "our"],
    96:  ["all", "to / for all", "of all", "to / with every", "all / every", "all / every"],
    97:  ["to / for us", "us"],
    98:  ["me", "I", "of me"],
    99:  ["his / of him", "him", "to them", "them", "of them", "to him", "she / they"],
    104: ["spirit / of the spirit", "by / with the spirit", "the spirit (object)", "to the spirit"],
    106: ["this / these", "this", "this", "of this", "by this", "this (object)", "to / by these"],
    107: ["father", "of the father", "to the father", "by / with the father", "the father (object)"],
    109: ["you are", "I am", "let it be / is", "was", "will be", "you (plural) are", "was / has been", "will have been"],
    110: ["ages", "of the ages", "age"],
    111: ["Christ (object)", "O Christ", "to / with Christ"],
    112: ["his own", "his own", "his own", "his own", "his own", "his own", "his own", "his own", "to himself"],
    113: ["by that", "to those", "to that / those", "those", "that one", "that"],
    114: ["to / for you", "with you"],
    117: ["of the master / masters", "to / with the master"],
    118: ["sons / of the son", "son", "to / with the son", "O son", "of the sons"],
    119: ["earth / by the earth", "of / to the earth", "of the lands", "the earth (object)", "in / with the lands"],
    121: ["almighty", "to the almighty", "almighty (object)"],
    122: ["glory", "glory (object)", "of / to glory"],
    123: ["hand / hands", "to / with the hands", "the hand (object)", "to / with the hands"],
    124: ["blessed / of the blessed", "to the blessed", "blessed (object)", "blessed (object)", "blessed"],
    126: ["Jesus", "Jesus (object)"],
    127: ["by himself", "himself", "to himself / themselves", "herself / itself", "himself", "of himself"],
    129: ["heart", "hearts", "with the heart"],
    130: ["of the world", "world", "in / to the world", "the world (object)", "the world"],
    133: ["saying", "he says", "I say"],
    134: ["he said", "say!", "they will say", "I said", "to say", "he said"],
    136: ["give!", "he will give", "I give"],
    137: ["of the apostle / apostles", "to / with the apostles", "of the apostles", "the apostles (object)"],
    139: ["eternal", "eternal", "eternal", "eternal"],
    140: ["let us pray", "pray!", "to pray", "to pray", "he prays", "pray! (plural)"],
    141: ["of heaven / the heavens", "in the heavens", "heaven (object)", "of heaven"],
    142: ["the soul (object)", "soul", "of / to the soul", "of the souls"],
    143: ["blessed", "blessed", "blessed"],
    145: ["king", "by / with the king", "of the king", "kings", "to the king"],
    150: ["name", "by / in the name"],
    151: ["of the gospel", "the gospel", "the gospel"],
    153: ["under", "under"],
    154: ["let it be / may it be", "to be done", "let them be"],
    155: ["sins", "for / by the sins", "by the sin"],
    156: ["the victim (object)", "the victim (object)", "victim"],
    157: ["peace (object)", "in / with peace", "of peace", "peace"],
    159: ["day / days", "on the day", "the day (object)"],
    160: ["of the Virgin", "from / with the Virgin", "the Virgin (object)", "to the Virgin"],
    162: ["of Paul", "to / with Paul"],
    163: ["of sinners", "to / for sinners"],
    164: ["he reigns", "you reign"],
    165: ["by / with power", "power", "power (object)", "powers", "of power"],
    166: ["of the man", "of men", "man", "to / for men", "by / with the man"],
    170: ["the chalice (object)", "the chalice (object)"],
    171: ["mercy (object)", "mercy", "of / to mercy"],
    172: ["in / from heaven", "heaven (object)", "in / from heaven"],
    173: ["worthily", "worthy", "worthy (plural)"],
    174: ["light (object)", "of light", "light", "by / with light", "light"],
    180: ["according to", "according to"],
    181: ["in unity", "of unity"],
    182: ["lamb", "of the lamb", "to / with the lamb", "O lamb"],
    183: ["great", "great (object)", "great (object)"],
    184: ["life (object)", "life", "of / to life"],
    185: ["salvation (object)", "of salvation", "by / with salvation", "salvation"],
    190: ["he made", "you made"],
    191: ["lips", "with the lips"],
    192: ["of / to Mary", "Mary (object)"],
    194: ["of majesty", "in majesty"],
    195: ["in time", "times"],
    196: ["by / with the word", "words"],
    197: ["altar", "altar", "of the altar"],
    204: ["you take away", "to take away"],
    205: ["he / she lives", "I live"],
    206: ["to / with Peter", "Peter (object)"],
    207: ["praise", "praise (object)", "of praise"],
    208: ["with the voice", "voice (object)", "of the voice"],
    209: ["he comes / he came", "may he come"],
    210: ["honour (object)", "honour", "with honour"],
    211: ["of all / the whole", "one", "one"],
    217: ["free / deliver", "of the book"],
    218: ["mother", "mother (object)"],
    219: ["living / you live", "living / the living"],
    220: ["of the body", "body"],
    221: ["deeds", "deed"],
    222: ["fruit", "fruit (object)"],
    223: ["of the resurrection", "resurrection (object)", "I rose again"],
    224: ["he has", "we have", "to have"],
    225: ["of the people", "to / for the peoples", "to / for the people", "the people (object)"],
    226: ["I saw", "they will see", "you (plural) will have seen"],
    235: ["in the sight", "sight (object)"],
    236: ["we offer", "I have offered"],
    237: ["of the faithful", "to / for the faithful"],
    238: ["of death", "death (object)"],
    239: ["in the heavens", "of the heavens"],
    240: ["received / accepted", "to receive", "he received", "may you receive"],
    241: ["offered", "offering (object)", "with the offerings"],
    242: ["by / with power", "power", "powers"],
    252: ["head", "with the head"],
    253: ["among / to women", "woman"],
    254: ["with the mouth", "mouth"],
    255: ["secretly", "the silent prayer"],
    256: ["sign", "signs"],
    257: ["angels / of the angel", "the angel (object)"],
    258: ["do!", "may you do"],
    259: ["gifts", "gift"],
    260: ["to / for the servants", "and of the handmaids", "of the servants"],
    261: ["will", "by / with the will", "of the will"],
    279: ["I confess", "I will confess"],
    280: ["deign / be pleased", "having deigned"],
    281: ["of / to the church", "church"],
    282: ["strength (object)", "strength"],
    283: ["humility (object)", "of humility"],
    284: ["prayer (object)", "prayer"],
    285: ["full", "full"],
    286: ["seat / seats", "on the seats"],
    287: ["blood (object)", "blood"],
    288: ["truly / indeed", "but / truly"],
    289: ["your", "your / of you"],
    290: ["by / in work", "works"],
    291: ["to / with the archangel", "the archangel (object)"],
    292: ["the Baptist (object)", "of / to the Baptist"],
    293: ["let us bless", "we bless"],
    294: ["to John", "of John"],
    295: ["tongue", "with tongues"],
    296: ["Michael (object)", "to Michael"],
    297: ["to cleanse", "you have cleansed"],
    298: ["of the throne / thrones", "the throne (object)"],
    299: ["we give / we do", "doing", "let us do"],
    300: ["he receives", "I will receive", "receive! (plural)"],
    318: ["divine", "divine"],
    319: ["I lifted", "lift up! (plural)"],
    320: ["night", "by / at night"],
    321: ["I will place", "you have placed"],
    322: ["he filled", "fill!"],
    323: ["wisdom", "wisdom (object)"],
    324: ["holding", "they were holding"],
    325: ["they adored", "they will adore", "we adore", "to adore", "he is adored"],
    356: ["clothed", "clothed", "clothed"],
    357: ["you (plural) have heard", "we have heard"],
    358: ["to bless", "he blessed"],
    359: ["good", "good"],
    360: ["forgive!", "we forgive"],
    361: ["he rescued", "deliver / be rescued"],
    362: ["they rejoice", "let us rejoice"],
    363: ["to / among the nations", "of the nations"],
    364: ["just", "just / the just"],
    365: ["in the place", "the place (object)"],
    366: ["evils / from evil", "from evil"],
    367: ["he will send", "to send"],
    368: ["many", "to / with many"],
    369: ["merits", "by the merits"],
    370: ["prayers", "and with prayers"],
    371: ["in the beginning", "the beginning"],
    372: ["filled", "filled (plural)"],
    373: ["sacraments", "by / with the sacraments"],
    374: ["saving", "saving / of salvation"],
    375: ["may it be hallowed", "sanctify!"],
    376: ["knowledge", "knowledge (object)"],
    377: ["word", "word (object)"],
    378: ["of the Trinity", "Trinity"],
    379: ["to come", "to come"],
    476: ["acceptable", "and acceptable"],
    477: ["receiving", "to those receiving"],
    690: ["may he kindle", "kindle!"],
    691: ["by helping", "to be helped"],
    692: ["a little / somewhat", "a little / somewhat"],
    693: ["of others", "and others"],
    694: ["let us walk", "you (plural) may walk"],
}

FORM_RE = re.compile(r"^(.*?)\((\d+)\)\s*$")


def main():
    with open(STATIC, "r", encoding="utf-8") as fh:
        data = json.load(fh)

    notes = data.get("notes", [])
    mismatches = []
    patched = 0
    cleared = 0

    for n in notes:
        fs = n.get("forms_summary")
        if not fs:
            n.pop("forms_detail", None)
            continue
        forms = [p.strip() for p in fs.split("|") if p.strip()]
        if len(forms) <= 1:
            # single-form note: dictionary form, base English is correct
            n.pop("forms_detail", None)
            cleared += 1
            continue

        nid = n.get("id")
        glosses = GLOSSES.get(nid)
        if glosses is None:
            mismatches.append((nid, n.get("latin"), "NO GLOSS ENTRY", len(forms), fs))
            n.pop("forms_detail", None)
            continue
        if len(glosses) != len(forms):
            mismatches.append((nid, n.get("latin"),
                               "COUNT MISMATCH glosses=%d forms=%d" % (len(glosses), len(forms)),
                               len(forms), fs))
            n.pop("forms_detail", None)
            continue

        detail = []
        for raw, gloss in zip(forms, glosses):
            m = FORM_RE.match(raw)
            if m:
                form_text, count = m.group(1).strip(), int(m.group(2))
            else:
                form_text, count = raw, None
            detail.append({"f": form_text, "n": count, "g": gloss})
        n["forms_detail"] = detail
        patched += 1

    if mismatches:
        print("ERROR: %d note(s) need attention -- static.json NOT written:\n" % len(mismatches))
        for nid, latin, why, nf, fs in mismatches:
            print("  #%s %s -- %s" % (nid, latin, why))
            print("     forms(%d): %s" % (nf, fs))
        sys.exit(1)

    tmp = STATIC + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, STATIC)
    print("OK: forms_detail written to %d multi-form notes "
          "(%d single-form notes left as-is)." % (patched, cleared))


if __name__ == "__main__":
    main()
