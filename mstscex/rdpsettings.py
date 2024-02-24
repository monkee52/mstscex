"""RDP settings and related."""

from base64 import b64encode
from collections.abc import Iterable
import os
from struct import pack
import textwrap
from types import MappingProxyType

from .util import log, x509_sign


class RdpLine:
    """Configuration line for an RDP file."""

    _name: str
    _type: str
    _value: str | int

    def __init__(self, name: str, typ: str, val: str | int):
        """Create a configuration line."""
        self._name = name
        self._type = typ.lower()

        if self.type == "i":
            val = int(val)
        elif self.type != "s":
            raise TypeError("Unrecognised type:", self.type)

        self.value = val

    @property
    def name(self) -> str:
        """Get the name of the config item."""
        return self._name

    @property
    def type(self) -> str:
        """Get the type of the config item."""
        return self._type

    @property
    def value(self) -> str | int:
        """Get the value of the config line."""
        return self._value

    @value.setter
    def value(self, val: str | int) -> None:
        """Set the value of the config line."""
        if self.type == "i":
            val = int(val)

        self._value = val

    def __str__(self) -> str:
        """Return the RDP file representation of this config line."""
        return "%s:%s:%s" % (self.name, self.type, str(self.value))


class RdpSettings:
    """Collection of RDP settings."""

    FULL_ADDRESS = "full address"
    ALTERNATE_FULL_ADDRESS = "alternate full address"

    SIGNATURE_SCOPE = "signscope"
    SIGNATURE = "signature"

    REMOTE_APPLICATION_MODE = "remoteapplicationmode"

    SECURE_SETTINGS = MappingProxyType(
        {
            "full address": "Full Address",
            "alternate full address": "Alternate Full Address",
            "pcb": "PCB",
            "use redirection server name": "Use Redirection Server Name",
            "server port": "Server Port",
            "negotiate security layer": "Negotiate Security Layer",
            "enablecredsspsupport": "EnableCredSspSupport",
            "disableconnectionsharing": "DisableConnectionSharing",
            "autoreconnection enabled": "AutoReconnection Enabled",
            "gatewayhostname": "GatewayHostname",
            "gatewayusagemethod": "GatewayUsageMethod",
            "gatewayprofileusagemethod": "GatewayProfileUsageMethod",
            "gatewaycredentialssource": "GatewayCredentialsSource",
            "support url": "Support URL",
            "promptcredentialonce": "PromptCredentialOnce",
            "require pre-authentication": "Require pre-authentication",
            "pre-authentication server address": "Pre-authentication "
            "server address",
            "alternate shell": "Alternate Shell",
            "shell working directory": "Shell Working Directory",
            "remoteapplicationprogram": "RemoteApplicationProgram",
            "remoteapplicationexpandworkingdir": "RemoteApplication"
            "ExpandWorkingdir",
            "remoteapplicationmode": "RemoteApplicationMode",
            "remoteapplicationguid": "RemoteApplicationGuid",
            "remoteapplicationname": "RemoteApplicationName",
            "remoteapplicationicon": "RemoteApplicationIcon",
            "remoteapplicationfile": "RemoteApplicationFile",
            "remoteapplicationfileextensions": "RemoteApplication"
            "FileExtensions",
            "remoteapplicationcmdline": "RemoteApplicationCmdLine",
            "remoteapplicationexpandcmdline": "RemoteApplicationExpandCmdLine",
            "prompt for credentials": "Prompt For Credentials",
            "authentication level": "Authentication Level",
            "audiomode": "AudioMode",
            "redirectdrives": "RedirectDrives",
            "redirectprinters": "RedirectPrinters",
            "redirectcomports": "RedirectCOMPorts",
            "redirectsmartcards": "RedirectSmartCards",
            "redirectposdevices": "RedirectPOSDevices",
            "redirectclipboard": "RedirectClipboard",
            "devicestoredirect": "DevicesToRedirect",
            "drivestoredirect": "DrivesToRedirect",
            "loadbalanceinfo": "LoadBalanceInfo",
            "redirectdirectx": "RedirectDirectX",
            "rdgiskdcproxy": "RDGIsKDCProxy",
            "kdcproxyname": "KDCProxyName",
            "eventloguploadaddress": "EventLogUploadAddress",
        }
    )

    _settings: dict[str, RdpLine]
    _lines: list[str | RdpLine | None]

    def __init__(self) -> None:
        """Create a collection of RDP settings."""
        self.clear()

    def clear(self) -> None:
        """Remove all settings."""
        self._settings = {}
        self._lines = []

    def _add_line(self, raw: str = "") -> None:
        if raw is None:
            raw = ""

        self._lines.append(raw)

    def parse_line(self, orig_line: str | None) -> bool:
        """Add a string as an RDP setting."""
        if orig_line is None:
            return False

        line = orig_line.strip()

        if line == "":
            self._add_line(orig_line)

            return True

        try:
            c_pos = line.index(":")
            c2_pos = line.index(":", c_pos + 1)

            name = line[:c_pos]
            typ = line[c_pos + 1 : c2_pos]
            val = line[c2_pos + 1 :]

            self.set(name, val, typ)

            return True
        except ValueError:
            log("WARNING", "Unable to parse line:", line)

        return False

    def set(
        self,
        name: str,
        val: str | int | None,
        typ: str = "s",
    ) -> None:
        """Set a configuration item."""
        if val is None:
            self.remove(name)

            return

        name_l = name.lower()

        if typ is None:
            typ = "s"

        is_new = True

        if name_l in self._settings:
            typ = self._settings[name_l].type
            is_new = False

        prop = RdpLine(name, typ, val)

        self._settings[name_l] = prop

        if is_new:
            self._lines.append(prop)

        # remove signature
        if (
            name_l in self.SECURE_SETTINGS
            and name_l != self.SIGNATURE_SCOPE
            and name_l != self.SIGNATURE
        ):
            del self[self.SIGNATURE_SCOPE]
            del self[self.SIGNATURE]

    def __setitem__(self, key: str, val: str | int | None) -> None:
        """Set a configuration item."""
        self.set(key, val)

    def get(self, name: str) -> str | int | None:
        """Get a configuration item."""
        try:
            return self._settings[name.lower()].value
        except KeyError:
            return None

    def __getitem__(self, key: str) -> str | int | None:
        """Get a configuration item."""
        return self.get(key)

    def __contains__(self, key: str) -> bool:
        """Get whether a config item has been set."""
        return key.lower() in self._settings

    def remove(self, key: str) -> None:
        """Remove a configuration item."""
        # remove setting
        try:
            del self._settings[key]
        except KeyError:
            pass

        # remove line position
        try:
            self._lines.remove(key)
        except ValueError:
            pass

    def __delitem__(self, key: str) -> None:
        """Remove a configuration item."""
        self.remove(key)

    @property
    def lines(self) -> Iterable[str]:
        """Get all configuration items as strings."""
        for line in self._lines:
            yield str(line)

        # end with blank line :)
        yield ""

    def __iter__(self) -> Iterable[str]:
        """Get all configuration items as strings."""
        return self.lines

    def __str__(self) -> str:
        """Get all configuration items as a complete string."""
        return os.linesep.join(self.lines)

    @property
    def signed(self) -> bool:
        """Get whether the RDP file is signed."""
        return self.SIGNATURE_SCOPE in self and self.SIGNATURE in self

    @property
    def full_address(self) -> str:
        """Get the address that will be used to connect."""
        ret = self[self.FULL_ADDRESS]

        if ret is None:
            return ""

        return str(ret)

    @full_address.setter
    def full_address(self, val: str) -> None:
        """Set the address that will be used to connect."""
        self[self.FULL_ADDRESS] = val

    @property
    def is_remote_app(self) -> bool:
        """Get whether this file uses RemoteApp."""
        return self[self.REMOTE_APPLICATION_MODE] == 1

    def sign(self, cert: bytes, key: bytes) -> None:
        """Sign this collection of settings."""
        # prevent hacks via alternate full address
        if self[self.ALTERNATE_FULL_ADDRESS] is None:
            if self[self.FULL_ADDRESS] is not None:
                self._add_line()

                self[self.ALTERNATE_FULL_ADDRESS] = self[self.FULL_ADDRESS]

        sign_settings = []
        sign_names = []

        for name, secure_name in self.SECURE_SETTINGS.items():
            if name in self:
                sign_settings.append(self._settings[name])
                sign_names.append(secure_name)

        scope = ",".join(sign_names)

        log("INFO", "Signature scope:", ", ".join(sign_names))

        blob = (
            "\r\n".join(str(line) for line in sign_settings)
            + "\r\nsignscope:s:"
            + scope
            + "\r\n\0"
        ).encode("UTF-16LE")

        blob_sig = x509_sign(cert, key, blob)

        sig = b""
        sig += pack("<III", 0x00010001, 0x00000001, len(blob_sig))
        sig += blob_sig

        # reset line numbers
        del self[self.SIGNATURE_SCOPE]
        del self[self.SIGNATURE]

        self._add_line()

        # set signature
        self[self.SIGNATURE_SCOPE] = scope
        self[self.SIGNATURE] = "  ".join(
            textwrap.wrap(b64encode(sig).decode("ascii"), 64)
        )
