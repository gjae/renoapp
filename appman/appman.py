def copy_front(payload, rollback: bool = False):
    pass

def install_requirements(payload, rollback: bool = False):
    pass

def run_migrations(payload, rollback: bool = False):
    pass

def restart_server(payload, rollback: bool = False):
    pass

def check_reno_dependencies(payload, rollback: bool = False):
    pass

def generate_app(payload, rollback: bool = False):
    pass

def update_settings(payload, rollback: bool = False):
    pass


class Appman:
    pipeline = [
        check_reno_dependencies,
        generate_app,
        update_settings,
        install_requirements,
        copy_front,
        run_migrations,
        restart_server,
    ]

    stack = [

    ]

    def __init__(self, payload: "InstallAppPayload"):
        self.payload = payload

    def add_task(self, task):
        self.pipeline.append(task)
    
    def execute(self):
        for task in self.pipeline:
            task(self.payload)
            self.stack.append(task)

    def rollback(self):
        while self.stack:
            task = self.stack.pop()
            task(self.payload, rollback=True)

    def get_payload(self):
        return self.payload