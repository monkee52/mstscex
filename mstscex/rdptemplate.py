"""RDP template file handling."""

import subprocess
import time
from typing import Iterable, TextIO

from .rdpbuilder import generate_rdp
from .util import TSPortalNameGenerator, log


class RdpTemplate:
    """Generator for an RDP file."""

    _rdp_file: str

    _name_gen: TSPortalNameGenerator

    def __init__(
        self,
        template: str | TextIO,
        args: Iterable[str],
        sign_with: tuple[str, str] | None = None,
    ):
        """Create a file generator for an RDP file."""
        self._name_gen = TSPortalNameGenerator()

        self._rdp_file = generate_rdp(
            template, args, pre_sign_hook=None, sign_with=sign_with
        )

    def writeto(self, file: TextIO) -> int:
        """Write the generated file to an IO stream."""
        return file.write(self._rdp_file)

    def launch(self, wait: bool = False) -> None:
        """Launch the generated file."""
        try:
            # write the rdp file
            filename = self._name_gen.rdp

            log("INFO", "Generated RDP file:", filename)

            with open(filename, "w", encoding="utf-16le") as f:
                f.write("\ufeff")

                self.writeto(f)

            log("INFO", "Launching RDP file")

            # launch - mstsc will delete the file
            mstsc_proc = subprocess.Popen(
                ["mstsc.exe", "/Web", "/WebFileName:" + filename]
            )

            time.sleep(1)

            if wait:
                mstsc_proc.wait()
        finally:
            self._name_gen.cleanup()
