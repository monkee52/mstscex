"""Signed RDP file builder."""

import os
from typing import Any, Callable, TextIO, cast

import jinja2

from .bufferedlineiterator import BufferedLineIterator
from .functions import can_ping, contains, vpn_is, wifi_is
from .rdpsettings import RdpSettings
from .util import log


class RdpBuilder:
    """RDP file builder."""

    sign_with: tuple[bytes, bytes] | None

    _settings: RdpSettings
    _environment: jinja2.Environment
    _template: jinja2.Template
    _pre_sign_hook: Callable[["RdpBuilder", Any], None] | None

    def __init__(
        self,
        template: str | TextIO,
        template_name: str | None = None,
        pre_sign_hook: Callable[["RdpBuilder", Any], None] | None = None,
    ):
        """Create an RDP file builder."""
        self.sign_with = None

        self._settings = RdpSettings()

        if not isinstance(template, str):
            if template_name is None:
                template_name = template.name

            data = template.read()
        else:
            if template_name is None:
                template_name = template

            with open(template_name, "r") as f:
                data = f.read()

        loader = jinja2.FileSystemLoader(
            [
                os.path.dirname(cast(str, template_name)),
                "./",
                os.path.dirname(__file__),
            ]
        )
        environment = jinja2.Environment(autoescape=False, loader=loader)

        environment.globals.update(
            **{
                "contains": contains,
                "wifi_is": wifi_is,
                "vpn_is": vpn_is,
                "can_ping": can_ping,
                "get_setting": self.settings.get,
                "sign": self._delayed_sign_template,
            }
        )

        self._environment = environment

        self._template = environment.from_string(data)

        self._pre_sign_hook = pre_sign_hook

    def generate(self, args: Any) -> str:
        """Use template to generate a file with supplied arguments."""
        line_buffer = BufferedLineIterator()

        for part in self.template.generate(args=args):
            line_buffer.push(part)

            for line in line_buffer:
                self.settings.parse_line(line)

        # handle last line
        print(line_buffer.buffer)
        self.settings.parse_line(line_buffer.buffer)

        # pre sign hook
        if callable(self._pre_sign_hook):
            self._pre_sign_hook(self, args)

        # sign if applicable
        if self.sign_with is not None:
            try:
                log("INFO", "Signing RDP file")

                self.settings.sign(*self.sign_with)
            except Exception as e:
                log("WARNING", "Signing failed:", e)

        result = str(self.settings)

        log("DEBUG", "Generated file:")
        log("DEBUG", result)

        return result

    @property
    def settings(self) -> RdpSettings:
        """Get raw RDP settings."""
        return self._settings

    @property
    def environment(self) -> jinja2.Environment:
        """Get the Jinja environment."""
        return self._environment

    @property
    def loader(self) -> jinja2.BaseLoader:
        """Get the Jinja loader."""
        return self.environment.loader

    @property
    def template(self) -> jinja2.Template:
        """Get the Jinja template."""
        return self._template

    def _delayed_sign_template(self, cert_name: str, key_name: str) -> str:
        # store signature settings for delayed signing
        cert_tmpl = self.loader.get_source(self.environment, cert_name)

        log("INFO", "Template certificate:", cert_tmpl[1])

        key_tmpl = self.loader.get_source(self.environment, key_name)

        # we need them as bytes
        cert = cert_tmpl[0].encode("utf-8")
        key = key_tmpl[0].encode("utf-8")

        self.sign_with = (cert, key)

        return ""

    def delayed_sign(self, cert_name: str, key_name: str) -> None:
        """Sign the file after it has been generated."""
        with open(cert_name, "rb") as f:
            cert = f.read()

        log("INFO", "Certificate:", cert_name)

        with open(key_name, "rb") as f:
            key = f.read()

        self.sign_with = (cert, key)


def generate_rdp(
    template: str | TextIO,
    args: Any,
    pre_sign_hook: Callable[[RdpBuilder, Any], None] | None = None,
    sign_with: tuple[str, str] | None = None,
) -> str:
    """Return a generated RDP file."""
    builder = RdpBuilder(template, pre_sign_hook=pre_sign_hook)

    if sign_with is not None:
        builder.delayed_sign(*sign_with)

    return builder.generate(args)
