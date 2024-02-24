"""Entry point for utility."""

import argparse
import os
import sys

from . import RdpTemplate


def main() -> None:
    """Run main entry point for mstscex utilitity."""
    parser = argparse.ArgumentParser("mstscex")

    parser.add_argument("templatefile", metavar="<file>", help="Template file")
    parser.add_argument(
        "-o",
        "--output",
        metavar="<destination>",
        help="Generated file destination",
    )
    parser.add_argument(
        "rest", metavar="[...arguments]", nargs=argparse.REMAINDER
    )

    parser.add_argument(
        "-s",
        "--sign",
        metavar=("<cert>", "<key>"),
        help="Sign the generated file",
        nargs=2,
    )
    parser.add_argument(
        "-l", "--launch", help="Launch generated RDP file", action="store_true"
    )

    args = parser.parse_args()

    # determine input file
    input_filename = args.templatefile
    input_file = None

    if input_filename == "-":
        input_file = os.fdopen(sys.stdin.fileno(), "r", closefd=False)
    else:
        input_file = open(input_filename, "r")

    template = RdpTemplate(input_file, args.rest, args.sign)

    output_filename = args.output
    output_file = None

    if output_filename == "-":
        output_file = os.fdopen(sys.stdout.fileno(), "w", closefd=False)
    elif output_filename:
        output_file = open(output_filename, "w")

    if output_file:
        with output_file:
            template.writeto(output_file)

    if not output_file or args.launch:
        template.launch()


if __name__ == "__main__":
    main()
