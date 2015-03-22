import xml.etree.ElementTree as ET
import os

class Parser(object):
    fpath = os.path.dirname(os.path.realpath(__file__))
    xml_dir = os.path.join(fpath, 'voice_control.xml')
    setting_tree = ET.parse(xml_dir)
    root_setting_xml = setting_tree.getroot()

    key_words = {}

    for child in root_setting_xml:
        key_words[child.get('name').lower()] = child.get('name').lower()

    if child.get('alias') == "True":
        for grandchildren in child:
            key_words[grandchildren.get('name').lower()] = child.get('name').lower()

    @classmethod
    def parse(self, text):
        words = text.split(' ')
        tup = ()
        for x in range(1, len(words)):
            command = ""
            args = ""

            for y in range(0, x):
                if y == 0:
                    command = words[y]
                else:
                    command += " " + words[y]
          
            for y in range(x, len(words)):
                if y == len(words) - 1:
                    args += words[y]
                else:
                    args += words[y] + " "

            if command.lower() in self.key_words:
                tup = (self.key_words[command.lower()], args)
            else:
                break

        return tup

if __name__ == '__main__':
    print Parser.parse("Call Alpha Bravo")