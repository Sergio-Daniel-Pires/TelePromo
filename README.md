TelePromo
===

Python web scrapper project to search promos a and send to a telegram chat 

## 📝 Let's Start!
Try it on [@telepromo](https://t.me/telepromobr_bot) telegram chat bot! Supported sites:
|            |   |                    |   |
|------------|---|--------------------|---|
| Aliexpress | ✅ | Estante Virtual    | ✅ |
| Shein      | ✅ | Madeira Madeira    | ✅ |
| Adidas     | ✅ | Terabyte           | ✅ |
| Nike       | ✅ | Casas Bahia        | ✅ |
| Kabum      | ✅ | Pichau             | ✅ |
| Cobasi     | ✅ | Amazon (Soon)      | ⚠️ |
| Magalu     | ✅ | GearBest (Removed) | ❌ |

![GIF](https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExM211enhodHk2MmUyaml1ODJrOW50bTRxb2lhMXAwazZpY3YxYW8yMCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/TqLVxJdp4WZLGfPizU/giphy.gif)

## 🔧 Technologies
| Stack     | Techology used               |
|-----------|------------------------------|
| Backend   | Python                       |
| Frontend  | No front (Check on Telegram) |
| Database  | MongoDB and Redis            |
| Server    | Ngrok (dev) / VPS (prod)     |
| Container | Docker / Docker Compose      |
| Metrics   | Prometheus                   |
| Dashboard | Grafana                      |

## 🚀 Features
1. Create (and edit) a product wish list
2. Filters for products wish. Max/Min price and blacklist
3. List wish

## 🔨 Build
First, clone this repo using SSH:
```
git clone git@github.com:Sergio-Daniel-Pires/TelePromo.git
```
or, using HTTPS:
```
https://github.com/Sergio-Daniel-Pires/TelePromo.git
```

To run local project, you need to follow some steps:
1. Install dependecies with `pip install -r requirements.txt`
2. Start MongoDB and Redis locally
3. (Optional) Start grafana/prometheus and configure ngrok to receive a external link
4. Run project using
```sh
bash run.sh
```
5. Cheers!

...or just use docker for container:
```sh
docker compose up --build 
```

Disclaimer:
This bot is a PROMO HUNTER, it's not a PRICE OBSERVER (There's difference)

### License

MIT

---------------------------

Made by [Sérgio Pires](https://www.linkedin.com/in/sergio-daniel-pires-2582271b9/)
