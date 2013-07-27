ConfigMerge
===========

ConfigMerge is a Python script for creating multiple IOS/NX-OS configurations based on a template.  It will take a template configuration file and a variables file.  The script will read in the variables for each device from the variables file, and then create a configuration from each device based on the template file.

Additional Features (beyond basic find/replace)
* Provides a list of all hosts found in the variables for review file prior to export.
* Allows for a review of all variables loaded for each host, prior to export.
* Will compare all variables found in the template file and the variables file and point out any that only exist in one file or the other (orphaned).
* --verbose (-v) flag that will force a variables review and give additional information during the write process.
* --quiet (-q) flag that skips all the review and questions and just exports the files (if you are feeling confident).  Will still alert on orphaned variables.


Additional functionality planned:

1) Make the variable review function show in the same order as the brief list of hosts found in the variables file.

2) Find a more user friendly way to alert that the files referenced as arguments for the script do not exist.
