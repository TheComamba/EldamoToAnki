import os
import sys

filename = sys.argv[1]

new_data_directory = "output/"
new_data_file_path = os.path.join(new_data_directory, filename)
old_data_directory = "anki_exports/"
old_data_file_path = os.path.join(old_data_directory, filename)

if not os.path.exists(new_data_directory):
    print("Data for ", filename, " was not found.")
    print("You need to run the generate.py script first.")
    sys.exit(1)

if not os.path.exists(old_data_file_path):
    print("Anki Export for ", filename, " was not found.")
    print("Go to the Ank app and klick on 'Browse'.")
    print("Then click on 'Notes' -> 'Export Notes'.")
    print("Choose the 'Notes in Plain Text' option, tick the 'Include unique identifier' checkbox, and click 'Export'.")
    print("Save the file to ", old_data_file_path)
    sys.exit(1)

new_data = []
with open(new_data_file_path, "r") as new_data_file:
    for line in new_data_file:
        front, back = line.strip().split("|")
        new_data.append((front, back))

preamble = []
old_data = []
with open(old_data_file_path, "r") as old_data_file:
    for line in old_data_file:
        if line.startswith("#"):
            preamble.append(line)
        else:
            guid, front, back = line.strip().split("\t")
            old_data.append((guid, front, back))

with open(old_data_file_path, "w") as old_data_file:
    for line in preamble:
        old_data_file.write(line)
    
    for guid, front, back in old_data:
        old_data_file.write(f"{guid}\t{front}\t{back}\t\n")
