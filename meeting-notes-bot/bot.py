import discord
import os
import json
import validators
from dotenv import load_dotenv

client = discord.Client()
load_dotenv()

LINK_FP = './meeting-note-links.json'


async def register_note(message, args):
    if not args:
        send_help(f'Could not interpret register command {message.content}', message.channel)

    link = args[0]
    entry = args[1]

    if not validators.url(link):
        await message.channel.send(f'Invalid link: {link}')
        return

    meeting_link_data = await open_json_file(LINK_FP)

    if entry in meeting_link_data:
        await message.channel.send(f'A link already exists for {entry}: Updating link...')

    meeting_link_data.update({entry: link})

    await save_to_json_file(meeting_link_data, LINK_FP)

    await message.channel.send(f'Saved link for {entry}')


async def serve_note(message, args):
    if not args:
        send_help('Could not interpret serve command', message.channel)
        return

    entry = args[0]
    meeting_link_data = await open_json_file(LINK_FP)

    if entry not in meeting_link_data.keys():
        await message.channel.send(f'No link exists for {entry}')
        return

    await message.channel.send(f'Here\'s that link! {meeting_link_data[entry]}')


@client.event
async def on_ready():
    print(f'Logged in as {client.user}')


@client.event
async def on_message(message):
    command_map = {
        'reg': register_note,
        'serve': serve_note
    }

    if message.author == client.user:
        return

    if message.content.strip() == '!notes':
        send_help('You didn\'t seem to put a command in!', message)
        return

    if message.startswith('!notes'):
        command = message.content.split()[1]

        if command not in command_map.keys():
            send_help(f'Could not interpret command {command}', message)
            return

        command_map[command](message, args=compose_args(command))


def compose_args(command):
    return command[2:] if len(command) >= 3 else None


async def send_help(error_msg, message):
    await message.channel.send(error_msg)
    await message.channel.send(help_embed())


def help_embed():
    embed = discord.Embed(
        title="Commands Help",
        description="test",
        color=0x00ff00
    )

    embed.add_field(
        name="this is a test",
        value="of what embeds look like. this embed is not inline",
        inline=False
    )

    embed.add_field(
        name="this is another test",
        value="of what embeds look like. this embed is inline",
        inline=True
    )

    return embed


async def open_json_file(fp):
    with open(fp) as file:
        return json.load(file)


async def save_to_json_file(data, fp):
    with open(fp, 'w') as file:
        json.dump(data, file)


def main():
    client.run(os.getenv('BOT_TOKEN'))


if __name__ == '__main__':
    main()
