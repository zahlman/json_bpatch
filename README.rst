::::::
1. About
::::::

``json_bpatch`` is a utility designed for patching binary files that have any kind of internal structure that relies on "pointer" values (i.e., integer values that in some way encode another location in the file). This could be a file that will be memory-mapped to a specific location, or a data structure in the static data section of an executable. The idea is that a JSON document is used to represent the structure of the data to be inserted, while raw chunks of binary data to write can be stored in auxiliary binary files (referred to by filename), or specified directly in hex or base64 dumps.

TODO: In the future, it will also be possible to use a JSON document to specify regions of the file to zero out (or fill with some other pattern), and/or "mark as free" (so that another patch can be written in that space).

::::::::::::::::::::::
2. Basic Usage: Applying a Patch
::::::::::::::::::::::

After installation, you can run the json_bpatch package as a script from the command line::

    python -m json_bpatch <name of file to patch> <name of JSON patch file>

In general, one or more additional options will need to be specified, because the patching routine makes no assumptions about what is allowed to be overwritten. The ``-l``, ``--limit`` option can be used to allow the file to be expanded up to a certain size; but this will not help if the patch mandates (see section 5) that certain things are written to specific locations. In order to indicate "free" locations, use the ``-f``, ``--free-input`` option to specify a JSON file listing those locations (see section 3). 

You may also want to use ``-F``, ``--free-output`` to specify an output file listing free space *after* applying the patch. (By default, the input freespace file will be overwritten, if provided; otherwise, no output file is written.) Similarly, the ``-o``, ``--output`` option allows specifying an output filename, rather than having the patcher overwrite the input file.

A "defaults" file, specified with ``-d``, ``--defaults``, may be required by some patches. It specifies default values for configuring the pointers, representing the target architecture, which can reduce redundancy in the main patch file.

Finally, the ``-r``, ``--roots`` option allows you to specify which "items" (see section 4) in the patch get written. The patcher will always write a *transitive closure* of items pointed to from the "roots"; that is, if something is written that includes a pointer to something else, "something else" is also always written. However, the "roots" option lets you specify items that are written even without being pointed to. By default, every patch item whose name starts with an underscore gets written.

The patcher will first attempt to determine where to write each patch item; if this is successful, it will then compute the byte values for each pointer and write everything. Otherwise, it will report that "Fitting failed", without modifying any files. Note that no attempt is made to conserve memory during this process.

TODO: In the future, the defaults file might also specify values for command line options, which could then be explicitly overridden at the command line. The pointer defaults might also get moved into the main patch file format.

::::::::::::::
3. The Freespace File
::::::::::::::

To indicate locations in the target file that are safe to overwrite, a simple JSON file is used. It should be formatted as a single JSON array, where each element is an array of start:end value pairs. Example::

    [[100, 200], [300, 400]]

This file would indicate that bytes 100 through 199 inclusive, and 300 through 399 inclusive, of the target may be safely overwritten.

:::::::::::::::::::::::::::::::::::::::
4. The Patch File: Basic Structure / How to Create a Patch
:::::::::::::::::::::::::::::::::::::::

The top level of the patch file is a JSON object, where the keys give names to the "patch items" stored in the values.

Each patch item is a JSON array, where each element is either a *Datum* (representing constant binary data) or a *Pointer* (representing bytes that reference another patch item, which places restrictions on where that item may be placed). When a patch item is written into the target file, each element's data will be written sequentially, with no gaps in between. Either the bytes represented by a Datum are written literally, or a fixed number of bytes is written representing a computed Pointer value.

A *Datum* is represented with a JSON string, formatted as follows:

* If the string begins with an ``@``, it is interpreted as the name of a file, whose contents will be read and used literally.

* If the string begins with an ``=``, it is interpreted as base-64 encoding of data.

* Otherwise, the string is interpreted as a hex dump. Spaces are required between the characters for each byte. Digits may be specified using 0-9, and either lowercase a-f or uppercase A-F. Single nybbles will be interpreted as setting the low-order nybble; ``"F 0 0"`` is the same as ``"0F 00 00"``.

There is no provision for including literal binary data in the JSON file. JSON is fundamentally a text format (mandating UTF-8 encoding), and in the era of Unicode, this is just too error-prone.

A *Pointer* is represented with a JSON object, with some or all of the following keys:

* ``"referent"``: (string) The name of the patch item that this Pointer points at.
* ``"bigendian"``: (boolean) Indicates byte order for the pointer value.
* ``"signed"``: (boolean) True if the value should be interpreted as signed; false otherwise.
* ``"size"``: (int) Number of bytes to use for this Pointer.
* ``"stride"``: (int) See below.
* ``"offset"``: (int) See below.
* ``"align"``: (int) Must be a positive power of 2. Pointer value is restricted to be a multiple of this.

In general, if a Pointer has a value ``V``, stride ``S`` and offset ``O``, it refers to a patch item located at offset ``V*S + O`` in the file. The ``align`` value restricts ``V``, not the computed location.

Each of these values must be provided either directly or via the defaults JSON file - there are no "program defaults". In addition, the ``referent`` may not be specified via the defaults.

A simple, complete example patch file might look like::

    {
        "_root": [
            {
                "referent": "payload", "bigendian": true, "signed": true,
                "size": 0, "stride": 1, "offset": 42, "align": 1
            }
        ],
        "payload": [
            "@data.bin",
            "=SGVsbG8sIFdvcmxkIQo=",
            "00 00 00"
        ]
    }

This patch will skip 42 bytes at the start of the file (see section 5 for how this works), and then write the contents of the auxiliary ``data.bin`` file, followed by ``Hello, World!`` (in 7-bit ASCII) and a line feed, then three zero bytes. It would need to be accompanied by ``data.bin``, as well as an appropriate freespace file.

TODO: In the future, "patch" files might also represent chunks of a file to zero out and/or mark as freespace (for example, to replace a set of "resources" in the file, it would make sense to first chase the pointers in the old data to indicate what's being removed, rather than hard-coding locations in the initial freespace file. (If such a patch duplicated data from the original, it could be used to make patching "reversible" - although this might be seen as inferior to XOR-based patching strategies.) The patch file might also include default values for pointers, as suggested in section 2.

Also, it would probably be a good idea to default ``align`` and ``stride`` to 1 even if not specified, and ignore certain missing parameters for zero-length pointers. :/

::::::::::::
5. Tips and Tricks
::::::::::::

Since Pointers can be any length, a zero-length Pointer can be used to mandate that a particular patch item is written to a specific location. (This is typically necessary somewhere along the line, so that the executable - or whatever is interpreting your binary file - will be able to find the newly written data.) Since they are zero length, nothing will be written into the file to represent them; and again since they are zero length, their value is always zero and thus they can only "point at" one specific location (i.e. the specified ``offset`` for the pointer). This in turn restricts the fitting algorithm to only place the referent at that location (and fail if the space there isn't free).

For organizational purposes, it is recommended to write patches with a single root item that contains all the zero-length pointers.

Through careful use of the "roots" feature, it is possible to store multiple independent patches in the same patch file.

If your patch uses a long hex or base64 dump, it can be broken up into several items for line-wrapping (although perhaps it would be better to use an external binary dump)::

    "loadsahex": [
        "00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F",
        "00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F",
        "00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F",
        "00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F",
        "00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F",
        "00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F"
    ]


The patch item ``loadsahex`` will be written as 96 consecutive bytes.

The ``stride`` parameter for Pointers is provided mainly for completeness. Theoretically, it allows for representing array indices; however, this is only helpful when the location of the array is known ahead of time (and can thus be specified via the ``offset``). In these cases it is probably better to hard-code a value, since you probably don't want to insert data as an arbitrary element of an existing array (although you *could* - if you're replacing multiple elements with multiple new values, and for some reason don't care about their order, but *do* require something to keep track of that order).

::::::::::::::::::::::::::
6. The Gory Details: Patching Strategy
::::::::::::::::::::::::::

When the patcher determines the location for writing a patch item, it is constrained by three factors:

* The length of the item (since every Datum is constant and Pointers have a predetermined size, this can be determined up front)

* The available freespace

* The *gamut* of Pointers which refer to the item

Basically, every Pointer that refers to a given patch item, must have some value it can represent, that translates to the location where the item is being written. This can easily be impossible, in which case fitting will fail. For example, no locations within the gamut of a Pointer are free (in particular, the single location specified by a zero-length pointer might not be usable), or two Pointers might be specified to the same item that have the same, nonzero stride and unaligned offsets::

    {
        "_root": {
            {"size": 0, "offset": 0, "referent": "first_pointer"}, 
            {"size": 0, "offset": 4, "referent": "second_pointer"}
        },
        "first_pointer": {"offset": 2, "stride": 4, "referent": "thing"},
        "second_pointer": {"offset": 0, "stride": 4, "referent": "thing"},
        "thing": "00 01 02 03"
    }

In this example, regardless of the default pointer settings, fitting will fail - even if writing ``first_pointer`` and ``second_pointer`` is possible, there is no location for ``thing`` that could possibly be represented by both Pointers.

Conceptually, fitting works according to the following strategy:

* For optimization purposes, a mapping is first created which stores (using Python ``range`` objects, or ``None`` to indicate "no restriction") a gamut of possible locations where each item could be written, computed as the intersection of the gamuts of all Pointers to each item. 

* First, the item with the least "freedom" in where it can be placed (fewest number of locations that will allow it to fit in free space and which are also within the precomputed gamut-intersection) is selected for a trial fitting.

* Recursively, we attempt to fit that item in the "first available" legal location, by seeing if all the remaining items can be fit into the remaining space (after marking the space that would be taken by the current item as not free). If this works (i.e. the recursion reaches a point where there are no items left to fit), we recursively report back that fitting was successful.

* If no fit is found for the other items, we try the next available location and make the recursive call again (a new freespace mapping is created each time). If no location works, we recursively report back that fitting failed.

Locations for a given patch item are tried in "round-robin" order: that is, first iterating over freespace chunks that are big enough to hold the item, trying to place the item at the "beginning" of each chunk (subject to pointer gamut restrictions), then cycling back around to the first chunk and trying the next legal location within it, etc. It is believed that in the general case, this should minimize the expected amount of work; however, it is also believed that in the real world, most patches will not pose a serious challenge to the fitting algorithm anyway.
