# EPUB Translator Reader

The EPUB Translator Reader is a web-based application designed to read EPUB files with word-for-word translations, making it easier to enjoy books in foreign languages while learning new vocabulary and grammar. Unlike traditional flashcards, this tool lets you dive straight into reading, naturally reinforcing important words through their frequent appearance in the text and introducing basic grammar as you go. It supports multiple languages and integrates with translation services like Google Translate and LibreTranslate for a seamless experience.

## Features

- **Word-for-Word Translations**: View translations below each word or phrase as you read EPUB files, perfect for language learners.
- **Engaging Learning Experience**: Start reading immediately without memorizing flashcards, with frequent words reinforced naturally and grammar learned in context.
- **Multi-Language Support (in progress)**: Select from various source and target languages. Currently, a Spanish-German dictionary is included; other dictionaries can be generated using the `dictionaries/generate/convert_enwiktionary.py` script.
- **Dark Mode**: Switch between light and dark themes for comfortable reading.
- **Translation Caching**: Cache translations locally to improve performance and reduce API calls.
- **Integration with Translation Services**: Use Google Translate or LibreTranslate for words not found in the dictionary.
- **Customizable Settings**: Adjust the number of translations per word and enable/disable translation services.

## Screenshot

![EPUB Translator Reader Screenshot](screenshot.png)

## Setup

To set up and run the EPUB Translator Reader, follow these steps:

1. **Serve the Directory**:
   - Use a local server to serve the directory containing the `index.html`. You can use Python's built-in HTTP server:
     ```bash
     python -m http.server 8000
     ```
   - Access the application at `http://[::]:8000/`.

2. **Download Wiktionary Extracts**:
   - The application uses dictionaries generated from Wiktionary extracts. Download the extracts from:
     - [Wikimedia Dumps](https://dumps.wikimedia.org/)
     - For English Wiktionary (which includes many languages as translations): [enwiktionary-latest-pages-articles-multistream.xml.bz2](https://dumps.wikimedia.org/enwiktionary/latest/enwiktionary-latest-pages-articles-multistream.xml.bz2)

3. **Process Wiktionary Extracts**:
   - Use the `dictionaries/generate/convert_enwiktionary.py` script to process the downloaded extracts (the plain XML) and generate the necessary dictionary files.
   - Place the generated dictionary files in the `dictionaries/` directory.

4. **Optional: Set Up LibreTranslate**:
   - To use LibreTranslate for additional translations, follow the instructions in the [Translation Services](#translation-services) section.

## Usage

1. **Select Languages**:
   - Choose the source language of the book and the target language for translations from the dropdown menus.

2. **Load an EPUB File**:
   - Click on "Select File" and choose your EPUB file.

3. **Adjust Settings**:
   - Optionally, set the maximum number of translations per word.
   - Enable or disable Google Translate and LibreTranslate as needed.

4. **Read the Book**:
   - The book content will be displayed with translations. Use the navigation buttons to move between pages.
   - Toggle translation visibility and the settings panel using the respective buttons.

5. **Interact with Translations**:
   - Click on a word to open a popup with more translation details.
   - Hover over a word to see a floating box with translations.

## Translation Services

The EPUB Translator Reader supports integration with Google Translate and LibreTranslate to provide translations for words not found in the dictionary.

### Google Translate

- **Enable Google Translate**:
  - Check the "Enable Google Translate" checkbox.
  - Enter your Google Translate API key in the provided field.
- **Usage**:
  - The application will use Google Translate to fetch translations for words not found in the dictionary.

### LibreTranslate

- **Set Up LibreTranslate**:
  1. Create a directory for LibreTranslate:
     ```bash
     mkdir libretranslate
     cd libretranslate
     ```
  2. Set up a virtual environment:
     ```bash
     uv venv
     source .venv/bin/activate
     ```
  3. Install dependencies:
     ```bash
     brew install icu4c pkg-config # for MacOS
     # sudo apt install -y libicu-dev pkg-config # for Linux
     export PATH="/opt/homebrew/opt/icu4c/bin:$PATH"
     export PATH="/opt/homebrew/opt/icu4c/sbin:$PATH"
     export PKG_CONFIG_PATH="/opt/homebrew/opt/icu4c/lib/pkgconfig:$PKG_CONFIG_PATH"
     uv pip install "libretranslate>=1.6.0" --no-deps
     uv pip install argos-translate-files flask flask_babel flask_session flask_swagger flask_swagger_ui redis apscheduler langdetect lexilang expiringdict waitress
     ```
  4. Run LibreTranslate with the desired languages:
     ```bash
     libretranslate --load-only es,de,en
     ```
- **Enable LibreTranslate**:
  - Check the "Enable LibreTranslate" checkbox in the application.
- **Usage**:
  - The application will use LibreTranslate to fetch translations for words not found in the dictionary.

## Dictionary Management

- **Cache**:
  - The application caches translations locally to improve performance.
  - Clear the cache using the "Clear Dictionary Cache" button if needed.
- **Export Cache**:
  - After using the application, you can export the cached translations via the browser console:
    ```javascript
    const dictLines = [];
    for (const [original, translations] of state.dictionary.cacheTranslations) {
      for (const translation of translations) {
        dictLines.push(`${original}\t${translation}`);
      }
    }
    console.log(dictLines.join('\n'));
    ```
  - Append the exported translations to the dictionary files in `dictionaries/dict_<srclang>-<targetlang>_more.txt`.
- **Dictionary Files**:
  - Dictionaries are stored in the `dictionaries/` directory with filenames like `dict_<srclang>-<targetlang>.txt`.
  - Additional entries can be manually added to `dict_<srclang>-<targetlang>_more.txt` files.

## License Information

The dictionaries used in this application are derived from Wiktionary extracts, which are licensed under the [Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0) License](https://creativecommons.org/licenses/by-sa/4.0/). For more details, see the [Wikimedia License Information](https://dumps.wikimedia.org/legal.html).

This project is licensed under the [GNU General Public License 3 (GPLv3)](https://www.gnu.org/licenses/gpl-3.0.de.html).

## Troubleshooting

- **Translation Issues**:
  - If translations are not appearing, ensure that the dictionary files are correctly placed in the `dictionaries/` directory.
  - Verify that the source and target languages are correctly selected.
- **Performance**:
  - For large EPUB files, the initial loading and translation process may take some time. Please be patient while the content is being processed.
- **API Keys**:
  - Ensure that you have entered a valid Google Translate API key if you have enabled Google Translate.
- **LibreTranslate**:
  - Make sure that LibreTranslate is running locally and that the correct languages are loaded.

## Credits

This application uses the following third-party libraries and resources:
- [Tailwind CSS](https://tailwindcss.com) for styling.
- [JSZip](http://stuartk.com/jszip) for unpacking EPUB files.
- [LibreTranslate](https://github.com/LibreTranslate/LibreTranslate) for local translation services.
- [Wiktionary](https://en.wiktionary.org) for dictionary data.
