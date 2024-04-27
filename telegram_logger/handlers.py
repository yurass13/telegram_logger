import atexit
import logging
import requests
import time

from multiprocessing import Queue

logger = logging.getLogger('TelegramLogger')


class TelegramHandler(logging.handlers.QueueHandler):
    def __init__(self, token: str, chat_id: str | list[str],
                 disable_notifications: bool = False, disable_preview: bool = False) -> None:
        queue = Queue()
        super().__init__(queue)

        self.handler = TelegramSender(token, chat_id, disable_notifications, disable_preview)
        listener = logging.handlers.QueueListener(queue, self.handler)
        listener.start()
        atexit.register(listener.stop)


class TelegramSender(logging.Handler):
    TIMEOUT = 10
    MAX_MSG_LEN = 4096
    API_CALL_INTERVAL = .1

    def __init__(self, token: str, chat_id: str | list[str],
                 disable_notifications: bool=False, disable_preview: bool=False) -> None:
        self.token = token
        self.chat_id = chat_id
        self.disable_notifications = disable_notifications
        self.disable_preview = disable_preview
        self.session = requests.Session()
        super().__init__()


    @property
    def url_format_sting(self):
        return "https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={text}&" \
               "disable_web_page_preview={disable_web_page_preview}&disable_notifications={disable_notifications}"

    def handle(self, record):
        """
        Perform message splitting in case if it is big
        """
        record = self.format(record)

        # if len(record) > self.MAX_MSG_LEN:
        #     # telegram max length of text is 4096 chars, we need to split our text into chunks

        #     start_chars, end_chars = "", self.formatter.END_CODE_BLOCK
        #     start_idx, end_idx = 0, self.MAX_MSG_LEN - len(end_chars)  # don't forget about markdown symbols (```)
        #     new_record = record[start_idx:end_idx]

        #     while new_record:
        #         # remove whitespaces, markdown fmt symbols and a carriage return
        #         new_record = start_chars + new_record.rstrip("` \n") + end_chars
        #         self.emit(new_record)

        #         start_chars, end_chars = self.formatter.START_CODE_BLOCK, self.formatter.END_CODE_BLOCK
        #         start_idx, end_idx = end_idx, end_idx + self.MAX_MSG_LEN - (len(start_chars) + len(end_chars))
        #         new_record = record[start_idx:end_idx]
        # else:
        self.emit(record)

    def emit(self, record, chat_id: str | None = None):
        if isinstance(self.chat_id, str): 
            url = self.url_format_sting.format(
                token=self.token,
                chat_id=chat_id if chat_id is not None else self.chat_id,
                # mode=self.formatter.MODE,
                text=record,
                disable_web_page_preview=self.disable_preview,
                disable_notifications=self.disable_notifications
            )

            response = self.session.get(url, timeout=self.TIMEOUT)
            if not response.ok:
                logger.warning("Telegram log dispatching failed with status code '%s'" % response.status_code)
                logger.warning("Response is: %s" % response.text)

            # telegram API restrict more than 30 calls per second, this is a very pessimistic sleep,
            # but should work as a temporary workaround
            time.sleep(self.API_CALL_INTERVAL)
        else:
            for chat_id_ in self.chat_id:
                self.emit(record, chat_id_)

    def __del__(self):
        self.session.close()
