# file server for hosting screenshots + screenshot utility
was bored so i whipped this up in two and a half hours. not meant for production, at all.

features:
- auth
- config
- fast

versions:
- python server -> original, prolly not trustworthy
- go server -> came afterwards, maybe trustworthy

## python server
`pip install -r requirements-server.txt`

`python server.py`

it will automatically generate a config file if it doesn't exist.
(scroll down for config info)

## go server
`go run server.go`

## config
```yaml
auth_token: string
port: integer (1-65535)
upload_url: string (http://localhost:port/upload)
```

## usage
run the screenshot.py (tested on xorg gnome only for now), select the area you want to screenshot, and it will automatically upload it to the server, and copy the url to your clipboard.

## todo
- [ ] better error handling
- [ ] better config handling
- [ ] better auth handling
- [ ] better readme
- [ ] better everything

## license
MIT, do whatever you want with it. don't use this in production, as if anyone would. 