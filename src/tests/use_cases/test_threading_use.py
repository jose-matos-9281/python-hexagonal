import threading
from queue import Queue
from typing import Any

from example.contacto.application import ContactoAppAPI
from example.contacto.domain.contacto import TipoContacto

from .base import BaseTest


class TestThreadingUse(BaseTest):
    temp_db = __file__.replace(".py", ".db")

    def test_threading_use(self):
        stats = {"ok": 0, "error": 0}
        sentinela = object()
        cola: Queue[Any] = Queue(maxsize=5000)
        lock = threading.Lock()

        def worker(api_local: ContactoAppAPI[Any]):
            while True:
                telefono = cola.get()
                if telefono is sentinela:
                    cola.task_done()
                    break
                try:
                    api_local.contacto.crear(TipoContacto.TELEFONO, telefono)
                    with lock:
                        stats["ok"] += 1
                except Exception as e:
                    with lock:
                        stats["error"] += 1
                        print(f"ERROR {telefono}: {e}")
                finally:
                    cola.task_done()

        def main(api_local: ContactoAppAPI[Any], telefonos: list[str]):
            n_hilos = 4

            hilos = [
                threading.Thread(target=worker, daemon=False, args=(api_local,))
                for _ in range(n_hilos)
            ]
            for h in hilos:
                h.start()

            for telefono in telefonos:
                cola.put(telefono)

            for _ in hilos:
                cola.put(sentinela)

            cola.join()
            for h in hilos:
                h.join()

            print(stats)

        api_local = self.api_wrapper.contacto

        telefonos = [
            "+18090000000",
            "+18090000080",
            "+18090000088",
            "+18090000135",
            "+18090002552",
            "+18090003263",
            "+18090005002",
            "+18090005545",
            "+18090012012",
            "+18090012121",
        ]
        main(api_local, telefonos)
        assert stats["ok"] == len(telefonos)
        assert stats["error"] == 0
