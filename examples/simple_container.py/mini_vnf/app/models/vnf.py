
class Vnf:
    def __init__(self):
        self.name: str = 'Default'
        self.type: str = 'Default'
        self.cpu: float = 1.0
        self.ram: float = 0.1
        self.rom: float = 1.0
        self.route: dict[str:list] = {}
        self.param: int = 1

vnf = Vnf()
