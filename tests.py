from main import app
app.testing = True
c = app.test_client()

assert c.get('/').data == b'OK'
assert c.get('/ping').data == b'pong'
assert int(c.get('/visits').data) >= 0
tmp = int(c.get('/visits').data)
c.get('/ping')
assert int(c.get('/visits').data) - tmp == 1

print('tests.py passed')
