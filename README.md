# Solution Architecture Case Studies

This repository contains architecture diagrams created using [Diagrams](https://diagrams.mingrammer.com/) - a Python library for drawing cloud system architecture diagrams as code.

## Project Structure

Each case study is organized in its own numbered directory:

```
.
├── 01/              # Case Study 01
│   ├── *.py         # Python diagram scripts
│   ├── diagrams/    # Generated diagrams for this case study
│   └── README.md    # Case study documentation
├── 02/              # Case Study 02
│   ├── *.py
│   ├── diagrams/    # Generated diagrams for this case study
│   └── README.md
├── generate-diagrams.sh
├── docker-compose.yml
└── Dockerfile
```

## Quick Start

**Prerequisites:** Docker and Docker Compose installed
- [Install Docker Desktop](https://www.docker.com/products/docker-desktop) (includes Docker Compose)

**Generate diagrams:**
```bash
./generate-diagrams.sh
```

That's it! The script uses Docker Compose to:
- Build the Docker image with all dependencies (first time only)
- Find all Python files in the case study directory
- Generate diagrams for each Python file
- Save them to `<case_study_number>/diagrams/`
- Automatically clean up when done

## Usage

**Generate diagrams for the latest case study (default):**
```bash
./generate-diagrams.sh
```

**Generate diagrams for a specific case study:**
```bash
./generate-diagrams.sh 01
./generate-diagrams.sh 02
```

**Generate diagrams for all case studies:**
```bash
./generate-diagrams.sh all
```

Diagrams are saved in each case study's `diagrams/` directory (e.g., `01/diagrams/`, `02/diagrams/`).

**Note:** The first run will take a bit longer as it builds the Docker image. Subsequent runs will be faster.

## Adding a New Case Study

1. **Create a new numbered directory:**
   ```bash
   mkdir 02
   ```

2. **Add your Python diagram script(s):**
   ```bash
   # Create your diagram script
   vim 02/my_architecture.py
   ```

3. **Create a README for the case study:**
   ```bash
   vim 02/README.md
   ```

4. **Generate the diagrams:**
   ```bash
   ./generate-diagrams.sh 02
   ```

The script will automatically find all `.py` files in the directory and generate diagrams for each one, saving them to `02/diagrams/`.

## How to Display Diagrams on GitHub

1. **Generate the diagrams:**
   ```bash
   ./generate-diagrams.sh 01
   ```

2. **Commit the PNG files:**
   ```bash
   git add 01/diagrams/*.png
   git commit -m "Add case study 01 diagrams"
   git push
   ```

3. **Reference in README** - Add the image to your README.md using Markdown:
   ```markdown
   ![Case Study 01 Diagram](01/diagrams/demo_diagram.png)
   ```

The diagrams will automatically render in your GitHub repository!

#
