# Re:dnd — аварийное восстановление

Последняя проверка процедуры: **21 августа 2026 года**.

Этот документ нужен для восстановления сайта, формы заявок и публикации после
потери локальной рабочей папки. Значения секретов здесь намеренно не хранятся.

## 1. Что восстанавливает GitHub

Канонический репозиторий:
`https://github.com/kremlebot-tg/freelance-portfolio.git`.

В Git входят:

- RU/EN HTML, стили, JavaScript, шрифты и изображения;
- исходники интерактивных демо и сгенерированные браузерные версии;
- тесты, SEO-сборщик и проверки публикации;
- GitHub Actions для Pages и IndexNow;
- read-only CI для pull request и обновлений Dependabot;
- исходник Yandex Cloud Function и исторический VPS-вариант формы;
- `CNAME`, документация и публичный security contact.

Git не должен содержать значения секретов, заявки пользователей, содержимое
Object Storage, доступы к регистратору или recovery-коды аккаунтов.

## 2. Восстановление исходников с нуля

Нужны Git, Node.js 24+, npm и Python 3.

```bash
git clone https://github.com/kremlebot-tg/freelance-portfolio.git
cd freelance-portfolio
git fetch --tags
npm ci
npm test
npm run launch:check
npm audit --omit=dev --audit-level=high
git diff --check
```

Текущая production-ветка — `main`. Контрольная точка этого recovery-аудита —
тег `production-2026-08-21`. Тег используют только как известную рабочую
версию; дальнейшие исправления остаются в `main`.

Локальная проверка без внешних запросов:

```bash
python3 -m http.server 8788
# http://localhost:8788 и http://localhost:8788/en/
```

## 3. Восстановление GitHub Pages

Если репозиторий пришлось создать заново:

1. Загрузить полную Git-историю, включая теги.
2. Сделать `main` веткой по умолчанию.
3. В Settings → Pages выбрать **GitHub Actions**.
4. Создать environment `github-pages`.
5. Добавить Actions secret `INDEXNOW_KEY` из защищённой внешней копии.
6. Установить custom domain `rednd.ru` и включить HTTPS.
7. Запустить workflow `Deploy public site`.
8. После успешной публикации запустить `Notify Yandex IndexNow` только для
   новых, изменённых или удалённых индексируемых URL.

`CNAME` уже хранится в Git. Проверка после публикации:

```bash
curl -fsSI https://rednd.ru/
curl -fsS https://rednd.ru/services.html >/dev/null
curl -fsS https://rednd.ru/en/services.html >/dev/null
curl -fsS https://rednd.ru/sitemap.xml >/dev/null
```

## 4. Восстановление формы в Yandex Cloud

Актуальная схема и ID существующих ресурсов перечислены в `README.md`.
Исходник функции — `yandex-function/index.py`. Полного Infrastructure as Code
пока нет, поэтому потеря всего Yandex Cloud потребует ручного создания
ресурсов или будущего Terraform-проекта.

### Несекретная конфигурация функции

- `LEADS_BUCKET`
- `S3_SECRET_ID`
- `TG_SECRET_ID`

### Ключи в Lockbox

- секрет S3: `S3_KEY_ID`, `S3_SECRET`;
- секрет Telegram: `TG_BOT_TOKEN`, `TG_CHAT_ID`.

Порядок восстановления:

1. Проверить приватный Object Storage bucket в `ru-central1`.
2. Проверить выделенный service account и минимальное право записи в bucket.
3. Восстановить оба Lockbox-секрета из зашифрованной внешней копии.
4. Дать service account функции право читать только нужные секреты и писать
   только в нужный bucket.
5. Создать версию функции из `yandex-function/index.py` по команде из README.
6. Проверить route API Gateway `/submit` и допустимые origin
   `https://rednd.ru`, `https://www.rednd.ru`.
7. Обновить `formEndpoint` в `site-config.js`, если адрес Gateway изменился.

Безопасная проверка CORS, не создающая заявку:

```bash
curl -i -X OPTIONS \
  -H 'Origin: https://rednd.ru' \
  -H 'Access-Control-Request-Method: POST' \
  'https://d5d7olk60q94hjb111lj.kocrdvxt.apigw.yandexcloud.net/submit'
```

Не отправлять тестовую заявку с реальным контактом только ради диагностики.
После восстановления провести один согласованный тестовый сценарий и отдельно
проверить запись в Object Storage до уведомления в Telegram.

## 5. Домен и внешние доступы

GitHub не восстанавливает аккаунт регистратора и DNS-зону. В отдельном
зашифрованном хранилище должны быть:

- доступ и recovery-коды регистратора домена;
- актуальная DNS-зона или её экспорт;
- recovery-коды GitHub и Yandex Cloud;
- значения перечисленных выше секретов;
- ответственный владелец каждого доступа и дата последней проверки.

Не копировать эти значения в Issue, README, Actions log или публичный Release.

## 6. Резервная политика

- После значимого production-релиза создавать подписанный или аннотированный
  тег и GitHub Release с кратким описанием.
- Хранить второй полный Git mirror или `git bundle` вне GitHub и не на том же
  физическом диске, что рабочая копия.
- Не считать Actions artifacts постоянным backup: у них ограничен срок жизни.
- Раз в квартал выполнять чистый clone, `npm ci`, тесты и сборку артефакта.
- После изменения секретов сразу обновлять их зашифрованную внешнюю копию.

## 7. Критерий готовности

Восстановление считается завершённым только когда одновременно:

- чистый clone проходит все проверки;
- RU и EN страницы открываются с HTTPS без ошибок консоли;
- Pages workflow завершён успешно;
- форма проходит согласованный E2E со сначала сохранённой записью в РФ;
- sitemap и canonical соответствуют production;
- доступы и резервные копии снова распределены минимум по двум независимым
  точкам хранения.
