#!/usr/bin/env python3

from abc import ABC, abstractmethod
from collections import namedtuple
import csv
from datetime import datetime
from enum import Enum, auto
import os

import toml

CONFIG_PATH = "/etc/songsparrow-ii.toml"
OUTPUT_DIRECTORY = "/var/log/songsparrow-ii/"
LOG_EXTENSION = "tsv"
LOG_DELIMITER = "\t"


class Side(Enum):
    A = "a"
    B = "b"

    def other(self):
        return self.A if self is self.B else self.B


Press = namedtuple("Press", ("when", "key", "song_played"))


def simple_quota_schedule(key, history):
    quota = 30

    """Given a pressed key and a list of previous presses from earlier in the
    day, return which song to play """
    spent = len([press for press in history if press.key is key])
    return key if spent < quota else None


def get_log_path(config, when):
    day = when.strptime("%Y-m-d")
    return os.path.join(OUTPUT_DIRECTORY, f"{day}.{LOG_EXTENSION}")


def log_press(config, press):
    path = get_log_path(config, press.when)
    existed_already = os.path.isfile(path)
    with open(path, "a") as log_file:
        writer = csv.DictWriter(
            log_file,
            delimiter=LOG_DELIMITER,
            fieldnames=["timestamp", "key", "song_played"],
        )
        if not existed_already:
            # write a header row
            writer.writeheader()
        writer.writerow(
            {
                "timestamp": press.when.timestamp(),
                "key": config["key_labels"][press.key.value],
                "song_played": config["song_labels"].get(press.key.value, ""),
            }
        )


def parse_log_row(config, row):
    def unlabel(song_label):
        if song_label == config["song_labels"][Side.A.value]
    when = float(row["timestamp"])
    key = Side.A if row["key"] == config["key_labels"][Side.A.value] else Side.B
    song_played = unlabel(row["song_played"])
    return Press(when, key, song_played)


def parse_log(config, when):
    path = get_log_path(config, when)
    if not os.path.isfile(path):
        return []
    with open(path, "r") as log_file:
        reader = csv.DictReader(log_file, delimiter=LOG_DELIMITER)
        return [parse_log_row(config, row) for row in reader[1:]]


def read_config():
    with open(CONFIG_PATH, "r") as config_file:
        return toml.load(config_file)


if __name__ == "__main__":
    config = read_config()
    history = parse_log(config)
