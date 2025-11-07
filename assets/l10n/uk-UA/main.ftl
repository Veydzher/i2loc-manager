## Main
language-name = Українська

yes-button = Так
no-button = Ні
ok-button = Гаразд
apply-button = Застосувати
close-button = Закрити
cancel-button = Скасувати
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
open-recent-menu = Відкрити недавні
open-recent-tooltip = Відкрити недавно відкритий {$filename}.
clear-recent-button = Очистити недавно відкриті
clear-recent-tooltip = Очистити список недавно відкритих файлів.
save-button = Зберегти
save-tooltip = Зберегти вмісти до дамп файлу UABEA.
app-language-menu = Мова
exit-app-button = Вихід
exit-app-tooltip = Вийти із застосунку.

## Edit section
edit-menu-title = Редагувати
refresh-table-button = Оновити таблицю
refresh-table-tooltip = Оновити таблиця уручну.
theme-menu = Тема
theme-menu-tooltip = Ця тема сумісна з вашою ОС.

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
error-parsing-txt = Помилка розпакування наступного: {$error}.

warning-no-languages = У файлі не визначено жодної мови.
warning-invalid-language-format = Недійсний формат мови.
warning-language-exists = Мова «{$language}» уже існує!

question-save-file = Бажаєте зберегти зміни перед тим, як вийти?


## File explorer titles
open-title = Відкрити
save-title = Зберегти

## File extension names
all-files = Усі файли
text-file = Текстові документи
json-file = JSON файли
dump-file = Дамп файли
csv-file = CSV файли
tsv-file = TSV файли


## Status bar messages
opening-file = Відкриття файлу: {$file_path}
opened-file = Файл відкрито: {$file_path}
saved-file = Файл збережено: {$file_path}


## Export module

export-translations-title = Експортувати переклади
export-languages-label = Оберіть мови для експортування:
select-all-button = Вибрати всі
deselect-all-button = Зняти всі
export-button = Експортувати
export-button-disabled = Оберіть принаймні одну мову для експортування.

# Status bar message
exporting-language-data = Експортування даних мов...

## Helper text
and-text = {$langs} та {$last_lang}.

## Popup messages
warning-no-terms-found = Не знайдено термінів для експортування.
error-export-file = Помилка експортування файлу: {$error}
warning-no-available-languages = Немає доступних мов для експортування.
warning-no-languages-selected = Не вибрано жодної мови для експортування.
error-processing-term = Помилка обробки терміну №{$num} ({$term_name}): {$error}
error-export-languages = Помилка експортування мов: {$error}
info-success-export = Успішно експортовано {$translation_num ->
    [one] {$translation_num} переклад
    [few] {translation_num} переклади
    *[other] {$translation_num} перекладів
} для {$language_num ->
    [one] {$language_num} мови
    *[other] {$language_num} мов
} до файлу {$filename}.

    Експортовані мови: {$languages}


## Import module

import-translations-title = Імпортувати переклади
import-select-languages = Оберіть мови, які бажаєте імпортувати:
imported-language-label = <b>Імпортована мова</b>
import-to-language-label = <b>Цільова мова</b>
do-not-import-option = Не імпортувати
import-button = Імпортувати
import-button-disabled = Оберіть принаймні одну цільову мову для імпортування.
importing-progress-label = Імпортування перекладів...

## Popup messages
error-no-headers = Файл порожній або без заголовків.
error-missing-headers = У файлі відсутні небхідні стовпці: {$headers}.
error-no-langauges-columns = Файл не містить стовпців мов.
error-no-available-model = Модель таблиці недоступна.
error-import-file = Помилка імпортування файлу: {$error}.
info-success-import = Переклади успішно імпортовано.

    Оновлено {$count ->
        [one] {$count} переклад
        [few] {$count} переклади
        *[other] {$count} перекладів
    }.

import-no-imported = Жодних нових перекладів для імпортування.

## Manage languages module

-ml-title-term = Менеджер мов
ml-title = {-ml-title-term}
ml-warning-desc = ПРИМІТКА: не кожна відеогра має динамічне керування мовами.
    Деякі з них можуть мати власне запрограмоване керування мовами.
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
warning-duplicate-language = Мова з назвою «{$name}» уже існує.
warning-duplicate-code = Мова з кодом «{$code}» уже існує.
warning-reserved-names = Введене вами назва або код зарезервовано. Будь ласка, введіть інше.
