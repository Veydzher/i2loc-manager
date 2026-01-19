# I2 Localization Manager

<p align="center">
    <img src="assets/icon.ico" alt="Logo" width="128" height="128">
</p>

<p align="center">
    A lightweight tool for managing <a href="http://inter-illusion.com/tools/i2-localization/">I2 Localization</a> assets exported via <a href="https://github.com/nesrak1/UABEA">UABEA</a> as dump files with ease.
</p>

<p align="center">
    <a href="#current-features">Current Features</a> •
    <a href="#planned-features">Planned Features</a> •
    <a href="#contributing">Contributing</a>
</p>

<p align="center">
    <img src="assets/docs/i2loc-manager-thumbnail.png" alt="I2 Localization Manager Thumbnail" width="720"/>
</p>

## Current Features

- Support for `.txt` and `.json` [UABEA](https://github.com/nesrak1/UABEA) dump files
- Conversion between `.txt` and `.json`
- Support for import and export of `CSV` and `TSV` files
- Modify language details directly using `Tools -> Language Manager`

## Planned Features

- I2 Localization metadata options menu
- Pluralization translation tags handling [**i2p_**...]
- Specialization translation tags handling [**i2s_**...]

## Contributing

Contributions are welcome!
Please feel free to submit [issues](https://github.com/Veydzher/i2loc-manager/issues), feature requests, or pull requests.

Here is a guide on how to set up everything:

Recommended Python version: 3.10+

1. **Clone the repository:**
```bash
git clone https://github.com/YOUR_USERNAME/i2loc-maneger.git
cd i2loc-maneger
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
python i2loc_manager.py
```

## Dependencies
- **PySide6** - GUI Framework
- **fluent** - Localization Framework

## License

For the complete licensing terms, please read the [license](https://github.com/Veydzher/i2loc-manager/blob/main/LICENSE).

---

<p align="center">
  Made with ❤️ using Python by veydzh3r
</p>