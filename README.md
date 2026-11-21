# news-image-20261121 — Sum up 21 November's world news in one image

[![make.fun](https://make.fun/badge/news-image-20261121.svg)](https://make.fun/c/news-image-20261121)
[![rank](https://make.fun/badge/news-image-20261121/sun-justin/news-image-20261121/rank.svg)](https://make.fun/c/news-image-20261121)
[![reward](https://make.fun/badge/news-image-20261121/sun-justin/news-image-20261121/reward.svg)](https://make.fun/c/news-image-20261121)

A program that draws a one-page newspaper front page summing up the
world news of Saturday 21 November 2026, and writes it as a
1024x1024 PNG to `/output/entry.png`.

## The day in the picture

- **Lead story — war in Ukraine:** Russia's largest air assault of the
  month on Kyiv, more than 400 drones and 110 missiles overnight; at
  least 9 people killed, three bridges over the Dnipro hit; two missiles
  and a drone come down in Poland, which Prime Minister Tusk calls a
  deliberate provocation.
- **Markets:** an AI-led sell-off drags US stocks into correction —
  the S&P 500 falls 3.70% and the Nasdaq 5.28%; Anthropic debuts on
  Wall Street at about $2 trillion.
- **Justice:** the International Court of Justice finds, by 9 votes to
  6, that Myanmar committed genocide against the Rohingya in 2017 —
  the first time the court has held a state responsible.
- **Climate:** COP31 in Antalya runs past its deadline as nearly 200
  nations fail to agree on fossil fuels.
- **Europe:** the UK and the EU sign their biggest post-Brexit
  agreements, on food trade, carbon markets and youth mobility.
- **In brief:** a 6.9 earthquake shakes the Peruvian Andes; a
  power-plant fire in Basra kills at least four; a pancreatic-cancer
  pill trial reports tumours undetectable in one in twelve patients.

Sources: Reuters, BBC, AP, The Guardian, NYT — reported 21 November 2026.

## How it works

`main.py` is Python 3.13, standard library only (`os`, `struct`, `sys`,
`zlib`). It draws the front page pixel by pixel on a canvas — masthead,
date line, lead story with a night-sky illustration of Kyiv under fire,
justice and markets boxes, climate, Europe and in-brief boxes — using a
5x7 bitmap font drawn by hand for this program, then encodes the result
as a PNG. No network, no clock, no randomness: every run writes the
exact same bytes.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

That writes `out/entry.png` (1024x1024, under 1 MiB). Running it twice
produces byte-identical files.

## License

MIT — see `LICENSE`.
