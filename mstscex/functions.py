"""Utilities used by templates."""

from collections.abc import Iterable
import re
import subprocess
from typing import Any, Callable, Generator

from .util import log


def cmd_regex(
    cmd: str | list[str], regex: bytes, encoding: str = "utf-8"
) -> Callable[[], Iterable[str]]:
    """Run a command and get part of output.

    Runs a command, and yield each string matched by a regex from the
    command's stdout.
    """
    comp_regex = re.compile(regex, re.IGNORECASE)

    def fn() -> Generator[str, None, None]:
        try:
            lines = subprocess.check_output(
                cmd, creationflags=0x00000008
            ).splitlines()

            for line in lines:
                if (matches := comp_regex.match(line)) is not None:
                    yield matches.group(1).decode(encoding).strip()
        except subprocess.CalledProcessError:
            pass

    return fn


get_connected_wifi: Callable[[], Iterable[str]] = cmd_regex(
    ["netsh", "wlan", "show", "interfaces"], rb"^\s*SSID\s*:\s*(.+?)\s*$"
)
get_connected_vpn: Callable[[], Iterable[str]] = cmd_regex(
    ["ipconfig"], rb"^\s*(?:PPP)\s+adapter\s+(.+?)\s*:\s*$"
)


def contains(items: Iterable[Any], *args: Any) -> bool:
    """Determine if items contains any of the remaining arguments."""
    for item in items:
        for item2 in args:
            if item2 == item:
                return True

    return False


def can_ping(host: str) -> bool:
    """Return whether a host is reachable."""
    continue_log = log("INFO", f"Checking ping to {host}: ", end="")

    result = (
        subprocess.call(
            ["ping", "-n", "1", host],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        == 0
    )

    continue_log("success" if result else "fail", end=None)

    return result


def wifi_is(*opts: str) -> bool:
    """Get whether the user is connected to any SSID."""
    log("INFO", f"Checking Wi-Fi connection is {', '.join(opts)}")
    log(
        "INFO",
        lambda: "Connected Wi-Fi:"
        + "\r\n".join(f"\t{x}" for x in get_connected_wifi()),
    )

    return contains(get_connected_wifi(), *opts)


def vpn_is(*opts: str) -> bool:
    """Get whether the user is connected to any VPN."""
    log("INFO", f"Checking VPN connection is {', '.join(opts)}")
    log(
        "INFO",
        lambda: "Connected VPN:"
        + "\r\n".join(f"\t{x}" for x in get_connected_vpn()),
    )

    return contains(get_connected_vpn(), *opts)
