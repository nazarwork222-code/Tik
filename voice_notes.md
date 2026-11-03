# Озвучка Степана (оновлено 01.11.2026, після ролика «Рольганг»)

## ГОЛОС СТЕПАНА — ElevenLabs «Yevhen – Resonant and Distinctive» (назавжди)
- Сервіс: ElevenLabs (elevenlabs.io), акаунт Назара, тариф Starter (платний, комерційна ліцензія).
- Voice ID: `TEyBWD5tAHAWqAGEv6yI`
- Мова: українська (Ukrainian, Standard accent).
- Модель: **Eleven v4** (підтримує теги емоцій), у API `model_id: "eleven_v4"`.
- Налаштування: Stability ≈0.5, Similarity ≈0.75, Language — Auto.
- Формат API: **`mp3_44100_128`**. `pcm_44100` на Starter дає 403 (лише Pro); запасний — `pcm_24000`.
- Параметр `speed` модель v4 ігнорує → темп ×1.2 робиться ffmpeg `atempo` після обрізки тиші (build.py, `TEMPO`).
- Усе, що згенеровано на безкоштовному тарифі, — тільки для тестів, у TikTok не йде.

## Як писати текст для озвучки
- Звичайний український текст, числа словами, без знаків наголосу.
- Теги емоцій англійською в квадратних дужках перед фразою:
  - `[calm]` — спокійна розповідь (основний тон Степана)
  - `[curious]` — питання, інтрига, гачок
  - `[thoughtful]` — пояснення «по кроках», емоція think
  - `[confident]` — висновок, фінальна репліка
  - `[excited]` — wow, радість
  - `[whispers]` — жарт / коментар у бік
- Паузи: «...» і тире «—».
- Тест-фраза:
  `[calm] Кроковий двигун. [curious] А чому він крутиться... кроками? [thoughtful] Дивіться. Двісті кроків — і повний оберт. [confident] Тому верстат ріже деталь міліметр у міліметр. [whispers] Ну... майже завжди.`

## Доступ до API (як це працює)
- Ключ ElevenLabs доданий як **мережевий секрет** середовищ «CNC TikTok» і «Default» на claude.ai/code (хост `api.elevenlabs.io`, заголовок `xi-api-key`, без префікса).
- Змінної `ELEVENLABS_API_KEY` немає і не треба: проксі сам підставляє ключ. Запити робити БЕЗ заголовка ключа, наприклад:
  `curl https://api.elevenlabs.io/v1/user/subscription`
- Синтез: `POST https://api.elevenlabs.io/v1/text-to-speech/TEyBWD5tAHAWqAGEv6yI?output_format=mp3_44100_128` з JSON `{"text": ..., "model_id": "eleven_v4", "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}}`. Кожну сцену окремим запитом. Робить `python build.py videos/<slug> voice`.
- Звуки дій: `POST /v1/sound-generation` `{"text", "duration_seconds", "prompt_influence": 0.6}` — спершу шукай у sfx_lib/.
- Музика: `POST /v1/music?output_format=mp3_44100_128` `{"prompt", "music_length_ms": 50000}` — працює на Starter; за замовчуванням спільна sfx_lib/music.mp3 (зациклюється з кросфейдом).
- Перевірка тексту: теги вголос не зачитуються; `python build.py … check` розпізнає мову з готового файлу (шепіт розпізнається гірше — слухати).
- УВАГА: у звичайних чатах проєкту на claude.ai API недоступне (там вбудоване середовище без секретів). Там — запасний шлях: Claude генерує на сайті ElevenLabs у Chrome Назара, Назар скачує файл і прикріплює.

## Обробка й мікс (база «живого» звуку)
- Голос: highpass 90 → EQ −2 dB @300 Hz → −1.5 dB @2.5 kHz → deesser → компресор 3:1 (release ~200 ms) → highshelf +1.5 dB від 10 kHz → легкий відгук маленької майстерні → loudnorm −16 LUFS.
- Між фразами — паузи 0.25–0.4 с (ORDER у video.py); ширші (до 0.7) — якщо ролик укладається в 55 с.
- Шепіт: окрема репліка, EQ «вбік» (highpass 280 / lowpass 5500 / +3 dB @1.8k), −5 dB у міксі.
- Фон майстерні (гул + далекий верстат) під усім роликом, притихає під голос.
- Легкий механічний шар (дзижчання/тикання кроків) під мовою Степана — гучність на слух.
- Музика — ducking під голос (sidechaincompress threshold 0.05, ratio 4, attack 200, release 1000).
- Підсумок ролика: −14 LUFS, true peak −1 dB.

## Запасні варіанти (не основні)
- StyleTTS2 українська, «Артем Окороков»: безкоштовно, без емоцій.
- Piper «Микита» — звучить «як ШІ».
- Відкинуто: ICE-012-Audio (акцент), Pavlo – Warm Ukrainian Baritone.
