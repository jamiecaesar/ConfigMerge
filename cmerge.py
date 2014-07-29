#!/usr/bin/python
import argparse, os, re, csv

def Yes(question):
    answered = False
    count = 0
    while not answered:
        answ = raw_input(question + " ")
        if answ.lower() == "yes" or answ.lower() == "y":
            return True
        elif answ.lower() == "no" or answ.lower() == "n":
            return False
        else:
            print "I did not understand that response."
            if count > 4:
                print "Too many missed attempts.  Exiting..."
                exit(1)
            count += 1


def find_unique_vars(template):
    '''
    This function searches the supplied template file for all unique find/replace 
    variables, and returns all unique variables in a list.
    '''
    all_vars = []

    # Compile a regex that searches for non-whitespace chars between a < and >
    reg=re.compile(r"<.*?>")

    # Verify and open the template file
    try:
        with open(template, 'r') as tempFile:
            tempFile.seek(0)
            for line in tempFile:
                #Use findall because some lines may have more than 1 variable on it.
                linematch = reg.findall(line)
                for item in linematch:
                    all_vars.append(item)
    except IOError:
        print ("The template file {} cannot be found.\nPlease try again "
        "with a valid filename\n".format(args.template))
        exit(5)
    # Sets can't have duplicate items, so by converting the list to a set and back, we will
    # be left with a list with only one copy of each unique variable.
    return list(set(all_vars))


def create_var_file(dVars, csvFile):
    '''
    This fuction writes the variables CSV file to disk.  It takes a list of variables and
    the name of the CSV file that should be written.
    '''
    # We want the HOSTNAME variable to be the first one in the list. 
    # If there isn't a hostname field in the template, throw an error.  Otherwise remove it 
    # from the list of vars, because it will be statically entered into the file.    
    if "<HOSTNAME>" in dVars:
        dVars.remove("<HOSTNAME>")
    else:
        print ("The template MUST contain a '<HOSTNAME>' variable (case sensitive).\n"
            "Please add one after the 'hostname' or 'switchname' command in the template "
            "and try again.\n")
        exit(0)
    sorted_vars = sorted(dVars)
    sorted_vars.insert(0, "<HOSTNAME>")

    # Write the CSV file using the information from sorted_vars
    try:
        with open(csvFile, 'wb') as newfile:
            outputcsv = csv.writer(newfile)
            outputcsv.writerow(sorted_vars)
            print "File {} was successfully created.".format(csvFile)
    except IOError:
        print "The CSV filename is invalid.  Please try again with a valid filename."
        exit(5)


def import_csv(csvFile):
    '''
    This function opens the variables CSV file and loads the data into a data structure 
    that can later be used to write out each config script.  The data structure is a 
    dictionary with each hostname as the key, and the value being another dictionary. 
    The host-specific dictionary uses each variable name as a key and the replacement
    string as the value
    '''
    data_dict = {}
    host_list = []

    try:
        with open(csvFile, 'rU') as varFile:
            #Reset file position to beginnig (just in case)
            varFile.seek(0)
            csvreader = csv.reader(varFile)
            header = csvreader.next()
            #Check Header Row for proper syntax
            headreg = re.compile(r"^<.*?>$")
            for item in header:
                if headreg.match(item) == None:
                    print("Invalid Header Row.  Item: '{}' is not the proper format.\n"
                                "EXITING...\n".format(item))
                    exit(1)
            # Start building host_list and data_dict
            for row in csvreader:
                #skip over header row, if somehow file position resets
                if row == header:
                    pass
        
                #Make sure data row is the same length as header row  
                if len(row) != len(header): 
                    print("ERROR: The following row does not match the header row.\n"
                            "Row Data:\n{}\n"
                            "EXITING...\n".format(row))
                    exit(1)
                    
                host_list.append(row[0])
                data_dict[row[0]] = {}
                for key, value in zip(header, row):
                    data_dict[row[0]][key] = value
    except IOError:
        print ("The file {} cannot be found, please try again with a valid "
                "filename\n".format(csvFile))
        exit(1)

    #Return the list of hosts and the data structure to the main program.
    return host_list, data_dict


def same_list(tVars, cVars):
    '''
    This function will compare two lists to make sure they are the same.  It does this
    by converting the lists to sets and finding the symmetric difference, which gives
    the values that are only in one set or the other, but not both.  If this value is
    not 0, then the lists do not have the same elements.
    '''
    if len(set(tVars) ^ set(cVars)) == 0:
        return True
    else:
        return False


def write_configs(templateFile, lHosts, dData, verbosity):
    '''
    This fuction writes each host's configuration file.  It should be passed both the 
    template file to use, as well as the data structure generated by the import_csv() 
    function.
    '''
    try:
        template = open(templateFile, 'r')
    except IOError:
        print ("The template file {} cannot be found.\nPlease try again "
        "with a valid filename\n".format(args.template))
        exit(5)
    config_count = 0    
    for host in lHosts:
        config_count += 1
        #reset the template read position to start for each host
        template.seek(0)
        #create file name based on hostname of the device
        filename = host + ".txt"
        #Check that the "configs" directory exists.  If not, create it.
        if not os.path.exists("configs"):
            os.makedirs("configs")
        dstfile = open("./configs/" + filename, 'w')
        if verbosity >= 2:
                print "-" * 60
        if verbosity >= 1:
            print "Starting write of file {}.".format(filename)
        line_num = 1
        for line in template:
            # For each line of the template, do a search for each find/replace "key".  
            # If it is found replace it with the actual value.  Each line is process for 
            # every find/replace key in case the line has more than one.  
            # i.e.  ip address <INSIDE_IP> <INSIDE_MASK>
            ok_to_write = True
            for key, value in dData[host].iteritems():
                if key in line:
                    if value == "":
                        # Do not write the line if there is no value for the variable 
                        # that matched the line
                        ok_to_write = False
                        if verbosity >= 2:
                            print( "Found empty value for variable {} on line {}. Line '{}' "
                                "removed.".format(key, line_num, line))
                    else:
                        line = line.replace(key,value)
                        if verbosity >= 2:
                            print( "Found an instance of {} on line {} and replaced it with '{}'"
                                    .format(key, line_num, value))
            else:
                # After the line has been checked/modified for all applicable keys 
                # (for loop completed), and the value for the variable wasn't empty, 
                # write the line to the output file.
                if ok_to_write:
                    dstfile.write(line)
                    line_num += 1
        # Close file before the next iteration opens it back up 
        dstfile.close()
        if verbosity >= 2:
            print "Configuration %s has been completed" % filename
    else:
        # Once the entire loop has finished, all lines in the template have been 
        # modified and written, close the file.
        if verbosity >= 1:
            print "-" * 60
        print "Successfully exported {} configuration files.\n".format(config_count)


def main(args):
    '''
    The main function for the ConfigMerge program.  This function receives the 
    arguments from argparse and launches the rest of the functions.
    '''
    templateVars = find_unique_vars(args.template)
    # If outputCSV is supplied, we need to create a variables file.
    if (args.outputCSV is not None):
        if args.verbosity >= 1:
            print "The following variables were found in the template file:"
            for item in templateVars:
                print item
            if not Yes("Do you want to continue? (y/n)"):
                print "Exiting due to user selection."
                exit(1)
        # If filename exists already
        if os.path.isfile(args.outputCSV) and not Yes("The file {} already exists.  "
          "Overwrite? (y/n)".format(args.outputCSV)):
            print "Exiting.  Please re-run with correct filename."
            exit(5)
        # If we didn't exit because the filename existings and we didn't want to overwrite, then
        # create the file.
        create_var_file(templateVars, args.outputCSV)
    
    # If inputCSV is supplied, we need to parse it and create configuration files.
    elif (args.inputCSV is not None):
        if args.verbosity >= 1:
            print "Comparing lists of variables from %s and %s" % (args.template, args.inputCSV)
        
        # Check for the save variables in both the template and the CSV file.
        # The ^ operator gives all elements that are only in one set, not both.
        csvVars = find_unique_vars(args.inputCSV)
        if not same_list(templateVars, csvVars):
            if len(set(templateVars) - set(csvVars)) != 0:
                print("{} only exists in {}\n"
                    .format(list(set(templateVars) - set(csvVars)), args.template))
            if len(set(csvVars) - set(templateVars)) != 0:
                print("{} only exists in {}\n"
                    .format(list(set(csvVars) - set(templateVars)), args.csvVars))
            print "Exiting.  Please correct input files and try again."
            exit(1)
        else:
            if args.verbosity >= 1:
                print "Variable lists from both files match."
            if args.verbosity == 1:
                print "-" * 60
        #Write configuration files
        lHosts, dData = import_csv(args.inputCSV)
        if len(lHosts) != len(list(set(lHosts))):
            print "Duplicate hostnames found in CSV File.  Exiting..."
            exit(1)
        write_configs(args.template, lHosts, dData, args.verbosity)
    # Other cases (either both supplied or neither supplied) should never happen if Argparse
    # is set up correctly.  Throw an error and close if this happens.
    else:
        print "ERROR! Argparse shouldn't allow input and output CSV to be both blank or specified."
        exit(1)


# This portion only gets called if the script is run directly from the interpreter. 
# If this file is imported into another program, this part will not run.
if __name__ == '__main__':
    #Clear the screen
    os.system('cls' if os.name=='nt' else 'clear')

    # Define arguments that can be passed to the program.
    parser = argparse.ArgumentParser(description="This script will generate "
        "configuration files for multiple devices.  It needs a template "
        "configuration file that contains variable to be replaced by this "
        "script.  This script also needs a CSV file that contains the variables "
        "and the replacement value for each device that a configuration is being "
        "created for.")   
    parser.add_argument("-v", "--verbosity", action="count", default = 0, 
        help="Will provide a more verbose output.  -v is verbose, -vv is very verbose.")   
    parser.add_argument("template", help="Name of the file that contains the configuration "
        "template.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-i", "--inputCSV", help="Name of the CSV file that contains replacement "
        "values for each device.")
    group.add_argument("-o", "--outputCSV", help="Name of the CSV file that this script will "
        "generate.  This file will only contain a header row based on all the variables found "
        "in the supplied template file.")

    #Assign input arguments to the "args" variable for reference later in the script.
    args = parser.parse_args()

    #Call the main function with parsed arguments
    main(args)
