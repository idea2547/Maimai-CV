# MaiMai Trainer Project Documentation

## Project Overview
The MaiMai Trainer is a desktop application that simulates the SEGA arcade game maimai using computer vision and real-time hand tracking. This project combines OpenCV, MediaPipe, and Pygame to create an interactive training environment where players can practice maimai patterns without requiring the actual arcade machine.

## Core Features
1. Virtual MaiMai Interface
   - Circular play area mimicking the arcade layout
   - Animated notes moving from center to edge
   - Visual feedback for hits and misses

2. Hand Tracking System
   - Real-time hand detection using MediaPipe
   - Gesture recognition for taps and slides
   - Coordinate mapping from webcam to virtual play area

3. Scoring and Feedback
   - Timing-based scoring system
   - Real-time performance feedback
   - Post-game analysis and tips

## Technical Requirements

### Hardware Requirements
- Webcam (standard laptop camera or better)
- Decent lighting conditions
- Sufficient processing power for real-time video processing

### Software Dependencies
- Python 3.x
- OpenCV (cv2)
- MediaPipe
- Pygame
- NumPy (for calculations)

### Installation
```bash
pip install opencv-python
pip install mediapipe
pip install pygame
pip install numpy
```

## Project Structure
```
maimai-trainer/
├── src/
│   ├── main.py              # Main application entry point
│   ├── game/
│   │   ├── interface.py     # Pygame interface implementation
│   │   ├── notes.py         # Note pattern and animation logic
│   │   └── scoring.py       # Scoring system implementation
│   ├── vision/
│   │   ├── hand_tracker.py  # Hand detection and tracking
│   │   └── gesture.py       # Gesture recognition logic
│   └── utils/
│       ├── config.py        # Configuration settings
│       └── helpers.py       # Utility functions
├── assets/
│   ├── songs/              # Song files (WAV format)
│   └── patterns/           # Note pattern files (JSON)
├── docs/
│   └── context.md          # Project documentation
└── README.md               # Project overview and setup instructions
```

## Implementation Details

### Game Interface
- Circular play area with 300px radius
- Notes spawn from center and move outward
- Visual feedback for hits and misses
- Score display and combo counter

### Hand Tracking
- Uses MediaPipe's Hand module for hand landmark detection
- Tracks index finger tip (landmark 8) for primary interaction
- Maps webcam coordinates to virtual play area
- Calibration system for accurate position mapping

### Note Types
1. Tap Notes
   - Simple circular notes
   - Must be tapped within timing window
   - Hitbox radius: 50 pixels

2. Slide Notes (Future Implementation)
   - Continuous movement tracking
   - Path-based scoring
   - Multiple checkpoints

### Scoring System
- Perfect: ±50ms timing window
- Great: ±150ms timing window
- Good: ±200ms timing window
- Miss: Outside timing window or wrong position

## Development Roadmap

### Phase 1: Basic Implementation
- [x] Project setup and documentation
- [ ] Basic game interface
- [ ] Hand tracking integration
- [ ] Simple tap note detection

### Phase 2: Core Features
- [ ] Complete scoring system
- [ ] Note pattern loading
- [ ] Basic song integration
- [ ] Performance feedback

### Phase 3: Advanced Features
- [ ] Slide note implementation
- [ ] Practice mode
- [ ] Performance analysis
- [ ] Custom pattern creation

### Phase 4: Polish
- [ ] UI/UX improvements
- [ ] Performance optimization
- [ ] Additional song support
- [ ] User settings

## Technical Challenges and Solutions

### Challenge 1: Hand Detection Accuracy
**Problem**: Inconsistent hand detection in varying lighting conditions
**Solution**: 
- Implement lighting calibration
- Adjust MediaPipe confidence thresholds
- Use multiple frames for gesture confirmation

### Challenge 2: Coordinate Mapping
**Problem**: Inaccurate mapping between webcam and virtual play area
**Solution**:
- Implement calibration system
- Use perspective transformation
- Add dynamic adjustment based on hand position

### Challenge 3: Timing Accuracy
**Problem**: Input lag and timing inconsistencies
**Solution**:
- Implement frame timing system
- Use high-precision timers
- Buffer input processing

## Future Enhancements
1. Multi-hand support for complex patterns
2. Machine learning-based gesture recognition
3. Online leaderboards
4. Custom song and pattern creation tools
5. VR/AR integration possibilities

## Contributing
Contributions are welcome! Please read our contributing guidelines and submit pull requests to our repository.

## License
This project is licensed under the MIT License - see the LICENSE file for details. 