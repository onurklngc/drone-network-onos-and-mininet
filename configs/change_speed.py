from lxml import etree

FILE_NAME = 'besiktas-speed-40/osm.net.xml'
SPEED_SCALE = 2

root = etree.parse(FILE_NAME)
for elt in root.iter():
    if "speed" in elt.attrib:
        current_speed = float(elt.attrib["speed"])
        elt.attrib["speed"] = str(current_speed * SPEED_SCALE)
    if "limitTurnSpeed" in elt.attrib:
        current_speed = float(elt.attrib["limitTurnSpeed"])
        elt.attrib["limitTurnSpeed"] = str(current_speed * SPEED_SCALE)
    print(elt)
# getting the parent tag of
# the xml document
b_xml = etree.tostring(root, pretty_print=True)

with open(FILE_NAME, "wb") as f:
    f.write(b_xml)
