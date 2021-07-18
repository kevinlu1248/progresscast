# the main loadbar

from tqdm.auto import tqdm as std_tqdm # type: ignore

from connection import Connection


class LoadbarHelper(std_tqdm):
    def __init__(self, iterable=None, desc=None, total=None, *args, **kwargs):
        if total == None and hasattr(iterable, "__len__"):
            total = len(iterable)
        CONNECTION_PARAMS = ("status", "do_use_async", "do_print_url", "do_capture_log")
        conn_kwargs = {}
        for param in CONNECTION_PARAMS:
            if param in kwargs:
                conn_kwargs[param] = kwargs[param]
                kwargs.pop(param, None)
        self.conn = Connection(total, **conn_kwargs)
        super().__init__(iterable, desc, total, *args, **kwargs)

    def update(self, n=1):
        displayed = super().update(n)
        if displayed:
            status = "completed" if self.n == self.total else "in progress"
            new_log = self.conn.stop_redirect_stdout() # getting currently added logs
            self.conn.update({"current": n, "status": status, "log": new_log}) # updating backend
            if new_log:
                print(new_log)
            self.conn.start_redirect_stdout()
        return displayed


def Loadbar(
    iterable,
    total=None,
    status="not started",
    # do_use_tqdm=True,
    do_capture_log=True,
    *args,
    **kwargs
):
    # capture output
    loadbarHelper = LoadbarHelper(
        iterable=iterable, total=total, status=status, do_capture_log=do_capture_log, *args, **kwargs
    )
    iterator = iter(loadbarHelper)
    loadbarHelper.conn.start_redirect_stdout()
    while True:
        try:
            yield next(iterator)
        except StopIteration:
            break
        except BaseException as e:
            # reporting error
            loadbarHelper.conn.update({"status": "error"})
            raise e
    # reporting progress as complete
    loadbarHelper.conn.update({"status": "completed"})
    loadbarHelper.conn.close() # cleanup

if __name__ == "__main__":
    N = int(1e3)
    import time

    start = time.time()
    for i in Loadbar(range(N)):
        pass
    print(time.time() - start)
    

    from tqdm import tqdm
    start = time.time()
    Connection(N)
    for i in tqdm(range(N)):
        pass
    print(time.time() - start)

    start = time.time()
    Connection(N)
    for i in range(N):
        pass
    print(time.time() - start)

