# MMD Bone Renamer

A Blender addon that automatically renames bones between different naming conventions, with special support for translating Japanese MMD (MikuMikuDance) bone names to English using both Google Translate and a static dictionary.

## Features

- Convert between multiple bone naming formats:
  - MMD English
  - MMD Japanese
  - MMD Japanese L/R
  - XNALara
  - DAZ/Poser
  - Blender Rigify
  - Sims 2
  - Motion Builder
  - 3ds Max
  - Type X
  - BEPu

- Japanese to English translation using:
  - Online Google Translate (optional)
  - Built-in static dictionary
  - Intelligent L/R suffix handling
  - Configurable translation timeout

- Additional Features:
  - Optional finger bone renaming
  - Pick armature directly from viewport
  - Bone name display toggle
  - Clean name formatting for Blender compatibility

## Installation

1. Download `BoneRenamer_v1.2.py`
2. In Blender, go to Edit > Preferences > Add-ons
3. Click "Install" and select the downloaded file
4. Enable the addon by checking the box

### Optional: Google Translate Support

To enable online translation:
```bash
pip install googletrans==3.1.0a0
```

## Usage

1. Open the Animation tab in the 3D Viewport's sidebar (press N if hidden)
2. Find the "Bone Renamer" panel
3. Select your armature using the picker or dropdown
4. Choose source and target formats
5. Configure options:
   - Include fingers
   - Use online translation (if available)
   - Set translation timeout
6. Click "Rename Bones" or "Translate Japanese Names"

## Options

- **Source/Target Format**: Choose between different naming conventions
- **Include Fingers**: Toggle finger bone renaming
- **Use Online Translation**: Enable Google Translate for unknown Japanese terms
- **Translation Timeout**: Maximum wait time for online translation

## Supported Bone Types

- Basic body bones (head, neck, spine, etc.)
- Arm and leg bones
- Finger bones
- Common MMD auxiliary bones
- IK bones

## Requirements

- Blender 2.80 or newer
- Python 3.7+
- Internet connection (for online translation feature)

## Known Limitations

- Online translation requires additional package installation
- Some very specific or custom bone names may not be recognized
- Complex bone hierarchies might need manual adjustment after renaming

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## License

This project is licensed under MIT License - see the LICENSE file for details.