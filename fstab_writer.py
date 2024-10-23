#!/usr/bin/env python3

def yaml_to_fstab(yaml_file, fstab_file):
    print(f"YAML file is: {yaml_file}")
    print(f"fstab file is: {fstab_file}")


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

