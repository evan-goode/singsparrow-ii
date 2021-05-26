#!/usr/bin/env python3

"""SingSparrow II operant conditioning software"""

from collections import namedtuple
import csv
from datetime import datetime
from functools import partial
from gpiozero import Button
import os
from pathlib import Path
import random
from signal import pause
import subprocess
import time  # TODO

import toml

CONFIG_PATH = "/etc/singsparrow-ii.toml"
OUTPUT_DIRECTORY = "/var/log/singsparrow-ii/"

Event = namedtuple("Event", ("when", "sensor", "song_played"))


def other_side(side):
    """In the case that there are two sensors and two songs, return the sensor
    or song on the other side"""
    return int(not side)


def simple_quota_schedule(_config, key, _when, history):
    """If the quota has been reached, play nothing. Otherwise, play the
    associated song."""
    quota = 50

    spent = sum(1 for press in history if press.song_played == key)

    print("spent:", spent)
    return key if spent < quota else None


def self_balancing_schedule(_config, key, _when, history):
    """Attempt to balance the number of plays of each song while maintaining
    the associations between key and song"""
    quota = 50

    maximum_odds = 3 / 4
    minimum_odds = 1 / 2

    def compute_odds(value, maximum, minimum, halfway):
        """Exponentially decay from `maximum`, asymptotically to `minimum`,
        crossing the arithmetic mean of `maximum` and `minimum` at value =
        `halfway`"""
        difference = maximum - minimum
        return (difference / (2 ** (value / halfway))) + minimum

    other = other_side(key)

    key_plays = sum(1 for press in history if press.song_played == key)
    other_plays = sum(1 for press in history if press.song_played == other)

    if key_plays >= quota and other_plays >= quota:
        return None
    if key_plays >= quota:
        return other
    if other_plays >= quota:
        return key

    if key_plays < other_plays or (history and history[-1].key == other):
        return key

    deficit = key_plays - other_plays

    odds = compute_odds(deficit, maximum_odds, minimum_odds, 1 / 4 * quota)
    return key if random.random() < odds else other


def get_day(when):
    """Format a datetime `when` as an ISO 8601 date"""
    return when.strftime("%Y-%m-%d")


def get_log_path(when):
    """Given a datetime `when`, get the path to the appropriate log file"""
    os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)
    return os.path.join(OUTPUT_DIRECTORY, f"{get_day(when)}.tsv")


def get_label(the_item, items):
    """Given the index of a sensor or song, return its label"""
    if the_item is None:
        return repr(the_item)
    try:
        return items[the_item]["label"]
    except IndexError as error:
        raise RuntimeError(f"") from error


def unlabel(the_label, items):
    """Given the label of a sensor or song, return its index"""
    if the_label == repr(None):
        return None
    for index, item in enumerate(items):
        if item["label"] == the_label:
            return index
    raise RuntimeError(
        f'Couldn\'t tell what "{the_label}" refers to. '
        "Corrupt log, or maybe labels were changed in {CONFIG_PATH}?"
    )


def log_event(config, event):
    """Log an event to the appropriate TSV file"""
    path = get_log_path(event.when)
    existed_already = os.path.isfile(path)
    with open(path, "a") as log_file:
        writer = csv.DictWriter(
            log_file, delimiter="\t", fieldnames=["timestamp", "sensor", "song-played"]
        )
        if not existed_already:
            writer.writeheader()
        writer.writerow(
            {
                "timestamp": event.when.timestamp(),
                "sensor": get_label(event.sensor, config["sensor"]),
                "song-played": get_label(event.song_played, config["song"]),
            }
        )


def parse_log_row(config, row):
    """Parse an Event from one row of a log file"""
    when = datetime.fromtimestamp(float(row["timestamp"]))
    sensor = unlabel(row["sensor"], config["sensor"])
    song_played = unlabel(row["song-played"], config["song"])
    return Event(when, sensor, song_played)


def parse_log(config, when):
    """Read Events from earlier in the day"""
    path = get_log_path(when)
    if not os.path.isfile(path):
        return []
    with open(path, "r") as log_file:
        reader = csv.DictReader(log_file, delimiter="\t")
        return [parse_log_row(config, row) for row in reader]


def verify_readable(path):
    """Raise an error if `path` is unreadable"""
    try:
        open(path).close()
    except IOError as error:
        raise RuntimeError(f"Couldn't open {path} for reading!") from error


def verify_writable(path):
    """Raise an error if `path` is unwritable"""
    existed_already = os.path.isfile(path)
    try:
        Path(path).touch(exist_ok=True)
    except OSError as error:
        raise RuntimeError(f"Couldn't open {path} for writing!") from error
    if not existed_already:
        os.remove(path)


def read_config():
    """Read and validate the TOML config file"""
    with open(CONFIG_PATH, "r") as config_file:
        config = toml.load(config_file)
    for song in config["song"]:
        verify_readable(song["path"])
    return config


def play_song(config, song):
    """Play a song given its index"""
    subprocess.check_call(["aplay", config["song"][song]["path"]])


schedule_map = {
    "simple": simple_quota_schedule,
    "self-balancing": self_balancing_schedule,
}


def main():
    """Entry point"""
    config = read_config()
    schedule = schedule_map[config["schedule"]]
    verify_writable(get_log_path(when=datetime.now()))
    history = parse_log(config, datetime.now())
    print(f"Read {len(history)} events from history.")

    def handle_sensor(sensor):
        now = datetime.now()
        if history and get_day(now) != get_day(history[-1].when):
            print("It's a new day, clearing history...")
            history.clear()

        song = schedule(config, sensor, now, history)
        if song is not None:
            play_song(config, song)
        event = Event(now, sensor, song)
        print(f"Logging {event}...")
        history.append(event)
        log_event(config, event)

    for index, sensor in enumerate(config["sensor"]):
        button = Button(sensor["pin"])
        button.when_pressed = partial(handle_sensor, index)
    pause()


if __name__ == "__main__":
    main()
