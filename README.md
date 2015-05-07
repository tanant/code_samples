code_samples 
===========

For anyone who is curious as to see what I get up to, how I think in python, and how I approach problems. It's very much a counterpart to my reel (http://vimeo.com/tanantish/reel2015) since I'd like to present myself as a technical artist.

As at _7/5/2015_, included in this stack is:

**FrameCatcher** : Nuke/C++/Python plugin and associated glue code (compiles against Nuke 7, 8) to intercept tree calls and work out what frames are being used downstream.

**maya_python_UDIM** - a snippet of code posted on the python_inside_maya mailing list demonstrating how to analyse a mesh's UVs and work out what UDIM tiles are occupied. Done as a timing/approach test, so equivalent functions written against PyMEL, maya.cmds and the Python API 1.0

**FileReferenceBrowser** - Maya/PySide/QT helper UI to assist in packaging maya scene files for shipping to vendor

**fury_shotbrowser** - Maya/PySide/QT simple artist shot interface to open up projects, set environments, etc

**3DE_lensdistortion** - Nuke/TCL to silently migrate old-style TDE4 lensdistortion nodes to the new LD\_3DE4\_* class.

**fury\_slate\_search** - Nuke/PySide/QT simple python panel for integration into Nuke to hook into our offline, allowing artists to bring in proxy slates for bash comps

**convert\_to\_jpg** - standalone converter functions for artist self-service DPX conversions.

**reference_data** - Python classes encapsulating our reference data 'capsule' concept (a standardized asset container) and output packages

**scripts/compare\_edl\_to\_csv** - Python standalone support for Editorial, letting them compare a CSV dump from Filemaker to an Avid EDL to highlight issues.

**scripts/di\_matte\_check** - Python standalone support for DI, feeding in dumps from Baselight to detect single-character errors en-masse (e.g. two right eyes being used) and to highlight where versioning issues in place to help DI automate tasks.