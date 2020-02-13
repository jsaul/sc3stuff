scxmldump-public-with-mt
========================

Dump origin and moment tensor information to SC3 XML.

Could be invoked like::

  scxmldump-public-with-mt --debug -d "$db" -E "$evid" |
  sccnv -f -i trunk:- -o qml1.2:"$evid-mt.QuakeML"

The above will dump the event information to QuakeML 1.2

The functionality of scxmldump-public-with-mt is similar to
scxmldump. The difference is that scxmldump-public-with-mt doesn't
load arrivals and picks for speed, but also loads additional origins
references by the moment tensor objects, like triggering and derived
origins. Due to not loading arrivals it is also very fast.
