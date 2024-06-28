# Eldamo To Anki

Takes the marvellous wordlist from [eldamo.org][eldamo] and converts it into input digestable by Anki.

# Usage

The decks for [Neo-Quenya][neo-quenya] and [Neo-Sindarin][neo-sindarin] based on the lists in this repository can be found on Anki (unless they get deleted because they do not receive enough downloads).

Some lists can be found in the [`output`][output] folder of this repository. They are ready to be imported. They do not include any names or phrases. The Neo-Quenya and Neo-Sindarin lists do not include deprecated words.

The lists are:
- Adunaic (ca. 180 cards)
- Black Speech (ca. 40 cards)
- Khuzdul (ca. 40 cards)
- Noldorin (ca. 1300 cards)
- Quenya (ca. 2200 cards)
- Neo-Quenya (ca. 4400 cards)
- Sindarin (ca. 1200 cards)
- Neo-Sindarin (ca. 2500 cards)
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
- `--include-deprecated`: Include words that Paul Strack has marked as deprecated in neo lists.
- `--check-for-updates`: Forces a re-download of the Eldamo database.

You can check out the [`generate_all.sh`][generate_all.sh] script for example usages.

# Design Decisions

In the simplest case, the generated words are given without any further adjustments for the Tolkienian language. The English translation lists the part of speech:

> corto|circle (n)
>
> costaima|debatable (adj)

If a word is listed with a dedicated word stem, that stem is appended in parentheses:

> oron (oront-)|mountain (n)

Some words have several translation. The script tries to make the Tolkienian side unique, first by checking if the part of speech will do that:

> cuiva (adj)|awake (adj)
>
> cuiva (n)|animal (n)

If this does not suffice to make the words unique, and if a category is provided for that word, then the latter is used instead:

> au (Mind and Thought)|if only (adv)
>
> au (Spatial Relations)|away, off, not here (of position) (adv)

Finally, if this doesn't help as well, the translations are merged into one:

> hyarna|(1) compact, [ᴹQ.] compressed; (2) southern (adj)

This last step is also true for English words with several Tolkienian translations:

> (1) artatúrë; (2) ohérë|government (n)

Some Tolkienian words are listed with variant versions. The script recognises this and treats them as a single word, so the inputs `lá` and `(a)lá` are listed as one:

> (a)lá|yes (interj)

Some English translations are prepended with the marker `*`, `?` or `⚠️`, denoting some uncertainty. These markers are retained, unless the word is listed more than once, and at least one translation does not have this marker:

> canya-|?to command (vb)

Several words are provided with additional information on the spelling in Tengwar, if it deviates from the default. This information is appended in brackets:

> isilmë [þ]|moonlight (n)
>
> nairë [ñ-]|space (as a physical dimension) (n)

## Special Tengwar Treatment for Quenya

The list also contains some archaïc words which still incorporate the old spelling. To reduce duplicated information, the script recognises these and derives the Tengwar annotations. Since this treatment needs to happen on a per language and per sound basis, it is currently implemented only for my personal use-case (Neo-)Quenya. The relevant linguistic information is taken from the [Eldamo Quenya course](https://eldamo.org/intro-quenya/eldamo-intro-quenya-03.html#c3-1-2).

Any `þ` is replaced with `s`, so `minaþurië` becomes:

> minasurië [þ]|enquiry (n)

Initial `ñ-` is replaced with `n-`, turning `ñwalmë` into:

> nwalmë [ñ-]|torment (n)

The rules for `w` [are more complicated](https://eldamo.org/content/words/word-3625908403.html). Any `w` following a consonant or the diphthongs `ai` or `oi` is retained, any other `w` is replaced with `v`.

Because the archaïc `w`-origin of `v` [is *not* represented in Tengwar](https://eldamo.org/intro-quenya/eldamo-intro-quenya-03.html#c3-1-2-2), it is also *not* included in the output:

> artanwa|award (n)
>
> maiwë|gull (n)
>
> oiwa|glossy (adj)
>
> lassevinta|leaf fall, autumn, *(lit.) leaf blowing (n)
>
> vilya|air, sky (n)

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
