#!/usr/bin/env python3

import re
import sys
import pprint

CONFIG = {
    "device_pattern": r'^(/[^:]+|((25[0-5]|2[0-5][0-9]|1[0-9]{2}|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])):$',  # Regex pattern for block devices, IPs
    "uuid_pattern": r'^(LABEL|UUID|PARTUUID|PARTLABEL)=[\w-]+$',  # Regex pattern for UUIDs, LABELs, PARTUUIDs, PARTLABELs
    "key_value_patten": r'^([\w-]+):\s*(.*)$' # Regex pattern for key-value for each device
}

def parse_yaml_file(yaml_file):
    fstab_dict = {}
    current_device = None
    
    try:
        # Read YAML file
        with open(yaml_file, 'r') as file:

            for line in file:
                # Remove whitespaces
                line = line.strip()

                if re.match(CONFIG['device_pattern'], line) or re.match(CONFIG['uuid_pattern'], line):
                    current_device = line[:-1].strip() if line.endswith(':') else line.strip()
                    fstab_dict[current_device] = {} # Initialize dict for device
                elif current_device:
                    key_value_match = re.match(CONFIG['key_value_patten'], line)
                    if key_value_match:
                        key, value = key_value_match.groups() # Assign matched key and value of current line

                        if key == 'options':
                            fstab_dict[current_device][key] = [] # Initialize options key
                        else:
                            fstab_dict[current_device][key] = value.strip()
                    elif line.startswith('-'):
                        option = line[1:].strip()
                        fstab_dict[current_device]['options'].append(option)

        return fstab_dict

    
    except Exception as e:
        print(f"Error while parsing YAML file: {str(e)}")
        sys.exit(1)


def yaml_to_fstab(yaml_file, fstab_file):
    
    parsed_fstab = parse_yaml_file(yaml_file)
    pprint.pprint(parsed_fstab)


def main():
    # Import argparse module to read command-line arguments
    import argparse

    # Initialize parser
    parser = argparse.ArgumentParser(description="Process YAML to generate /etc/fstab file")

    # Add arguments (first argument, yaml_file, is mandatory)
    parser.add_argument('yaml_file', type=str, help='Path to YAML file')
    parser.add_argument('--fstab_file', type=str, default='/etc/fstab', help='Path to fstab file')

    # Read command-line arguments and return args object
    args = parser.parse_args()

    # Call yaml_to_fstab function
    yaml_to_fstab(args.yaml_file, args.fstab_file)


if __name__ == "__main__":
    main()

