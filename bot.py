import json

import sentry_sdk
from discord.ext import commands

from lib.DatabaseManager import DatabaseManager


class SteekerBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        with open("config.json") as config:
            self._config = json.load(config)
        self._cogs = ["jishaku", "cogs.steeker"]
        self.database = DatabaseManager(self._config["database"]["uri"], self._config["database"]["name"], self.loop)

    def startup(self):
        for cog in self._cogs:
            try:
                self.load_extension(cog)
                print(f"Loaded {cog}")
            except Exception as e:
                print(f"Error while loading {cog} - {e}")

    async def on_command_error(self, context, exception):
        if isinstance(exception, commands.MissingRequiredArgument):
            await context.send_help(context.command)

    def start_bot(self):
        self.startup()
        return self.run(self._config["token"])


if __name__ == "__main__":
    sentry_sdk.init(
        "https://6bd16f6e36a54c3eae239e3ea14a5a74@o170856.ingest.sentry.io/5645906",
        traces_sample_rate=1.0,
    )


    def get_prefix(bot, message):
        prefixes = ["s!"]
        return commands.when_mentioned_or(*prefixes)(bot, message)


    SteekerBot(command_prefix=get_prefix).start_bot()
