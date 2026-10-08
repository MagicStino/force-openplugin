# FIND filtering correction — unreleased

In 3.9.1.4, typing edited the active search immediately. Combined with a
category or Installed/Updates filter, this could hide all catalog cards.
Workaround: FIND → Show all, then CATALOG → DISCOVER → All.

The corrected source keeps draft text separate. Filter catalog applies it,
trims surrounding whitespace and resets to Discover/All. Show all clears
both draft and active search. Searches match partial, case-insensitive names,
IDs, authors, tags, kind and descriptions: `800` matches `JV-800 Synth`.
No-match guidance points back to Show all.

Native regression tests cover draft isolation, partial numeric titles,
case-insensitive matching, description fragments, applying and clearing,
and category/tab reset. Host sanitizer tests pass. The published 3.9.1.4
IMG does not contain this correction; device testing is still required.
