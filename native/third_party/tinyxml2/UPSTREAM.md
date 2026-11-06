# TinyXML2

Vendored from https://github.com/leethomason/tinyxml2/tree/10.0.0
Files: tinyxml2.cpp, tinyxml2.h, LICENSE.txt. Version 10.0.0.
Used by the standalone skin-location settings helper. See LICENSE.txt.

OpenPlugin patch: XMLPrinter emits numeric character references for LF, CR and tab inside attributes. This preserves embedded preference XML when re-read by standards-compliant XML parsers. Text-node serialization is unchanged. Covered by the skin registration and locations helper regression tests.
