#!/usr/local/bin/python3
"""
Argument parser for the linode CLI
"""

from importlib import import_module

from linodecli import plugins

def register_args(parser):
    """
    Register static command arguments
    """
    parser.add_argument("command",
        metavar="COMMAND", nargs="?", type=str,
        help="The command to invoke in the CLI.")
    parser.add_argument("action",
        metavar="ACTION", nargs="?", type=str,
        help="The action to perform in this command.")
    parser.add_argument( "--help",
        action="store_true",
        help="Display information about a command, action, or the CLI overall.")
    parser.add_argument("--text",
        action="store_true",
        help="Display text output with a delimiter (defaults to tabs).")
    parser.add_argument("--delimiter",
        metavar="DELIMITER", type=str,
        help="The delimiter when displaying raw output.")
    parser.add_argument("--json",
        action="store_true",
        help="Display output as JSON.")
    parser.add_argument("--markdown",
        action="store_true",
        help="Display output in Markdown format.")
    parser.add_argument("--pretty",
        action="store_true",
        help="If set, pretty-print JSON output.")
    parser.add_argument("--no-headers",
        action="store_true",
        help="If set, does not display headers in output.")
    parser.add_argument("--page",
        metavar="PAGE", default=1, type=int,
        help="For listing actions, specifies the page to request")
    parser.add_argument("--page-size",
        metavar="PAGESIZE", default=100, type=int,
        help="For listing actions, specifies the number of items per page, "
             "accepts any value between 25 and 500")
    parser.add_argument("--all",
        action="store_true",
        help="If set, displays all possible columns instead of "
             "the default columns. This may not work well on some terminals.")
    parser.add_argument("--format",
        metavar="FORMAT", type=str,
        help="The columns to display in output. Provide a comma-"
             "separated list of column names.")
    parser.add_argument("--no-defaults",
        action="store_true",
        help="Suppress default values for arguments.  Default values "
             "are configured on initial setup or with linode-cli configure")
    parser.add_argument("--as-user",
        metavar="USERNAME", type=str,
        help="The username to execute this command as.  This user must "
             "be configured.")
    parser.add_argument("--suppress-warnings",
        action="store_true",
        help="Suppress warnings that are intended for human users. "
             "This is useful for scripting the CLI's behavior.")
    parser.add_argument("--no-truncation",
        action="store_true", default=False,
        help="Prevent the truncation of long values in command outputs.")
    parser.add_argument("--version", "-v",
        action="store_true",
        help="Prints version information and exits.")
    parser.add_argument("--debug",
        action="store_true",
        help="Enable verbose HTTP debug output.")

    return parser

# TODO: maybe move to plugins/__init__.py
def register_plugin(module, config, ops):
    """
    Handle registering a plugin
    Registering sets up the plugin for all CLI users
    """
    # attempt to import the module to prove it is installed and exists
    try:
        plugin = import_module(module)
    except ImportError:
        return f"Module {module} not installed", 10

    try:
        plugin_name = plugin.PLUGIN_NAME
    except AttributeError:
        msg = f"{module} is not a valid Linode CLI plugin - missing PLUGIN_NAME"
        return msg, 11

    try:
        call_func = plugin.call
        del call_func
    except AttributeError:
        msg = f"{module} is not a valid Linode CLI plugin - missing call"
        return msg, 11

    if plugin_name in ops:
        msg = "Plugin name conflicts with CLI operation - registration failed."
        return msg, 12

    if plugin_name in plugins.available_local:
        msg = "Plugin name conflicts with internal CLI plugin - registration failed."
        return msg, 13

    reregistering = False
    if plugin_name in plugins.available(config):
        print(f"WARNING: Plugin {plugin_name} is already registered.\n\n")
        answer = input(f"Allow re-registration of {plugin_name}? [y/N] ")
        if not answer or answer not in "yY":
            return "Registration aborted.", 0
        reregistering = True

    already_registered = []
    if config.config.has_option("DEFAULT", "registered-plugins"):
        already_registered = config.config.get("DEFAULT", "registered-plugins").split(",")

    if reregistering:
        already_registered.remove(plugin_name)
        config.config.remove_option("DEFAULT", f"plugin-name-{plugin_name}")

    already_registered.append(plugin_name)
    config.config.set("DEFAULT", "registered-plugins", ",".join(already_registered))
    config.config.set("DEFAULT", f"plugin-name-{plugin_name}", module)
    config.write_config()

    msg = ("Plugin registered successfully!\n\n"
           "Invoke this plugin by running the following:\n\n"
           "  linode-cli {plugin_name}")
    return msg, 0
