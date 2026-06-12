class AppmanException(Exception):
    pass

class RollbackException(AppmanException):
    pass

class AppInstallException(AppmanException):
    pass

class AppRollbackException(AppmanException):
    pass

class RequirementsException(AppmanException):
    pass

class RequirementsRollbackException(AppmanException):
    pass

class MigrationsException(AppmanException):
    pass

class MigrationsRollbackException(AppmanException):
    pass

class FrontendException(AppmanException):
    pass

class FrontendRollbackException(AppmanException):
    pass

class PostInstallTaskException(AppmanException):
    pass

class PostInstallTaskRollbackException(AppmanException):
    pass

class ServerRestartException(AppmanException):
    pass

class ServerRestartRollbackException(AppmanException):
    pass

class AppmanException(AppmanException):
    pass