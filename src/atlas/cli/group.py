from typer.core import TyperGroup


class FallbackToShowGroup(TyperGroup):
    """Unknown subcommands become `show <name>`, so `atlas area health` works."""

    def parse_args(self, ctx, args):
        args = list(args)
        if args and not args[0].startswith("-") and args[0] not in self.list_commands(ctx):
            args.insert(0, "show")
        return super().parse_args(ctx, args)
