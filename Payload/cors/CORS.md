## CORS

`curl --head -s 'http://example.com/api/v1/secret' -H 'Origin: http://evil.com'`

Check to see what the server responds with in the `Access-Control-Allow-Origin:` (if anything) and if so, check if `Access-Control-Allow-Credentials: true` is present.

```
Origin: null
Origin: attacker.com
Origin: attacker.target.com
Origin: attackertarget.com
Origin: sub.attackertarget.com
Origin: attacker.com and then change the method Get to post/Post to Get
Origin: sub.attacker target.com
Origin: sub.attacker%target.com
Origin: attacker.com/target.com
```