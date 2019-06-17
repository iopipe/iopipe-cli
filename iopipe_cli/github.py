import http.client

conn = http.client.HTTPSConnection("iopipe.auth0.com")

payload = '{"client_id":"DBqlDk7LyNDF7Mrulo3g8F15ajxhHmGW","client_secret":"YIj5LWLVVZ-Hgj59dXGXg3rVFp6ZlSSi5qz3BxHdpsIeSRECyNuG_oTnhKqg45nj","audience":"https://graphql.iopipe.com/","grant_type":"client_credentials"}'

headers = {"content-type": "application/json"}

conn.request("POST", "/oauth/token", payload, headers)

res = conn.getresponse()
data = res.read()

print(data.decode("utf-8"))
