# MaiMai Trainer

A desktop application that simulates the SEGA arcade game maimai using computer vision and real-time hand tracking.

## Features

- Virtual MaiMai interface with circular play area
- Real-time hand tracking using webcam
- Gesture recognition for taps and slides
- Timing-based scoring system
- Performance feedback and analysis

## Requirements

- Python 3.x
- Webcam
- Sufficient lighting conditions
- Processing power for real-time video processing

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/maimai-trainer.git
cd maimai-trainer
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the application:
```bash
python src/main.py
```

### Controls
- ESC: Exit the application
- Mouse click: (Future implementation) Select menu options

## Project Structure

```
maimai-trainer/
├── src/                    # Source code
│   ├── main.py            # Main entry point
│   ├── game/              # Game logic
│   ├── vision/            # Computer vision components
│   └── utils/             # Utility functions
├── assets/                # Game assets
│   ├── songs/            # Song files
│   └── patterns/         # Note patterns
└── docs/                 # Documentation
```

## Development Status

Currently in Phase 1: Basic Implementation
- [x] Project setup and documentation
- [ ] Basic game interface
- [ ] Hand tracking integration
- [ ] Simple tap note detection

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 