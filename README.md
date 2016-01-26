4ch-to-mw
=====================
This is a crappy-ass python tool that can be used to recompile a 4chan thread (or sup/tg/ archive) to a mediawiki dump.

Why? Because...well. Threads after 5 on http://wiki.magicalgirlnoir.com are hard to read. This was originally coded in bash. Thank god nobody saw that mess.

Read the header for usage, for now. I'll make proper console syntax sometime soon. For now though; it works.

It can even only pull relevant threads based on nametag (Or tripcode. Or `$(echo nametag|sed 's|t|f|')`...not that I like that term.)

Example usage of filtering functionality in header. 

You need:
 * python2
 * lxml

An example of output is provided in the folder examples/mgn-1. What that is should be predictable.

Licensing? Bah. If you're really a legal freak, then WTFPL. To summarize, I don't care.
