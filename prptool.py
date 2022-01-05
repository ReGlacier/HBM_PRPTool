from PRP import PRPReader, PRPWriter
from PRP import PRPStructureError, PRPBadDefinitionError, PRPBadInstructionError
from PRP import PRPDefinition, PRPInstruction, PRPDefinitionType, PRPOpCode

from enum import Enum
import argparse
import logging
import json
import sys


class ToolMode(Enum):
    Compile = 'compile'
    Decompile = 'decompile'

    def __str__(self):
        return self.value


def cli_compile(what: str, result: str):
    with open(what, "r") as source_file:
        json_data = json.load(source_file)
        if 'is_raw' in json_data and 'flags' in json_data and 'definitions' in json_data and 'properties' in json_data:
            prp_is_raw: bool = json_data['is_raw']
            prp_flags: int = json_data['flags']
            prp_definitions: [PRPDefinition] = []
            prp_properties: [PRPInstruction] = []
            prp_unk0x13 = 0

            for json_definition in json_data['definitions']:
                prp_definitions.append(PRPDefinition.from_json(json_definition))

            for json_property in json_data['properties']:
                prp_properties.append(PRPInstruction.from_json(json_property))

            prp_writer: PRPWriter = PRPWriter(result)
            prp_writer.write(prp_flags, prp_definitions, prp_properties, prp_is_raw, prp_unk0x13)
            logging.info(f"PRP file {what} was compiled to file {result} successfully!")
        else:
            logging.error(f"Failed to prepare file {what} because it's invalid JSON representation of PRP")


def cli_decompile(what: str, result: str):
    prp_reader: PRPReader = PRPReader(what)
    try:
        prp_reader.parse()

        with open(result, "w") as result_file:
            result_file.write(json.dumps({
                'is_raw': prp_reader.is_raw,
                'flags': prp_reader.flags,
                'definitions': [x.__dict__() for x in prp_reader.definitions],
                'properties': [x.__dict__() for x in prp_reader.instructions]
            }, indent=4, sort_keys=False))

        logging.info(f"PRP file {what} was decompiled to file {result} successfully!")
    except PRPStructureError as structure_error:
        logging.error(f"Bad structure of PRP file {what}. Reason: {structure_error}")
    except PRPBadDefinitionError as definition_error:
        logging.error(f"Bad z-def structure of PRP file {what}. Reason: {definition_error}")



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
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler()
        ]
    )
    cli_main()
