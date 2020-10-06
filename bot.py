import discord
import os
import json
import validators
from dotenv import load_dotenv

# Instantiate client and load environment
client = discord.Client()
load_dotenv()

# Filepath for link JSON
LINK_FP = './meeting-note-links.json'


# Register a link to a note in the JSON file at LINK_FP
async def register_note(message, args):
    if not args:
        # Args could not be passed in some way
        await send_help(f'Could not interpret register command {message.content}', message)
        return

    if len(args) < 2:
        # There are not enough arguments to complete the command
        await send_help(f'Not enough arguments in {message.content}', message)
        return

    # Note link is first argument, entry is second argument
    link = args[0]
    entry = args[1]
    should_update = False

    if len(args) == 3:
        should_update = True if args[2] == '--update' else False

    if not validators.url(link):
        # URL is not valid
        await message.channel.send(f'Invalid URL: {link}')
        return

    # Fetch all the data from the JSON file at LINK_FP
    meeting_link_data = await open_json_file(LINK_FP)

    if entry in meeting_link_data:
        # There is already an entry with the given name in the JSON file at LINK_FP
        if should_update:
            # The user is already aware that there is a link at this entry and would like to update the link
            await message.channel.send(f'A link already exists for {entry}: Updating link...')
        else:
            # The user is likely unaware that there is a link at this entry
            await send_help(
                f'A link already exists for {entry}, and you did not specify to update using --update.',
                message
            )
            return

    # Update the imported link data
    meeting_link_data.update({entry: link})

    # Save the updated data to the JSON file at LINK_FP
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
    help_embed = discord.Embed(
        title='Commands Help',
        description='How to use me to register and serve up meeting notes!',
        color=0xff0000
    )

    help_embed.add_field(
        name='Serve notes',
        value='Usage: !notes serve <NAME>'
    )

    help_embed.add_field(
        name="this is a test",
        value="of what embeds look like. this embed is not inline",
        inline=False
    )

    help_embed.add_field(
        name="this is another test",
        value="of what embeds look like. this embed is inline",
        inline=True
    )

    await message.channel.send(error_msg)
    await message.channel.send(embed=help_embed)


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
