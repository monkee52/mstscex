# MSTSCEX
Create and connect to Remote Desktop servers via templated files.

## Usage
`mstscex [-h] [-o <destination>] [-s <cert> <key>] [-l] <file> [...]`

- **&lt;file&gt;**: The template filename
- **[...]**: Arguments supplied to the template.

- **-o &lt;destination&gt;**: Output the generated RDP to the supplied path
  rather than launching.
- **-l**: Launch the generated RDP if it was written to a supplied
  file.
- **-s &lt;cert&gt; &lt;key&gt;**: Sign the generated file with the supplied
  certificate and key. Overrides `sign()` directive in the template
  (if any).

## Template Directives
- ### {{ argv[1] }} / {{ args }}
Remainder of arguments passed to the program. `argv` Is a list of
arguments, `args` is a quoted string of the arguments.

- ### contains(a, b, ...)
Returns whether the iterable `a` contains any of the remaining arguments.

- ### can_ping(host)
Returns `True` if the host can be pinged, otherwise `False`

- ### get_connected_wifi() / wifi_is(name, ...)
Returns all currently connected SSIDs

```
{% if not contains(get_connected_wifi(), "My Work SSID") %}
gatewayhostname:s:rdgateway.example.local
{% endif %}
```

```
{% if not vpn_is("My Work SSID") %}
gatewayhostname:s:rdgateway.example.local
{% endif %}
```

- ### get_connected_vpn() / vpn_is(name, ...)
Returns all currently connected VPNs (PPP connections)

```
{% if not contains(get_connected_vpn(), "My Work VPN") %}
gatewayhostname:s:rdgateway.example.local
{% endif %}
```

```
{% if not vpn_is("My Work VPN") %}
gatewayhostname:s:rdgateway.example.local
{% endif %}
```

- ### get_setting(rdp_setting_name)
Get the current value of a setting from the generated RDP file. The setting
must have been set prior to the usage of `get_setting()`

```
{% if not can_ping(get_setting("full address")) %}
gatewayhostname:s:rdgateway.example.local
{% endif %}
```

- ### sign(cert_name, key_name)
Sign the generated RDP file with the supplied certificate and key. This
can be declared anywhere in the template, and won't apply until the generated
file is created.

```
{{ sign("my.crt", "my.key") }}
```
