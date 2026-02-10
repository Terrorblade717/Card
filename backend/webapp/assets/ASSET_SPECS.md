# TON Arena Asset Specs (каркас)

Ниже базовые размеры, под которые можно спокойно готовить ассеты, чтобы они выглядели чётко на мобильном Telegram WebApp и не «убивали» производительность.

## 1) Карточки героев (изображения)
- **Рабочий формат в UI сейчас:** `120% x 220px` (внутри карточки `~120px` шириной).
- **Рекомендуемый исходник (master):** `768x1024` (3:4, PNG/WebP).
- **Оптимизированный runtime-файл:** `384x512` (WebP, качество ~80).
- **Именование:** `assets/heroes/<HeroName>.webp`
- **Пример:** `assets/heroes/Reaper.webp`

## 2) Иконки главного меню
- **Базовый размер:** `64x64` (PNG/SVG).
- **Retina-версия:** `128x128`.
- **Формат:** лучше `SVG`, fallback `PNG`.
- **Именование:** `assets/ui/icons/<name>.svg`
- **Пример:** `assets/ui/icons/battle.svg`

## 3) Фон главного меню
- **Master:** `1440x2560` (портрет, ~9:16).
- **Runtime target:** `720x1280` (WebP).
- **Именование:** `assets/backgrounds/menu-bg.webp`

## 4) Фон арены
- **Master:** `1920x1080` (16:9).
- **Runtime target:** `1280x720` (WebP).
- **Доп. мобильный вариант:** `1080x1920` (портрет), если нужен отдельный layout.
- **Именование:** `assets/backgrounds/arena-bg.webp`

## 5) Видео-анимации скиллов
- **Формат:** `webm (VP9)` + fallback `mp4 (H.264)`.
- **Длительность:** `0.6s - 1.4s` (короткие боевые вставки).
- **Разрешение:**
  - single-target: `512x512`
  - full-screen/aoe overlay: `1280x720`
- **FPS:** 30 (достаточно для мобильных).
- **Без звука** в файле, звук лучше отдельно.
- **Именование:** `assets/video/skills/<ability>.webm`
- **Пример:** `assets/video/skills/execute.webm`

## 6) Видео/эффекты ударов (весомость удара)
- **Формат:** `webm`.
- **Размер:** `256x256` или `512x512` для hit-vfx.
- **Длительность:** `250ms - 500ms`.
- **Именование:** `assets/video/hits/<effect>.webm`
- **Пример:** `assets/video/hits/heavy-slash.webm`

## 7) Бюджет по весу (важно)
- Hero image runtime: до `80-150 KB` за файл.
- Menu/Arena background runtime: до `250-400 KB` за фон.
- Skill video: до `300-700 KB` за клип.
- Hit video: до `80-200 KB` за клип.

## 8) Каркас структуры папок
```
assets/
  heroes/
  ui/
    icons/
  backgrounds/
  video/
    skills/
    hits/
```

