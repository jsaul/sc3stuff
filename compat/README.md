## SeisComP compatibility package ##

There are currently plans to change the naming of the Python packages from 
the current "seiscomp3" with mixed-case submodul names to "seiscomp" and 
lower-case submodul names. This change will probably take place with the 
next major SesComP release.

For example, the current ```seiscomp3.DataModel``` will become 
```seiscomp.datamodel```. This is nice indeed! Other than that there will 
be no change; class names in particular will not be changed.

This is a compatibility package to allow the usage of the future package 
naming in current Python scripts already. After the transition we can then 
use a similar meachanism in order to prevent existing custom scripts from 
breaking using a new SeisComP package.

Install using the usual ```setup.py``` script:

    python setup.py install --home=$HOME/seiscomp3

and the compatibility package will be installed along with the other
seiscomp3 stuff. You don't need to do anything else.
