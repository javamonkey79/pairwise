#!/usr/bin/env python

# from __future__ import print_function, division, absolute_import, unicode_literals
from __future__ import print_function, division, absolute_import
import argparse
import json
# import os.path
# import sys

import slacker

HISTORY = "./pairwise_history.json"
CREDS = "./slack_creds.json"


def parse_cli(test_args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dry-run", dest="dry_run", action='store_true',
                        help="dry run everything")
    if test_args is None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(test_args)
    return args


def get_slack_details(args):
    global CREDS
    with open(CREDS, 'r') as f:
        jdict = json.load(f)
    try:
        slack_api_token = jdict['slack_api_token']
    except KeyError:
        sys.exit("ERROR: {0} must specify a key 'slack_api_token'".format(CREDS))
    args.slack = slacker.Slacker(slack_api_token)
    try:
        args.user = jdict['user']
    except:
        sys.exit("ERROR: {0} must specify a key 'user' for your slack username".format(CREDS))
    try:
        args.channel = jdict['channel']
    except:
        sys.exit("ERROR: {0} must specify a key 'channel' for the channel to post all pairings".format(CREDS))
    try:
        args.dm_template_two = jdict['dm_template_two']
    except KeyError:
        args.dm_template_two = "Hey @{0}! you've been paired with @{1} in #face-to-face.  Please setup a meeting when you can.  If you have any questions, concerns or issues, please contact @{2}"
    try:
        args.dm_template_three = jdict['dm_template_three']
    except KeyError:
        args.dm_template_three = "Hey @{0}! you've been paired with @{1} and @{2} in #face-to-face.  Please setup a meeting when you can.  If you have any questions, concerns or issues, please contact @{3}"
    if args.user.startswith("@"):
        sys.exit("ERROR: user value in slack_creds file can not start with an @ sign")
    if args.channel.startswith("#"):
        sys.exit("ERROR: channel value in slack_creds file can not start with an # sign")


def get_most_recent_pairs(args):
    global HISTORY
    with open(HISTORY, 'r') as f:
        history = json.load(f)
    latest_key = sorted(history.keys())[-1]
    return history[latest_key]


def make_messages(pair, args):
    messages = {}
    # key will be recipient, value will be message
    if len(pair) == 2:
        messages[pair[0]] = args.dm_template_two.format(pair[0], pair[1], args.user)
        messages[pair[1]] = args.dm_template_two.format(pair[1], pair[0], args.user)
    elif len(pair) == 3:
        messages[pair[0]] = args.dm_template_three.format(pair[0], pair[1], pair[2], args.user)
        messages[pair[1]] = args.dm_template_three.format(pair[1], pair[0], pair[2], args.user)
        messages[pair[2]] = args.dm_template_three.format(pair[2], pair[0], pair[1], args.user)
    return messages


def send_message_pairings(pair, args):
    "Formats messages and sends as DMs to the appropriate users"
    messages = make_messages(pair, args)
    for recipient in messages:
        if args.dry_run is True:
            print("This message would be sent to {0}".format(recipient))
            print(messages[recipient])
        else:
            try:
                args.slack.chat.post_message("@" + recipient, messages[recipient], username=args.user)
            except Exception:
                print("could not pair: " + recipient + ", " + messages[recipient] + ", " + args.user)
    if args.dry_run is True:
        print()


def send_all_pairings(pairs, args):
    message = ""
    counter = 0
    for pair in pairs:
        counter += 1
        if len(pair) == 2:
            message += "Pair {0:02d}: {1} and {2}\n".format(counter, pair[0], pair[1])
        elif len(pair) == 3:
            message += "Pair {0:02d}: {1}, {2} and {3}\n".format(counter, pair[0], pair[1], pair[2])
    if args.dry_run is True:
        print("would send this message to {0}".format(args.channel))
        print(message)
    else:
        args.slack.chat.post_message(args.channel, message, username=args.user)


def main():
    args = parse_cli()
    get_slack_details(args)
    pairs = get_most_recent_pairs(args)
    for pair in pairs:
        send_message_pairings(pair, args)
    send_all_pairings(pairs, args)


if __name__ == "__main__":
    main()
