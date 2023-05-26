# -*- coding: utf-8 -*-

from ws_server import get_app
from log.logger import logger

application = get_app()
logger.info("v2v ws server is running now.")


def main():
    get_app().run(port=8888, debug=True)


if __name__ == '__main__':
    main()
