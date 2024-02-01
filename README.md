# DT UI
## Overview

This is streamlit demo for Barnes with ChatGPT.

## Installation

1. Clone the repository

```bash
git clone $URL
```

2. Move to project directory

```bash
cd DT_UI
```

3. Create a `.env` file inside the `src` directory and add below variable environments:

```bash
OPENAI_API_KEY={OPENAI_API_KEY}
```

4. The project uses poetry to manage dependency
    - To initialize project
        ```
        poetry shell
        ```
    - To install existing packages
        ```
        poetry install
        ```
    - To add new packages
        ```
        poetry add
        ```

5. Run the Streamlit application
    - The project uses docker compose to run external dependencies and streamlit application
        ```
        docker-compose up
        ```

## Usage
Once the application is running, you can interact with it by following the on-screen instructions at `http://localhost:8000`
