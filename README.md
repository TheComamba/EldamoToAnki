# Eldamo To Anki

Takes the marvellous wordlist from [eldamo.org][eldamo] and converts it into input digestable by Anki.

# Usage

The decks for [Neo-Quenya][neo-quenya] and [Neo-Sindarin][neo-sindarin] based on the lists in this repository can be found on Anki (unless they get deleted because they do not receive enough downloads).

Some lists can be found in the [`output`][output] folder of this repository. They are ready to be imported. They do not include any names or phrases. The lists are:
- Adunaic (ca. 180 cards)
- Black Speech (ca. 40 cards)
- Khuzdul (ca. 40 cards)
- Noldorin (ca. 1300 cards)
- Quenya (ca. 2200 cards)
- Quenya plus Neo-Quenya (ca. 4800 cards)
- Sindarin (ca. 1200 cards)
- Sindarin plus Neo-Sindarin (ca. 2700 cards)
- Telerin (ca. 200 words)

Thanks to the very structured [input data][eldamo-data] curated by [Paul Strack][pfstrack], it is extremely easy to add more languages to that list. Just drop me an issue and I'll do that for you.

If you want to curate your own version of a list you can use the [`generate.py`][generate.py] script to do that. It is called from the command line via:
```
python3 generate.py <language>
```
Depending on your Python install, the first command may be `py` or `python` instead.

For the `<language>` argument, type the name of the language, or its id (usually its first letter).

You can add optional arguments:
- `--neo-words`: Include words invented by fans rather than Tolkien.
- `--individual-names`: Include names of individuals and places.
- `--collective-names`: Include names for collective people.
- `--proper-names`: Include proper names.
- `--phrases`: Include phrases.
- `--check-for-updates`: Forces a re-download of the Eldamo database.

You can check out the [`generate_all.sh`][generate_all.sh] script for example usages.

# Acknowledgments

Almost all the credit here goes to [Paul Strack][pfstrack], maintainer of the [Eldamo website][eldamo] and [database][eldamo-data]. They gathered all canonical Tolkienian words in one place, collected thousands of fan-made extensions, and organise it all in the structured xml format. Finding this database made writing this script pure bliss.

[eldamo]: https://eldamo.org/
[eldamo-data]: https://github.com/pfstrack/eldamo/tree/master/src/data
[pfstrack]: https://github.com/pfstrack
[generate.py]: https://github.com/TheComamba/EldamoToAnki/blob/main/generate.py
[generate_all.sh]: https://github.com/TheComamba/EldamoToAnki/blob/main/generate_all.sh
[output]: https://github.com/TheComamba/EldamoToAnki/tree/main/output
[neo-quenya]: https://ankiweb.net/shared/info/1556726257
[neo-sindarin]: https://ankiweb.net/shared/info/1398531602?cb=1717323372536
