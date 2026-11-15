from slugify import slugify
assert slugify("Hello World") == "hello-world"
assert slugify("Hi, there!") == "hi-there"
assert slugify("a  b") == "a-b"
print("ok")
