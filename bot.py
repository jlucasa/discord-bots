import discord
import os
import json
import validators
import glob
import boto3
from botocore import exceptions
from dotenv import load_dotenv


# TODO: make dictionary of arguments for each function to provide help with more modularity
# TODO: make functions part of an object to safely store information in sessions

# Instantiate client and load environment
client = discord.Client()
load_dotenv()

s3_conn = boto3.resource(
    service_name='s3',
    region_name='us-west-1',
    aws_access_key_id=os.getenv('ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('SECRET_ACCESS_KEY')
)

prefix = '!waiter'


# Register a link to a note in the JSON file at LINK_FP
async def register_note(message, args=None, reserves=None):
    if not args:
        # Args could not be passed in some way
        await send_help(message, error_msg=f'Could not interpret register command {message.content}')
        return

    if len(args) < 3:
        # There are not enough arguments to complete the command
        await send_help(message, error_msg=f'Not enough arguments in "{message.content}"')
        return

    # Filepath is first argument, entry is second argument, link is third argument
    # Note link is first argument, entry is second argument
    fp = f'link-files/{args[0]}'
    entry = args[1]
    link = args[2]
    should_update = True if len(args) == 4 and args[3] == '--update' else False

    file_retrieval_code = await file_already_exists_check(fp)

    if file_retrieval_code == 1:
        await message.channel.send(f'Invalid filepath')
        return
    elif file_retrieval_code == 2:
        await message.channel.send('Something went wrong when retrieving your file')
        return

    if not validators.url(link):
        # URL is not valid
        await message.channel.send(f'Invalid URL: {link}')
        return

    if entry in reserves:
        # Entry is a reserved word
        await message.channel.send(f'This entry name is reserved: {entry}')
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
                message,
                error_msg=f'A link already exists for {entry}, and you did not specify to update using --update.'
            )
            return

    # Update the imported link data
    meeting_link_data.update({entry: link})

    # Save the updated data to the JSON file at fp
    await save_to_json_file(meeting_link_data, fp)

    await message.channel.send(f'Saved link for {entry}')


async def serve_note(message, args=None, reserves=None):
    if not args:
        await send_help(message, error_msg='Could not interpret serve command')
        return

    if len(args) < 2:
        await send_help(message, error_msg=f'Not enough arguments in "{message.content}"')
        return

    fp = f'link-files/{args[0]}'
    entry = args[1]

    meeting_link_data = await open_json_file(fp)

    if entry not in meeting_link_data.keys():
        await message.channel.send(f'No link exists for {entry}')
        return

    await message.channel.send(f'Here\'s that link! {meeting_link_data[entry]}')


async def search_for_notes(message, args=None, reserves=None):
    if not args:
        await send_help(message, error_msg='Could not interpret search command')
        return

    if len(args) < 2:
        await send_help(message, error_msg=f'Not enough arguments in "{message.content}"')
        return

    fp = f'link-files/{args[0]}'
    search_entry = args[1]

    data = await open_json_file(fp)
    all_entries = list(data.keys())
    results = []

    file_retrieval_code = await file_already_exists_check(fp)

    if file_retrieval_code == 1:
        await send_help(message, error_msg=f'File "{fp}" doesn\'t exist')
        return
    elif file_retrieval_code == 2:
        await message.channel.send('Something went wrong when retrieving the file')
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
            value=f'Command: {prefix} serve {fp} {result_i}'
        )

    await message.channel.send(embed=results_embed)


async def register_notefile(message, args=None, reserves=None):
    if not args:
        # Args could not be passed in some way
        await send_help(message, error_msg='Could not interpret regfile command')
        return

    if args[0] in reserves:
        await message.channel.send(f'Reserved file name: {args[0]}')
        return

    notefp = f'link-files/{args[0]}'
    file_retrieval_code = await file_already_exists_check(notefp)

    if file_retrieval_code == 0:
        await send_help(message, error_msg=f'File {notefp} already exists')
        return
    elif file_retrieval_code == 2:
        await message.channel.send('Something went wrong when retrieving your file')
        return

    await create_json_file(notefp)
    await message.channel.send(f'Successfully created note file {notefp}')


async def list_allfiles(message, args=None, reserves=None):
    all_objs = s3_conn.Bucket('jamens-link-bucket').objects.filter(Delimiter='/', Prefix='link-files/')

    if len([all_objs]) == 0:
        await message.channel.send('There were no files to be found!')
        return

    files_embed = discord.Embed(
        title='All files',
        color=0xff0000
    )

    for file_obj in all_objs:
        files_embed.add_field(
            name=file_obj.key.split('/')[-1],
            value='test'
        )

    await message.channel.send(embed=files_embed)


async def send_help(message, args=None, error_msg=None, reserves=None):
    help_embed = discord.Embed(
        title='Commands Help',
        description='Here\'s what I can do for you! I don\'t get paid enough for this',
        color=0xff0000
    )

    help_embed.add_field(
        name='Serve link',
        value=f'Serves a link based on an entry.\nUsage: {prefix} serve <FILENAME> <ENTRYNAME>'
    )

    help_embed.add_field(
        name='Register link',
        value=f'Registers a link with an entry.\nUsage: {prefix} register <FILENAME> <ENTRYNAME> <LINK>',
    )

    help_embed.add_field(
        name='Register file',
        value=f'Registers a file. \nUsage: {prefix} registerfile <FILENAME>'
    )

    help_embed.add_field(
        name='List all files',
        value=f'Lists all files. \nUsage: {prefix} listallfiles'
    )

    if error_msg is not None:
        await message.channel.send(error_msg)
    await message.channel.send(embed=help_embed)


async def download_file(src_fp, dest_fp):
    s3_conn.Bucket('jamens-link-bucket').download_file(Key=src_fp, Filename=dest_fp)


async def upload_file(src_fp, dest_fp):
    s3_conn.Bucket('jamens-link-bucket').upload_file(Filename=src_fp, Key=dest_fp)


async def open_json_file(fp):
    dest_fp = fp.split('/')[-1]

    await download_file(fp, dest_fp)

    with open(dest_fp) as file:
        return json.load(file)
    # s3_conn.Bucket('jamens-link-bucket').download_file(Key=fp, Filename=dest_fp)


    # with open(dest_fp, 'w+') as file:
    #     print(file)
    #     return json.load(file)

    # try:
    #     s3_conn.Bucket('jamens-link-bucket').download_file(Key=fp, Filename=fp)
    #
    #     with open(fp, 'w') as file:
    #         return json.load(file)
    # except exceptions.ClientError as e:
    #     if e.response['Error']['Code'] == '404':
    #         return json.loads('{"ERROR": "Not Found"}')
    #
    #     return json.loads('{"ERROR": "Something unknown went wrong."}')


async def save_to_json_file(data, fp):
    src_fp = fp.split('/')[-1]

    with open(src_fp, 'w') as file:
        json.dump(data, file)

    await upload_file(src_fp, fp)
    os.remove(src_fp)


async def create_json_file(fp):
    src_fp = fp.split('/')[-1]

    with open(src_fp, 'w+') as file:
        json.dump({"START": "TEST"}, file)

    s3_conn.Bucket('jamens-link-bucket').upload_file(Filename=fp.split('/')[-1], Key=fp)
    os.remove(src_fp)


'''
Returns 0 for already exists, 1 for could not find, and 2 for 
something went wrong.
'''
async def file_already_exists_check(fp):
    try:
        s3_conn.Bucket('jamens-link-bucket').Object(key=fp).load()
    except exceptions.ClientError as e:
        if int(e.response['Error']['Code']) == 404:
            return 1
        return 2

    return 0

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

    # for obj in s3_conn.Bucket('jamens-link-bucket').objects.all():
    #     print(obj)

@client.event
async def on_message(message):
    command_map = {
        'register': register_note,
        'serve': serve_note,
        'registerfile': register_notefile,
        'search': search_for_notes,
        'listallfiles': list_allfiles,
        'help': send_help
    }

    reserved_words = [
        'ERROR'
    ]

    if message.author == client.user:
        return

    if message.content.strip() == prefix:
        await send_help(message, error_msg='You didn\'t seem to put a command in!')
        return

    if message.content.startswith(prefix):
        split_message = message.content.split()
        command = split_message[1]
        message_args = split_message[2:] if len(split_message) >= 3 else None

        if command not in command_map.keys():
            await send_help(message, error_msg=f'Could not interpret command {command}')
            return

        await command_map[command](message, args=message_args, reserves=reserved_words)


def main():
    client.run(os.getenv('BOT_TOKEN'))


if __name__ == '__main__':
    main()
