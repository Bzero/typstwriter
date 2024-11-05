import argparse

import typstwriter


class APA(argparse.ArgumentParser):
    """
    A customized subclass of argparse.ArgumentParser.

    Displays the description before the usage in the help output, capitalizes the section titles and adds a prolog section.
    """

    def __init__(self, *args, prolog=None, **kwargs):
        """Patch positionals and optionals display names."""
        argparse.ArgumentParser.__init__(self, *args, **kwargs)
        self.prolog = prolog
        self._positionals.title = "Arguments"
        self._optionals.title = "Options"

    def format_usage(self):
        """Format the usage text."""
        formatter = self._get_formatter()
        formatter.add_usage(self.usage, self._actions, self._mutually_exclusive_groups, "Usage: ")
        return formatter.format_help()

    def format_help(self):
        """Format the help text."""
        formatter = self._get_formatter()

        # description
        formatter.add_text(self.description)

        # prolog
        formatter.add_text(self.prolog)

        # usage
        formatter.add_usage(self.usage, self._actions, self._mutually_exclusive_groups, "Usage: ")

        # positionals, optionals and user-defined groups
        for action_group in self._action_groups:
            formatter.start_section(action_group.title)
            formatter.add_text(action_group.description)
            formatter.add_arguments(action_group._group_actions)
            formatter.end_section()

        # epilog
        formatter.add_text(self.epilog)

        # format help message
        return formatter.format_help()


def parse_args():
    """Parse CLI arguments."""
    parser = APA(description=typstwriter.__doc__, add_help=False)

    parser.add_argument("files", nargs="*", help="The list of files to open.")

    parser.add_argument(
        "-h",
        "--help",
        action="help",
        help="Show this help message and exit.",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"Typstwriter {typstwriter.__version__}",
        help="Show the Typstwriter version and exit.",
    )
    parser.add_argument(
        "--working-directory",
        action="store",
        type=str,
        help="Set the working directory.",
    )

    return parser.parse_args()


Args = parse_args()
