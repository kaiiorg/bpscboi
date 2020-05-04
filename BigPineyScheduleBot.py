#!/bin/python3
import requests, difflib, re, time, random, discord, asyncio, json, traceback, datetime, pytz
from bs4 import BeautifulSoup

class BigPineyScheduleBoi(discord.Client):
    tz = pytz.timezone('America/Chicago')
    discord_config_file = 'discord_config.json'
    discord_config = None
    discord_status_message = None

    club_schedule_page = 'https://www.tapatalk.com/groups/bigpineysportsmansclub/viewtopic.php?f=14&t=125&view=print'
    last_change_file_name = './last_known_change.txt'
    viewer_diff_file_name = './viewerDiff.json'
    word_regex_string = r'([\w\(\)\.\:\-\/\\\,\@\&\$]+)'
    word_regex = re.compile(word_regex_string)
    next_check_in = 60
    
    def __init__(self, *args, **kwargs):
        print('Init super()')
        super().__init__(*args, **kwargs)
        print('Getting config from file')
        self.GetDiscordConfigFromFile()
        print('Setting up background task')
        self.bg_task = self.loop.create_task(self.Check())

    ###################################
    # File operations
    ###################################
    def GetDiscordConfigFromFile(self):
        with open(self.discord_config_file, "r") as token_file:
            raw_config = token_file.read()
            self.discord_config = json.loads(raw_config)
            if 'token' not in self.discord_config:
                raise Exception(f'Token not found in {self.discord_config_file} file')
            if 'default_channel' not in self.discord_config:
                raise Exception(f'Default channel not found in {self.discord_config_file} file')
            if 'channels' not in self.discord_config:
                raise Exception(f'Channels not found in {self.discord_config_file} file')


    def LoadOldPage(self):
        with open(self.last_change_file_name, "r", encoding="utf-8") as last_change_file:
            lines = last_change_file.readlines()
            stripped_lines = []
            for line in lines:
                words = self.word_regex.findall(line)
                if (words):
                    new_line = ''
                    for word in words:
                        new_line = f'{new_line} {word}'
                    stripped_lines.append(new_line)
            return stripped_lines

    def OverwriteOldPage(self, new_page):
        with open(self.last_change_file_name, "w", encoding="utf-8") as last_change_file:
            for line in new_page:
                last_change_file.write(f'{line}\n')

    def SaveViewerDiff(self, lines):
        with open(self.viewer_diff_file_name, 'w', encoding='utf-8') as viewer_diff_file:
            viewer_diff_file.write(
                json.dumps(lines)
            )

    ###################################
    # Web request operations
    ###################################
    def GetCurrentPage(self):
        r = requests.get(self.club_schedule_page)
        soup = BeautifulSoup(r.text, 'html.parser')
        stripped_lines = []
        for line in soup.stripped_strings:
            words = self.word_regex.findall(line)
            if (words):
                new_line = ''
                for word in words:
                    new_line = f'{new_line} {word}'
                stripped_lines.append(new_line)
        return stripped_lines

    ###################################
    # Diff operations
    ###################################
    def DiffPages(self):
        new_page = self.GetCurrentPage()
        old_page = self.LoadOldPage()

        new_page_line_count = len(new_page)
        old_page_line_count = len(old_page)
        print(f"new_page line count: {new_page_line_count}")
        print(f"old_page line count: {old_page_line_count}")

        print('Getting diff with context for posting within discord')
        diff = difflib.unified_diff(
            old_page,
            new_page
        )

        print('Overwriting old page')
        self.OverwriteOldPage(new_page)

        return diff

    ###################################
    # Backgound tasks
    ###################################
    async def Check(self):
        print('Waiting until the discord client is ready')
        await self.wait_until_ready()
        print('Starting to check the Big Piney Sportsman Club\'s schedule on tapatalk')

        while not self.is_closed():
            print(f'Checking in {self.next_check_in} seconds')
            await asyncio.sleep(self.next_check_in)

            discord_diff = '```diff\n'
            viewer_diff = []
            diff = self.DiffPages()

            diff_count = 0
            for d in diff:
                print(d)
                discord_diff = f'{discord_diff}\n{d}'
                viewer_diff.append(d)
                diff_count = diff_count + 1

            print()
            self.next_check_in = random.randrange(60, 120)
            next_check_message = f'No change since last check at `{self.NowAtRangeLocalTime()}`, local time\nNext check in about `{self.next_check_in}` seconds.'
            if diff_count == 0:
                print('No differences found')
                await self.SendDiscordMessage(next_check_message)
            else:
                print('Differences found')
                discord_diff = f'{discord_diff}```\nNext check in {next_check_message}'
                self.SaveViewerDiff(viewer_diff)
                try:
                    await self.SendDiscordMessage(discord_diff, edit=False)
                except IndexError:
                    await self.SendDiscordMessage('There are new changes, but its too much to show here.', edit=False)

    ###############################
    # Discord events
    ###############################
    async def on_ready(self):
        print('We have logged in as {0.user}'.format(discord_client))

        # Purge this bot's existing messages in the default channel
        channel = self.get_channel(self.discord_config['default_channel'])
        if channel == None:
            print('Default channel missing!')
        await self.PurgeSelf(channel, False)

        self.discord_status_message = await self.SendDiscordMessage(
            f'I\'m ready to go!\nChecking in about `{self.next_check_in}` seconds.', 
            edit=False
        )

    async def on_message(self, message):
        print(f'Message in channel {message.channel}:')
        print(message.content)

        # Skip if the message is from self
        #if message.author == self.user:
        if self.MessageFromSelf(message):
            print('Message from self, skipping')
            return

        # Check if the message is in a channel we're configured to ignore
        if message.channel.id not in self.discord_config['channels']:
            print('Message in channel we\'re configured to ignore, skipping')
            return

        # ping;
        # Reply with "pong" to confirm that the script is running
        if message.content.startswith('ping;'):
            print('Ping requested')
            await message.channel.send('pong')

        # channels;
        # Reply with list of channels
        if message.content.startswith('channels;'):
            print('Channels have been requested. Sending...')
            channels = self.GetDiscordChannels()
            await message.channel.send(channels)

        # purge;
        # Delete last messages that the bot has posted
        if message.content.startswith('purge;'):
            print('Purge of this bot\'s messages requested')
            await self.PurgeSelf(message.channel)

    ###################################
    # Utility
    ###################################
    def MessageFromSelf(self, message):
        return message.author == self.user

    async def PurgeSelf(self, channel, print_count=True):
        try:
            deleted = await channel.purge(limit=100, check=self.MessageFromSelf)
            print(f'Deleted {len(deleted)} from self')
            if print_count:
                self.discord_status_message = await self.SendDiscordMessage(
                    f'Purge complete, deleted {len(deleted)} messages from self',
                    edit=False,
                    channel=channel
                )
        except discord.errors.Forbidden as e:
            print(f'Unable to purge: forbidden')
            await self.SendDiscordMessage(f'Unable to purge: {e}', edit=False, channel=channel)

    def GetDiscordChannels(self):
        channels = '```\nid: name'
        for channel in self.get_all_channels():
            channels = f'{channels}{channel.id}: {channel.name}\n'
        channels = f'{channels}```'
        return channels

    # If channel is set to none, it uses the default channel in the config
    async def SendDiscordMessage(self, message_string, edit=True, channel=None):
        # If the message string is over the 2000 character limit, raise an exception
        if len(message_string) > 2000:
            raise IndexError

        try:
            if edit:
                return await self.discord_status_message.edit(content=message_string)
            else:
                if channel == None:
                    channel = self.get_channel(
                        self.discord_config['default_channel']
                    )
                return await channel.send(message_string)
        except Exception as e:
            print(traceback.format_exc())
            print(e)

    def NowAtRangeLocalTime(self):
        return datetime.datetime.now(self.tz)


try:
    discord_client = BigPineyScheduleBoi()
    print('Starting discord client')
    discord_client.run(discord_client.discord_config['token'])
except KeyboardInterrupt:
    exit(0)
except Exception as e:
    print(traceback.format_exc())
    print(e)
    exit(1)