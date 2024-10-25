#!/usr/bin/env python3

""" YAML to FSTAB Converter Script

This script reads a YAML configuration file describing filesystem mount points
and converts it into a valid '/etc/fstab' file format. It supports backup of
existing fstab files, validation of changes, and automatic rollback if needed.

Command-line Arguments:
    --yaml_file (str): Path to the YAML file (default: './fstab.yaml').
    --fstab_file (str): Path to the output fstab file (default: '/etc/fstab').
    --dry_run: Displays generated fstab entries without making changes.
    --root_reserve : Apply root reserve settings for partitions if applicable.

Usage:
    sudo python3 fstab_writer.py
    sudo python3 fstab_writer.py --yaml_file /path/file.yaml
    sudo python3 fstab_writer.py --fstab_file /path/fstab
    sudo python3 fstab_writer.py --dry_run
    sudo python3 fstab_writer.py --root_reserve
    or any combination of arguments

Requirements:
    - Python 3.x
    - Sudo privileges (to modify /etc/fstab)

Notes:
    - Run the script as root for write permissions on '/etc/fstab'.
    - Ensure the YAML file is properly formatted to prevent errors.
    - Backup files are saved in the specified backup directory in config
      (default: '~/backups/fstab/').
    - Apply root reserve is not implemented fully yet.

License:
    GNU General Public License v3.0 (GPL-3.0).

Author:
    Ata Mahmoudi

Last Updated:
    25.10.2024

"""

import re
import shutil
import subprocess
import sys
import os
from datetime import datetime

# Global configuration settings, including regex patterns and default paths.
CONFIG = {
    # Regex pattern for block devices, IPs..
    "device_pattern": (
        r'^(/[^:]+|((25[0-5]|2[0-5][0-9]|1[0-9]{2}|[1-9]?[0-9])\.){3}'
        r'(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])):$'
    ),

    # Regex pattern for UUIDs, LABELs, PARTUUIDs, PARTLABELs.
    "uuid_pattern": r'^(LABEL|UUID|PARTUUID|PARTLABEL)=[\w-]+$',

    # Regex pattern for key-value for each device.
    "key_value_patten": r'^([\w-]+):\s*(.*)$',

    # Supported filesystem types for the fstab.
    "supported_mount_type": [
        "sysfs", "tmpfs", "bdev", "proc", "cgroup", "cgroup2", "cpuset",
        "devtmpfs", "configfs", "debugfs", "tracefs", "securityfs",
        "sockfs", "bpf", "pipefs", "ramfs", "hugetlbfs", "devpts", "ext3",
        "ext2", "ext4", "squashfs", "vfat", "ecryptfs", "fuseblk", "fuse",
        "fusectl", "efivarfs", "mqueue", "pstore", "autofs", "binfmt_misc",
        "vboxsf", "overlay", "none", "xfs", "nfs", "swap"
        ],

    # Paths for backup and default file locations.
    "backup_path": "~/backups/fstab/",
    "default_fstab_file": "/etc/fstab",
    "default_yaml_file": "./fstab.yaml"
}


def parse_yaml_file(yaml_file):
    """
    Parse the provided YAML file and return a dictionary of fstab entries.

    Args:
        yaml_file (str): Path to the YAML file.

    Returns:
        dict: Parsed fstab data.
    """
    fstab_dict = {}
    current_device = None

    try:
        # Read YAML file.
        with open(yaml_file, 'r') as file:

            for line in file:
                # Remove whitespaces.
                line = line.strip()

                # Check for device or UUID lines.
                if (
                    re.match(CONFIG['device_pattern'], line) or
                    re.match(CONFIG['uuid_pattern'], line)
                ):
                    current_device = (
                        line[:-1].strip() if line.endswith(':')
                        else line.strip()
                    )
                    # Initialize dict for device.
                    fstab_dict[current_device] = {}
                elif current_device:
                    key_value_match = (
                        re.match(CONFIG['key_value_patten'], line)
                    )
                    if key_value_match:
                        # Assign matched key and value of current line.
                        key, value = key_value_match.groups()

                        if key == 'options':
                            # Initialize options key.
                            fstab_dict[current_device][key] = []
                        else:
                            fstab_dict[current_device][key] = value.strip()
                    # Handle options list (e.g., options: -rw).
                    elif line.startswith('-'):
                        option = line[1:].strip()
                        fstab_dict[current_device]['options'].append(option)

        return fstab_dict

    except Exception as e:
        print("Error while parsing YAML file:", e)
        sys.exit(1)


def generate_fstab(parsed_fstab, dry_run, root_reserve):
    """
    Generate fstab lines from the parsed YAML data.

    Args:
        parsed_fstab (dict): Parsed fstab entries.
        dry_run (bool): If True, only print the changes without applying them.
        root_reserve (bool): If True, apply root reserve for partitions.

    Returns:
        list: A list of fstab entry lines.
    """
    try:

        fstab_lines = []

        for device_name, device_details in parsed_fstab.items():
            # Extract mount point, type, and other necessary fields.
            if 'mount' in device_details and device_details['mount']:
                mount_point = device_details.get('mount')
            else:
                raise ValueError(
                    f"Error generating fstab line for {device_name}, "
                    "mount point is missing."
                                 )

            if (
                'type' in device_details
                and device_details['type']
                and device_details['type'] in CONFIG['supported_mount_type']
            ):
                mount_type = device_details.get('type')
            else:
                raise ValueError(
                    f"Error generating fstab line for {device_name},"
                    "mount type is missing or not supported."
                    )

            # Handle NFS mount cases.
            if mount_type == 'nfs':
                nfs_path = device_details.get('export')
                if nfs_path:
                    device_name = f"{device_name}:{nfs_path}"
                else:
                    raise ValueError(
                        f"NFS mount {device_name} is missing 'export' field."
                        )

            # Collect options, dump, and pass values.
            mount_options = device_details.get('options', ['defaults'])
            mount_options = ",".join(mount_options)
            mount_dump = device_details.get('dump', '0')
            mount_pass = device_details.get('pass', '0')

            # Format the fstab line.
            line = (
                f"{device_name} {mount_point} {mount_type}"
                f"{mount_options} {mount_dump} {mount_pass}"
            )

            fstab_lines.append(line)

            # Root reserve function will be call here after implementation.
            if (
                'root-reserve' in device_details
                and device_details['root-reserve']
                and not dry_run and root_reserve
            ):
                print(
                    f"Apply root reserve of {device_details['root-reserve']}"
                    f" on {device_name} partition..."
                    )

        return fstab_lines

    except Exception as e:
        print("Error while generating fstab file:", e)
        sys.exit(1)


def write_fstab(generated_fstab, fstab_file, dry_run):
    """
    Write the generated fstab to the target file.

    Args:
        generated_fstab (list): List of fstab lines.
        fstab_file (str): Path to the target fstab file.
        dry_run (bool): If True, only print the changes without applying them.
    Returns:
        str: DRY_RUN or fstab_file
    """
    try:
        if not dry_run:
            with open(fstab_file, 'w') as fstab:
                print(f"Writing fstab to: {fstab_file}")
                for line in generated_fstab:
                    fstab.write(line + "\n")
        else:
            for line in generated_fstab:
                print(line)
            return 'DRY_RUN'
        return fstab_file

    except PermissionError:
        print(f"Error: Insufficient permissions to write on {fstab_file}.")
        sys.exit(1)

    except Exception as e:
        print("Error while fstab file writing.", e)
        sys.exit(1)


def backup_fstab(dry_run):
    """
    Backup the current /etc/fstab file.

    Args:
        dry_run (bool): If True, do not create an actual backup.
    Returns:
        str: Path to the backup file.
    """
    try:
        if dry_run:
            return 'DRY_RUN'
        path = os.path.expanduser(CONFIG["backup_path"])
        if not os.path.exists(path):
            os.makedirs(path)
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(path, f"fstab_{current_time}.bak")
        shutil.copy('/etc/fstab', backup_file)
        print(f"Backup of fstab created: {backup_file}")

        return backup_file

    except PermissionError:
        print(
            "Error: Insufficient permissions to "
            f"create a backup of '/etc/fstab' in {path}."
            )
        sys.exit(1)

    except Exception as e:
        print("Error while creating backup fstab.", e)
        sys.exit(1)


def validate_fstab():
    """
    Validate the new fstab configuration by running 'mount -a'.

    Returns:
        bool: True if validation succeeds, False otherwise.
    """
    try:
        # Execute the `mount -a` command to remount filesystems
        subprocess.run(['mount', '-a'],
                       check=True,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE
                       )
        return True

    except subprocess.CalledProcessError as e:
        print(f"Error during 'mount -a': {e.stderr.decode().strip()}")
        return False

    except Exception as e:
        print(f"Unexpected error during 'mount -a': {str(e)}")
        return False


def restore_last_backup(last_backup):
    """
    Restore the last backup of the fstab file.

    Args:
        last_backup (str): Path to the last backup file.
    """
    try:
        shutil.copy(last_backup, CONFIG["default_fstab_file"])
        print(f"Last fstab backup '{last_backup}' has been restored.")
        return 2

    except PermissionError:
        print(
            "Error: Insufficient permissions "
            "to restore a backup of '/etc/fstab'."
            )
        sys.exit(1)

    except Exception as e:
        print(f"Error during restore: {str(e)}")
        sys.exit(1)


def yaml_to_fstab(yaml_file, fstab_file, dry_run, root_reserve):
    """
    Convert a YAML file into an fstab file.

    Args:
        yaml_file (str): Path to the YAML file.
        fstab_file (str): Path to the fstab file.
        dry_run (bool): If True, only print changes without applying.
        root_reserve (bool): If True, apply root reserve settings.
    """
    parsed_fstab = parse_yaml_file(yaml_file)
    generated_fstab = generate_fstab(parsed_fstab, dry_run, root_reserve)
    last_backup = backup_fstab(dry_run)
    result = write_fstab(generated_fstab, fstab_file, dry_run)

    if not dry_run:
        print(f"fstab wrote successfully in the following path: {result}")

        if fstab_file == '/etc/fstab':
            validate_result = False
            validate_result = validate_fstab()
            if not validate_result:
                print(
                    "Validation of changes failed;"
                    "changes will be rolled back..."
                      )
                restore_last_backup(last_backup)
            else:
                print("fstab update validated successfully.")
                return 0


def main():
    """
    Main entry point for the script.
    Parses command-line arguments and calls the appropriate functions.
    """
    import argparse

    # Initialize parser
    parser = (
        argparse.ArgumentParser(
            description="Process YAML to generate /etc/fstab file"
            )
    )

    # Add arguments
    parser.add_argument(
        '--yaml_file',
        type=str,
        default=CONFIG["default_yaml_file"],
        help='Path to YAML file'
        )
    parser.add_argument(
        '--fstab_file',
        type=str,
        default=CONFIG["default_fstab_file"],
        help='Path to fstab file'
        )
    parser.add_argument(
        '--dry_run',
        action='store_true',
        help='Print generated fstab entries without change files'
        )
    parser.add_argument(
        '--root_reserve',
        action='store_true',
        help='Apply root reserve'
        )

    # Read command-line arguments and return args object
    args = parser.parse_args()

    # Call yaml_to_fstab function
    yaml_to_fstab(
        args.yaml_file, args.fstab_file, args.dry_run, args.root_reserve
        )


if __name__ == "__main__":
    main()
