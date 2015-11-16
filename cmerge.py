#!/usr/bin/python
import os
import sys
import argparse
import re
import csv


def responded_yes(question):
    """
    A function for returning the response to the provided question.

    :param question: A string that will be presented to the user.
    :return: Boolean, specifying if the user responding with a "yes" (True) or "no" (False).
    """
    answered = False
    while not answered:
        response = raw_input(question + " ")
        if response.lower() == "yes" or response.lower() == "y":
            return True
        elif response.lower() == "no" or response.lower() == "n":
            return False
        else:
            print "Invalid response. Please respond with 'y'/'yes' or 'n'/'no'."


def find_unique_vars(filename):
    """
    This function opens the supplied filename and searches for all unique variables.

    :param filename: The template filename that has been passed into the program as an argument (via argparse).
    :return: A set (because it can't contain duplicates) containing the variables found in the file.
    """

    all_vars = set()

    # Compile a regex that searches for variables (non-whitespace chars between a '<' and a '>' )
    template_var = re.compile(r"<.*?>")

    # Verify and open the template file
    try:
        with open(filename, 'r') as tempFile:
            tempFile.seek(0)
            for line in tempFile:
                # Use findall because some lines may have more than 1 variable on it.
                matches_on_line = template_var.findall(line)
                for item in matches_on_line:
                    all_vars.add(item)
    except IOError as e:
        sys.stderr.write("I/O error({0}) opening '{1}': {2}\n".format(e.errno, filename, e.strerror))
        exit(e.errno)
    return all_vars


def create_csv_file(all_vars, args):
    """
    This function tasks the variable names from find_unique_vars() and writes an empty CSV file with only the header
    row.

    :param all_vars: This should be the set returned from find_unique_vars.
    :param args: The collection of args created by the argparse module.
    :return: Nothing.  Only writes a file to disk.
    """

    # Sort the list in alpha order, so its easier for a human to add data into the CSV by hand.
    sorted_vars = sorted(list(all_vars))

    # If in single_mode, use default sort.  If in normal mode, move the key value to the front of the sorted list.
    if not args.single_mode:
        if args.key in all_vars:
            sorted_vars.remove(args.key)
            sorted_vars.insert(0, args.key)
        else:
            sys.stderr.write("The template does not contain the unique key variable {0}.\nThere are 3 ways to correct "
                             "this:\n1. Add {0} to the template file.\n2. Specify the correct unique key value with -k"
                             "\n3. If only a single file is being created, run in single config mode (-s)\n"
                             .format(args.key))
            exit(1)

    # If filename exists already, prompt to overwrite.
    if os.path.isfile(args.outputCSV):
        if not responded_yes("The file {0} already exists. Overwrite? (y/n)".format(args.outputCSV)):
            print "File exists and user chose not to overwrite file. Exiting."
            exit(0)

    # Write CSV file, using appropriately sorted list.
    try:
        with open(args.outputCSV, 'wb') as new_file:
            output_csv = csv.writer(new_file)
            output_csv.writerow(sorted_vars)
        print "{0} was successfully created.".format(args.outputCSV)
    except IOError as e:
        sys.stderr.write("I/O Error({0}) creating CSV file '{1}': {2}\n".format(e.errno, args.outputCSV, e.strerror))
        exit(e.errno)


def process_csv(args):
    """
    This function reads in the data from the supplies CSV file and returns a dictionary.  Each key in the dictionary is
    the unique key or each device, and the value for each

    :param args:
    :return:
    """

    data_dict = {}

    try:
        with open(args.inputCSV, 'rU') as csv_file:
            csv_reader = csv.reader(csv_file)
            # Get the first (header) row.
            header_row = csv_reader.next()

            # Make sure every item in the header row is a variable (i.e. surrounded with < > )
            for item in header_row:
                if item[0] != '<' and item[-1] != '>':
                    sys.stderr.write("Invalid Header Row. Item: '{0}' is not in the correct variable format.\n"
                                     .format(item))
                    exit(1)

            if args.single_mode:
                # Only capture the next row, because in single mode, there should only be one (if more, ignore them).
                only_row = csv_reader.next()
                for key, value in zip(header_row, only_row):
                    data_dict[key] = value
            else:
                # For normal mode, add each row as a dictionary into data_dict.
                for row in csv_reader:
                    if row[0].strip() == "":
                        sys.stderr.write("ERROR: Row missing unique key ({0}) value. Skipping row.".format(args.key))
                        continue
                    if row[0] in data_dict.keys():
                        sys.stderr.write("ERROR: Duplicate entry for {0} found. Skipping duplicate row.".format(row[0]))
                        continue
                    data_dict[row[0]] = {}
                    for key, value in zip(header_row, row):
                        data_dict[row[0]][key] = value
    except IOError as e:
        sys.stderr.write("I/O Error({0}) parsing CSV file '{1}': {2}\n".format(e.errno, args.inputCSV, e.strerror))
        exit(e.errno)

    return data_dict


def compare_keys(vars_from_template, vars_from_csv, args):
    """

    :param vars_from_template:
    :param vars_from_csv:
    :param args:
    :return:
    """

    # If the unique key variable doesn't exist in  the template, exit with an error (not single mode)
    if not args.single_mode and args.key not in vars_from_template:
        sys.stderr.write("The template does not contain the unique key variable {0}.\nThere are 3 ways to correct "
                         "this:\n1. Add {0} to the template file.\n2. Specify the correct unique key value with -k"
                         "\n3. If only a single file is being created, run in single config mode (-s)\n"
                         .format(args.key))
        exit(1)

    # If the 2 sets aren't equal, then the CSV has variables not in the template, or vice versa.
    if not vars_from_csv == vars_from_template:
        # If there are items left after removing the CSV items from the template items
        template_only = vars_from_template - vars_from_csv
        if len(template_only) > 0:
            sys.stderr.write("{0} only exists in {1}\n".format(list(template_only), args.template))
        csv_only = vars_from_csv - vars_from_template
        if len(csv_only) > 0:
            sys.stderr.write("{0} only exists in {1}\n".format(list(csv_only), args.inputCSV))
        sys.stderr.write("Exiting.  Please correct input files and try again.")
        exit(1)
    else:
        return True


def write_configs(merge_data, args):
    """

    :param merge_data:
    :param args:
    :return:
    """

    try:
        template = open(args.template, 'r')
    except IOError as e:
        sys.stderr.write("I/O Error({0}) opening template file '{1}': {2}\n".format(e.errno, args.template, e.strerror))
        exit(e.errno)
    else:
        config_count = 0
        if args.single_mode:
            config_count += 1
            file_root, file_ext = os.path.splitext(args.template)
            filename = file_root + "-merged" + file_ext

            # Check that the "configs" directory exists.  If not, create it.
            if not os.path.exists("configs"):
                os.makedirs("configs")

            full_path = os.path.join("configs", filename)
            this_config = open(full_path, 'w')

            line_num = 1
            for line in template:
                # For each line of the template, do a search for each find/replace "key".
                # If it is found replace it with the actual value.  Each line is process for
                # every find/replace key in case the line has more than one.
                # i.e.  ip address <INSIDE_IP> <INSIDE_MASK>
                ok_to_write = True
                for key, value in merge_data.iteritems():
                    if key in line:
                        if value == "":
                            # Do not write the line if there is no value for the variable
                            # that matched the line
                            ok_to_write = False
                        else:
                            line = line.replace(key, value)
                else:
                    # After the line has been checked/modified for all applicable keys
                    # (for loop completed), and the value for the variable wasn't empty,
                    # write the line to the output file.
                    if ok_to_write:
                        this_config.write(line)
                        line_num += 1

            this_config.close()
            # Once the loop is finished, print a status message.
            print "Successfully exported {0} configuration files.\n".format(config_count)
        else:
            list_of_hosts = merge_data.keys()
            for host in list_of_hosts:
                config_count += 1
                # reset the template read position to start for each host
                template.seek(0)
                filename = host + ".txt"

                # Check that the "configs" directory exists.  If not, create it.
                if not os.path.exists("configs"):
                    os.makedirs("configs")

                full_path = os.path.join("configs", filename)
                this_config = open(full_path, 'w')

                line_num = 1
                for line in template:
                    # For each line of the template, do a search for each find/replace "key".
                    # If it is found replace it with the actual value.  Each line is process for
                    # every find/replace key in case the line has more than one.
                    # i.e.  ip address <INSIDE_IP> <INSIDE_MASK>
                    ok_to_write = True
                    for key, value in merge_data[host].iteritems():
                        if key in line:
                            if value == "":
                                # Do not write the line if there is no value for the variable
                                # that matched the line
                                ok_to_write = False
                            else:
                                line = line.replace(key, value)
                    else:
                        # After the line has been checked/modified for all applicable keys
                        # (for loop completed), and the value for the variable wasn't empty,
                        # write the line to the output file.
                        if ok_to_write:
                            this_config.write(line)
                            line_num += 1
                # Close file before the next iteration opens it back up
                this_config.close()
            else:
                # Once the entire loop has finished, all lines in the template have been
                # modified and written, close the file.
                print "Successfully exported {0} configuration files.\n".format(config_count)


def config_merge(args):
    """
    The main function for the ConfigMerge program.  This function receives the
    arguments from argparse and takes the appropriate actions.

    :param args: The arguments returned from argparse.
    :return: Nothing
    """

    # Output CSV is supplied.  Create CSV file with header containing variables found in the template.
    if args.outputCSV:
        vars_from_template = find_unique_vars(args.template)
        create_csv_file(vars_from_template, args)

    # Input CSV is supplied. Parse CSV and create configuration files.
    elif args.inputCSV:
        vars_from_template = find_unique_vars(args.template)
        vars_from_csv = find_unique_vars(args.inputCSV)
        compare_keys(vars_from_template, vars_from_csv, args)
        merge_data = process_csv(args)
        write_configs(merge_data, args)

    else:
        # Other cases (either both supplied or neither supplied) should never happen if Argparse
        # is set up correctly.  Throw an error and close if this happens.
        print "ERROR! Argparse shouldn't allow input and output CSV to be both blank or specified."
        exit(1)


# This portion only gets called if the script is run directly from the command line (i.e. not imported)
if __name__ == '__main__':
    # Clear the screen
    os.system('cls' if os.name == 'nt' else 'clear')

    # Define arguments that can be passed to the program.
    parser = argparse.ArgumentParser(description=""
                                     "This script will generate configuration files for multiple devices.  It needs a "
                                     "template configuration file that contains variable to be replaced by this script."
                                     "  This script also needs a CSV file that contains the variables and the "
                                     "replacement value for each device that a configuration is being created for.")

    # Create an optional mutually exclusive group -- either single config mode is chosen, which won't require a unique
    # key, like "HOSTNAME", or we can specify what the key should be with -k.
    key_group = parser.add_mutually_exclusive_group()
    key_group.add_argument("-s", "--single_mode", action="store_true",
                           help="Runs in single device mode.  No unique key required. Limit 1 input line in CSV file.")
    key_group.add_argument("-k", "--key", default="HOSTNAME",
                           help="Specify the unique key for each output file. (Default = HOSTNAME)")

    # Create mutually exclusive group that specifies whether to take the CSV file as in input (create configs), or as
    # an output (create CSV from template)
    csv_group = parser.add_mutually_exclusive_group(required=True)
    csv_group.add_argument("-i", "--inputCSV", help="Name of the CSV file that contains replacement values for each "
                                                    "device.")
    csv_group.add_argument("-o", "--outputCSV", help="Name of the CSV file that this script will generate.  This file "
                                                     "will only contain a header row based on all the variables found "
                                                     "in the supplied template file.")

    # Add argument for the name of the template file.  This is always required.
    parser.add_argument("template", help="Name of the file that contains the configuration template.")

    # Assign input arguments to the "args" variable for reference later in the script.
    arguments = parser.parse_args()

    # Convert the key name to variable format (i.e. key-string to <key-string>), as long as no pointy brackets are in
    # the name.
    if '<' in arguments.key or '>' in arguments.key:
        print "The specified key cannot contain the '<' or '>' characters."
        exit(1)
    else:
        arguments.key = '<' + arguments.key + '>'

    # Call the main function with parsed arguments
    config_merge(arguments)
