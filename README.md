
## Зависимости
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
- Запускаем python (пока что там просто 2 + 2)
  ```bash
  python main.py
  ```

## Замечания
Для корректной работы lsp на python-е с либой на rust-е нужно обновлять
описание сигнатур в docs\_parser.pyi, неприятно, но не критично. В целом очень
даже вкусно

Про тесты на rust-е напишу потом
