def read_organisms(num):
    file_object = open("save_one", "r")
    things = [file_object, file_object.read(), file_object.readlines()]
    print(things[num])

def read_lines():
    with open("save_one") as f:
        contents = f.read()
    print(contents.split(":\n"))

read_organisms(0)
input("")
read_organisms(1)
input("")
read_organisms(2)
input("")
read_lines()