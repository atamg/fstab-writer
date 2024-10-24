#!/usr/bin/env python3

import re
import sys

CONFIG = {
    "device_pattern": r'^(/[^:]+|((25[0-5]|2[0-5][0-9]|1[0-9]{2}|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])):$',  # Regex pattern for block devices, IPs
    "uuid_pattern": r'^(LABEL|UUID|PARTUUID|PARTLABEL)=[\w-]+$',  # Regex pattern for UUIDs, LABELs, PARTUUIDs, PARTLABELs
    "key_value_patten": r'^([\w-]+):\s*(.*)$', # Regex pattern for key-value for each device
    "supported_mount_type": [
        "sysfs","tmpfs","bdev","proc","cgroup","cgroup2","cpuset",
        "devtmpfs","configfs","debugfs","tracefs","securityfs",
        "sockfs","bpf","pipefs","ramfs","hugetlbfs","devpts","ext3",
        "ext2","ext4","squashfs","vfat","ecryptfs","fuseblk","fuse",
        "fusectl","efivarfs","mqueue","pstore","autofs","binfmt_misc",
        "vboxsf","overlay", "none", "xfs", "nfs", "swap"
        ],
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
        print("Error while parsing YAML file:", e)
        sys.exit(1)


def generate_fstab(parsed_fstab):
    try:
        
        fstab_lines = []

        for device_name, device_details in parsed_fstab.items(): 
            
            if 'mount' in device_details and device_details['mount']:
                mount_point = device_details.get('mount')
            else:
                raise ValueError(f"Error generating fstab line for {device_name}, mount point is missing.")
            
            if 'type' in device_details and device_details['type'] and device_details['type'] in CONFIG['supported_mount_type']:
                mount_type = device_details.get('type')
            else:
                raise ValueError(f"Error generating fstab line for {device_name}, mount type is missing or not supported.")
            
            if mount_type == 'nfs':
                nfs_path = device_details.get('export')
                if nfs_path:
                    device_name = f"{device_name}:{nfs_path}"
                else:
                    raise ValueError(f"NFS mount {device_name} is missing 'export' field.")


            mount_options = device_details.get('options', ['defaults'])
            mount_options = ",".join(mount_options)

            mount_dump = device_details.get('dump', '0')

            mount_pass = device_details.get('pass', '0')

            line = f"{device_name} {mount_point} {mount_type} {mount_options} {mount_dump} {mount_pass}"

            fstab_lines.append(line)

            if 'root-reserve' in device_details and device_details['root-reserve']: # In case we need to apply root reserve we should call related function here
                print(f"Apply root reserve of {device_details['root-reserve']} on {device_name} partition...")

        return fstab_lines

    except Exception as e:
        print("Error while generating fstab file:", e)
        sys.exit(1)    


def write_fstab(generated_fstab, fstab_file):
    try:
        with open(fstab_file, 'w') as fstab:
            print(f"Writing fstab to: {fstab_file}")
            for line in generated_fstab:
                fstab.write(line + "\n")
        
        return fstab_file

    except Exception as e:
        print("Error while fstab file writing.")



def yaml_to_fstab(yaml_file, fstab_file):
    
    parsed_fstab = parse_yaml_file(yaml_file)
    
    generated_fstab = generate_fstab(parsed_fstab)
    
    result = write_fstab(generated_fstab, fstab_file)

    print(f"fstab wrote successfully in the following path: {result}")

def main():
    # Import argparse module to read command-line arguments
    import argparse

    # Initialize parser
    parser = argparse.ArgumentParser(description="Process YAML to generate /etc/fstab file")

    # Add arguments (first argument, yaml_file, is mandatory)
    parser.add_argument('yaml_file', type=str, help='Path to YAML file')
    parser.add_argument('--fstab_file', type=str, default='./fstab', help='Path to fstab file')

    # Read command-line arguments and return args object
    args = parser.parse_args()

    # Call yaml_to_fstab function
    yaml_to_fstab(args.yaml_file, args.fstab_file)


if __name__ == "__main__":
    main()

