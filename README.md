# Docs search
<!-- здесь должно быть описание проекта -->

## Зависимости и их установка
### Ubuntu
```bash
sudo apt update
sudo apt install -y build-essential pkg-config clang llvm-dev libclang-dev \
                    libleptonica-dev libtesseract-dev tesseract-ocr \
                    tesseract-ocr-rus tesseract-ocr-eng python3 python3-pip
```

### Arch Linux
```bash
sudo pacman -Syu --needed --noconfirm build-essential pkgconf clang llvm \
                                      leptonica tesseract tesseract-data-rus \
                                      tesseract-data-eng python-pip
```

- maturin:
  ```bash
  # Запускаете .venv
  pip install maturin
  ```
## Как запускать? (работа только в .venv окружении)
- Билдим rust либу
  ```bash
  cd parser
  maturin develop
  ```
- Запускаем python
  ```bash
  python main.py
  ```
