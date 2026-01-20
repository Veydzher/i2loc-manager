## Main
language-name = Українська

ok-button = Гаразд
no-button = Ні
yes-button = Так
save-button = Зберегти як...
apply-button = Застосувати
close-button = Закрити
cancel-button = Скасувати
discard-button = Відхилити
all-languages = Усі мови
term-count-label = Усього термінів: {$count}
report-dev = Просимо опублікувати цю помилку та прикріпити файл, який ви намагалися відкрити, у вкладці {$link}.


## About popup
about-app = Про застосунок
about-app-version = Версія: {$version}
about-app-desc = Простий інструмент для керування асетами {$I2Localization}, експортованими через {$UABEA} у вигляді дамп файлів.


## File section
file-menu-title = Файл
open-button = Відкрити
open-tooltip = Відкрити дамп файл UABEA.
open-recent-menu = Недавні...
open-recent-tooltip = Відкрити недавно відкритий {$file_name}.
clear-recent-button = Очистити недавні
clear-recent-tooltip = Очистити список недавно відкритих файлів.
save-button = Зберегти
save-tooltip = Зберегти дамп файл UABEA.
save-as-button = Зберегти як...
save-as-tooltip = Зберегти дамп файл UABEA як...
exit-app-button = Вихід
exit-app-tooltip = Вийти із застосунку.


## Edit section
edit-menu-title = Редагувати
undo-button = Скасувати
undo-tooltip = Скасувати правку.
redo-button = Повторити
redo-tooltip = Повторити правку.
cut-button = Вирізати
cut-tooltip = Вирізати вміст вибраного рядка.
copy-button = Копіювати
copy-tooltip = Скопіювати вміст вибраного рядка.
paste-button = Вставити
paste-tooltip = Вставити вміст буфера обміну у вибраний рядок.
delete-button = Видалити
delete-tooltip = Видалити вміст вибраного рядка.


## View section
view-menu-title = Вигляд
refresh-table-button = Оновити таблицю
refresh-table-tooltip = Оновити таблиця вручну.
theme-menu = Тема
theme-menu-tooltip = Ця тема сумісна з вашою ОС.
app-language-menu = Мова
check-updates-now-button = Перевірити на наявність оновлення
check-updates-now-tooltip = Уручну перевірити на наявність оновлення.
check-updates-startup-button = Перевіряти на наявність оновлення
check-updates-startup-tooltip = Автоматично перевіряти на наявність оновлення під час запуску застосунку.


## Tools section
tools-menu-title = Інструменти
export-translations-button = Експортувати переклади
export-translations-tooltip = Експортувати переклади до файлу CSV/TSV.
import-translations-button = Імпортувати переклади
import-translations-tooltip = Імпортувати переклади з файлу CSV/TSV.
manage-languages-button = Керувати мовами
manage-languages-tooltip = Керувати мовами у таблиці.


## Popup titles
error-title = Помилка
warning-title = Увага
information-title = Інформація
question-title = Підтвердження

## Popup messages
warning-no-file = Жодного файлу не відрикто.
warning-file-not-found = Файлу не існує: {$file_path}.
error-invalid-file = Недійсний файл.
error-invalid-extension = Недійсне розширення файлу.
error-no-terms-language = Не знайдено терміни/мови!
error-unknown-import-type = Невідомий тип імпортування: {$type}.

error-save-failed = Помилка збереження: {$error}.
error-invalid-data = Недійсний формат даних: {$error}.
error-file-access = Помилка доступу до файлу: {$error}.

warning-no-languages = У файлі не визначено жодної мови.
warning-invalid-language-format = Недійсний формат мови.
warning-language-exists = Мова «{$language}» уже існує!

question-save-file-open = Бажаєте зберегти зміни?
question-save-file-exit = Бажаєте зберегти зміни перед виходом?


## File explorer titles
open-title = Відкрити
save-title = Зберегти

## File extension names
all-files = Усі файли
text-file = Текстові документи
json-file = JSON файли
dump-file = UABEA дамп файли
csv-file = CSV файли
tsv-file = TSV файли


## Status bar messages
opening-file = Відкриття файлу: {$file_path}
opened-file = Файл відкрито: {$file_path}
saving-file = Збереження файлу: {$file_path}
saved-file = Файл збережено: {$file_path}


## Update module
update-available-title = Доступне оновлення
update-available-message = Доступний новий випуск: {$name}
changelog-label = 📝 Список змін:
download-update-button = Завантажити
skip-update-button = Пропустити
install-now-button = Установити
install-later-button = Пізніше
installing-update = 📦 Установлення оновлення...
checking-for-updates = Перевірка на наявність оновлення...
downloading-update = ⏳ Завантаження оновлення...
download-complete = ✅ Завантаження завершено!
download-error = ❌ Помилка завантаження!
info-no-updates-available = Ви використовує останню версію!
error-check-updates-failed = Не вдалоси перевірити на наявність оновлення: {$error}
error-download-failed = Не вдалося завантажити: {$error}
error-install-failed = Не вдалося встановити: {$error}


## Export module

export-translations-title = Експортувати переклади
export-languages-label = Оберіть мови для експортування:
select-all-button = Вибрати всі
deselect-all-button = Зняти всі
export-button = Експортувати
export-button-disabled = Оберіть принаймні одну мову.

# Status bar message
exporting-language-data = Експортування даних з файлу {$file_name}...

## Helper text
and-text = {$langs} та {$last_lang}.

## Popup messages
warning-no-terms-found = Не знайдено термінів для експортування.
error-export-file = Помилка експортування файлу: {$error}
warning-no-available-languages = Немає доступних мов для експортування.
warning-no-languages-selected = Не вибрано жодної мови для експортування.
error-processing-term = Помилка опрацювання терміну №{$num} ({$term_name}): {$error}
error-export-languages = Помилка експортування мов: {$error}
info-success-export = Успішно експортовано {$translation_num ->
    [one] {$translation_num} переклад
    [few] {$translation_num} переклади
    *[other] {$translation_num} перекладів
} для {$language_num ->
    [one] {$language_num} мови
    *[other] {$language_num} мов
} до файлу {$file_name}.

    Експортовані мови: {$languages}


## Import module

import-translations-title = Імпортувати переклади
import-select-languages = Оберіть мови, які бажаєте імпортувати:
imported-language-label = <b>Імпортована мова</b>
import-to-language-label = <b>Цільова мова</b>
auto-map-button = Авто. впорядкувати
clear-mappings-button = Зняти всі
do-not-import-option = Не імпортувати
import-button = Імпортувати
import-button-disabled = Оберіть принаймні одну цільову мову.
importing-progress-label = Перевірка перекладів на імпортування...
importing-progress-title = Імпортування

# Status bar message
importing-file-data = Імпортування даних з файлу {$file_name}...
importing-file-canceled = Імпортування з файлу {$file_name} скасовано.
imported-data-success = Успішно імпортовано дані з файлу {$file_name}.

## Popup messages
error-no-headers = Файл порожній або без заголовків.
error-missing-headers = У файлі відсутні небхідні стовпці: {$headers}.
error-no-langauges-columns = Файл не містить стовпців мов.
error-no-available-model = Модель таблиці недоступна.
error-import-file = Помилка імпортування файлу: {$error}.
info-no-imported = Жодних нових перекладів для імпортування.
info-success-import = Переклади успішно імпортовано.

    Оновлено {$count ->
        [one] {$count} переклад
        [few] {$count} переклади
        *[other] {$count} перекладів
    }.


## Manage languages module

-ml-title-term = Менеджер мов
ml-title = {-ml-title-term}
ml-warning-desc = УВАГА: не кожна гра має динамічне керування мовами. Деякі з них можуть
    мати власне запрограмоване або базоване на Unity керування мовами.
ml-languages-label = Мови:
ml-reorder-label = Упорядкування
ml-move-up-button = Перемістити вгору
ml-move-down-button = Перемістити вниз
ml-details-label = Подробиці
ml-manage-label = Керування
ml-add-language = Додати мову
ml-remove-language = Вилучити мову
ml-languages-count = {$count ->
    [one] {$count} мова
    [few] {$count} мови
    *[other] {$count} мов
}

lang-flag-enabled = Увімкнено
lang-flag-disabled = Вимкнено

## Add language dialog

add-language-title = {-ml-title-term}: додати мову
add-language-selection = Вибір мови
add-language-manually = Ввести вручну...
add-language-details = Подробиці мови
add-language-native-name = Використовувати рідну назву
add-language-name = Назва:
add-language-code = Код:
add-language-flag = Стан:
add-language-initialize = Створити з
add-language-initialize-option-1 = Порожніми рядками
add-language-initialize-option-2 = Копіюванням рядків з:

## Popup messages
confirm-language-removal = Ви дійсно бажаєте вилучити мову «{$language}»?

    Цю дію не можна буде скасувати.
warning-invalid-language = Будь ласка, введіть назву мови та її код.
warning-duplicate-code = Мова з кодом «{$code}» уже існує.
warning-reserved-names = Введене вами назва або код зарезервовано. Будь ласка, введіть інше.
warning-invalid-code-letters = Код мови повинен містити лише літери ASCII.
