picksender.py
=============

A simple SeisComP 3 Python script for importing picks from a
non-SeisComP picker, e.g. an existing legacy picker.

This is only an example, which simply reads "picks" produced by a
dummy picker from standard input and sends it to a SeisComP
messaging. Option --test enables test mode.

In a real-world-interface, however, you likely have other, different
information produced by the legacy picker; the parse() function will
have to be adapted accordingly.
