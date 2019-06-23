#!/usr/bin/env python3

from collections import namedtuple
import csv
from datetime import datetime
import os
from pathlib import Path
import random
import subprocess
import time  # TODO

import toml

CONFIG_PATH = "/etc/singsparrow-ii.toml"
OUTPUT_DIRECTORY = "/var/log/singsparrow-ii/"
LOG_EXTENSION = "tsv"
LOG_DELIMITER = "\t"

SIDE_A = "a"
SIDE_B = "b"
SIDE_NEITHER = "neither"


Press = namedtuple("Press", ("when", "key", "song_played"))


def other_side(side):
    return SIDE_A if side == SIDE_B else SIDE_B


def simple_quota_schedule(config, key, when, history):
    """If the quota has been reached, play nothing. Otherwise, play the
    associated song."""
    quota = 50

    spent = sum(1 for press in history if press.song_played == key)
    print("spent is: ", spent)
    return key if spent < quota else SIDE_NEITHER


def self_balancing_schedule(config, key, history):
    """Attempt to balance the number of plays of each song while maintaining
    the associations between key and song"""
    quota = 50

    maximum_odds = 3 / 4
    minimum_odds = 1 / 2

    def compute_odds(x, a, b, halfway):
        """Exponentially decay from `a`, asymptotically to `b`, crossing the
        arithmetic mean of `a` and `b` at x = `halfway`"""
        return ((a - b) / (2 ** (x / halfway))) + b

    other = other_side(key)

    key_plays = sum(1 for press in history if press.song_played == key)
    other_plays = sum(1 for press in history if press.song_played == other)

    if key_plays >= quota and other_plays >= quota:
        return SIDE_NEITHER
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
    return when.strftime("%Y-%m-%d")


def get_log_path(when):
    os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)
    return os.path.join(OUTPUT_DIRECTORY, f"{get_day(when)}.{LOG_EXTENSION}")


def log_press(config, press):
    path = get_log_path(press.when)
    existed_already = os.path.isfile(path)
    with open(path, "a") as log_file:
        writer = csv.DictWriter(
            log_file,
            delimiter=LOG_DELIMITER,
            fieldnames=["timestamp", "key", "song-played"],
        )
        if not existed_already:
            writer.writeheader()
        writer.writerow(
            {
                "timestamp": press.when.timestamp(),
                "key": config["key-labels"][press.key],
                "song-played": config["song-labels"][press.song_played],
            }
        )


def parse_log_row(config, row):
    def unlabel(the_label, labels):
        for side, label in labels.items():
            if label == the_label:
                return side
        raise ValueError(
            f'Couldn\'t tell which side "{the_label}" was on. '
            "Corrupt log, or maybe labels were changed in {CONFIG_PATH}?"
        )

    when = datetime.fromtimestamp(float(row["timestamp"]))
    key = unlabel(row["key"], config["key-labels"])
    song_played = unlabel(row["song-played"], config["song-labels"])
    return Press(when, key, song_played)


def parse_log(config, when):
    path = get_log_path(when)
    if not os.path.isfile(path):
        return []
    with open(path, "r") as log_file:
        reader = csv.DictReader(log_file, delimiter=LOG_DELIMITER)
        return [parse_log_row(config, row) for row in reader]


def verify_readable(path):
    try:
        open(path).close()
    except IOError as error:
        raise RuntimeError(f"Couldn't open {path} for reading!") from error


def verify_writable(path):
    existed_already = os.path.isfile(path)
    try:
        Path(path).touch(exist_ok=True)
    except OSError as error:
        raise RuntimeError(f"Couldn't open {path} for writing!") from error
    if not existed_already:
        os.remove(path)


def read_config():
    def verify_path(config, *path):
        for key in path:
            try:
                config = config[key]
            except KeyError as error:
                message = f'Couldn\'t find option "{".".join(path)} in config file!'
                raise RuntimeError(message) from error

    with open(CONFIG_PATH, "r") as config_file:
        config = toml.load(config_file)

        # get the KeyErrors out of the way before we get going
        for side in ("a", "b"):
            verify_path(config, "key-labels", side)
            verify_path(config, "key-pins", side)
            verify_path(config, "song-labels", side)
            verify_path(config, "song-paths", side)
            verify_readable(config["song-paths"][side])
        verify_path(config, "song-labels", "neither")
        return config


def play_song(config, song):
    subprocess.check_call(["aplay", config["song-paths"][song]])


def main():
    config = read_config()
    verify_writable(get_log_path(when=datetime.now()))
    history = parse_log(config, datetime.now())
    print(f"Read {len(history)} presses from history.")

    def handle_key_press(key_pressed):
        now = datetime.now()
        if history and get_day(now) != get_day(history[-1].when):
            print("It's a new day, clearing history...")
            history.clear()

        song = simple_quota_schedule(config, key_pressed, now, history)
        if song != SIDE_NEITHER:
            play_song(config, song)
        press = Press(now, key=key_pressed, song_played=song)
        print(f"Logging {press}...")
        history.append(press)
        log_press(config, press)

    # simulations TODO
    time.sleep(1)
    for _ in range(30):
        handle_key_press(SIDE_A)
        handle_key_press(SIDE_B)


if __name__ == "__main__":
    main()
