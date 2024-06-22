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

deleted_cards = []
for i, (guid, front, back) in enumerate(old_data):
    wasFound = False
    for new_front, new_back in new_data:
        isSameFront = front == new_front
        isSameBack = back == new_back
        if isSameFront and isSameBack:
            wasFound = True
            break
        if isSameFront and not isSameBack:
            old_data[i] = (guid, front, new_back)
            wasFound = True
            break
        if not isSameFront and isSameBack:
            old_data[i] = (guid, new_front, back)
            wasFound = True
            break
    if not wasFound:
        deleted_cards.append((guid, front, back))

if len(deleted_cards) > 0:
    print()
    print("The following outdated cards need to be deleted manually:")
for guid, front, back in deleted_cards:
    print(guid, "|", front, "|", back)
    old_data.remove((guid, front, back))

new_cards = []
for new_front, new_back in new_data:
    is_new = True
    for guid, front, back in old_data:
        isSameFront = front == new_front
        isSameBack = back == new_back
        if isSameFront and isSameBack:
            is_new = False
            break
    if is_new:
        new_cards.append((new_front, new_back))

if len(new_cards) > 0:
    print()
    print("The following cards need to be added manually:")
for front, back in new_cards:
    print("|", front, "|", back)

with open(old_data_file_path, "w") as old_data_file:
    for line in preamble:
        old_data_file.write(line)
    
    for guid, front, back in old_data:
        old_data_file.write(f"{guid}\t{front}\t{back}\t\n")

print()
print("Finished updating.")
print("When importing the file, make very sure to update front and back, not front and tags!")
