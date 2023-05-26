# -*- coding: utf-8 -*-

import os
from flask_cors import CORS

from log.logger_name import set_logger_name
set_logger_name("v2v_ws_server")

from log.logger import logger
from server.locator import set_global_locator
from mc.mc_model import MCModel
from zk.dlocator import DLocator
from utils.pitrix_folder import PitrixFolder
from utils.global_conf import get_pg, get_zk, connect_zk, get_mc
from utils.misc import exit_program
from db.pg_model import PGModel
from db.constants import DB_GLOBAL

import context
import connexion
from connexion.apps.flask_app import FlaskJSONEncoder
from constants import PITRIX_CONF_HOME
from comm.base_client import BaseClient


class WebService(object):
    """ web service is a v2v restful server """

    def __init__(self, conf_file):
        """
        constructor
        :param conf_file:
        """

        self.conf_file = conf_file

        # initialize context
        ctx = context.instance()
        ctx.conf_file = conf_file
        if os.environ.get("ENV") == "local":
            PitrixFolder.build()
            PitrixFolder.CONF_HOME = "/pitrix/new_testing_conf"
            ctx.pattern = "local"
        # connect to postgresql db
        ctx.pg = get_pg(DB_GLOBAL, maxconn=50)
        if ctx.pg is None:
            logger.error("connect to PostgreSQL failed: can't connect")
            exit_program(-1)
        ctx.pgm = PGModel(ctx.pg)

        # connect to zookeeper
        ctx.locator = DLocator()
        ctx.zk = get_zk(WebService._zk_connect_cb,
                        WebService._zk_disconnect_cb)
        if 0 != connect_zk(ctx.zk):
            logger.error("connect to zookeeper failed: can't connect")
            exit_program(-1)

        set_global_locator(ctx.locator)

        # connect to memcached
        ctx.mcclient = get_mc()
        if not ctx.mcclient:
            logger.error("connect to memcached failed: can't connect")
            exit_program(-1)
        ctx.mcm = MCModel(ctx.mcclient)

        # shared base client
        ctx.client = BaseClient(use_sock_pool=True)

        self.connexion_app = connexion.App(__name__,
                                           specification_dir='./spec/')
        self.connexion_app.app.json_encoder = FlaskJSONEncoder
        self.connexion_app.add_api('swagger.yaml',
                                   arguments={'title': 'Swagger Petstore'})
        CORS(self.connexion_app.app)

    @staticmethod
    def _zk_disconnect_cb():
        """ callback when zookeeper is disconnected """
        # stop locator service
        ctx = context.instance()
        ctx.locator.stop()

    @staticmethod
    def _zk_connect_cb():
        """ callback when zookeeper is connected """
        # start locator service
        ctx = context.instance()
        ctx.locator.start(ctx.zk)

        # register self as server
        # 请求直接由外围的haproxy转发，uwsgi受理请求，因为app无需注册服务发现
        # from utils.constants import V2V_WEB_SERVICE_UWSGI_PORT
        # ctx.locator.register(SERVER_TYPE_V2V_WEB_SERVICE, get_hostname(), V2V_WS_PORT)

    def run(self, port=None, server=None, debug=None, host=None, **options):
        # pragma: no cover
        ctx = context.instance()
        ctx.conf_file = self.conf_file
        self.connexion_app.run(port=port, server=server, debug=debug,
                               host=host, **options)

    def __call__(self, environ, start_response):  # pragma: no cover
        """
        Makes the class callable to be WSGI-compliant.
        As Flask is used to handle requests, this is a passthrough-call to
          the Connexion/Flask callable class.
        This is an abstraction to avoid directly referencing the app attribute
          from outside the class and protect it from unwanted modification.
        """
        ctx = context.instance()
        ctx.conf_file = self.conf_file
        return self.connexion_app(environ, start_response)


def get_app():
    conf_file = "%s/%s.yaml" % (PITRIX_CONF_HOME, "v2v_ws")
    app = WebService(conf_file)
    logger.info("v2v ws server is running now.")
    return app


def main():
    get_app().run(port=8888, debug=True)


if __name__ == '__main__':
    main()

__all__ = [get_app]
