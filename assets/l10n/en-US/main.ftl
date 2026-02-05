## Main
language-name = English US

ok-button = Ok
no-button = No
yes-button = Yes
apply-button = Apply
close-button = Close
cancel-button = Cancel
discard-button = Discard
all-languages = All Languages
term-count-label = Total Terms: {$count}
report-dev = Please attach the file you were trying to open and post this error in {$link} tab.


## About popup
about-app = About
about-app-tooltip = View the information about the application.
about-app-version = Version: {$version}
about-app-desc = A lightweight tool for managing {$I2Localization} assets exported via {$UABEA} as dump files with ease.


## File section
file-menu-title = File
open-button = Open
open-tooltip = Open a UABEA dump file.
open-recent-menu = Recent...
open-recent-tooltip = Open recently opened {$file_name}.
clear-recent-button = Clear Recently Opened
clear-recent-tooltip = Clear the list of recently opened files.
save-button = Save
save-tooltip = Save the UABEA dump file.
save-as-button = Save As...
save-as-tooltip = Save the UABEA dump file as...
exit-app-button = Exit
exit-app-tooltip = Exit the application.


## Edit section
edit-menu-title = Edit
undo-button = Undo
undo-tooltip = Undo the edit.
redo-button = Redo
redo-tooltip = Redo the edit.
cut-button = Cut
cut-tooltip = Cut the content of selected row.
copy-button = Copy
copy-tooltip = Copy the content of selected row.
paste-button = Paste
paste-tooltip = Paste clipboard's entry to selected row.
delete-button = Delete
delete-tooltip = Delete the content of selected row.


## View section
view-menu-title = View
refresh-table-button = Refresh Table
refresh-table-tooltip = Refresh the table manually.
theme-menu = Theme
theme-menu-tooltip = This theme is compatible with your OS.
app-language-menu = Language
check-updates-now-button = Check for Updates Now
check-updates-now-tooltip = Manually check for available updates.
check-updates-startup-button = Check for Updates on Startup
check-updates-startup-tooltip = Automatically check for updates when the application starts.


## Tools section
tools-menu-title = Tools
export-translations-button = Export Translations
export-translations-tooltip = Export translations to CSV/TSV file.
import-translations-button = Import Translations
import-translations-tooltip = Import translations from CSV/TSV file.
manage-languages-button = Manage Languages
manage-languages-tooltip = Manage languages in the table.


## Popup titles
error-title = Error
warning-title = Warning
information-title = Information
question-title = Confirmation

## Popup messages
warning-no-file = No file loaded.
warning-file-not-found = File does not exist: {$file_path}.
error-invalid-file = Invalid file.
error-invalid-extension = Invalid file extension.
error-no-terms-language = No terms/languages found!
error-unknown-import-type = Unknown import type: {$type}.

error-save-failed = Failed to save: {$error}.
error-invalid-data = Invalid data format: {$error}.
error-file-access = File access error: {$error}.

warning-no-languages = No languages defined in the file.
warning-invalid-language-format = Invalid language format.
warning-language-exists = Language '{$language}' already exists!

question-save-file-open = Would you like to save changes to the file?
question-save-file-exit = Would you like to save changes before exiting?


## File explorer titles
open-title = Open
save-title = Save

## File extension names
all-files = All files
text-file = Text documents
json-file = JSON files
dump-file = UABEA dump files
csv-file = CSV files
tsv-file = TSV files


## Status bar messages
opening-file = Opening file: {$file_path}
opened-file = File opened: {$file_path}
saving-file = Saving file: {$file_path}
saved-file = File saved: {$file_path}


## Update module
update-available-title = Update Available
update-available-message = A new release is available: {$name}
changelog-label = 📝 Changelog:
download-update-button = Download Now
skip-update-button = Skip For Now
install-now-button = Install Now
install-later-button = Install Later
question-install-pending-update = A previously downloaded update (version {$version}) is ready to install. Would you like to install it now?
question-delete-pending-update = Would you like to delete the downloaded update file?
installing-update = Installing update...
checking-for-updates = Checking for updates...
downloading-update = ⏳ Downloading update...
download-complete = ✅ Download complete!
download-error = ❌ Download failed!
info-no-updates-available = You are using the latest version!
error-check-updates-failed = Failed to check for updates: {$error}
error-download-failed = Download failed: {$error}
error-install-failed = Installation failed: {$error}


## Export module

export-translations-title = Export Translations
export-languages-label = Select languages to export:
select-all-button = Select all
deselect-all-button = Deselect all
export-button = Export
export-button-disabled = Select at least one language to export.

# Status bar message
exporting-file-data = Exporting data from {$file_name}...

## Helper text
and-text = {$langs} and {$last_lang}.

## Popup messages
warning-no-terms-found = No terms found to export.
error-export-file = Failed to export file: {$error}
warning-no-available-languages = No available languages to export.
warning-no-languages-selected = No languages selected to export.
error-processing-term = Error processing term #{$num} ({$term_name}): {$error}
error-export-languages = Failed to export languages: {$error}
info-success-export = Successfully exported {$translation_num ->
    [one] {$translation_num} translation
    *[other] {$translation_num} translations
} for {$language_num ->
    [one] {$language_num} language
    *[other] {$language_num} languages
} to {$file_name}.

    Exported languages: {$languages}


## Import module

import-translations-title = Import Translations
import-select-languages = Select which languages you want to import to:
imported-language-label = <b>Imported Language</b>
import-to-language-label = <b>Target Language</b>
auto-map-button = Auto-Map
clear-mappings-button = Clear All
do-not-import-option = Do not import
import-button = Import
import-button-disabled = Select at least one target language to import.
importing-progress-label = Checking translations to import...
importing-progress-title = Importing

## Status bar messages
importing-file-data = Importing data from {$file_name}...
importing-file-canceled = Import from {$file_name} canceled.
imported-data-success = Successfully imported data from {$file_name}.

## Popup messages
error-no-headers = The file is empty or has no headers.
error-missing-headers = The file is missing required columns: {$headers}.
error-no-langauges-columns = The file does not contain any language columns.
error-no-available-model = No table model available.
error-import-file = Failed to import file: {$error}.
info-no-imported = No new translations to import.
info-success-import = Successfully imported translations.

    Updated {$count ->
        [one] {$count} translation
        *[other] {$count} translations
    }.


## Manage languages module

-ml-title-term = Language Manager
ml-title = {-ml-title-term}
ml-warning-desc = NOTE: Not every videogame has a dynamic language management.
    Some of them might have their own hardcoded or Unity-based language management.
ml-languages-label = Languages:
ml-reorder-label = Reorder
ml-move-up-button = Move up
ml-move-down-button = Move down
ml-details-label = Details
ml-manage-label = Manage
ml-add-language = Add language
ml-remove-language = Remove language
ml-languages-count = {$count ->
    [one] {$count} language
    *[other] {$count} languages
}

lang-flag-enabled = Enabled
lang-flag-disabled = Disabled

## Add language dialog

add-language-title = {-ml-title-term}: Add Language
add-language-selection = Language Selection
add-language-manually = Enter manually...
add-language-details = Language Details
add-language-native-name = Use native name
add-language-name = Name:
add-language-code = Code:
add-language-flag = State:
add-language-initialize = Initialize with
add-language-initialize-option-1 = Empty strings
add-language-initialize-option-2 = Copy strings from:

## Popup messages
confirm-language-removal = Are you sure you want to remove '{$language}' language?

    This action cannot be undone.
warning-invalid-language = Please enter both a language name and code.
warning-duplicate-language = A language named '{$name}' already exists.
warning-duplicate-code = A language with the code '{$code}' already exists.
warning-reserved-names = The name or code you entered is reserved. Please use a different one.
warning-invalid-code-letters = Code of the language should contain ASCII letters only.
