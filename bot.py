import discord
import os
import json
import validators
import glob
from dotenv import load_dotenv

# TODO: make dictionary of arguments for each function to provide help with more modularity
# TODO: make functions part of an object to safely store information in sessions

# Instantiate client and load environment
client = discord.Client()
load_dotenv()


# Register a link to a note in the JSON file at LINK_FP
async def register_note(message, args):
    if not args:
        # Args could not be passed in some way
        await send_help(f'Could not interpret register command {message.content}', message)
        return

    if len(args) < 3:
        # There are not enough arguments to complete the command
        await send_help(f'Not enough arguments in "{message.content}"', message)
        return

    # Filepath is first argument, entry is second argument, link is third argument
    # Note link is first argument, entry is second argument
    fp = f'./files/{args[0]}'
    entry = args[1]
    link = args[2]
    should_update = True if len(args) == 4 and args[3] == '--update' else False

    if not await file_already_exists_check(fp):
        await message.channel.send(f'Invalid filepath')

    if not validators.url(link):
        # URL is not valid
        await message.channel.send(f'Invalid URL: {link}')
        return

    # Fetch all the data from the JSON file at fp
    meeting_link_data = await open_json_file(fp)

    if entry in meeting_link_data:
        # There is already an entry with the given name in the JSON file at fp
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

    # Save the updated data to the JSON file at fp
    await save_to_json_file(meeting_link_data, fp)

    await message.channel.send(f'Saved link for {entry}')


async def serve_note(message, args):
    if not args:
        await send_help('Could not interpret serve command', message)
        return

    if len(args) < 2:
        await send_help(f'Not enough arguments in "{message.content}"', message)
        return

    fp = f'./files/{args[0]}'
    entry = args[1]

    meeting_link_data = await open_json_file(fp)

    if entry not in meeting_link_data.keys():
        await message.channel.send(f'No link exists for {entry}')
        return

    await message.channel.send(f'Here\'s that link! {meeting_link_data[entry]}')


async def search_for_notes(message, args):
    if not args:
        await send_help('Could not interpret search command', message)
        return

    if len(args) < 2:
        await send_help(f'Not enough arguments in "{message.content}"', message)
        return

    fp = f'./files/{args[0]}'
    search_entry = args[1]

    data = await open_json_file(fp)
    all_entries = list(data.keys())
    results = []

    if not await file_already_exists_check(fp):
        await send_help(f'File "{fp}" doesn\'t exist', message)
        return

    results.append(entry_i for entry_i in all_entries if entry_i.startswith(search_entry))

    if len(results) > 10:
        await message.channel.send('Greater than 10 results for entry -- only showing first 10')
        results = results[:10]

    results_embed = discord.Embed(
        title='Search Results',
        color=0xff0000
    )

    for result_i in results:
        results_embed.add_field(
            name=str(result_i),
            value=f'Command: !notes serve {fp} {result_i}'
        )

    await message.channel.send(embed=results_embed)


async def register_notefile(message, args):
    if not args:
        # Args could not be passed in some way
        await send_help('Could not interpret regfile command', message)
        return

    notefp = f'./files/{args[0]}'

    if await file_already_exists_check(notefp):
        await send_help(f'File {notefp} already exists', message)
        return

    await create_json_file(notefp)
    await message.channel.send(f'Successfully created note file {notefp}')


async def list_allfiles(message, args):
    os.chdir('files')
    all_files = glob.glob('*.json')
    os.chdir('..')

    if len(all_files) == 0:
        await message.channel.send('There were no files to be found!')
        return

    files_embed = discord.Embed(
        title='All files',
        color=0xff0000
    )

    for file in all_files:
        files_embed.add_field(
            name=file,
            value='test'
        )

    await message.channel.send(embed=files_embed)


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


async def create_json_file(fp):
    with open(fp, 'w+') as file:
        return


async def file_already_exists_check(fp):
    return os.path.exists(fp)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')


@client.event
async def on_message(message):
    command_map = {
        'reg': register_note,
        'serve': serve_note,
        'regfile': register_notefile,
        'search': search_for_notes,
        'listfiles': list_allfiles
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
