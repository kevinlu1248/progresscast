# wrapper for the Firebase functions backend

from multiprocessing.dummy import Pool
from io import StringIO
import sys

import requests
from typing import Tuple, Type, Union

# TODO: configure rest api connection since it's faster, using database rules
# https://firebase.google.com/docs/database/rest/start
# https://firebase.google.com/docs/database/rest/retrieve-data#section-rest-streaming


class Connection:
    API_URL: str = "https://us-central1-progresscast.cloudfunctions.net/api/"
    VALID_STATUSES: Tuple[str, str, str, str, str] = (
        "not started",
        "in progress",
        "completed",
        "error",
        "disconnected or crashed",
    )

    def __init__(
        self,
        total: int,
        current: int = 0,
        status: str = "not started",
        do_print_url: bool = True,
        do_use_async: bool = True,
        do_raise_request_error: bool = False,
        do_capture_log: bool = True
    ) -> None:
        if total <= 0:
            raise ValueError("Total must be positive")
        if current < 0:
            raise ValueError("Current progress cannot be negative")
        if status not in Connection.VALID_STATUSES:
            raise TypeError(
                f"{status} is not a valid status, must be one of {Connection.VALID_STATUSES}"
            )

        self.total: int = total
        self.current: int = current
        self.status: str = status
        self.new_log: StringIO = StringIO()
        self.do_raise_request_error: bool = do_raise_request_error
        self.do_capture_log: bool = do_capture_log

        self.do_use_async = do_use_async
        if do_use_async:
          self.pool = Pool()

        response = requests.post(
            Connection.API_URL + "getKey",
            json={"total": total, "current": current, "status": status},
        )
        if response.ok:
            responseObj = response.json()
            self.slug = responseObj["slug"]
            self.url = "https://progresscast.web.app/" + self.slug
            if do_print_url:
                print(f"Loading bar casted to {self.url} !")
            self.__apiKey = responseObj["apiKey"]
        else:
            raise Exception(f"Invalid response {response} from backend")

    def update(self, updateObj: dict):
        # Throws error on error, otherwise returns none
        assert self.slug and self.__apiKey and updateObj
        updateObj["slug"] = self.slug
        updateObj["apiKey"] = self.__apiKey

        if self.do_use_async: 
          def on_error(error):
            if self.do_raise_request_error:
              raise ConnectionError(f"Error updating data: {error}")

          self.pool.apply_async(
              requests.post,
              args=[Connection.API_URL + "update", updateObj],
              error_callback=on_error,
          )
        
        else:
          response = requests.post(Connection.API_URL + "update", json=updateObj)
          if not response.ok:
            raise Exception(f"Invalid response {response} from backend")

    def start_redirect_stdout(self):
      if self.do_capture_log:
        self._stdout = sys.stdout # temporary storage
        sys.stdout = self.new_log
    
    def stop_redirect_stdout(self) -> Union[str, None]:
      if self.do_capture_log:
        return_string = self.new_log.getvalue()
        sys.stdout = self._stdout
        self.new_log.close()
        self.new_log = StringIO()
        return return_string
      else:
        return None

    def close(self):
      if self.do_use_async:
        self.pool.close()
      if self.do_capture_log:
        self.stop_redirect_stdout()

    def __repr__(self):
        return f"Connection(slug={self.slug}, progress{self.current}/{self.total}, status={self.status})"


if __name__ == "__main__":
    conn = Connection(5)
    print(f"Got connection: {conn}")
    resp2 = conn.update({"current": 1})
    print(f"Got response on updating: {resp2}")
