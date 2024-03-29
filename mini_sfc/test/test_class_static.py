
import code

class MyClass(object):
    __instance = None

    a = None

    def __new__(cls,*args,**kwargs):
        if not cls. __instance:
            cls.__instance = super().__new__(cls,*args,**kwargs)
        return cls.__instance
    
    def __init__(self) -> None:
        self.a = 5
    
    @staticmethod
    def change_value():
        MyClass.a += 1

    @staticmethod
    def set_value(value):
        MyClass.a = value

    @staticmethod
    def get_value():
        return MyClass.a



if __name__ == "__main__":
    a = MyClass()
    b = MyClass()
    print(a == b)
    print(id(a) == id(b))

    code.interact(banner="",local=locals())


