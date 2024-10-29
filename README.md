# Garbage Bin Detection System

This project implements an automated garbage bin detection system using YOLOv8 object detection and MQTT communication. It processes camera images to detect garbage bins within a specified zone and reports their status through MQTT messages.

## Features

- Real-time garbage bin detection using YOLOv8 World model
- Automatic model download and management
- Zone-based detection to focus on specific areas
- MQTT integration for status reporting and image sharing
- Non-maximum suppression for improved detection accuracy
- Base64 encoded image transmission
- Configurable detection parameters
- Home Assistant integration for smart home automation
- Docker support with GPU acceleration
- Crontab support for automated execution

## Requirements

- Python 3.x
- Dependencies (installed via pip):
  - paho-mqtt
  - requests
  - ultralytics
  - opencv-python
  - python-dotenv
  - CLIP
- For Docker deployment:
  - Docker and Docker Compose
  - NVIDIA GPU with appropriate drivers (for GPU acceleration)
  - NVIDIA Container Toolkit

## Installation

### Standard Installation

1. Clone the repository:
```bash
git clone [repository-url]
```

2. Create and activate a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required dependencies:
```bash
pip install -r requirements.txt
```

4. Copy the configuration files:
```bash
cp .env.example .env
cp configuration.yaml.example configuration.yaml
```

5. Configure the environment variables in `.env`:
```
MQTT_BROKER=your_mqtt_broker
MQTT_PORT=your_mqtt_port
MQTT_TOPIC=camera1/bins/result
MQTT_TOPIC_IMAGE=camera1/bins/picture
IMAGE_LINK=your_camera_image_url
```

### Docker Installation

1. Ensure Docker, Docker Compose, and NVIDIA Container Toolkit are installed
2. Create the installation directory:
```bash
sudo mkdir -p /opt/dc
```
3. Copy project files to the installation directory:
```bash
sudo cp -r * /opt/dc/
```
4. Create required directories:
```bash
sudo mkdir -p /opt/dc/mounts/yolo/input /opt/dc/mounts/yolo/output
```
5. Start the container:
```bash
cd /opt/dc && docker-compose up -d
```

The Docker setup includes:
- GPU acceleration support
- Persistent storage for input/output
- Automatic restart capability
- IPC host sharing for improved performance

## Configuration

### Environment Variables

- `MQTT_BROKER`: MQTT broker address
- `MQTT_PORT`: MQTT broker port
- `MQTT_TOPIC`: Topic for publishing detection results
- `MQTT_TOPIC_IMAGE`: Topic for publishing processed images
- `IMAGE_LINK`: URL of the camera image to process

### MQTT Configuration

The `configuration.yaml` file defines the MQTT sensors and image configuration:
- Image sensor for displaying the processed image
- Numeric sensor for total bins detected
- List sensors for found and missing bins
- JSON sensor for detailed detection results

## Home Assistant Integration

This project is designed to work seamlessly with Home Assistant. The MQTT sensors defined in `configuration.yaml` will automatically appear in your Home Assistant instance once properly configured. You can use these sensors to:

- Display the current state of garbage bin detection
- Create automations based on bin presence/absence
- Visualize detection results in your dashboard
- Monitor the system through the processed images

### Setting up in Home Assistant

1. Ensure your MQTT broker is configured in Home Assistant
2. Add the MQTT sensors from `configuration.yaml` to your Home Assistant configuration
3. Restart Home Assistant to load the new sensors
4. The sensors will automatically appear under the device "garbage bin status"

## Usage

### Running with Python

1. Ensure your MQTT broker is running and accessible
2. Configure your environment variables and MQTT settings
3. Run the detection script:
```bash
python main.py
```

### Running with Docker

1. Place your input images in `/opt/dc/mounts/yolo/input`
2. Start the container:
```bash
cd /opt/dc && docker-compose up -d
```
3. Monitor the output in `/opt/dc/mounts/yolo/output`

### Automated Execution with Crontab

To run the script automatically at specified intervals:

1. Copy your Python script to the input directory:
```bash
sudo cp your_script.py /opt/dc/mounts/yolo/input/test.py
```

2. Edit the crontab:
```bash
sudo crontab -e
```

3. Add the following line to run the script (example for running every 5 minutes):
```
*/5 * * * * cd /opt/dc && /usr/bin/docker compose exec yolo /opt/conda/bin/python3 /input/test.py
```

Note: Adjust the timing (*/5) according to your needs. The current setting runs the script every 5 minutes.

The system will:
1. Download the YOLOv8 model if not present
2. Process the image from the specified URL
3. Detect garbage bins within the defined zone
4. Publish results and processed image to MQTT topics

### Detection Results

The system publishes the following information to MQTT:
- Total number of bins detected in the zone
- List of detected bin types
- List of missing bin types
- Processed image with detection visualization

## Project Status

Current project progress and upcoming tasks:

- [x] Create GitHub repository
- [x] Create virtual environment
- [x] Create requirements.txt
- [x] Create .env.example for demo and production
- [x] Upload to git
- [x] Improve README
- [x] Add Docker Compose configuration
- [x] Add crontab execution instructions
- [ ] Extend Home Assistant information

## License

This project is licensed under the terms specified in the LICENSE file.
