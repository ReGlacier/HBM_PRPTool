from PRP import PRPReader, PRPWriter
from enum import Enum
import argparse
import json


class ToolMode(Enum):
    Compile = 'compile'
    Decompile = 'decompile'

    def __str__(self):
        return self.value


def cli_compile(what: str, result: str):
    # TODO: Finish later)
    pass


def cli_decompile(what: str, result: str):
    prp_reader: PRPReader = PRPReader(what)
    prp_reader.parse()

    with open(result, "w") as result_file:
        result_file.write(json.dumps({
            'definitions': [x.__dict__() for x in prp_reader.definitions],
            'instructions': [x.__dict__() for x in prp_reader.instructions]
        }, indent=4, sort_keys=False))


def cli_main():
    cli_parser = argparse.ArgumentParser(description='Compiler or decompile PRP file format from Glacier 1 engine')
    cli_parser.add_argument('source', help='Source path (PRP or JSON)')
    cli_parser.add_argument('destination', help='Destination path (PRP or JSON)')
    cli_parser.add_argument('mode', help='Specify mode: decompile/compile', type=ToolMode, choices=list(ToolMode))
    cli_args = cli_parser.parse_args()

    cli_mode: ToolMode = cli_args.mode
    cli_src: str = cli_args.source
    cli_dst: str = cli_args.destination

    if cli_mode == ToolMode.Compile:
        cli_compile(cli_src, cli_dst)
    elif cli_mode == ToolMode.Decompile:
        cli_decompile(cli_src, cli_dst)
    else:
        raise NotImplementedError("Not implemented mode")


if __name__ == "__main__":
    cli_main()
