import threading
from functools import lru_cache
from pathlib import Path
from typing import Any

from fluent.runtime import FluentLocalization, FluentResourceLoader
from fluent.syntax import FluentParser, ast

from utils.app_config import config
from utils.helpers import pathfind


class AppLocale:
    def __init__(self):
        self.default_locale = "en-US"
        self.locale_dir = Path(pathfind("assets\\l10n"))
        self.cache_size = 512

        self._cache_lock = threading.RLock()
        self._translation_cache = {}
        self._resource_cache = {}

        print(f"[LOCALE] Locale Directory: {self.locale_dir}")

        if not self.locale_dir.exists():
            raise FileNotFoundError(f"[LOCALE] Locale directory not found: {self.locale_dir}")

        self.available_locales = self.get_locales()
        if not self.available_locales:
            raise ValueError(f"[LOCALE] No locale directories found in {self.locale_dir}")

        self._localizer_cache = {}
        self.loader = FluentResourceLoader(str(self.locale_dir / "{locale}"))
        self.current_locale = config.get_config("language") or self.default_locale

        if self.current_locale not in self.available_locales:
            print(f"[LOCALE] Warning: Locale '{self.current_locale}' not found, falling back to '{self.default_locale}' locale.")
            self.current_locale = self.default_locale
            config.set_config("language", self.current_locale)

        self.get_localizer(self.current_locale)
        self._setup_translation_cache()

    def change_locale(self, new_locale: str):
        if new_locale != self.current_locale:
            self.current_locale = new_locale
        else:
            return

        if self.current_locale not in self.available_locales:
            print(f"[LOCALE] Locale '{new_locale}' is not available, falling back to '{self.default_locale}' locale. Available locales: {self.available_locales}")
            self.current_locale = self.default_locale

        self._cached_translate.cache_clear()
        self.get_localizer(self.current_locale)
        config.set_config("language", self.current_locale)

    def _setup_translation_cache(self):
        @lru_cache(maxsize=self.cache_size)
        def _cached_translate(locale: str, msg_id: str, args_tuple: tuple | None):
            localizer = self.get_localizer(locale)
            try:
                args_dict = dict(args_tuple) if args_tuple else {}
                result = localizer.format_value(msg_id, args_dict)

                if result is None or result == msg_id:
                    if msg_id.islower():
                        print(f"[LOCALE] Could not find translation for '{msg_id}' key.")
                    else:
                        print(f"[LOCALE] Could not find key for {repr(msg_id)} translation.")

                    result = f"[{msg_id}]" if msg_id.islower() else msg_id

                return result
            except Exception as e:
                print(f"[LOCALE] Error processing translation for '{msg_id}' key: {str(e)}")
                return f"[{msg_id}]"

        self._cached_translate = _cached_translate

    @staticmethod
    def _get_cache_key(locale: str, msg_id: str, args: dict[str, Any] | None):
        if args:
            args_str = "&".join(f"{k}={v}" for k, v in sorted(args.items()))
            cache_key = f"{locale}:{msg_id}:{args_str}"
        else:
            cache_key = f"{locale}:{msg_id}"

        return cache_key

    def get_localizer(self, locale: str):
        if locale not in self._localizer_cache:
            cache_key = f"resources:{locale}"

            with self._cache_lock:
                if cache_key in self._resource_cache:
                    ftl_files = self._resource_cache[cache_key]
                    print(f"[LOCALE] Using cached resources for '{locale}' locale.")
                else:
                    ftl_files = self.get_ftl_files(locale)
                    self._resource_cache[cache_key] = ftl_files
                    print(f"[LOCALE] Cached resources for {locale} locale.")

            fallback_locales = [locale]
            if locale != self.default_locale:
                fallback_locales.append(self.default_locale)

            self._localizer_cache[locale] = FluentLocalization(fallback_locales, ftl_files, self.loader)
            print(f"[LOCALE] Created and cached localizer for {locale} locale.")

        return self._localizer_cache[locale]

    def get_ftl_files(self, locale: str):
        locale_dir = self.locale_dir / locale

        if not locale_dir.exists():
            print(f"[LOCALE] Warning: Locale directory '{locale_dir}' does not exist.")
            return []

        ftl_files = [f.name for f in locale_dir.glob("*.ftl") if f.is_file()]
        print(f"[LOCALE] Found .ftl files for {locale}: {ftl_files}.")
        return ftl_files

    def tr(self, msg_id: str, args: dict[str, Any] | None = None):
        if not args:
            cache_key = f"{self.current_locale}:{msg_id}"

            with self._cache_lock:
                if cache_key in self._translation_cache:
                    return self._translation_cache[cache_key]

            result = self._cached_translate(self.current_locale, msg_id, None)
            with self._cache_lock:
                self._translation_cache[cache_key] = result
        else:
            args_tuple = tuple(sorted(args.items()))
            result = self._cached_translate(self.current_locale, msg_id, args_tuple)

        return result

    def tr_batch(self, texts: list[str | tuple[str, dict[str, Any]]]):
        results = {}
        cache_misses = []

        with self._cache_lock:
            for text in texts:
                m_id = text[0] if isinstance(text, tuple) else text
                args = text[1] if isinstance(text, tuple) else None

                cache_key = self._get_cache_key(self.current_locale, m_id, args)
                if cache_key in self._translation_cache:
                    results[m_id] = self._translation_cache[cache_key]
                else:
                    cache_misses.append((m_id, args))

        for msg_id, args in cache_misses:
            translation = self.tr(msg_id, args)
            results[msg_id] = translation

        return results

    def get_locales(self):
        try:
            return [d.name for d in self.locale_dir.iterdir() if d.is_dir()]
        except (FileExistsError, PermissionError, OSError) as e:
            raise e from e

    def get_languages(self):
        parser = FluentParser()
        languages = {}

        try:
            for locale_code in self.locale_dir.iterdir():
                ftl_path = self.locale_dir / locale_code / "main.ftl"
                if not ftl_path.is_file():
                    continue

                with open(ftl_path, "r", encoding="utf-8") as f:
                    content = f.read()

                    resource = parser.parse(content)
                    for entry in resource.body:
                        if isinstance(entry, ast.Message) and entry.id.name == "language-name":
                            value = ""

                            for element in entry.value.elements:  # type: ignore
                                if isinstance(element, ast.TextElement):
                                    value += element.value

                            languages[locale_code.name] = value.strip()
                            break
        except Exception as e:
            raise Exception(f"[LOCALE] {str(e)}") from e

        return languages


fluent = AppLocale()
ftr = fluent.tr
