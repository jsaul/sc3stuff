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

Install using the usual ```python setup.py install``` but make sure that 
you add the installation directory to your ```PYTHONPATH``` environment 
variable *before* the SeisComP environment variables.
