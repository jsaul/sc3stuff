#!/usr/bin/env seiscomp-python
#
# Dump some moment tensor meta information to text.
#
# Could be invoked in a pipeline like:
#
#  python scxmldump-public-with-mt.py --debug -d "$db" -E "$evid" |
#  python scxml-to-mt-creation-info.py
#

import sys
import seiscomp.client, seiscomp.datamodel, seiscomp.io
import sc3stuff.util


def meta(fm):
    real_name_map = { "J. Saul":["saul"], "":["hanka", "winfried"], "A. Strollo":["strollo", "angelo"] }

    update = fm.creationInfo().creationTime().toString("%Y-%m-%d %H:%M:%S UTC")
    author = fm.creationInfo().author()
    author_real_name = None
    for real_name in real_name_map:
        for user in real_name_map[real_name]:
            if author.startswith(user):
                author_real_name = real_name

    txt = ""
    if author_real_name is not None:
        if author_real_name == "":
            txt = txt + "Analysis performed manually\n"
        else:
            txt = txt + "Analysis performed manually by "+author_real_name+"\n"
    else:
        if fm.evaluationMode() == seiscomp.datamodel.MANUAL:
            txt = txt + "Analysis performed manually\n"
        else:
            txt = txt + "Analysis performed automatically\n"
    txt = txt + "Last updated "+update+"\n"

    return txt


class MomentTensorInfoDumper(seiscomp.client.Application):

    def __init__(self, argc, argv):
        seiscomp.client.Application.__init__(self, argc, argv)
        self.setMessagingEnabled(False)
        self.setDatabaseEnabled(False, False)
        self.xmlInputFile = "-"


    def run(self):
        ep = sc3stuff.util.readEventParametersFromXML(self.xmlInputFile)
        for i in range(ep.focalMechanismCount()):
            fm = ep.focalMechanism(i)
            txt = meta(fm)
            print(txt)
        del ep
        return True


def main():
    argv = sys.argv
    argc = len(argv)
    app = MomentTensorInfoDumper(argc, argv)
    app()

if __name__ == "__main__":
    main()
