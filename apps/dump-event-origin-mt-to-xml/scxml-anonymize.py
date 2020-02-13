#!/usr/bin/env seiscomp-python
#
# Remove some meta information from creationInfo
#
# Could be invoked in a pipeline like:
#
#  python scxmldump-public-with-mt.py -d "$db" -E "$evid" |
#  python scxml-anonymize.py > $evid.xml
#

import sys
import seiscomp.client, seiscomp.datamodel, seiscomp.io
import sc3stuff.util

class ObjectAnonymizer(seiscomp.client.Application):

    def __init__(self, argc, argv):
        seiscomp.client.Application.__init__(self, argc, argv)
        self.setMessagingEnabled(False)
        self.setDatabaseEnabled(False, False)
        self.xmlInputFile = "-"

    def run(self):
        ep = sc3stuff.util.readEventParametersFromXML(self.xmlInputFile)
        for obj in sc3stuff.util.EventParametersIterator(ep):
            try:
                ci = obj.creationInfo()
            except:
                continue
            ci.setAuthor("")
            obj.setCreationInfo(ci)
        sc3stuff.util.writeEventParametersToXML(ep)
        del ep
        return True


def main():
    argv = sys.argv
    argc = len(argv)
    app = ObjectAnonymizer(argc, argv)
    app()

if __name__ == "__main__":
    main()
