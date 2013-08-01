import argparse
import os
import re
os.system('cls' if os.name=='nt' else 'clear')

def find_unique_vars(file):
    """This function searches the file for all unique find/replace variables, and returns a list
        of unique variables"""
        
    #A list to collect every variable delimited by < >.  All instances (duplicates) will be added.
    all_vars = []

    file.seek(0)
    #Compile a regex that searches for non-whitespace chars between a < and >
    reg=re.compile(r"<\S*?>")
    for line in file:
        #Use findall because some lines may have more than 1 variable on it. Output is a list.
        linematch = reg.findall(line)
        for item in linematch:
            #ignore this special string that only marks the end of a hosts variable block    
            if item == "<--END-->":
                pass
            else:
                #If it is anything else, append it to the list of variables found
                all_vars.append(item)
    else:
        #Sets can't have duplicate items, so by converting the list to a set and back, we will
        #be left with a list with only one copy of each unique variable.
        find_unique_vars = list(set(all_vars))
    return find_unique_vars
    
def write_host_block(hostname):
    if args.verbose:
        print "Writing line for <HOSTNAME>"
    newfile.write("<HOSTNAME>::" + hostname + "\n")
    for var in sorted(t_vars):
        if args.verbose:
            print "Writing Line For " + var
        newfile.write(var + "::\n")
    newfile.write("<--END-->\n")

#This section manages the (-h) help output, with the help of ArgParse, and makes sure that all required arguments are passed to the script when run.
parser = argparse.ArgumentParser(description="This script will generate a variables file, for use with ConfigMerge, based on the variables found in the template configuration you specify.")
group = parser.add_mutually_exclusive_group()
group.add_argument("-v", "--verbose", action="store_true", help="Will provide a more verbose output")
parser.add_argument("template", help="Name of the file that is the configuration template")
#Assign input arguments to the "args" variable for reference later in the script.
args = parser.parse_args()

template = open(args.template)

t_vars = find_unique_vars(template)

if args.verbose:
    print "Found the following variables: " + str(t_vars)[1:(len(str(t_vars))-2)]
    
if "<HOSTNAME>" in t_vars:
    t_vars.remove("<HOSTNAME>")
else:
    print "The template MUST contain a '<HOSTNAME>' variable.  Please add one after the 'hostname' or 'switchname' command in the template and try again"
    exit(0)

while True:
    numhosts = eval(raw_input("How many device blocks do you want added to the output file? "))
    if type(numhosts) == int:
        break
    else:
        print "Value must be a whole number.  Please try again."

#If filename ends with .txt, remove it, so the final file won't have .txt in the middle
if args.template[-4:] == ".txt":
    newfile = open(args.template[:-4] + "-vars.txt", 'w')
else:
    newfile = open(args.template + "-vars.txt", 'w')
    
#Write File Header
if args.verbose:
    print "Writing File Header"
newfile.write("###############################################################################\n")
newfile.write("#     Lines starting with # will be ignored\n")
newfile.write("#\n")
newfile.write("#     All Find/Replace items for the same device should be grouped together.\n")
newfile.write("#     The variable should be contained in angle brackets  ->  < >\n")
newfile.write("#     These variable names will be replaced if found in the template config file\n")
newfile.write("#	  Variable names MUST NOT have spaces in them\n")
newfile.write("#     The variable should be separated by its value with a double colon. -> ::\n")
newfile.write("#     The grouping MUST start with the <HOSTNAME> variable\n")
newfile.write("#     The grouping ends with the <--END--> tag.\n")
newfile.write("#     Add information for as many hosts as you'd like.\n")
newfile.write("###############################################################################\n")

count = 1
while numhosts > 0:
    write_host_block("Host" + str(count) + "-Router")
    count = count + 1
    numhosts = numhosts - 1

newfile.close()

print str(count - 1) + " variable blocks written to file: " + args.template + "-vars.txt"

    

