# Multilingual Semantic Keyword Set
A tool for extracting and managing keywords with semantic deduplication.

## Supported languages
Russian and English.

## What it does
It extracts keywords from a given text.

For English it does so quite straightforward. As for Russian, it normalizes collocations, making every word of the collocation singular, masculine (if verb or adjective), nominative case (e.g. 'нейронные сети' becomes 'нейронный сеть').