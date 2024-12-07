#!/usr/bin/env python3

import datetime
import json
import logging
import os
import sqlite3
import xml.etree.cElementTree as ET

logging.basicConfig(level = logging.INFO)

categories = {
  "Lu": "Uppercase Letter",
  "Ll": "Lowercase Letter",
  "Lt": "Titlecase Letter",
  "LC": "Cased Letter",
  "Lm": "Modifier Letter",
  "Lo": "Other Letter",
  "L": "Letter",
  "Mn": "Nonspacing Mark",
  "Mc": "Spacing Mark",
  "Me": "Enclosing Mark",
  "M": "Mark",
  "Nd": "Decimal Number",
  "Nl": "Letter Number",
  "No": "Other Number",
  "N": "Number",
  "Pc": "Connector Punctuation",
  "Pd": "Dash Punctuation",
  "Ps": "Open Punctuation",
  "Pe": "Close Punctuation",
  "Pi": "Initial Punctuation",
  "Pf": "Final Punctuation",
  "Po": "Other Punctuation",
  "P": "Punctuation",
  "Sm": "Math Symbol",
  "Sc": "Currency Symbol",
  "Sk": "Modifier Symbol",
  "So": "Other Symbol",
  "S": "Symbol",
  "Zs": "Space Separator",
  "Zl": "Line Separator",
  "Zp": "Paragraph Separator",
  "Z": "Separator",
  "Cc": "Control",
  "Cf": "Format",
  "Cs": "Surrogate",
  "Co": "Private Use",
  "Cn": "Unassigned",
  "C": "Other",
}

# def charName(char):
#   name = char.attrib["na"]
#   if name == "":
#     name = "<control>"
#   return name


def charNameOrOldName(char):
  name = char.attrib["na"]
  if name == "":
    name = char.attrib["na1"]
  if name == "":
    for alias in char.findall("{http://www.unicode.org/ns/2003/ucd/1.0}name-alias"):
      if alias.attrib["type"] != "abbreviation":
        name = alias.attrib["alias"]
  return name


def charTitle(char):
  return charNameOrOldName(char) + " (U+" + char.attrib["cp"] + ")"


def charLink(char):
  return "<a href='%s'>%s</a>" % (char.attrib["cp"] + ".html", "U+" + char.attrib["cp"])


def charLinks(c, chars):
  return " ".join([charLink(chars[int(char, 16)]) for char in c.split(" ")])


root = ET.parse('ucd.nounihan.flat.xml').getroot()
title = root.find("{http://www.unicode.org/ns/2003/ucd/1.0}description")
assert title is not None and title.text is not None
title_cs = title.text.split(" ")
assert len(title_cs) == 2 and title_cs[0] == "Unicode"
unicode_version = title_cs[-1]
version = "%s/%s" % (unicode_version, datetime.datetime.now(datetime.timezone.utc).isoformat())
logging.info("generating docset version %s", version)

docsDir = "UnicodeCharacters.docset/Contents/Resources/Documents"
generatedDocsDir = os.path.join(docsDir, "c")
dbFile = "UnicodeCharacters.docset/Contents/Resources/docSet.dsidx"
docsetFile = "docset.json"

if not os.path.exists(generatedDocsDir):
  os.makedirs(generatedDocsDir)

if os.path.exists(dbFile):
  os.remove(dbFile)
db = sqlite3.connect(dbFile)
c = db.cursor()

c.execute('''CREATE TABLE searchIndex(id INTEGER PRIMARY KEY, name TEXT, type TEXT, path TEXT)''')

chars = {}
for char in root.findall(
  "{http://www.unicode.org/ns/2003/ucd/1.0}repertoire/{http://www.unicode.org/ns/2003/ucd/1.0}char"
):
  if "cp" in char.attrib:
    chars[int(char.attrib["cp"], 16)] = char

blocks = []
charToBlock = {}
for block in root.findall(
  "{http://www.unicode.org/ns/2003/ucd/1.0}blocks/{http://www.unicode.org/ns/2003/ucd/1.0}block"
):
  i = len(blocks)
  blocks.append(block)
  first = int(block.attrib["first-cp"], 16)
  last = int(block.attrib["last-cp"], 16)
  for char in range(first, last + 1):
    charToBlock[char] = i

for _, char in chars.items():
  cp = char.attrib["cp"]
  title = charTitle(char)
  s = chr(int(cp, 16))
  entity = "&#" + str(int(cp, 16)) + ";"
  block = blocks[charToBlock[int(cp, 16)]]
  if len(cp) > 4:
    python = "u\"\\U" + cp.rjust(8, "0") + "\""
  else:
    python = "u\"\\u" + cp.rjust(4, "0") + "\""

  docFile = cp + ".html"
  props = [
    (
      "Block",
      "<a href='%s'>%s</a>" % ("b" + block.attrib["first-cp"] + ".html", block.attrib["name"])
    ),
    # ("Category", "<a href='%s'>%s</a>" % ("c" + char.attrib["gc"] + ".html", categories[char.attrib["gc"]]))
    ("Category", "%s" % categories[char.attrib["gc"]]),
  ]

  if char.attrib.get("dm", "#") != "#":
    dms = [chars.get(int(dm, 16)) for dm in char.attrib["dm"].split(" ")]
    decomposition = []
    # I think sometimes this happens because i'm not looking at the full set
    if None in dms:
      for dm in char.attrib["dm"].split(" "):
        decomposition.append("U+" + dm)
    else:
      for dm in dms:
        assert dm is not None
        decomposition.append("<a href='%s'>%s</a>" % (dm.attrib["cp"] + ".html", charTitle(dm)))
    props.append(("Decomposition", " ".join(decomposition)))
  if char.attrib.get("uc", "#") != "#":
    props.append(("Upper case", charLinks(char.attrib["uc"], chars)))
  if char.attrib.get("tc", "#") != "#":
    props.append(("Title case", charLinks(char.attrib["tc"], chars)))
  if char.attrib.get("lc", "#") != "#":
    props.append(("Lower case", charLinks(char.attrib["lc"], chars)))

  props.extend(
    [
      ("Added", char.attrib.get("age")),
      ("UTF-8", " ".join([("0x%X" % b) for b in s.encode("utf-8")])),
      ("UTF-16", " ".join([("0x%X" % b) for b in s.encode("utf-16")])),
      ("UTF-32", " ".join([("0x%X" % b) for b in s.encode("utf-32")])),
      ("HTML", entity.replace("&", "&amp;")),
      ("Python", "<code>" + python + "</code>"),
    ]
  )
  with open(os.path.join(generatedDocsDir, docFile), "w") as f:
    f.write(
      "<head><link rel=\"stylesheet\" href=\"../c.css\"><title>%(title)s</title></head><body class='c'><h1>%(nameOrOldName)s <small>U+%(cp)s</small></h1><figure>%(entity)s</figure><table><tbody>%(props)s</tbody></table></body>"
      % {
        "nameOrOldName": charNameOrOldName(char),
        "cp": cp,
        "title": title,
        "entity": entity,
        "props": "".join(["<tr><th>%s</th><td>%s</td></tr>" % (k, v) for k, v in props]),
      }
    )
  c.execute(
    '''INSERT OR IGNORE INTO searchIndex(name, type, path) VALUES (?, ?, ?)''',
    (charTitle(char), "Element", "c/" + docFile)
  )

for block in blocks:
  name = block.attrib["name"]
  docFile = "b" + block.attrib["first-cp"] + ".html"
  first = int(block.attrib["first-cp"], 16)
  last = int(block.attrib["last-cp"], 16)
  overviewChars = []
  blockChars = []
  for char in range(first, last + 1):
    if char in chars:
      htmlChar = "&#%d;" % char
      htmlOverviewChar = htmlChar
      if chars[char].attrib["na"] == "":
        htmlOverviewChar = "<small>?</small>"
      overviewChars.append(
        "<a href='%s'>%s</a>" % (chars[char].attrib["cp"] + ".html", htmlOverviewChar)
      )
      blockChars.append(
        "<li><i>%s</i> <a href='%s'>%s</a></i>" %
        (htmlChar, chars[char].attrib["cp"] + ".html", charTitle(chars[char]))
      )
  with open(os.path.join(generatedDocsDir, docFile), "w") as f:
    f.write(
      "<head><link rel=\"stylesheet\" href=\"../c.css\"><title>%(name)s</title></head><body class='b'><h1>%(name)s</h1><h2>Overview</h2><nav>%(overviewChars)s</nav><h2>Characters</h2><ul>%(blockChars)s</ul></body>"
      % {
        "name": name,
        "overviewChars": " ".join(overviewChars),
        "blockChars": "".join(blockChars),
      }
    )
  c.execute(
    '''INSERT OR IGNORE INTO searchIndex(name, type, path) VALUES (?, ?, ?)''',
    (name, "Section", "c/" + docFile)
  )

# for categoryID, category in categories.items():
#   docFile = "c" + categoryID + ".html"
#   with open(os.path.join(generatedDocsDir, docFile), "w") as f:
#     f.write("<head><meta charset='UTF-8'><link rel=\"stylesheet\" href=\"../c.css\"><title>%(name)s</title></head><body><h1>%(name)s</h1></body>" % {
#       "name": category,
#     })
#   c.execute('''INSERT OR IGNORE INTO searchIndex(name, type, path) VALUES (?, ?, ?)''', (category, "Category", docFile))

db.commit()
db.close()

with open(os.path.join(docsDir, "index.html"), "w") as f:
  f.write(
    """<head>
  <link rel=\"stylesheet\" href=\"c.css\">
  <title>Unicode %(version)s Characters</title>
</head>
<body>
  <h1>Unicode %(version)s Characters</h1>
  <h2>Introduction</h2>
  <p>
    This docset contains a description of all characters in the Unicode
    database (without the <a href='http://www.unicode.org/reports/tr38/tr38-27.html'>Unihan characters</a>).
  </p>
  <p>
    Navigate the characters through the blocks below, or search them by name.
  </p>
  <p>
    <em>Note: Only characters that are supported by your browser font will be
    displayed</em>
  </p>
  <p>
    <h2>Blocks</h2>
    <ul>
      %(blocks)s
    </ul>
  </p>
</body>
""" % {
      "version":
        unicode_version,
      "blocks":
        "".join(
          [
            "<li><a href='%s'>%s</a> (%s - %s)</li>" % (
              "c/b" + b.attrib["first-cp"] + ".html", b.attrib["name"], b.attrib["first-cp"],
              b.attrib["last-cp"]
            ) for b in blocks
          ]
        )
    }
  )

with open(docsetFile, "w") as f:
  f.write(
    json.dumps(
      {
        "name": "Unicode Characters",
        "version": version,
        "archive": "UnicodeCharacters.tgz",
        "author": {
          "name": "Remko Tronçon",
          "link": "https://mko.re"
        },
        "aliases": [],
        "specific_versions": []
      },
      indent = 2
    )
  )
