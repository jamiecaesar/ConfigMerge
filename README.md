ConfigMerge
===========

ConfigMerge is a Python script for creating multiple IOS/NX-OS configurations based on a template.  It requires the following a template configuration file and a variables file.  The script will read in the variables for each device from the variables file, and then create a configuration for each device based on the template file. In short, this is an automated "Find and Replace", with some additional checks and reviews of the data to attempt to avoid errors.

##Additional Features (beyond basic find/replace)
* Provides a list of all hosts found in the variables for review file prior to export.
* Checks for duplicate hostnames in the variables file (in the case of copy/paste errors)
* Allows for a review of all variables loaded for each host, prior to export.
* Will compare all variables found in the template file and the variables file and point out any that only exist in one file or the other (orphaned).
* --verbose (-v) flag that will force a variables review and give additional information during the write process.
* --quiet (-q) flag that skips all the review and questions and just exports the files (if you are feeling confident).  Will still alert on orphaned variables.


##Planned Improvements:

* Find a more user friendly way to alert that the files referenced as arguments for the script do not exist.
