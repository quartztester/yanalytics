#!/usr/bin/env python3

import argparse
import hashlib
import uuid
from pathlib import Path

import requests

from .config import get_config


class YanalyticsInstance:
    def __init__(self, server: str, id_file: str) -> None:
        self.server = server
        self.base_id = self._load_or_create_id(Path(id_file))

    def _raise_err(self, response: requests.Response) -> None:
        if not response.ok:
            msg: str | dict[str, str] = response.json()
            if isinstance(msg, dict):
                msg = msg["error"]
            raise RuntimeError(msg)

    @staticmethod
    def _load_or_create_id(path: Path) -> str:
        """Random installation id, generated on first run and never sent
        to the server. Not derived from /etc/machine-id: that is a stable
        secret shared by cloned images and reversible by anyone who knows
        it."""
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(uuid.uuid4().hex)
        return path.read_text().strip()

    def uuid_for(self, tag: str) -> str:
        """Deterministic per-tag pseudonym of the installation id.

        Each tag (an app name, or "instance") yields an unrelated value,
        so the server can dedup repeat reports of one app without being
        able to tell that two reports come from the same installation.
        """
        return hashlib.sha256(f"{self.base_id}:{tag}".encode()).hexdigest()

    def push_stats(self) -> None:
        data: dict[str, str | dict[str, str]] = {
            "uuid": self.uuid_for("instance"),
            "versions": {
                "debian": "",
                "yunohost": "",
            },
        }
        url = f"{self.server}/api/v1/instance/analytic"
        response = requests.post(url, json=data, timeout=60)
        self._raise_err(response)

    def push_apps(self, apps: list[str]) -> None:
        url = f"{self.server}/api/v1/app/analytic"
        for app in apps:
            response = requests.post(
                url, json={"uuid": self.uuid_for(app), "app": app}, timeout=60
            )
            self._raise_err(response)

    def delete_apps(self, apps: list[str]) -> None:
        url = f"{self.server}/api/v1/app"
        for app in apps:
            response = requests.delete(
                url, params={"uuid": self.uuid_for(app), "app": app}, timeout=60
            )
            self._raise_err(response)

    def instance_delete(self) -> None:
        data = {"uuid": self.uuid_for("instance")}
        url = f"{self.server}/api/v1/instance"
        response = requests.delete(url, params=data, timeout=60)
        self._raise_err(response)


def show_analytics(server: str) -> None:
    pass


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-s", "--server", type=str, help="Yanalytics server", required=False
    )
    parser.add_argument("-c", "--config", type=Path, help="Configuration file")

    sub = parser.add_subparsers(required=True, dest="mode")
    parser_inst = sub.add_parser("instance")
    parser_inst.add_argument("action", type=str, choices=["push", "delete"])

    parser_apps = sub.add_parser("apps")
    parser_apps.add_argument("action", type=str, choices=["push", "delete"])
    parser_apps.add_argument("app", nargs="+", help="installed app ids")

    sub.add_parser("analytics")

    args = parser.parse_args()

    config = get_config(args.config)

    server = args.server or config.analytics_server
    if "://" not in server:
        server = f"https://{server}"

    match args.mode:
        case "instance":
            instance = YanalyticsInstance(server, config.id_file)
            match args.action:
                case "push":
                    instance.push_stats()
                case "delete":
                    instance.instance_delete()

        case "apps":
            instance = YanalyticsInstance(server, config.id_file)
            match args.action:
                case "push":
                    instance.push_apps(args.app)
                case "delete":
                    instance.delete_apps(args.app)

        case "analytics":
            show_analytics(server)


if __name__ == "__main__":
    main()
