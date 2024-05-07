docker build -t my-python-app .
docker run -p 5000:5000 -e ALLOWED_HOST='http://mein-zugelassener-host.com' my-python-app