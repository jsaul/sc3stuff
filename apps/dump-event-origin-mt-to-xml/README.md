scxmldump-public-with-mt
========================

Dump Origin and moment tensor information to SC3 XML.

Could be invoked like::

  scxmldump-public-with-mt --debug -d "$db" -E "$evid" |
  sccnv -f -i trunk:- -o qml1.2:"$evid-mt.QuakeML"

The above will dump the event information to QuakeML 1.2
