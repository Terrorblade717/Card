# TON Arena — каркас интеграции ассетов и отдельной арены

## Что уже подготовлено
- Созданы папки под ассеты:
  - `backend/webapp/assets/heroes/`
  - `backend/webapp/assets/ui/icons/`
  - `backend/webapp/assets/backgrounds/`
  - `backend/webapp/assets/video/skills/`
  - `backend/webapp/assets/video/hits/`
- Во фронтенд добавлены константы `ASSET_PATHS`, `MENU_ICONS`.
- Добавлен каркас-функция `playSkillVideoFx(ability)` с ожидаемыми путями для клипов.

## Рекомендованные размеры
Полная спецификация: `backend/webapp/assets/ASSET_SPECS.md`

Коротко:
- Герои: master `768x1024`, runtime `384x512`.
- Иконки меню: `64x64` (SVG предпочтительно).
- Фон меню: master `1440x2560`, runtime `720x1280`.
- Фон арены: master `1920x1080`, runtime `1280x720`.
- Видео скиллов: `512x512` или `1280x720`, `webm`.

## Как сделать «арену» отдельным экраном при нажатии «Бой»
1. Добавить экран-состояние `currentScreen = 'menu' | 'arena'`.
2. На `startBattle()`:
   - скрыть меню,
   - показать arena-root контейнер с фоном `arena-bg.webp`,
   - запустить бой.
3. После завершения боя:
   - вернуть пользователя в меню, либо оставить кнопку "В меню" на арене.

## Как сделать удары более «весомыми» (как в карточных играх)
1. Фаза "замах": карточка атакующего поднимается на `-14px` и слегка увеличивается (`scale(1.06)`) на `120ms`.
2. Фаза "рывок": быстрый рывок к цели (`180-220ms`, easing `cubic-bezier`).
3. Фаза "impact":
   - краткий shake цели (`120ms`),
   - вспышка/видео удара `hitVideos/*.webm`.
4. Фаза "возврат": карточка возвращается на место (`180ms`).

## Когда будут готовы видео-скиллы
Для каждого ability кладёшь файл:
- `backend/webapp/assets/video/skills/<ability>.webm`

Примеры:
- `execute.webm`
- `heal.webm`
- `aoe.webm`
- `stun.webm`

После этого можно заменить тело `playSkillVideoFx` на реальное создание `<video>` overlay.
