#!/usr/bin/env -S uv run --script
# fmt: off
#MISE description="Send a product update email to every confirmed subscriber"
#USAGE flag "-s --subject <subject>" required=#true help="The email's subject line"
#USAGE flag "-b --body-file <file>" required=#true help="Plain-text body; blank lines separate paragraphs"
# fmt: on
"""Send a product update to every confirmed subscriber.

The usage header parses the flags into usage_* env vars; the tested logic
lives in src/app/cli.py. Unlike standalone generator-style tasks, this
script carries no inline script metadata on purpose: without it, uv runs
it in the project environment (with it, uv isolates the script and ignores
the project — and this app is package = false, so it cannot be a script
dependency either). mise runs tasks from the project root, which the src
import path needs. In dev (ENVIRONMENT=dev + MY_UUID) the send is
restricted to you — the test-send path.
"""

import logging
import os
import sys


def main() -> int:
    sys.path.insert(0, os.getcwd())
    from src.app.cli import run_announcement

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    return run_announcement(os.environ["usage_subject"], os.environ["usage_body_file"])


if __name__ == "__main__":
    sys.exit(main())
