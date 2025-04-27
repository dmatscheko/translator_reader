import sys


def process_file(input_file):
    # Read all lines from the input file
    with open(input_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Filter valid lines and print invalid lines to stderr
    valid_lines = []
    for line in lines:
        stripped_line = line.strip()
        parts = stripped_line.split("\t")
        if len(parts) == 2:
            valid_lines.append(stripped_line)
        else:
            print(stripped_line, file=sys.stderr)

    # Define the key function for sorting
    def key_func(line):
        original, translation = line.strip().split("\t")
        word_count = len(translation.split())
        char_count = len(translation)
        return (original, word_count, char_count)

    # Sort the valid lines using the key function
    sorted_lines = sorted(valid_lines, key=key_func)

    # Remove duplicate lines while preserving sorted order and print unique lines
    prev_line = None
    for line in sorted_lines:
        if line != prev_line:
            print(line)
            prev_line = line


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python sort.py input_file", file=sys.stderr)
        sys.exit(1)

    input_file = sys.argv[1]
    process_file(input_file)
