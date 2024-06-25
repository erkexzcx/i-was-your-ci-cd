# i-was-your-ci-cd

`scx_rustland` kept stalling on my machine, but worked fine on developer's machine, so I made this CI/CD for developer to self-test it on my machine. 😅

# Usage

First, modify the code. Mostly written by ChatGPT (Python) and by hand (Bash).

Then: `python3 script.py`

Just setup port-forwarding in your router to the same port on your machine, so user from the internet can access it. Usage for another user: `curl -s 'http://123.123.123.123:52834/?branch=rustland-next'` 😅
