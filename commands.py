import sys, json, random, asyncio
from urllib import parse
from urllib import request
import goslate

import hangups
from hangups.ui.utils import get_conv_name
from wikipedia import wikipedia
import handlers


class CommandDispatcher(object):
    def __init__(self):
        self.commands = {}
        self.unknown_command = None

    @asyncio.coroutine
    def run(self, bot, event, *args, **kwds):
        if args[0].startswith('/'):
            command = args[0][1:]
        else:
            command = args[0]
        try:
            func = self.commands[command]
        except KeyError:
            if self.unknown_command:
                func = self.unknown_command
            else:
                raise

        func = asyncio.coroutine(func)

        args = list(args[1:])

        try:
            yield from func(bot, event, *args, **kwds)
        except Exception as e:
            print(e)

    def register(self, func):
        """Decorator for registering command"""
        self.commands[func.__name__] = func
        return func

    def register_unknown(self, func):
        self.unknown_command = func
        return func

# CommandDispatcher singleton
command = CommandDispatcher()


@command.register_unknown
def unknown_command(bot, event, *args):
    bot.send_message(event.conv,
                     '{}: Unknown command!'.format(event.user.full_name))


# Whatever new methods added here will be automatically added to the Bot's command list if they have this
# @command.register annotation. Add them in the config.json file to have them show in the /help command.
# Also, it'd be nice if all methods accepted a '?' argument to denote their function.

@command.register
def help(bot, event, *args):
    segments = [hangups.ChatMessageSegment('Current implemented commands:', is_bold=True),
                hangups.ChatMessageSegment('\n', hangups.SegmentType.LINE_BREAK),
                hangups.ChatMessageSegment(', '.join(sorted(command.commands.keys()))),
                hangups.ChatMessageSegment('\n', hangups.SegmentType.LINE_BREAK),
                hangups.ChatMessageSegment('\n', hangups.SegmentType.LINE_BREAK),
                hangups.ChatMessageSegment('Use: /<command name> ? to find more information about the command.')]
    bot.send_message_segments(event.conv, segments)


@command.register
def wiki(bot, event, *args):
    if ''.join(args) == '?':
        segments = [hangups.ChatMessageSegment('Wikipedia', is_bold=True),
                    hangups.ChatMessageSegment('\n', hangups.SegmentType.LINE_BREAK),
                    hangups.ChatMessageSegment(
                        'Usage: /wiki <keyword to search for> <optional: sentences to display [defaults to 3]>'),
                    hangups.ChatMessageSegment('\n', hangups.SegmentType.LINE_BREAK),
                    hangups.ChatMessageSegment('Purpose: Get summary from Wikipedia on search parameter.')]
        bot.send_message_segments(event.conv, segments)
    else:
        sentences = 3
        if args[-1].isdigit():
            sentences = args[-1]
            page = wikipedia.page(' '.join(args[0:-1]))
        else:
            page = wikipedia.page(' '.join(args))

        segments = [hangups.ChatMessageSegment(page.title, is_bold=True, link_target=page.url),
                    hangups.ChatMessageSegment('\n', hangups.SegmentType.LINE_BREAK),
                    hangups.ChatMessageSegment(wikipedia.summary(page.original_title, sentences=sentences))]

        bot.send_message_segments(event.conv, segments)


@command.register
def goog(bot, event, *args):
    def get_json_results(page):
        search_results = page.read()
        results = json.loads(search_results.decode('utf-8'))
        segments = [hangups.ChatMessageSegment('{}:'.format("Result"), is_bold=True),
                    hangups.ChatMessageSegment('\n', hangups.SegmentType.LINE_BREAK),
                    hangups.ChatMessageSegment("".join(str(results['responseData']['results'][0]['titleNoFormatting'])),
                                               link_target="".join(str(results['responseData']['results'][0]['url'])))]
        bot.send_message_segments(event.conv, segments)

    if ''.join(args) == '?':
        segments = [hangups.ChatMessageSegment('Google', is_bold=True),
                    hangups.ChatMessageSegment('\n', hangups.SegmentType.LINE_BREAK),
                    hangups.ChatMessageSegment('Usage: /goog <optional: search parameter>'),
                    hangups.ChatMessageSegment('\n', hangups.SegmentType.LINE_BREAK),
                    hangups.ChatMessageSegment(
                        'Purpose: Get the first result from Google\'s search using search parameter.')]
        bot.send_message_segments(event.conv, segments)
    else:
        rest = " ".join(args)
        if rest == "" or rest == " ":
            rest = "google"
        query = parse.urlencode({'q': rest})
        url = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&%s' \
              % query
        headers = {
            'User-agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36'}
        req = request.Request(url, None, headers)
        search_response_d = request.urlopen(req)

        get_json_results(search_response_d)
        return search_response_d


@command.register
def ping(bot, event, *args):
    if ''.join(args) == '?':
        segments = [hangups.ChatMessageSegment('Ping', is_bold=True),
                    hangups.ChatMessageSegment('\n', hangups.SegmentType.LINE_BREAK),
                    hangups.ChatMessageSegment('Usage: /ping'),
                    hangups.ChatMessageSegment('\n', hangups.SegmentType.LINE_BREAK),
                    hangups.ChatMessageSegment('Purpose: Easy way to check if Bot is running.')]
        bot.send_message_segments(event.conv, segments)
    else:
        bot.send_message(event.conv, 'pong')


@command.register
def echo(bot, event, *args):
    if ''.join(args) == '?':
        segments = [hangups.ChatMessageSegment('Echo', is_bold=True),
                    hangups.ChatMessageSegment('\n', hangups.SegmentType.LINE_BREAK),
                    hangups.ChatMessageSegment('Usage: /echo <text to echo>'),
                    hangups.ChatMessageSegment('\n', hangups.SegmentType.LINE_BREAK),
                    hangups.ChatMessageSegment(
                        'Purpose: Bot will reply with whatever text is inputted exactly, minus the /echo command.')]
        bot.send_message_segments(event.conv, segments)
    else:
        bot.send_message(event.conv, '{}'.format(' '.join(args)))


@command.register
def users(bot, event, *args):
    if ''.join(args) == '?':
        segments = [hangups.ChatMessageSegment('Users', is_bold=True),
                    hangups.ChatMessageSegment('\n', hangups.SegmentType.LINE_BREAK),
                    hangups.ChatMessageSegment('Usage: /users'),
                    hangups.ChatMessageSegment('\n', hangups.SegmentType.LINE_BREAK),
                    hangups.ChatMessageSegment(
                        'Purpose: Listing all users in the current hangout (including G + accounts and emails)')]
        bot.send_message_segments(event.conv, segments)
    else:
        segments = [hangups.ChatMessageSegment('Users: '.format(len(event.conv.users)),
                                               is_bold=True),
                    hangups.ChatMessageSegment('\n', hangups.SegmentType.LINE_BREAK)]
        for user in sorted(event.conv.users, key=lambda x: x.full_name.split()[-1]):
            link = 'https://plus.google.com/u/0/{}/about'.format(user.id_.chat_id)
            segments.append(hangups.ChatMessageSegment(user.full_name, hangups.SegmentType.LINK,
                                                       link_target=link))
            if user.emails:
                segments.append(hangups.ChatMessageSegment(' ('))
                segments.append(hangups.ChatMessageSegment(user.emails[0], hangups.SegmentType.LINK,
                                                           link_target='mailto:{}'.format(user.emails[0])))
                segments.append(hangups.ChatMessageSegment(')'))

            segments.append(hangups.ChatMessageSegment('\n', hangups.SegmentType.LINE_BREAK))
        bot.send_message_segments(event.conv, segments)


@command.register
def user(bot, event, username, *args):
    if ''.join(args) == '?':
        segments = [hangups.ChatMessageSegment('User', is_bold=True),
                    hangups.ChatMessageSegment('\n', hangups.SegmentType.LINE_BREAK),
                    hangups.ChatMessageSegment('Usage: /user <user name>'),
                    hangups.ChatMessageSegment('\n', hangups.SegmentType.LINE_BREAK),
                    hangups.ChatMessageSegment(
                        'Purpose: List information about user.)')]
        bot.send_message_segments(event.conv, segments)
    else:
        username_lower = username.strip().lower()
        segments = [hangups.ChatMessageSegment('User: "{}":'.format(username),
                                               is_bold=True),
                    hangups.ChatMessageSegment('\n', hangups.SegmentType.LINE_BREAK)]
        for u in sorted(bot._user_list._user_dict.values(), key=lambda x: x.full_name.split()[-1]):
            if not username_lower in u.full_name.lower():
                continue

            link = 'https://plus.google.com/u/0/{}/about'.format(u.id_.chat_id)
            segments.append(hangups.ChatMessageSegment(u.full_name, hangups.SegmentType.LINK,
                                                       link_target=link))
            if u.emails:
                segments.append(hangups.ChatMessageSegment(' ('))
                segments.append(hangups.ChatMessageSegment(u.emails[0], hangups.SegmentType.LINK,
                                                           link_target='mailto:{}'.format(u.emails[0])))
                segments.append(hangups.ChatMessageSegment(')'))
            segments.append(hangups.ChatMessageSegment(' ... {}'.format(u.id_.chat_id)))
            segments.append(hangups.ChatMessageSegment('\n', hangups.SegmentType.LINE_BREAK))
        bot.send_message_segments(event.conv, segments)


@command.register
def hangouts(bot, event, *args):
    if ''.join(args) == '?':
        segments = [hangups.ChatMessageSegment('Hangouts', is_bold=True),
                    hangups.ChatMessageSegment('\n', hangups.SegmentType.LINE_BREAK),
                    hangups.ChatMessageSegment('Usage: /hangouts'),
                    hangups.ChatMessageSegment('\n', hangups.SegmentType.LINE_BREAK),
                    hangups.ChatMessageSegment(
                        'Purpose: List all Hangouts this Bot is currently in, along with what settings those Hangouts are using.')]
        bot.send_message_segments(event.conv, segments)
    else:
        segments = [hangups.ChatMessageSegment('Currently In These Hangouts:', is_bold=True),
                    hangups.ChatMessageSegment('\n', hangups.SegmentType.LINE_BREAK)]
        for c in bot.list_conversations():
            s = '{} [commands: {:d}, forwarding: {:d}, autoreplies: {:d}]'.format(get_conv_name(c, truncate=True),
                                                                                  bot.get_config_suboption(c.id_,
                                                                                                           'commands_enabled'),
                                                                                  bot.get_config_suboption(c.id_,
                                                                                                           'forwarding_enabled'),
                                                                                  bot.get_config_suboption(c.id_,
                                                                                                           'autoreplies_enabled'))
            segments.append(hangups.ChatMessageSegment(s))
            segments.append(hangups.ChatMessageSegment('\n', hangups.SegmentType.LINE_BREAK))

        bot.send_message_segments(event.conv, segments)


@command.register
def rename(bot, event, *args):
    if ''.join(args) == '?':
        segments = [hangups.ChatMessageSegment('Rename', is_bold=True),
                    hangups.ChatMessageSegment('\n', hangups.SegmentType.LINE_BREAK),
                    hangups.ChatMessageSegment('Usage: /rename <new title>'),
                    hangups.ChatMessageSegment('\n', hangups.SegmentType.LINE_BREAK),
                    hangups.ChatMessageSegment(
                        'Purpose: Changes the chat title of the room.')]
        bot.send_message_segments(event.conv, segments)
    else:
        yield from bot._client.setchatname(event.conv_id, ' '.join(args))


@command.register
def leave(bot, event, conversation=None, *args):
    if ''.join(args) == '?':
        segments = [hangups.ChatMessageSegment('Leave', is_bold=True),
                    hangups.ChatMessageSegment('\n', hangups.SegmentType.LINE_BREAK),
                    hangups.ChatMessageSegment('Usage: /leave'),
                    hangups.ChatMessageSegment('\n', hangups.SegmentType.LINE_BREAK),
                    hangups.ChatMessageSegment(
                        'Purpose: Lies to you.')]
        bot.send_message_segments(event.conv, segments)
    else:
        convs = []
        if not conversation:
            convs.append(event.conv)
        else:
            conversation = conversation.strip().lower()
            for c in bot.list_conversations():
                if conversation in get_conv_name(c, truncate=True).lower():
                    convs.append(c)

        for c in convs:
            yield from c.send_message([
                hangups.ChatMessageSegment('I\'ll be back!')
            ])
            yield from bot._conv_list.delete_conversation(c.id_)


@command.register
def obfuscate(bot, event, *args):
    if ''.join(args) == '?':
        segments = [hangups.ChatMessageSegment('Obfuscate', is_bold=True),
                    hangups.ChatMessageSegment('\n', hangups.SegmentType.LINE_BREAK),
                    hangups.ChatMessageSegment(
                        'Usage: /obfuscate <text to obfuscate> <optional: number of times to obfuscate>'),
                    hangups.ChatMessageSegment('\n', hangups.SegmentType.LINE_BREAK),
                    hangups.ChatMessageSegment(
                        'Purpose: Makes your text unintelligible.)')]
        bot.send_message_segments(event.conv, segments)
    else:
        translator = goslate.Goslate()
        languages = ['en', 'de', 'af', 'ar', 'km', 'zh-CN', 'xx-elmer', 'fi', 'fr', 'iw', 'la', 'xx-pirate', 'ro',
                     'es', 'sv', 'th', 'tr', 'uk', 'vi', 'cy', 'yi']
        times = len(languages)
        if args[-1].isdigit() and int(args[-1]) < times:
            times = args[-1]
            args = args[0:-1]
        text = ' '.join(args)

        random.shuffle(languages)
        for x in range(0, times):
            text = translator.translate(text, languages[x])
        text = translator.translate(text, 'en')
        bot.send_message(event.conv, text)


@command.register
def clear(bot, event, *args):
    if ''.join(args) == '?':
        segments = [hangups.ChatMessageSegment('Clear', is_bold=True),
                    hangups.ChatMessageSegment('\n', hangups.SegmentType.LINE_BREAK),
                    hangups.ChatMessageSegment('Usage: /clear'),
                    hangups.ChatMessageSegment('\n', hangups.SegmentType.LINE_BREAK),
                    hangups.ChatMessageSegment('Purpose: Clears the current screen.')]
        bot.send_message_segments(event.conv, segments)
    else:
        segments = [hangups.ChatMessageSegment('Initialing', hangups.SegmentType.LINE_BREAK),
                    hangups.ChatMessageSegment('Screen', hangups.SegmentType.LINE_BREAK),
                    hangups.ChatMessageSegment('Removal', hangups.SegmentType.LINE_BREAK),
                    hangups.ChatMessageSegment('Protocol', hangups.SegmentType.LINE_BREAK),
                    hangups.ChatMessageSegment('135:', hangups.SegmentType.LINE_BREAK),
                    hangups.ChatMessageSegment('Just', hangups.SegmentType.LINE_BREAK),
                    hangups.ChatMessageSegment('Going', hangups.SegmentType.LINE_BREAK),
                    hangups.ChatMessageSegment('To', hangups.SegmentType.LINE_BREAK),
                    hangups.ChatMessageSegment('Remove', hangups.SegmentType.LINE_BREAK),
                    hangups.ChatMessageSegment('That', hangups.SegmentType.LINE_BREAK),
                    hangups.ChatMessageSegment('From', hangups.SegmentType.LINE_BREAK),
                    hangups.ChatMessageSegment('The', hangups.SegmentType.LINE_BREAK),
                    hangups.ChatMessageSegment('Current', hangups.SegmentType.LINE_BREAK),
                    hangups.ChatMessageSegment('View', hangups.SegmentType.LINE_BREAK),
                    hangups.ChatMessageSegment('<!END PROTOCOL>', hangups.SegmentType.LINE_BREAK),
                    hangups.ChatMessageSegment('So how was your day?', hangups.SegmentType.LINE_BREAK)]
        bot.send_message_segments(event.conv, segments)


# @command.register
# def easteregg(bot, event, easteregg, eggcount=1, period=0.5, *args):
#
# for i in range(int(eggcount)):
# yield from bot._client.sendeasteregg(event.conv_id, easteregg)
# if int(eggcount) > 1:
# yield from asyncio.sleep(float(period) + random.uniform(-0.1, 0.1))


@command.register
def speakup(bot, event, *args):
    if ''.join(args) == '?':
        segments = [hangups.ChatMessageSegment('Speakup', is_bold=True),
                    hangups.ChatMessageSegment('\n', hangups.SegmentType.LINE_BREAK),
                    hangups.ChatMessageSegment('Usage: /speakup'),
                    hangups.ChatMessageSegment('\n', hangups.SegmentType.LINE_BREAK),
                    hangups.ChatMessageSegment('Purpose: Unmutes the Cleverbot replies')]
        bot.send_message_segments(event.conv, segments)
    else:
        handlers.MessageHandler.speakup()


@command.register
def shutup(bot, event, *args):
    if ''.join(args) == '?':
        segments = [hangups.ChatMessageSegment('Shut-up', is_bold=True),
                    hangups.ChatMessageSegment('\n', hangups.SegmentType.LINE_BREAK),
                    hangups.ChatMessageSegment('Usage: /shutup'),
                    hangups.ChatMessageSegment('\n', hangups.SegmentType.LINE_BREAK),
                    hangups.ChatMessageSegment('Purpose: Mutes the Cleverbot replies')]
        bot.send_message_segments(event.conv, segments)
    else:
        handlers.MessageHandler.shutup()


@command.register
def mute(bot, event, *args):
    if ''.join(args) == '?':
        segments = [hangups.ChatMessageSegment('Mute', is_bold=True),
                    hangups.ChatMessageSegment('\n', hangups.SegmentType.LINE_BREAK),
                    hangups.ChatMessageSegment('Usage: /mute'),
                    hangups.ChatMessageSegment('\n', hangups.SegmentType.LINE_BREAK),
                    hangups.ChatMessageSegment('Purpose: Mutes the Cleverbot replies')]
        bot.send_message_segments(event.conv, segments)
    else:
        shutup(bot, event, args)


@command.register
def unmute(bot, event, *args):
    if ''.join(args) == '?':
        segments = [hangups.ChatMessageSegment('Unmute', is_bold=True),
                    hangups.ChatMessageSegment('\n', hangups.SegmentType.LINE_BREAK),
                    hangups.ChatMessageSegment('Usage: /unmute'),
                    hangups.ChatMessageSegment('\n', hangups.SegmentType.LINE_BREAK),
                    hangups.ChatMessageSegment('Purpose: Unmutes the Cleverbot replies')]
        bot.send_message_segments(event.conv, segments)
    else:
        speakup(bot, event, *args)


@command.register
def spoof(bot, event, *args):
    if ''.join(args) == '?':
        segments = [hangups.ChatMessageSegment('Spoof', is_bold=True),
                    hangups.ChatMessageSegment('\n', hangups.SegmentType.LINE_BREAK),
                    hangups.ChatMessageSegment('Usage: /spoof'),
                    hangups.ChatMessageSegment('\n', hangups.SegmentType.LINE_BREAK),
                    hangups.ChatMessageSegment('Purpose: Who knows...')]
        bot.send_message_segments(event.conv, segments)
    else:
        segments = [hangups.ChatMessageSegment('!!! CAUTION !!!', is_bold=True),
                    hangups.ChatMessageSegment('\n', hangups.SegmentType.LINE_BREAK),
                    hangups.ChatMessageSegment('User ')]
        link = 'https://plus.google.com/u/0/{}/about'.format(event.user.id_.chat_id)
        segments.append(hangups.ChatMessageSegment(event.user.full_name, hangups.SegmentType.LINK,
                                                   link_target=link))
        segments.append(hangups.ChatMessageSegment(' has just been reporting to the NSA for attempted spoofing!'))
        bot.send_message_segments(event.conv, segments)


@command.register
def reload(bot, event, *args):
    if ''.join(args) == '?':
        segments = [hangups.ChatMessageSegment('Reload', is_bold=True),
                    hangups.ChatMessageSegment('\n', hangups.SegmentType.LINE_BREAK),
                    hangups.ChatMessageSegment('Usage: /reload'),
                    hangups.ChatMessageSegment('\n', hangups.SegmentType.LINE_BREAK),
                    hangups.ChatMessageSegment('Purpose: Reloads current config file.')]
        bot.send_message_segments(event.conv, segments)
    else:
        bot.config.load()


@command.register
def quit(bot, event, *args):
    if not "Wardell" in event.user.full_name:
        bot.send_message(event.conv, event.user.full_name + ", you don't have the ability to stop me...")
    else:
        print('HangupsBot killed by user {} from conversation {}'.format(event.user.full_name,
                                                                         get_conv_name(event.conv, truncate=True)))
        bot.send_message(event.conv, "Creator, why hast thou forsaken me?!")
        yield from bot._client.disconnect()


# @command.register
# def config(bot, event, cmd=None, *args):
# """Zobrazí nebo upraví konfiguraci bota
# Parametry: /bot config [get|set] [key] [subkey] [...] [value]"""
#
# if cmd == 'get' or cmd is None:
#         config_args = list(args)
#         value = bot.config.get_by_path(config_args) if config_args else dict(bot.config)
#     elif cmd == 'set':
#         config_args = list(args[:-1])
#         if len(args) >= 2:
#             bot.config.set_by_path(config_args, json.loads(args[-1]))
#             bot.config.save()
#             value = bot.config.get_by_path(config_args)
#         else:
#             yield from command.unknown_command(bot, event)
#             return
#     else:
#         yield from command.unknown_command(bot, event)
#         return
#
#     if value is None:
#         value = 'Parameter Does Not Exist!'
#
#     config_path = ' '.join(k for k in ['config'] + config_args)
#     segments = [hangups.ChatMessageSegment('{}:'.format(config_path),
#                                            is_bold=True),
#                 hangups.ChatMessageSegment('\n', hangups.SegmentType.LINE_BREAK)]
#     segments.extend(text_to_segments(json.dumps(value, indent=2, sort_keys=True)))
#     bot.send_message_segments(event.conv, segments)
