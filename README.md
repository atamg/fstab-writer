# fstab-writer

This repository contains a Python script that converts a YAML file into a valid `/etc/fstab` file. It allows for backup, validation, and rollback of changes. It supports `dry_run` mode to preview changes without applying them and provides the option to apply root reserve settings for certain partitions.

## Features

- **YAML to FSTAB Conversion**: Converts a YAML configuration file into a properly formatted fstab file.
- **Backup and Restore**: Automatically backs up the existing fstab file before making changes.
- **Validation**: Uses the `mount -a` command to validate the new fstab configuration.
- **Dry Run Mode**: Print generated fstab entries without actually modifying files.
- **Root Reserve Application**: Apply root reserve settings for specified partitions. (Not implemented yet)

## Requirements

- Python 3.6 or later
- Sudo permission to be able to write on /etc/fstab
- Required Python libraries (built-in):
  - `re`
  - `shutil`
  - `subprocess`
  - `sys`
  - `os`
  - `datetime`
  - `argparse`

## Installation

Clone this repository to your local machine:

```bash
git clone https://github.com/atamg/fstab-writer.git
cd fstab-writer
```

## Usage
**Command-line Arguments:**

The script accepts the following command-line arguments:

- **--yaml_file:** Path to the YAML configuration file (default: ./fstab.yaml)
- **--fstab_file:** Path to the output fstab file (default: /etc/fstab)
- **--dry_run:** If specified, the script will print the generated fstab without making any changes.
- **--root_reserve:** Apply root reserve for the specified partitions (if supported by the filesystem).

**How to run:**

To run the script directly on Linux, you can make the script executable and run it from the command line. Here’s how:

```bash
chmod +x fstab_writer.py

sudo ./fstab_writer.py
```
or execute the script using python. Here’s how:
```bash
sudo python3 ./fstab-writer.py
```

**Example commands:**
```bash
    sudo python3 fstab_writer.py
    sudo python3 fstab_writer.py --yaml_file /path/file.yaml
    sudo python3 fstab_writer.py --fstab_file /path/fstab
    sudo python3 fstab_writer.py --dry_run
    sudo python3 fstab_writer.py --root_reserve
    sudo python3 fstab_writer.py --yaml_file /path/file.yaml --fstab_file /path/fstab
    sudo python3 fstab_writer.py --yaml_file /path/file.yaml --dry_run
    sudo python3 fstab_writer.py --yaml_file /path/file.yaml --fstab_file /path/fstab --root_reserve
```

## YAML File Structure

The YAML configuration file must follow a specific structure to represent the fstab entries. Below is an example:

```yaml
fstab:
  /dev/sda1: 
    mount: /boot 
    type: xfs 
  /dev/sda2: 
    mount: / 
    type: ext4 
  /dev/sdb1: 
    mount: /var/lib/postgresql 
    type: ext4 
    root-reserve: 10% 
  192.168.4.5: 
    mount: /home 
    export: /var/nfs/home 
    type: nfs 
    options: 
      - noexec 
      - nosuid
```

## Backup and Restore

Whenever the script modifies /etc/fstab, it creates a backup of the current fstab file in the directory specified by `CONFIG["backup_path"]` (default: ~/backups/fstab/). The backup files are named using the format fstab_YYYYMMDD_HHMMSS.bak.

If the validation step (mount -a) fails, the script automatically restores the most recent backup.


## Restoring a Backup Manually
To restore a backup manually, use the following command:
```bash
sudo cp ~/backups/fstab/fstab_YYYYMMDD_HHMMSS.bak /etc/fstab
```

## Dry Run

The `--dry_run` option allows you to see what the generated fstab will look like without modifying the actual file. This is useful for testing and verifying the output.
```bash
sudo python3 fstab_writer.py --yaml_file /path/file.yaml --dry_run
```

## Error Handling

- **Invalid YAML Format:** If the YAML file is not properly formatted or contains invalid keys, the script will exit with an error message.
- **Permission Issues:** The script requires root permissions to write to /etc/fstab and to back up the original fstab. Use sudo when necessary.

## Author
Ata Mahmoudi (@atamg)

## License
This project is licensed under the GNU General Public License v3.0 (GPL-3.0).
