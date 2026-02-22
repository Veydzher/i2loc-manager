# I2 Localization Manager

<p align="center">
    <img src="assets/icon.ico" alt="Logo" width="128" height="128">
    <br><br>
    A lightweight tool for managing <a href="http://inter-illusion.com/tools/i2-localization/">I2 Localization</a> assets exported via <a href="https://github.com/nesrak1/UABEA">UABEA</a> as dump files with ease.
    <br><br>
    <a href="https://github.com/Veydzher/i2loc-manager/releases/latest/download/i2-localization-manager.zip"><img alt="Download Windows Build" src="https://img.shields.io/badge/windows-download-first"></a>
    <a href="https://github.com/Veydzher/i2loc-manager/releases"><img alt="GitHub Downloads" src="https://img.shields.io/github/downloads/Veydzher/i2loc-manager/total"></a>
</p>

<p align="center">
    <a href="#current-features">Current Features</a> •
    <a href="#planned-features">Planned Features</a> •
    <a href="#contributing">Contributing</a> •
    <a href="#license">License</a>
</p>

<p align="center">
    <img src="assets/docs/i2loc-manager-thumbnail.png" alt="I2 Localization Manager Thumbnail" width="720"/>
</p>

## Current Features

- Support of `.txt` and `.json` [UABEA](https://github.com/nesrak1/UABEA) dump files
- Conversion between `.txt` and `.json`
- Support of `CSV` and `TSV` files import and export
- Modification of language details in `Tools -> Language Manager`

## Planned Features

- I2 Localization metadata options menu
- Proper handling of `Languages_Touch` array
- Pluralization translation tags handling [**i2p_**...]
- Specialization translation tags handling [**i2s_**...]

## Contributing

Contributions are welcome!
Please feel free to submit [issues](https://github.com/Veydzher/i2loc-manager/issues), feature requests, or pull requests.

Here is a guide on how to set up everything:

Recommended Python version: 3.10+

1. **Fork and clone the repository:**
```bash
git clone https://github.com/YOUR_USERNAME/i2loc-manager.git
cd i2loc-manager
```

2. **Create a virtual environment:**
```bash
python -m venv .venv
```

3. **Activate the virtual environment:**

Windows:
```bash
.venv\Scripts\activate
```

macOS/Linux:
```bash
source .venv/bin/activate
```

4. **Install dependencies:**
```bash
pip install -r requirements.txt
```

5. **Run the program:**
```bash
python main.py
```

## Dependencies
- **PySide6** - GUI Framework
- **fluent** - Localization Framework
- **requests** - HTTP Requests

## License

For the complete licensing terms, please read the [license](https://github.com/Veydzher/i2loc-manager/blob/main/LICENSE).

---

<p align="center">
  Made with ❤️ by veydzh3r
</p>