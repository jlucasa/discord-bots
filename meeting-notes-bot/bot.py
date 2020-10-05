import discord
import os
import json
import validators
from dotenv import load_dotenv

client = discord.Client()
load_dotenv()

LINK_FP = './meeting-notes-bot/meeting-note-links.json'


def is_valid_entry_string(entry):
    valid_month_names = [
        'jan',
        'feb',
        'mar',
        'apr',
        'may',
        'jun',
        'jul',
        'aug',
        'sep',
        'oct',
        'nov',
        'dec'
    ]

    valid_note_names = [
        'w1',
        'w2',
        'w3',
        'w4',
        'm',
        'other'
    ]

    split_entry = entry.split('-')
    month = split_entry[0]
    note_name = split_entry[1]

    return month in valid_month_names and note_name in valid_note_names


async def register_note(message, args):
    if not args:
        await send_help(f'Could not interpret register command {message.content}', message)
        return

    if len(args) < 2:
        await send_help(f'Not enough arguments in {message.content}', message)
        return

    link = args[0]
    entry = args[1]

    if not validators.url(link):
        await message.channel.send(f'Invalid link: {link}')
        return

    if not is_valid_entry_string(entry):
        await message.channel.send(f'Invalid entry: {entry}')
        return

    meeting_link_data = await open_json_file(LINK_FP)

    if entry in meeting_link_data:
        await message.channel.send(f'A link already exists for {entry}: Updating link...')

    meeting_link_data.update({entry: link})

    await save_to_json_file(meeting_link_data, LINK_FP)

    await message.channel.send(f'Saved link for {entry}')


async def serve_note(message, args):
    if not args:
        await send_help('Could not interpret serve command', message)
        return

    entry = args[0]
    meeting_link_data = await open_json_file(LINK_FP)

    if entry not in meeting_link_data.keys():
        await message.channel.send(f'No link exists for {entry}')
        return

    await message.channel.send(f'Here\'s that link! {meeting_link_data[entry]}')


async def send_help(error_msg, message):
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
    
    await message.channel.send(error_msg)
    await message.channel.send(embed)


async def open_json_file(fp):
    with open(fp) as file:
        return json.load(file)


async def save_to_json_file(data, fp):
    with open(fp, 'w') as file:
        json.dump(data, file)


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
        await send_help('You didn\'t seem to put a command in!', message)
        return

    if message.content.startswith('!notes'):
        split_message = message.content.split()
        command = split_message[1]
        message_args = split_message[2:] if len(split_message) >= 3 else None

        if command not in command_map.keys():
            await send_help(f'Could not interpret command {command}', message)
            return

        await command_map[command](message, args=message_args)


def main():
    client.run(os.getenv('BOT_TOKEN'))


if __name__ == '__main__':
    main()
