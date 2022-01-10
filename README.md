<p align="center">
	<img width="400" height="400" src=".github/logo.png">
</p>

PRP Tool
=========

PRP Tool is a utility that allows to you edit properties of entities on the level in "Hitman Blood Money".

More details about format [here](https://github.com/ReGlacier/ReHitmanTools/issues/3#issuecomment-769404149)

Usage
-----

 Decompile PRP to JSON:

```python prptool.py SomeLevel.PRP SomeLevel.JSON decompile```

 Compile JSON to PRP back:

```python prptool.py SomeLevel.JSON SomeLevel.PRP compile```

Options:
--------

 * source - path to source file (PRP for 'decompile' option and JSON for 'compile')
 * destination - path to result file
 * mode - what shall we do: **compile** or **decompile** file
