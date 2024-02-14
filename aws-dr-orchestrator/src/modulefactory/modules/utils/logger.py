##############################################################################
#  Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.   #
#                                                                            #
#  Licensed under the Apache License, Version 2.0 (the "License").           #
#  You may not use this file except in compliance                            #
#  with the License. A copy of the License is located at                     #
#                                                                            #
#      http://www.apache.org/licenses/LICENSE-2.0                            #
#                                                                            #
#  or in the "license" file accompanying this file. This file is             #
#  distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY  #
#  KIND, express or implied. See the License for the specific language       #
#  governing permissions  and limitations under the License.                 #
##############################################################################

import json
import logging

from .datetime_encoder import DateTimeEncoder


class Logger(object):
    def __init__(self, loglevel="info"):
        """Initializes logging"""
        self.config(loglevel=loglevel)

    def config(self, loglevel="info"):
        loglevel = logging.getLevelName(loglevel.upper())
        main_logger = logging.getLogger()
        main_logger.setLevel(loglevel)

        logfmt = (
            '{"time_stamp": "%(asctime)s",'
            '"log_level": "%(levelname)s",'
            '"log_message": %(message)s}\n'
        )
        if len(main_logger.handlers) == 0:
            main_logger.addHandler(logging.StreamHandler())
        main_logger.handlers[0].setFormatter(logging.Formatter(logfmt))
        self.log = logging.LoggerAdapter(main_logger, {})

    def _format(self, message):
        """formats log message in json, return string as is

        Args:
        message (str): log message, can be a dict, list, string, or json blob
        """
        if isinstance(message, str):
            return message
        try:
            message = json.loads(message)
        except Exception:
            pass
        try:
            return json.dumps(message, indent=4, cls=DateTimeEncoder)
        except Exception:
            return json.dumps(str(message))

    def debug(self, message, **kwargs):
        """wrapper for logging.debug call"""
        self.log.debug(self._format(message), **kwargs)

    def info(self, message, **kwargs):
        # type: (object, object) -> object
        """wrapper for logging.info call"""
        self.log.info(self._format(message), **kwargs)

    def warning(self, message, **kwargs):
        """wrapper for logging.warning call"""
        self.log.warning(self._format(message), **kwargs)

    def error(self, message, **kwargs):
        """wrapper for logging.error call"""
        self.log.error(self._format(message), **kwargs)

    def critical(self, message, **kwargs):
        """wrapper for logging.critical call"""
        self.log.critical(self._format(message), **kwargs)

    def exception(self, message, **kwargs):
        """wrapper for logging.exception call"""
        self.log.exception(self._format(message), **kwargs)

    def log_unhandled_exception(self, message):
        """log unhandled exception"""
        self.log.exception("Unhandled Exception: {}".format(message))

    def log_general_exception(self, file, method, exception):
        """log general exception"""
        message = {"FILE": file, "METHOD": method, "EXCEPTION": str(exception)}
        self.log.exception(self._format(message))
